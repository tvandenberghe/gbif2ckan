from entities import (Group, Organization, get_all_datasets_country, gbif_get_uuids_of_all_deleted_datasets,
                      purge_all_datasets, create_dataset)

from conf import COUNTRY_CODE, DATASET_TYPES

# TODO: Test more for API errors and throw exceptions


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