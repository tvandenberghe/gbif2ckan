from urllib.parse import urljoin
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
    url = urljoin(CKAN_INSTANCE_URL, action_url)
    headers = {'Authorization': ADMIN_API_KEY}
    result = None
    try:
        r = requests.post(url, json=params, headers=headers)
        result = r.json()
        return result
    except requests.exceptions.ConnectionError as e:
        print("There is a problem with your CKAN instance on "+ url+". It is not reachable.")



def dataset_title_to_name(title):
    return slugify(title)[:MAX_DATASET_NAME_LENGTH]
