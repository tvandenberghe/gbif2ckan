import urlparse

from collections import namedtuple

import requests

from entities import Group, Organization
from utilities import make_ckan_api_call, dataset_title_to_name

from conf import *

Dataset = namedtuple("Dataset", "publishing_organization_key title description uuid dataset_type")


# TODO: Test more for API errors and throw exceptions
# TODO: Create a class for Dataset


def create_dataset(dataset, all_organizations):
    params = {'title': dataset.title,
              'name': dataset_title_to_name(dataset.title),
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
    # Get all datasets published in the country
    print "Get Datasets information from GBIF..."
    datasets = get_all_datasets_country(COUNTRY_CODE)
    print "Get list of deleted datasets (to ignore)..."
    uuids_to_ignore = gbif_get_uuids_of_all_deleted_datasets()
    datasets = [d for d in datasets if d.uuid not in uuids_to_ignore]

    # Let's also retrieve data about linked organizations
    print "Get information about linked (publishing) organizations"
    organizations = {}
    for dataset in datasets:
        organization_key = dataset.publishing_organization_key
        if not organization_key in organizations:
            organizations[organization_key] = Organization.from_gbif_api(organization_key)


    print "CKAN: purge all datasets"
    purge_all_datasets()

    print "CKAN: purge all organizations"
    Organization.purge_all()

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