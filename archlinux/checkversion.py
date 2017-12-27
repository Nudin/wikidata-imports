#!/bin/env python3
import requests
from packaging.version import parse
import urllib.parse
from itertools import zip_longest
import re

# starttext = "List of outdated packages"
# missing = "%s has no package in Arch!"
# outofdate = "%s (%s) is out of date. Arch: %s – WD: %s"
# endtext = ""
starttext = """{|
! Package !! Version in Arch !! Version in Wikidata"""
missing = """|-
| [[%s|%s]] || Package does not exist!"""
outofdate = """|-
| [[%s|%s]] || %s || %s"""
endtext = "|}"

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
print(endtext)
