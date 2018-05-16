from urllib.parse import urljoin
from collections import namedtuple

from slugify import slugify
import requests

from utilities import make_ckan_api_call, dataset_title_to_name, CKANAPIException

from conf import ORGANIZATION_LOGOS

# TODO: Create a class for Dataset
Dataset = namedtuple("Dataset", "publishing_organization_key title description uuid dataset_type administrative_contact_full administrative_contact_name metadata_contact dwca_url website")

def create_dataset(dataset, all_organizations):
    params = {'title': dataset.title,
              'name': dataset_title_to_name(dataset.title),
              'notes': dataset.description,
              'owner_org': all_organizations[dataset.publishing_organization_key].name,
              'url': urljoin("http://www.gbif.org/dataset/", dataset.uuid),

              # Having difficulties adding extras to the dataset.
              # So far, it works IF the extras parameter is not named extras (myextras is good), and a dict
              # (not a list of dicts) is passed. It is, however, not shown in the web interface later...
              #'extras': [{'dataset_type': dataset.dataset_type}]
              'gbif_uuid': dataset.uuid,

              # A Heavy but perfectly working solution: add the field via a plugin like in the tutorial:
              # http://docs.ckan.org/en/latest/extensions/adding-custom-fields.html
              # Then pass the parameter as a first-class one (title, name, ...) (no list of dicts: just a key and value)
              'dataset_type': dataset.dataset_type,

              'administrative_contact': dataset.administrative_contact_full,
              'administrative_contact_name': dataset.administrative_contact_name,
              'metadata_contact': dataset.metadata_contact,
              }

    if dataset.dwca_url:
        params['dwca_url'] = dataset.dwca_url
    if dataset.website:
        params['dataset_website'] = dataset.website

    r = make_ckan_api_call("api/action/package_create", params)

    if not r['success']:
        raise CKANAPIException({"message": "Impossible to create dataset",
                                "dataset": dataset,
                                "error": r['error']})

def _find_primary_contact_of_type(contact_type, contacts_from_api):
    contact = ""
    contact_name = ""

    for c in contacts_from_api:
        if 'type' in c and c['type'] == contact_type and c['primary'] and 'firstName' in c and 'lastName' in c:
            contact_name = c['firstName'] + " " + c['lastName']
            contact = contact_name

            if 'position' in c and len(c['position']) > 0:
                contact += (' - ' + c['position'][0])

            if 'email' in c and len(c['email']) > 0:
                contact += (' - ' + c['email'][0])

            if 'phone' in c and len(c['phone']) > 0:
                contact += (' - ' + c['phone'][0])

    return contact, contact_name


def _prepare_contacts(contacts_from_api):
    administrative_contact_full, administrative_contact_name = _find_primary_contact_of_type('ADMINISTRATIVE_POINT_OF_CONTACT', contacts_from_api)
    metadata_contact_full, metadata_contact_name = _find_primary_contact_of_type('METADATA_AUTHOR', contacts_from_api)

    return administrative_contact_full, administrative_contact_name,  metadata_contact_full, metadata_contact_name

def get_all_datasets_country(country_code):
    LIMIT=20
    datasets = []
    offset = 0

    while True:
        params={"country": country_code, "limit": LIMIT, "offset": offset}
        r = requests.get("http://api.gbif.org/v1/dataset", params=params)
        response = r.json()

        for result in response['results']:
            try:
                description = result['description']
            except KeyError:
                description = ''

            administrative_contact, administrative_contact_name, metadata_contact, metadata_contact_name = _prepare_contacts(result['contacts'])

            dwca_url = None
            for e in result['endpoints']:
                if e['type'] == 'DWC_ARCHIVE':
                    dwca_url = e['url']
                    break

            try:
                homepage = result['homepage']
            except KeyError:
                homepage = ''

            datasets.append(Dataset(publishing_organization_key=result['publishingOrganizationKey'],
                                    title=result['title'],
                                    description=description,
                                    uuid=result['key'],
                                    dataset_type=result['type'],
                                    administrative_contact_full=administrative_contact,
                                    administrative_contact_name=administrative_contact_name,
                                    metadata_contact=metadata_contact,
                                    dwca_url=dwca_url,
                                    website=homepage))

        if response['endOfRecords']:
            break

        offset = offset + LIMIT
    return datasets

def get_existing_datasets_ckan():
    # Return list of strings (dataset names)
    r = make_ckan_api_call("api/action/package_list", {'all_fields': True})

    return r['result']

def purge_all_datasets():
    for dataset_name in get_existing_datasets_ckan():
        purge_dataset(dataset_name)

def purge_dataset(dataset_name_or_id):
    r = make_ckan_api_call("api/action/dataset_purge", {'id': dataset_name_or_id})

    if not r['success']:
        raise CKANAPIException({"message": "Impossible to create dataset",
                                "dataset": dataset_name_or_id,
                                "error": r['error']})


class Group(object):
    def __init__(self, title, logo_url=None ):
        self.title = title
        self.name = slugify(self.title)
        self.attached_datasets = []
        self.logo_url = logo_url

    def create_in_ckan(self):
        # Document is incorrect regarding packages: we need an id parameter, that in fact receive the dataset name... confusing.
        params = {'name': self.name,
                  'title': self.title,
                  'packages': [{'id': dataset_title_to_name(dataset.title)} for dataset in self.attached_datasets],
                  'image_url': self.logo_url
                  }

        try:
            r = make_ckan_api_call("api/action/group_create", params)
            return r['success']
        except ValueError:
            #FIXME: why does we sometimes (only in prod...) get a JSONDecodeError at this stage?
            print("Error decoding JSON")
            return True

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
    def __init__(self, key, title, description=None, homepages=None, city=None, lat=None, lon=None, contacts=None):
        self.key = key
        self.title = title
        self.description = description
        self.name = slugify(self.title)
        self.homepages = homepages
        self.city = city
        self.lat = lat
        self.lon = lon

        self.contacts = contacts

    def create_in_ckan(self):
        extras = []

        if self.homepages:
            extras.append({'key': 'Homepage(s)', 'value': ','.join(self.homepages)})

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
                   result.get('homepage', None),
                   result.get('city', None),
                   result.get('latitude', None),
                   result.get('longitude', None),
                   contacts)

    @classmethod
    def purge_all(cls):
        """
        Purge all organizations from the CKAN instance.

        """
        orgs = cls.get_existing_organizations_ckan()
        for org in orgs:
            org.purge_ckan()

    def purge_ckan(self):
        r = make_ckan_api_call("api/action/organization_purge", {'id': self.key})
        if not r['success']:
            raise CKANAPIException({"message": "Impossible to purge organization",
                                    "organization_key": self.key,
                                    "reason": r['error']['message']})

    @classmethod
    def get_existing_organizations_ckan(cls):
        r = make_ckan_api_call("api/action/organization_list", {'all_fields': True})
        return [cls(res['id'], res['title']) for res in r['result']]