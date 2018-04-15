#!/usr/bin/env python3
import os
import re
import requests
import subprocess
import sys
import urllib.parse
from datetime import datetime
from glob import glob
from itertools import zip_longest
from joblib import Memory
from packaging.version import parse
from tqdm import tqdm

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

if len(sys.argv) == 1:
    mode = "plain"
else:
    mode = sys.argv[1]

if mode == "plain":
    starttext = "List of outdated packages"
    missing = "%s has no package in Arch! (%s)"
    outofdate = "%s – %s (%s) is out of date. Arch: %s – WD: %s (%s) (%s)"
    statistics = """==Statistics==
    Items for software running on Linux: %i
    Items with Arch-Label: %i
    Items with Arch-Label & a version number: %i
    Items with matching version number: %i
    Items with outdated version number: %i
    Items with version number newer than Arch: %i
    """
    endtable = ""
    endtext = "Date: %s\nData from arch repos cached for up to %i minutes\nCachemisses: %i"
elif mode == "wiki":
    starttext = """{|
    ! Package !! Version in Arch !! Version in Wikidata !! Github"""
    missing = """|-
    | [[%s|%s]] || Package does not exist! || %s"""
    outofdate = """|-
    | (%s) [[%s|%s]] || %s || %s || %s """
    statistics = """==Statistics==
    Items for software running on Linux: %i
    Items with Arch-Label: %i
    Items with Arch-Label & a version number: %i
    Items with matching version number: %i
    Items with outdated version number: %i
    Items with version number newer than Arch: %i
    """
    endtable = "|}"
    endtext = "\n\Date: %s\nData from arch repos cached for up to %i minutes\nCachemisses: %i"
elif mode == "html":
    starttext = """<!DOCTYPE html><html lang='en'>
    <style>
        table { border-collapse: collapse; }
        table, th, td { border: 1px solid black; padding: 0.3em; }
        .major { background-color: red; }
        .minor { background-color: yellow; }
    </style>
    <body>
    <h1>Probably outdated Software-items on Wikidata</h1>
    <p>List of software where the newest version-number on Wikidata is older
    that the version available in the Arch-Linux-Repositories. "Package does
    not exist!" means, that there is a Arch-package-name set in Wikidata but no
    such Package in the Arch-Repos!</p>
    <table>
     <tr><th>Paket</th><th>Version in Arch</th><th>Version in Wikidata</th>
         <th>Newest (Beta) on Wikidata</th><th>github-repo</th></tr>"""
    missing = """<tr>
    <td><a href='https://www.wikidata.org/wiki/%s'>%s</td>
    <td>Package does not exist!</td>
    <td>%s</td></tr>"""
    outofdate = """<tr class='%s'>
    <td><a href='https://www.wikidata.org/wiki/%s'>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    </tr>"""
    statistics = """<h2>Statistics</h2>
    <ul>
    <li>Items Software running on Linux: %i</li>
    <li>Items with Arch-Label: %i</li>
    <li>Items with Arch-Label & a version number: %i
        (<a href="http://tinyurl.com/y9mz76w9">List of items without.</a>)</li>
    <li>Items with matching version number: %i</li>
    <li>Items with outdated version number: %i</li>
    <li>Items with version number newer than Arch: %i</li>
    </ul>
    <p><a href="http://tinyurl.com/y7d2ejp7">
    Items with multiple versions with identical Rank</a></p>
    """
    endtable = "</table>"
    endtext = """<br>Date: %s<br>
    Data from arch repos cached for up to %i minutes<br>
    Cachemisses: %i
    <body></html>"""

archurl = 'https://www.archlinux.org/packages/search/json/?name={}'
# List of repos in which we want to search
repos = ['Community', 'Community-Testing', 'Core', 'Extra',
         'Multilib', 'Multilib-Testing', 'Testing']
for repo in repos:
    archurl += '&repo={}'.format(repo)
wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
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

# blacklist of items not to check
blacklist = ['Q131344', 'Q295495', 'Q1151159', 'Q1165933', 'Q214743', 'Q1050420']
# greylist of items where to only check main version
greylist = ['Q2002007', 'Q286124', 'Q48524', 'Q401995', 'Q7439308', 'Q3353120',
            'Q204377', 'Q4779325', 'Q41242']


# Set up cache so we don't query the arch database every time
# delete cached values if they are older than a certain time
cachetime = 180
cachemisscounter = 0
directory = dname + "/archcache"
if not os.path.exists(directory):
    os.makedirs(directory)
subprocess.call(["touch"] +
                glob(directory) +
                glob(directory + "/joblib/") +
                glob(directory + "/joblib/*") +
                glob(directory + "/joblib/*/*/")
                )
