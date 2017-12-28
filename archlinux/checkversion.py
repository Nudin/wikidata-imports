#!/bin/env python3
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
    missing = "%s has no package in Arch!"
    outofdate = "%s (%s) is out of date. Arch: %s – WD: %s"
    endtext = "Date: %s"
elif mode == "wiki":
    starttext = """{|
    ! Package !! Version in Arch !! Version in Wikidata"""
    missing = """|-
    | [[%s|%s]] || Package does not exist!"""
    outofdate = """|-
    | [[%s|%s]] || %s || %s"""
    endtext = "|}\n\Date: %s"
elif mode == "html":
    starttext = """<!DOCTYPE html><html lang='en'>
    <style>table { border-collapse: collapse; }
    table, th, td { border: 1px solid black; padding: 0.3em; }</style>
    <body>
    <h1>Probably outdated Software-items on Wikidata</h1>
    <p>List of software where the newest version-number on Wikidata is older
    that the version available in the Arch-Linux-Repositories. "Package does
    not exist!" means, that there is a Arch-package-name set in Wikidata but no
    such Package in the Arch-Repos!</p>
    <table>
     <tr><th>Paket</th><th>Version in Arch</th><th>Version in Wikidata</th></tr>"""
    missing = """<tr>
    <td><a href='https://www.wikidata.org/wiki/%s'>%s</td><td>Does not exist</td></tr>"""
    outofdate = """<tr>
    <td><a href='https://www.wikidata.org/wiki/%s'>%s</td>
    <td>%s</td>
    <td>%s</td>
    </tr>"""
    endtext = "</table><br>Date: %s<body></html>"

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


def runquery(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["results"]
    else:
        return None


# We use this function to sort the list according to the
# "size" of the change of the version.
def mycomp(l):
    old = re.sub("[^0-9.]", "", str(l[3])).split('.')
    new = re.sub("[^0-9.]", "", str(l[2])).split('.')
    return [int(o)-int(n) for o, n in zip_longest(old, new, fillvalue=0)]


wdlist = runquery(wdqurl + urllib.parse.quote_plus(query))
softwarelist = {}
qidlist = {}
for software in wdlist['bindings']:
    qid = software['item']['value'][31:]
    name = software['archlabel']['value']
    wdversion = parse(software['vers']['value'])
    if name in softwarelist:
        softwarelist[name] = max(wdversion, softwarelist[name])
    else:
        softwarelist[name] = wdversion
        qidlist[name] = qid

print(starttext)
outdatedlist = []
for software in softwarelist:
    searchres = runquery(archurl.format(software))
    qid = qidlist[software]
    if searchres == []:
        print(missing % (qid, software))
    else:
        archversion = parse(searchres[0]["pkgver"])
        wdversion = softwarelist[software]
        if archversion > wdversion:
            outdatedlist.append([qid, software, archversion, wdversion])

# Sort (bigger steps in Versionsnummer fist)
outdatedlist = sorted(outdatedlist, key=mycomp)

for software in outdatedlist:
        print(outofdate % (software[0], software[1], software[2], software[3]))
print(endtext % datetime.now())
