#!/bin/env python3
import datetime
import re
import urllib.parse

import pywikibot
import requests

oldversion = '18.04.1'
newversion = '18.04.2'
pdate = pywikibot.WbTime(2018, 6, 5)


wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
select distinct ?item ?itemLabel where {
     ?item wdt:P361 wd:Q20712193.
     ?item wdt:P348 ?vers.
     FILTER (?vers = "%s")
     ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") .
} order by ?item
""" % oldversion


def runquery(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["results"]
    else:
        return None


site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

wdlist = runquery(wdqurl + urllib.parse.quote_plus(query))

srcurl = "https://download.kde.org/stable/applications/%s/src/" % newversion
r = requests.get(srcurl)
assert(r.status_code == 200)

srctitle = "Download archive"
statedin = pywikibot.Claim(repo, 'P854')
statedin.setTarget(srcurl)
title = pywikibot.Claim(repo, 'P1476')
title.setTarget(pywikibot.WbMonolingualText(srctitle, "en"))
retrieved = pywikibot.Claim(repo, 'P813')
today = datetime.date.today()
date = pywikibot.WbTime(year=today.year, month=today.month, day=today.day)
retrieved.setTarget(date)

lines = re.findall(r'\b\w+-' + re.escape(newversion) + r'.tar.xz\b', r.text)
cutof = len(newversion)+len('-.tar.xz')
lines = set(map(lambda l: l[0:-cutof], lines))
assert(len(lines) > 0)

for software in wdlist['bindings']:
    qid = software['item']['value'][31:]
    name = software['itemLabel']['value']
    print(name)
    if name.lower() not in lines:
        print("skipping")
        continue
    item = pywikibot.ItemPage(repo, qid)
    item.get()
    # Check if version is already there
    if 'P348' in item.claims and newversion in map(lambda x: x.getTarget(), item.claims['P348']):
        continue
    newclaim = pywikibot.Claim(repo, 'P348', datatype='string')
    newclaim.setTarget(newversion)
    item.addClaim(newclaim, summary='Add Update Version (%s)' % newversion)
    item.get(force=True)
    try:
        newclaim.changeRank('preferred')
    except AssertionError:
        print("Setting rank failed.")
    # add release date
    qualifier = pywikibot.Claim(repo, 'P577')
    qualifier.setTarget(pdate)
    newclaim.addQualifier(qualifier, summary='Adding a date of release.')
    # add stable release
    qualifier = pywikibot.Claim(repo, 'P548')
    qualifier.setTarget(pywikibot.ItemPage(repo, 'Q2804309'))
    newclaim.addQualifier(qualifier, summary='Adding stable release')
    # add source
    newclaim.addSources([statedin, title, retrieved], summary='Adding source.')
    # set old ranks back
    item.get(force=True)
    for oldclaim in item.claims['P348']:
        if oldclaim.getTarget() == newversion:
            continue
        try:
            if oldclaim.getRank() == 'preferred':
                oldclaim.changeRank('normal')
        except AssertionError:
            print("Setting rank back failed.")
