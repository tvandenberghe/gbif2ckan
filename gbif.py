import urlparse

from collections import namedtuple

from slugify import slugify
import requests

from conf import *

Dataset = namedtuple("Dataset", "publishing_organization_key title description uuid dataset_type")


# TODO: Test various return values
# TODO: Create a class for Dataset

MAX_DATASET_NAME_LENGTH = 100  # Ckan limitation

class Group(object):
    def __init__(self, title):
        self.title = title
        self.name = slugify(self.title)
        self.attached_datasets = []

    def create_in_ckan(self):
        # Document is incorrect regarding packages: we need an id parameter, that in fact receive the dataset name... confusing.
        params = {'name': self.name,
                  'title': self.title,
                  'packages': [{'id': _dataset_title_to_name(dataset.title)} for dataset in self.attached_datasets]
                  }

        r = make_ckan_api_call("api/action/group_create", params)
        return r['success']

    def purge_ckan(self):
        # Purge the group whose name is self.name
        r = make_ckan_api_call("api/action/group_purge", {'id': self.name})
        return r['success']

    def attach_dataset(self, dataset):
        self.attached_datasets.append(dataset)

    @classmethod
    def purge_all(cls):
        groups = cls.get_existing_groups_ckan()
        for g in groups:
            g.purge_ckan()

    @classmethod
    def get_existing_groups_ckan(cls):
        r = make_ckan_api_call("api/action/group_list", {'all_fields': True})

        return [cls(res['title']) for res in r['result']]

class OrganizationContact(object):
    def __init__(self, first_name, last_name, email_addresses, contact_type, phone_numbers):
        self.first_name = first_name
        self.last_name = last_name
        self.email_addresses = email_addresses
        self.contact_type = contact_type
        self.phone_numbers = phone_numbers

    @classmethod
    def from_gbif_json(cls, json):
        fn = json.get('firstName', None)
        ln = json.get('lastName', None)
        email = json.get('email', None)
        contact_type = json.get('type', None)
        phone = json.get('phone')

        return cls(fn, ln, email, contact_type, phone)


    def for_display(self):
        # Returns a tuple of strings: (contact_type, contact_info)

        # Contact types comes with values such as TECHNICAL_POINT_OF_CONTACT, make them human-friendly
        human_readable_contact_type = self.contact_type.replace('_', ' ').capitalize()

        if self.email_addresses:
            email_list = "({add})".format(add=", ".join(self.email_addresses))
        else:
            email_list = ""

        if self.phone_numbers:
            phone_list = "{p}".format(p=", ".join(self.phone_numbers))
        else:
            phone_list = ""

        contact_details = u"{fn} {ln} {email} {phone}".format(fn=self.first_name,
                                                              ln=self.last_name,
                                                              email=email_list,
                                                              phone=phone_list)

        return (human_readable_contact_type, contact_details)


class Organization(object):
    def __init__(self, key, title, description=None, homepage='', city=None, lat=None, lon=None, contacts=None):
        self.key = key
        self.title = title
        self.description = description
        self.name = slugify(self.title)
        self.homepage = homepage
        self.city = city
        self.lat = lat
        self.lon = lon

        self.contacts = contacts

    def create_in_ckan(self):

        extras = [{'key': 'Homepage', 'value': self.homepage}]

        if self.city:
            extras.append({'key': 'City', 'value': self.city})

        if self.lat:
            extras.append({'key': 'Latitude', 'value': self.lat})

        if self.lon:
            extras.append({'key': 'Longitude', 'value': self.lon})

        for c in self.contacts:
            contact_type, contact_details = c.for_display()

            # TODO: do we have an error if several contact have the same contact type?
            extras.append({'key': contact_type,
                           'value': contact_details})

        params = {'name': self.name,
                  'id': self.key,
                  'title': self.title,
                  'image_url': ORGANIZATION_LOGOS.get(self.key, ''),

                  # API documentation about extras is unclear, but this works:
                  'extras': extras
                   }

        if self.description:
            params['description'] = self.description

        r = make_ckan_api_call("api/action/organization_create", params)
        return r['success']

    @classmethod
    def from_gbif_api(cls, uuid):
        r = requests.get("http://api.gbif.org/v1/organization/{uuid}".format(uuid=uuid))

        result = r.json()

        contacts = [OrganizationContact.from_gbif_json(c) for c in result.get('contacts', [])]

        return cls(uuid,
                   result['title'],
                   result.get('description', None),
                   result['homepage'][0],
                   result.get('city', None),
                   result.get('latitude', None),
                   result.get('longitude', None),
                   contacts)

    @classmethod
    def purge_all(cls):
        orgs = cls.get_existing_organizations_ckan()
        for org in orgs:
            org.purge_ckan()

    def purge_ckan(self):
        r = make_ckan_api_call("api/action/organization_purge", {'id': self.key})
        return r['success']

    @classmethod
    def get_existing_organizations_ckan(cls):
        r = make_ckan_api_call("api/action/organization_list", {'all_fields': True})
        return [cls(res['id'], res['title']) for res in r['result']]


