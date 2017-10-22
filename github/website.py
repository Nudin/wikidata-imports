#!/bin/env python3
import requests
import urllib.parse
import pywikibot
from colorama import Fore, Back, Style


wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT ?item ?itemLabel ?itemDescription ?website
WHERE
{
  # Has a website
  ?item wdt:P856 ?website.
  FILTER REGEX(STR(?website), "https?://github.com/.*/.*") .
  
  FILTER NOT EXISTS {
      ?item wdt:P1324 ?arch.
  }.

  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
"""


# Run a Query and get the results block of the returned json
def runquery(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["results"]
    else:
        return None


# Normalise URL
# so that two urls with probably identical target result are identical
def normurl(url):
    url = url.lower()
    url = url.replace("https:", "http:")
    url = url.replace("://www.", "://")
    url = url.replace("/index.html", "/")
    if url[-1] == '/':
        url = url[0:-1]
    return url


# Ask a user a yes/no-question
def ask(question):
    answer = input(question + " [Y/n] ")
    return (answer == "" or str.lower(answer[0]) == "y")


def getvalue(software, key):
    if key in software:
        return software[key]['value']
    else:
        return ""


def addRepoToItem(qid, name):
    item = pywikibot.ItemPage(repo, qid)
    archclaim = pywikibot.Claim(repo, 'P1324', datatype='external-id')
    archclaim.setTarget(name)
    item.addClaim(archclaim, summary=u'Adding arch-package name')


site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

print("...")
wdlist = runquery(wdqurl + urllib.parse.quote_plus(query))
softwarelist = {}
qidlist = {}
done = []
for software in wdlist['bindings']:
    print('.', end='', flush=True)
    qid = getvalue(software, 'item')[31:]
    name = getvalue(software, 'itemLabel').lower()
    website = normurl(getvalue(software, 'website'))
    if software not in done:
        addRepoToItem(qid, website)
        done.append(qid)
