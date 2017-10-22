#!/bin/env python3
import requests
import urllib.parse
import pywikibot


archurl = 'https://www.archlinux.org/packages/search/json/?name={}'
wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT ?item ?itemLabel ?debian ?website
WHERE
{
  ?item wdt:P3442 ?debian.
  ?item wdt:P856 ?website
  FILTER NOT EXISTS {
      ?item wdt:P3454|wdt:P3473|wdt:P3463 ?arch.
  }.
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") .

  #FILTER(?debian = lcase(?itemLabel)). # <- Why does this not work!?
}
"""


def runquery(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["results"]
    else:
        return None


def normurl(url):
    url = url.lower()
    url = url.replace("https:", "http:")
    url = url.replace("://www.", "://")
    if url[-1] == '/':
        url = url[0:-1]
    return url


site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

wdlist = runquery(wdqurl + urllib.parse.quote_plus(query))
softwarelist = {}
qidlist = {}
done = []
for software in wdlist['bindings']:
    qid = software['item']['value'][31:]
    name = software['itemLabel']['value'].lower()
    debianname = software['debian']['value']
    website = normurl(software['website']['value'])
    if name == debianname:
        searchres = runquery(archurl.format(name))
        if searchres != []:
            website2 = normurl(searchres[0]['url'])
            if not (qid in done) and website == website2:
                print("Match " + name)
                item = pywikibot.ItemPage(repo, qid)
                archclaim = pywikibot.Claim(repo, 'P3454', datatype='external-id')
                archclaim.setTarget(debianname)
                item.addClaim(archclaim, summary=u'Adding arch-package name')
                done.append(qid)