subprocess.Popen(("find",
                 directory,
                 "-type", "d",
                 "-mmin", "+"+str(cachetime),
                 '-exec', 'rm', '-r', '{}', ';'
                 )).wait()

memory = Memory(cachedir=directory, verbose=0)


# Run a query against a web-api
def runquery(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["results"]
    else:
        return None


# Run a Spaql-Query
def runSPARQLquery(query):
    return runquery(wdqurl + urllib.parse.quote_plus(query))['bindings']


@memory.cache
def runarchquery(software):
    global cachemisscounter
    cachemisscounter += 1
    searchres = runquery(archurl.format(urllib.parse.quote_plus(software)))
    if searchres == []:
        return None
    return searchres[0]["pkgver"].split('+')[0]


# We use this function to sort the list according to the
# "size" of the change of the version.
def versiondelta(l):
    old = re.sub("[^0-9.]", "", str(l[3])).split('.')
    new = re.sub("[^0-9.]", "", str(l[2])).split('.')
    return [int(o)-int(n) for o, n in zip_longest(old, new, fillvalue=0)]


# get statistics
numberArchLinks = int(runSPARQLquery(queryNumberArchLinks)[0]['count']['value'])
numberVersion = int(runSPARQLquery(queryNumberVersions)[0]['count']['value'])
numberLinuxItems = int(runSPARQLquery(queryNumberLinuxItems)[0]['count']['value'])
countOutdated = 0
countNewer = 0

# Get newest version numbers from Wikidata
wdlist = runSPARQLquery(query)
softwarelist = {}
qidlist = {}
for software in wdlist:
    qid = software['item']['value'][31:]
    if qid in blacklist:
        continue
    name = software['archlabel']['value']
    wdversionstr = software['vers']['value'].replace('-', '.').replace(' patch ', '.')
    if qid in greylist:
        if len(wdversionstr.split('.')) > 1:
            wdversionstr = ' '.join(wdversionstr.split('.')[0:-1])
    wdversion = parse(wdversionstr)
    if name in softwarelist:
        softwarelist[name] = max(wdversion, softwarelist[name])
    else:
        softwarelist[name] = wdversion
        qidlist[name] = qid

wdlist_beta = runSPARQLquery(betaquery)
softwarelist_beta = {}
for software in wdlist_beta:
    qid = software['item']['value'][31:]
    if qid in blacklist:
        continue
    name = software['archlabel']['value']
    wdversionstr = software['vers']['value'].replace('-', '.')
    wdversion = parse(wdversionstr)
    if name in softwarelist_beta:
        softwarelist_beta[name] = max(wdversion, softwarelist_beta[name])
    else:
        softwarelist_beta[name] = wdversion

wdgithublist = runSPARQLquery(querygithub)
githublist = {}
for software in wdgithublist:
    qid = software['item']['value'][31:]
    github = software['github']['value']
    githublist[qid] = github

# Check every software against the Arch repos
print(starttext)
outdatedlist = []
for software in tqdm(softwarelist):
    archversion_str = runarchquery(software)
    qid = qidlist[software]
    wdversion = softwarelist[software]
    betaversion = softwarelist_beta.get(software, '')
    if archversion_str is None:
        print(missing % (qid, software, wdversion))
    else:
        if qid in greylist:
            if len(wdversionstr.split('.')) > 1:
                archversion_str = ' '.join(archversion_str.split('.')[0:-1])
        archversion = parse(archversion_str)
        # Skip release-candidates, betas, etc
        if archversion.is_prerelease:
            continue
        if archversion > wdversion and archversion != betaversion:
            outdatedlist.append([qid, software, archversion, wdversion, betaversion])
            countOutdated += 1
        elif archversion < wdversion:
            countNewer += 1


# Sort (bigger steps in Versionsnummer fist)
outdatedlist = sorted(outdatedlist, key=versiondelta)

# print out table of outdated versions
for software in outdatedlist:
    delta = versiondelta(software)
    if delta[0] != 0:
        lvl = "major"
    elif len(delta) > 1 and delta[1] != 0:
        lvl = "minor"
    else:
        lvl = "bug"
    print(outofdate % (lvl, software[0], software[1], software[2],
          software[3], software[4], githublist.get(software[0], '')))

print(endtable)
matchingversions = numberVersion - countOutdated - countNewer
print(statistics % (numberLinuxItems, numberArchLinks, numberVersion,
                    matchingversions, countOutdated, countNewer))
print(endtext % (datetime.now(), cachetime, cachemisscounter))
