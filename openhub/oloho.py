import os
import xml.etree.ElementTree as ET

import requests
from joblib import Memory

oh_api_key = open("mykey").readline()[:-1]


# Set up cache so we don't query the oloho api every time
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
directory = dname + "/oloho_cache"
if not os.path.exists(directory):
    os.makedirs(directory)

memory = Memory(cachedir=directory, verbose=0)

cache_miss = 0


@memory.cache
def _oloho_getdata_(query, olohoname):
    global cache_miss
    cache_miss += 1
    baseurl = "https://www.openhub.net/{}?api_key={}"
    url = baseurl.format(query.format(olohoname), oh_api_key)
    r = requests.get(url)
    if r.status_code == 404:
        return None
    elif r.status_code != 200:
        raise Exception("API-Error", r.status_code)
    return r.text


def oloho_getdata(query, olohoname):
    """
    Wrapper around oloho_getdata_ since we want to cache 404-errors but no
    other errors and raise an Exception for all status codes other then 200
    """
    res = _oloho_getdata_(query, olohoname)
    if res is None:
        raise Exception("API-Error", 404)
    else:
        return ET.fromstring(res)


def get_cache_miss():
    return cache_miss
