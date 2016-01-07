# Testing CKAN APIs: Create a basic dataset

#!/usr/bin/env python
import json
import pprint
import urllib
import urllib2
import urlparse



CKAN_INSTANCE_URL = "http://192.168.99.101:5780/"
ADMIN_API_KEY = "1b95f88b-9eb1-4ba4-909c-6245dcdd39a8"

# Put the details of the dataset we're going to create into a dict.
dataset_dict = {
    'name': 'my_dataset_name',
    'notes': 'A long description of my dataset',
    'owner_org': 'botanic-garden-meise'
}

# Use the json module to dump the dictionary to a string for posting.
data_string = urllib.quote(json.dumps(dataset_dict))

# We'll use the package_create function to create a new dataset.
request = urllib2.Request(
    urlparse.urljoin(CKAN_INSTANCE_URL, "api/action/package_create"))


request.add_header('Authorization', ADMIN_API_KEY)

# Make the HTTP request.
response = urllib2.urlopen(request, data_string)
assert response.code == 200

# Use the json module to load CKAN's response into a dictionary.
response_dict = json.loads(response.read())
assert response_dict['success'] is True

# package_create returns the created package as its result.
created_package = response_dict['result']
pprint.pprint(created_package)