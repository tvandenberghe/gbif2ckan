from urllib.parse import urljoin, urlparse, parse_qs
from collections import namedtuple

from slugify import slugify
import requests
import json

from utilities import make_ckan_api_call, dataset_title_to_name, CKANAPIException

from conf import ORGANIZATION_LOGOS

GBIF_API_LIMIT = 20


# TODO: Create a class for Dataset
# Dataset = namedtuple("Dataset", "publishing_organization_key title description uuid dataset_type administrative_contact_full administrative_contact_name metadata_contact dwca_url website")

class Dataset(object):

    def __init__(self, title, gbif_uuid, id, dwca_url, dataset_type, description, publishing_organization_key,
                 administrative_contact_full, administrative_contact_name, metadata_contact_full, metadata_contact_name,
                 originator_full, originator_name, website, resources, metadata_modified, metadata_created, keywords):
        self.title = title
        self.name = dataset_title_to_name(self.title)
        self.gbif_uuid = gbif_uuid
        self.id = id
        self.dwca_url = dwca_url
        self.dataset_type = dataset_type
        self.description = description
        self.publishing_organization_key = publishing_organization_key
        self.administrative_contact_full = administrative_contact_full
        self.administrative_contact_name = administrative_contact_name
        self.metadata_contact_full = metadata_contact_full
        self.metadata_contact_name = metadata_contact_name
        self.originator_full = originator_full
        self.originator_name = originator_name
        self.website = website
        self.resources = resources
        self.metadata_modified = metadata_modified
        self.metadata_created = metadata_created
        self.keywords = keywords

    def __hash__(self):
        return hash(self.gbif_uuid)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.gbif_uuid == other.uuid

    def create_in_ckan(self, all_organizations):
        params = {'title': self.title,
                  'name': self.id,
                  'gbif_uuid': self.gbif_uuid,
                  'dwca_url': self.dwca_url,
                  'dataset_type': self.dataset_type,
                  'notes': self.description,
                  'owner_org': all_organizations[self.publishing_organization_key].name,
                  'url': urljoin("http://www.gbif.org/dataset/", self.gbif_uuid),
                  'metadata_modified': self.metadata_modified,
                  'metadata_created': self.metadata_created,
                  'administrative_contact_full': self.administrative_contact_full,
                  'administrative_contact_name': self.administrative_contact_name,
                  'metadata_contact_full': self.metadata_contact_full,
                  'metadata_contact_name': self.metadata_contact_name,
                  'originator_full': self.originator_full,
                  'originator_name': self.originator_name,
                  'custom_text': 'TEST BLABLA3'
                  }
        if self.dwca_url:
            params['dwca_url'] = self.dwca_url
        if self.website:
            params['dataset_website'] = self.website
        improved_complex_keywords = []
        improved_simple_keywords = []
        for keyword in self.keywords:
            keyword = Keyword.create_in_ckan(keyword)
            if keyword is not None:
                if keyword.vocabulary_id is None:
                    improved_simple_keywords.append(keyword)
                else:
                    improved_complex_keywords.append(keyword)
        params['tags'] = [{'name': k.name, 'vocabulary_id': k.vocabulary_id} for k in improved_complex_keywords]
        #params['tags'] = params['tags'].append([{'name': k.name} for k in improved_simple_keywords])
        r = make_ckan_api_call("api/action/package_create", params)
        if r is not None:
            if not r['success']:
                raise CKANAPIException({"message": "Impossible to create dataset",
                                        "dataset": self,
                                        "error": r['error']})
        for resource in self.resources:
            Resource.create_in_ckan(resource)

    def get_all_datasets_network(network_uuid):
        datasets = set([])
        for dataset in Dataset.gbif_to_datasets("http://api.gbif.org/v1/network/" + network_uuid + "/constituents"):
            r = requests.get("http://api.gbif.org/v1/dataset/" + dataset.gbif_uuid)
            datasets.add(Dataset.gbif_to_dataset(r.json()))
        return datasets

    def get_all_datasets_country(country_code):
        params = {"country": country_code}
        return Dataset.gbif_to_datasets("http://api.gbif.org/v1/dataset", params=params)

    def gbif_to_datasets(url, params={}):
        datasets = set([])
        offset = 0
        params['limit'] = GBIF_API_LIMIT
        while True:
            params['offset'] = offset
            r = requests.get(url, params=params)
            response = r.json()
            for result in response['results']:
                datasets.add(Dataset.gbif_to_dataset(result))
            if response['endOfRecords']:
                break
            offset = offset + GBIF_API_LIMIT
        return datasets

    def gbif_to_dataset(single_gbif_dataset_json):
        title = single_gbif_dataset_json['title']
        gbif_uuid = single_gbif_dataset_json['key']
        metadata_created = single_gbif_dataset_json['created']
        metadata_modified = single_gbif_dataset_json['modified']
        dwca_url = None
        ipt_id = None
        resource_creation_date = None

        for e in single_gbif_dataset_json['endpoints']:
            if e['type'] == 'DWC_ARCHIVE':
                dwca_url = e['url']
                try:
                    if ipt_id is None:
                        ipt_id = parse_qs(urlparse(dwca_url).query)['r'][
                            0]  # 'http://ipt.vliz.be/eurobis/archive.do?r=ilvo_macrobenthos_2013-2016'
                except KeyError:
                    print("No identifier found in original DwC archive for '" + title + "'")
                break
            elif e['type'] == 'BIOCASE':
                biocase_url = e['url']
                try:
                    if ipt_id is None:
                        ipt_id = parse_qs(urlparse(dwca_url).query)['dsa'][
                            0]  # 'http://biocase.africamuseum.be/biocase_rmca/pywrapper.cgi?dsa=cabin_upn_phytopharmaceutiques'
                except KeyError:
                    print("No identifier found in original ABCD archive for '" + title + "'")
                break
        for i in single_gbif_dataset_json['identifiers']:
            if i['type'] == 'URL' and ipt_id in i['identifier']:
                resource_creation_date = i['created']
        keywords = []
        for kc in single_gbif_dataset_json['keywordCollections']:
            for k in kc['keywords']:
                keyword = Keyword(name=k, vocabulary_id=kc['thesaurus'] if kc['thesaurus'] is not None else None)
                keywords.append(keyword)

        ipt_resource = Resource(package_id=ipt_id, url=dwca_url, format='zipped DwC archive',
                                created=resource_creation_date, description="DarwinCore archive for " + ipt_id)
        gbif_occurrence_page = Resource(package_id=ipt_id,
                                        url='https://www.gbif.org/occurrence/search?dataset_key=' + gbif_uuid,
                                        format='html page on GBIF', description="Occurrences as shown on GBIF")
        resources = [ipt_resource, gbif_occurrence_page]
        dataset_type = single_gbif_dataset_json['type']
        try:
            description = single_gbif_dataset_json['description']
        except KeyError:
            description = ''

        administrative_contact_full, administrative_contact_name, metadata_contact_full, metadata_contact_name, originator_full, originator_name = Dataset._prepare_contacts(
            single_gbif_dataset_json['contacts'])
        publishing_organization_key = single_gbif_dataset_json['publishingOrganizationKey']

        try:
            homepage = single_gbif_dataset_json['homepage']
        except KeyError:
            homepage = ''
        return Dataset(title=title, gbif_uuid=gbif_uuid, id=ipt_id, dwca_url=dwca_url, dataset_type=dataset_type,
                       description=description,
                       publishing_organization_key=publishing_organization_key,
                       administrative_contact_full=administrative_contact_full,
                       administrative_contact_name=administrative_contact_name,
                       metadata_contact_full=metadata_contact_full,
                       metadata_contact_name=metadata_contact_name,
                       originator_full=originator_full,
                       originator_name=originator_name,
                       website=homepage,
                       resources=resources,
                       metadata_created=metadata_created,
                       metadata_modified=metadata_modified,
                       keywords=keywords)

    @staticmethod
    def get_existing_datasets_ckan():
        # Return list of strings (dataset names)
        r = make_ckan_api_call("api/action/package_list", {'all_fields': True})
        if r is not None:
            return r['result']
        else:
            return None

    @staticmethod
    def purge_ckan_all():
        json_result = Dataset.get_existing_datasets_ckan()
        if json_result is not None:
            for dataset_name in json_result:
                Dataset.purge_ckan(dataset_name)

    @classmethod
    def purge_ckan(cls, id):
        r = make_ckan_api_call("api/action/dataset_purge", {'id': id})

        if not r['success']:
            raise CKANAPIException({"message": "Impossible to purge dataset",
                                    "dataset": id,
                                    "error": r['error']})

    @staticmethod
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

    @staticmethod
    def _prepare_contacts(contacts_from_api):
        administrative_contact_full, administrative_contact_name = Dataset._find_primary_contact_of_type(
            'ADMINISTRATIVE_POINT_OF_CONTACT', contacts_from_api)
        metadata_contact_full, metadata_contact_name = Dataset._find_primary_contact_of_type('METADATA_AUTHOR',
                                                                                             contacts_from_api)
        originator_full, originator = Dataset._find_primary_contact_of_type('ORIGINATOR', contacts_from_api)

        return administrative_contact_full, administrative_contact_name, metadata_contact_full, metadata_contact_name, originator_full, originator


