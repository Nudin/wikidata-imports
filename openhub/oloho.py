import functools
import xml.etree.ElementTree as ET

import requests

oh_api_key = open("mykey").readline()[:-1]


@functools.lru_cache()
def oloho_getdata(query, olohoname):
    baseurl = "https://www.openhub.net/{}?api_key={}"
    url = baseurl.format(query.format(olohoname), oh_api_key)
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("API-Error", r.status_code)
    return ET.fromstring(r.text)
