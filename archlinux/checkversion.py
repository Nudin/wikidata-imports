#!/usr/bin/env python3
import re
import requests
import sys
import urllib.parse
from datetime import datetime
from itertools import zip_longest
from packaging.version import parse

if len(sys.argv) == 1:
    mode = "plain"
else:
    mode = sys.argv[1]

if mode == "plain":
    starttext = "List of outdated packages"
    missing = "%s has no package in Arch! (%s)"
    outofdate = "%s – %s (%s) is out of date. Arch: %s – WD: %s"
    statistics = """==Statistics==
    Items for software running on Linux: %i
    Items with Arch-Label: %i
    Items with Arch-Label & a version number: %i
    Items with matching version number: %i
    Items with outdated version number: %i
    Items with version number newer than Arch: %i
    """
    endtable = ""
    endtext = "Date: %s"
elif mode == "wiki":
    starttext = """{|
    ! Package !! Version in Arch !! Version in Wikidata"""
    missing = """|-
    | [[%s|%s]] || Package does not exist! || %s"""
    outofdate = """|-
    | (%s) [[%s|%s]] || %s || %s"""
    statistics = """==Statistics==
    Items for software running on Linux: %i
    Items with Arch-Label: %i
    Items with Arch-Label & a version number: %i
    Items with matching version number: %i
    Items with outdated version number: %i
    Items with version number newer than Arch: %i
    """
    endtable = "|}"
    endtext = "\n\Date: %s"
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
     <tr><th>Paket</th><th>Version in Arch</th><th>Version in Wikidata</th></tr>"""
    missing = """<tr>
    <td><a href='https://www.wikidata.org/wiki/%s'>%s</td>
    <td>Package does not exist!</td>
    <td>%s</td></tr>"""
    outofdate = """<tr class='%s'>
    <td><a href='https://www.wikidata.org/wiki/%s'>%s</td>
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
    """
    endtable = "</table>"
    endtext = "<br>Date: %s<body></html>"

archurl = 'https://www.archlinux.org/packages/search/json/?name={}'
wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT ?item ?itemLabel ?archlabel ?vers
WHERE
{
  ?item wdt:P3454 ?archlabel.
  ?item wdt:P348 ?vers.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
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

# blacklist of items not to check
blacklist = ['Q687332', 'Q131344', 'Q295495', 'Q1151159',
             'Q28877432', 'Q2527121', 'Q3200238']
# greylist of items where to only check main version
greylist = ['Q2002007', 'Q286124', 'Q41242', 'Q131382', 'Q1103066', 'Q58072', 'Q48524']


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
    # name = name.replace('-', '.')
    wdversionstr = software['vers']['value'].replace('-', '.')
    if qid in greylist:
        wdversionstr = ' '.join(wdversionstr.split('.')[0:-1])
    wdversion = parse(wdversionstr)
    if name in softwarelist:
        softwarelist[name] = max(wdversion, softwarelist[name])
    else:
        softwarelist[name] = wdversion
        qidlist[name] = qid


# Check every software against the Arch repos
print(starttext)
outdatedlist = []
for software in softwarelist:
    searchres = runquery(archurl.format(urllib.parse.quote_plus(software)))
    qid = qidlist[software]
    wdversion = softwarelist[software]
    if searchres == []:
        print(missing % (qid, software, wdversion))
    else:
        archversion_str = searchres[0]["pkgver"].split('+')[0]
        if qid in greylist:
            archversion_str = archversion_str.split('.')[0]
        archversion = parse(archversion_str)
        # Skip release-candidates, betas, etc
        if archversion.is_prerelease:
            continue
        if archversion > wdversion:
            outdatedlist.append([qid, software, archversion, wdversion])
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
    print(outofdate % (lvl, software[0], software[1], software[2], software[3]))

print(endtable)
matchingversions = numberVersion - countOutdated - countNewer
print(statistics % (numberLinuxItems, numberArchLinks, numberVersion,
                    matchingversions, countOutdated, countNewer))
print(endtext % datetime.now())