class Group(object):
    def __init__(self, title, logo_url=None):
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
            if r is not None:
                return r['success']
        except ValueError:
            # FIXME: why does we sometimes (only in prod...) get a JSONDecodeError at this stage?
            print("Error decoding JSON")
            return True

    @classmethod
    def purge_ckan_all(cls):
        groups = cls.get_existing_groups_ckan()
        if groups is not None:
            for g in groups:
                g.purge_ckan()

    def purge_ckan(self):
        # Purge the group whose name is self.name
        r = make_ckan_api_call("api/action/group_purge", {'id': self.name})
        return r['success']

    def attach_dataset(self, dataset):
        self.attached_datasets.append(dataset)

    @classmethod
    def get_existing_groups_ckan(cls):
        r = make_ckan_api_call("api/action/group_list", {'all_fields': True})
        if r is not None:
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

    def to_string(self):
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
            contact_type, contact_details = c.to_string()

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
        if r is not None:
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
    def purge_ckan_all(cls):
        """
        Purge all organizations from the CKAN instance.
        """
        orgs = cls.get_existing_organizations_ckan()
        if orgs is not None:
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
        if r is not None:
            return [cls(res['id'], res['title']) for res in r['result']]


class Resource(object):
    def __init__(self, package_id, url, revision_id=None, description=None, format=None, hash=None, mimetype=None,
                 size=None, created=None, last_modified=None):
        self.package_id = package_id
        self.url = url
        self.revision_id = revision_id
        self.description = description
        self.format = format
        self.hash = hash
        self.mimetype = mimetype
        self.size = size
        self.created = created
        self.last_modified = last_modified

    def create_in_ckan(self):
        params = {'package_id': self.package_id,
                  'url': self.url
                  }
        if self.revision_id:
            params['revision_id'] = self.revision_id
        if self.description:
            params['description'] = self.description
        if self.format:
            params['format'] = self.format
        if self.hash:
            params['hash'] = self.hash
        if self.mimetype:
            params['mimetype'] = self.mimetype
        if self.size:
            params['size'] = self.size
        if self.created:
            params['created'] = self.created.partition(".")[0]
        if self.last_modified:
            params['last_modified'] = self.last_modified.partition(".")[0]

        r = make_ckan_api_call("api/action/resource_create", params)
        if r is not None:
            return r['success']


