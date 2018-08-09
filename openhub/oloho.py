import os
import xml.etree.ElementTree as ET

import requests
from joblib import Memory

oh_api_key = open("mykey").readline()[:-1]

queryapi = "projects.xml?query={}"
mainapi = "p/{}.xml"
enlistmentsapi = "p/{}/enlistments.xml"

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
def _getdata_(query, olohoname):
    global cache_miss
    cache_miss += 1
    url = "https://www.openhub.net/" + query.format(olohoname)
    if "?" in query:
        url += "&api_key="
    else:
        url += "?api_key="
    url += oh_api_key
    r = requests.get(url)
    if r.status_code == 404:
        return None
    elif r.status_code == 401:
        raise PermissionError("API Limit Exceeded", r.status_code)
    elif r.status_code != 200:
        raise LookupError("API-Error %s" % r.status_code)
    return r.text


def getdata(query, olohoname):
    """
    Call the API and handle errors.

    If the API Limit is exceeded raise an Exception, else print a warning
    """
    res = _getdata_(query, olohoname)
    if res is None:
        raise LookupError("Project not found")
    else:
        return ET.fromstring(res)


def getprojectdata(olohoname):
    """
    Get the main data about a project via the (cached) API.
    """
    root = getdata(mainapi, olohoname)
    error = root.findtext("error")
    # The Oloho API returns no data at all if there is no analysis, even
    # through they might still have useful information, to bypass this
    # limitation, we use the query-api in these cases
    if error and error.startswith("No Analysis to display for"):
        root = getdata(queryapi, olohoname)
        project = root.find("result/project")
        if project.findtext("name") == olohoname:
            return project
        else:
            raise LookupError("Project not found")
    else:
        return root.find("result/project")


def getenlistments(olohoname):
    """
    Get the enlistments via the (cached) API.
    """
    root = getdata(enlistmentsapi, olohoname)
    return root.findall("result/enlistment")