def make_ckan_api_call(action_url, params=None):
    if not params:
        params = {}

    url = urlparse.urljoin(CKAN_INSTANCE_URL, action_url)
    headers = {'Authorization': ADMIN_API_KEY}

    r = requests.post(url, json=params, headers=headers)
    result = r.json()
    return result

def _dataset_title_to_name(title):
    return slugify(title)[:MAX_DATASET_NAME_LENGTH]

def create_dataset(dataset, all_organizations):
    params = {'title': dataset.title,
              'name': _dataset_title_to_name(dataset.title),
              'notes': dataset.description,
              'owner_org': all_organizations[dataset.publishing_organization_key].name,
              'url': urlparse.urljoin("http://www.gbif.org/dataset/", dataset.uuid),

              # Having difficulties adding extras to the dataset.
              # So far, it works IF the extras parameter is not named extras (myextras is good), and a dict
              # (not a list of dicts) is passed. It is, however, not shown in the web interface later...
              #'extras': [{'dataset_type': dataset.dataset_type}]


              # A Heavy but perfectly working solution: add the field via a plugin like in the tutorial:
              # http://docs.ckan.org/en/latest/extensions/adding-custom-fields.html
              # Then pass the parameter as a first-class one (title, name, ...) (no list of dicts: just a key and value)
              'dataset_type': dataset.dataset_type
              }

    r = make_ckan_api_call("api/action/package_create", params)
    return r['success']


def get_existing_datasets_ckan():
    # Return list of strings (dataset names)
    r = make_ckan_api_call("api/action/package_list", {'all_fields': True})

    return r['result']

def purge_all_datasets():
    for dataset_name in get_existing_datasets_ckan():
        purge_dataset(dataset_name)

def purge_dataset(dataset_name_or_id):
    r = make_ckan_api_call("api/action/dataset_purge", {'id': dataset_name_or_id})
    return r['success']

def gbif_get_uuids_of_all_deleted_datasets():
    """

    :rtype: set
    """
    uuids = set()

    LIMIT = 50
    offset = 0

    while True:
        params = {"limit": LIMIT, "offset": offset}
        r = requests.get("http://api.gbif.org/v1/dataset/deleted/", params=params)

        response = r.json()

        for result in response['results']:
            uuids.add(result['key'])

        if response['endOfRecords']:
            break

        offset = offset + LIMIT

    return uuids

def get_all_datasets_belgium():
    LIMIT=20
    datasets = []
    offset = 0

    while True:
        params={"country":"BE", "limit": LIMIT, "offset": offset}
        r = requests.get("http://api.gbif.org/v1/dataset", params=params)
        response = r.json()

        for result in response['results']:
            try:
                description = result['description']
            except KeyError:
                description = ''

            datasets.append(Dataset(publishing_organization_key=result['publishingOrganizationKey'],
                                    title=result['title'],
                                    description=description,
                                    uuid=result['key'],
                                    dataset_type=result['type']))

        if response['endOfRecords']:
            break

        offset = offset + LIMIT
    return datasets


def main():
    # Get all datasets published in Belgium
    print "Get Datasets information from GBIF..."
    datasets = get_all_datasets_belgium()
    print "Get list of deleted datasets (to ignore)..."
    uuids_to_ignore = gbif_get_uuids_of_all_deleted_datasets()
    datasets = [d for d in datasets if d.uuid not in uuids_to_ignore]

    # Let's also retreive data about linked organizations
    print "Get information about linked (publishing) organizations"
    organizations = {}
    for dataset in datasets:
        organization_key = dataset.publishing_organization_key
        if not organization_key in organizations:
            organizations[organization_key] = Organization.from_gbif_api(organization_key)

    # TODO: Add an option to purge all datasets and organizations prior to insertion

    print "CKAN: purge all organizations"
    Organization.purge_all()
    print "CKAN: purge all datasets"
    purge_all_datasets()

    print "CKAN: purge all groups"
    Group.purge_all()

    # Create organizations:
    print "CKAN: create organizations"
    for uuid, organization in organizations.iteritems():
        organization.create_in_ckan()

    print "CKAN: create datasets"
    for dataset in datasets:
        create_dataset(dataset, organizations)

    print "CKAN: Create a group for each dataset type..."

    #for group_name in set([d.dataset_type for d in datasets]):
    #    g = Group(DATASET_TYPES[group_name])
    #    g.create_in_ckan()

    # Sort datasets by type
    datasets_by_type = {}
    for d in datasets:
        if d.dataset_type not in datasets_by_type:
            datasets_by_type[d.dataset_type] = [d]
        else:
            datasets_by_type[d.dataset_type].append(d)

    # For each type, create a dedicated group
    for dataset_type, datasets in datasets_by_type.iteritems():
        g = Group(DATASET_TYPES[dataset_type])
        [g.attach_dataset(d) for d in datasets]
        g.create_in_ckan()

if __name__ == "__main__":
    main()