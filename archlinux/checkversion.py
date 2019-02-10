#!/usr/bin/env python3
import collections
import os
import re
import subprocess
import sys
import urllib.parse
from datetime import datetime
from glob import glob
from itertools import zip_longest

import requests
from jinja2 import Environment, FileSystemLoader
from joblib import Memory
from packaging.version import parse
from tqdm import tqdm

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

file_loader = FileSystemLoader(".")
env = Environment(loader=file_loader)
template = env.get_template("versioncomparing.html.jinja")


archurl = "https://www.archlinux.org/packages/search/json/?name={}"
archconn = requests.Session()

# List of repos in which we want to search
repos = [
    "Community",
    "Community-Testing",
    "Core",
    "Extra",
    "Multilib",
    "Multilib-Testing",
    "Testing",
]
for repo in repos:
    archurl += "&repo={}".format(repo)
wdqurl = "https://query.wikidata.org/sparql?format=json&query="
query = """
SELECT ?item ?itemLabel ?archlabel ?vers
WHERE
{
  ?item wdt:P3454 ?archlabel.
  ?item wdt:P348 ?vers.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
} order by ?item
"""

betaquery = """
SELECT ?item ?itemLabel ?archlabel ?vers
WHERE
{
  ?item wdt:P3454 ?archlabel.
  ?item p:P348 ?v.
  ?v ps:P348 ?vers.
  ?v pq:P548 ?q.
  FILTER NOT EXISTS {
      ?v pq:P548 wd:Q2804309.
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
} order by ?item
"""

queryNumberLinuxItems = """
SELECT (COUNT(DISTINCT ?item) AS ?count) WHERE {
  {?item wdt:P306 wd:Q388. } UNION {
  ?item wdt:P306 wd:Q3251801. } UNION {
  ?item wdt:P306 wd:Q14579. }
}
"""

queryNumberArchLinks = """
SELECT (COUNT(DISTINCT ?item) AS ?count)
WHERE
{
  ?item wdt:P3454 ?arch.
}
"""

queryNumberVersions = """
SELECT (COUNT(DISTINCT ?item) AS ?count)
WHERE
{
  ?item wdt:P3454 ?arch.
  ?item wdt:P348 ?vers.
}
"""

querygithub = """
  SELECT ?item ?github where {
  ?item wdt:P1324 ?github.
  FILTER contains( STR(?github), "github")
}
"""


class Software:
    def __init__(self, versionstr, fuzzy=False):
        self.originalstr = versionstr
        self.fuzzy = fuzzy
        self.versionstr = versionstr.replace("-", ".").replace(" patch ", ".")
        if fuzzy and len(self.versionstr.split(".")) > 1:
            self.versionstr = " ".join(self.versionstr.split(".")[0:-1])
        self.parsed = parse(self.versionstr)

    def __str__(self):
        return self.originalstr

    def __lt__(self, other):
        return self.parsed < other.parsed

    def ___le__(self, other):
        return self.parsed <= other.parsed

    def __eq__(self, other):
        if type(other) == str:
            return self.versionstr == other
        elif isinstance(other, Software):
            return self.versionstr == other.versionstr
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return self.parsed > other.parsed

    def __ge__(self, other):
        return self.parsed >= other.parsed

    def is_prerelease(self):
        return self.parsed.is_prerelease

    def __sub__(self, other):
        """
        Calculate the difference between two versions:

        Software(4.1.5) - Software(2.0.1) = [2, 1,4]
        """
        old = re.sub("[^0-9.]", "", self.versionstr).split(".")
        new = re.sub("[^0-9.]", "", other.versionstr).split(".")
        return [sint(o) - sint(n) for o, n in zip_longest(old, new, fillvalue=0)]


class MaxDict(collections.UserDict):
    def __setitem__(self, key, value):
        if key in self.data:
            self.data[key] = max(value, self.data[key])
        else:
            self.data[key] = wdversion


def sint(value):
    try:
        return int(value)
    except ValueError:
        return 0


# blacklist of items not to check
blacklist = ["Q131344", "Q295495", "Q1151159", "Q1165933", "Q214743", "Q1050420"]
# greylist of items where to only check main version
greylist = [
    "Q2002007",
    "Q286124",
    "Q48524",
    "Q7439308",
    "Q3353120",
    "Q4779325",
    "Q41242",
]