class Keyword(object):
    def __init__(self, name, vocabulary_id=None):
        self.name = name
        if vocabulary_id is not None and vocabulary_id.lower() != 'n/a':
            self.vocabulary_id = vocabulary_id
        else:
            self.vocabulary_id = None

    def create_in_ckan(self):
        params = {}
        r = None
        if self.name is not None:
            temp=self.vocabulary_id
            if self.vocabulary_id is not None:
                v = Vocabulary(name=self.vocabulary_id, tags=[self])
                vocabulary = v.create_or_update_in_ckan()
                self.vocabulary_id = vocabulary.id  # move from a name-based vocabulary_id to a uuid based one.
                params = {'vocabulary_id': self.vocabulary_id, 'name': self.name}
                r = make_ckan_api_call("api/action/tag_create", params)
                return self
                # params={'vocabulary_id': self.vocabulary_id,'name':self.name}
        #        else:
        #            params = {'name': self.name}
        #            r = make_ckan_api_call("api/action/tag_create", params)
        #            if r is not None:
        #                if not r['success']:
        #                    print("Couldn't create keyword " + self.name)
        else:
            print("Couldn't create keyword as it is empty")
        return self


class Vocabulary(object):
    def __init__(self, name, tags, id=None):
        self.id = id
        self.name = name
        self.tags = tags

    def create_or_update_in_ckan(self):
        existing_vocab = self.get_from_ckan()
        if existing_vocab is not None:
            self.id = existing_vocab.id
            params = {'id': self.id, 'name': self.name, 'tags': existing_vocab.tags+[{'name': k.name, 'vocabulary_id': self.id} for k in self.tags]}
            # params['id'] = existing_vocab.id

            r = make_ckan_api_call("api/action/vocabulary_update", params)
            print("Tried updating vocab " + self.name)
        else:
            params = {'name': self.name, 'tags': [{'name': k.name} for k in self.tags]}
            r = make_ckan_api_call("api/action/vocabulary_create", params)
            # if r is not None and r['success']:
            #    self.id=r['result']['id']
            print("Tried creating vocab " + self.name)
        if r is not None:
            if not r['success']:
                print("Couldn't create/update vocabulary " + self.name)
        return self

    def exists_in_ckan(self):
        params = {'id': self.name}
        r = make_ckan_api_call("api/action/vocabulary_show", params)
        if r is not None:
            return r['success']

    def get_from_ckan(self):
        params = {'id': self.name}
        r = make_ckan_api_call("api/action/vocabulary_show", params)
        if r is not None:
            return Vocabulary(id=r['result']['id'], name=r['result']['name'], tags=r['result']['tags'])
        else:
            a = 5
