import urlparse
import requests
from slugify import slugify

# TODO: Hmmm,importing the conf here is not clean.
from conf import *

MAX_DATASET_NAME_LENGTH = 100  # Ckan limitation

class CKANAPIException(Exception):
    pass

def make_ckan_api_call(action_url, params=None):
    if not params:
        params = {}

    url = urlparse.urljoin(CKAN_INSTANCE_URL, action_url)
    headers = {'Authorization': ADMIN_API_KEY}

    r = requests.post(url, json=params, headers=headers)
    result = r.json()
    return result

def dataset_title_to_name(title):
    return slugify(title)[:MAX_DATASET_NAME_LENGTH]