# Set up cache so we don't query the arch database every time
# delete cached values if they are older than a certain time
cachetime = 180
cachemisscounter = 0
directory = dname + "/archcache"
if not os.path.exists(directory):
    os.makedirs(directory)
subprocess.call(
    ["touch"]
    + glob(directory)
    + glob(directory + "/joblib/")
    + glob(directory + "/joblib/*")
    + glob(directory + "/joblib/*/*/")
)
subprocess.Popen(
    (
        "find",
        directory,
        "-type",
        "d",
        "-mmin",
        "+" + str(cachetime),
        "-exec",
        "rm",
        "-r",
        "{}",
        ";",
    )
).wait()

memory = Memory(cachedir=directory, verbose=0)


# Run a query against a web-api
def runquery(url, session=requests):
    r = session.get(url)
    if r.status_code == 200:
        return r.json()["results"]
    else:
        return None


# Run a Spaql-Query
def runSPARQLquery(query):
    res = runquery(wdqurl + urllib.parse.quote_plus(query))["bindings"]
    return [{k: v["value"] for (k, v) in r.items()} for r in res]


def getSPARQLcountvalue(query):
    return int(runSPARQLquery(query)[0]["count"])


@memory.cache
def runarchquery(software):
    global cachemisscounter
    cachemisscounter += 1
    searchres = runquery(archurl.format(urllib.parse.quote_plus(software)), archconn)
    if searchres == []:
        return None
    return searchres[0]["pkgver"].split("+")[0]


def auto_tqdm(iterlist):
    if sys.stderr.isatty():
        return tqdm(iterlist)
    else:
        return iterlist


# get statistics
statistics = {}
statistics["arch"] = getSPARQLcountvalue(queryNumberArchLinks)
statistics["version"] = getSPARQLcountvalue(queryNumberVersions)
statistics["linux"] = getSPARQLcountvalue(queryNumberLinuxItems)
statistics["outdated"] = 0
statistics["newer"] = 0

# Get newest version numbers from Wikidata
wdlist = runSPARQLquery(query)
versionlist = MaxDict()
names = {}
for software in wdlist:
    qid = software["item"][31:]
    name = software["archlabel"]
    wdversionstr = software["vers"]
    if qid in blacklist:
        continue
    wdversion = Software(wdversionstr, qid in greylist)
    versionlist[qid] = wdversion
    names[qid] = name

wdlist_beta = runSPARQLquery(betaquery)
betaversionlist = MaxDict()
for software in wdlist_beta:
    qid = software["item"][31:]
    name = software["archlabel"]
    wdversionstr = software["vers"]
    if qid in blacklist:
        continue
    wdversion = Software(wdversionstr)
    betaversionlist[qid] = wdversion

# Get Github-links from Wikidatas
wdgithublist = runSPARQLquery(querygithub)
githublist = {}
for software in wdgithublist:
    qid = software["item"][31:]
    github = software["github"]
    githublist[qid] = github

# Check every software against the Arch repos
outdatedlist = []
archversions = {}
orphanlist = []
for qid in auto_tqdm(versionlist):
    name = names[qid]
    wdversion = versionlist[qid]
    betaversion = betaversionlist.get(qid, "")
    archversion_str = runarchquery(name)
    if archversion_str is None:
        orphanlist.append(qid)
    else:
        archversion = Software(archversion_str, qid in greylist)
        archversions[qid] = archversion
        # Skip release-candidates, betas, etc
        if archversion.is_prerelease():
            continue
        if archversion > wdversion and archversion != betaversion:
            outdatedlist.append(qid)
            statistics["outdated"] += 1
        elif archversion < wdversion:
            statistics["newer"] += 1


def getdelta(qid):
    return archversions[qid] - versionlist[qid]


# Sort (bigger steps in Versionsnummer fist)
outdatedlist = sorted(outdatedlist, key=getdelta, reverse=True)

lvllist = {}
for qid in outdatedlist:
    delta = getdelta(qid)
    if delta[0] != 0:
        lvllist[qid] = "major"
    elif len(delta) > 1 and delta[1] != 0:
        lvllist[qid] = "minor"
    else:
        lvllist[qid] = "bug"

statistics["cachemiss"] = cachemisscounter
date = datetime.now()

# print out table of outdated versions
html = template.render(globals())
print(html)
