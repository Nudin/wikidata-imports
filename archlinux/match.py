#!/bin/env python3
import requests
import urllib.parse
import pywikibot
from colorama import Fore, Style


# archurl = 'https://www.archlinux.org/packages/search/json/?name={}&arch=any&arch=x86_64'
archurl = 'https://www.archlinux.org/packages/search/json/?q={}&arch=any&arch=x86_64'
wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT ?item ?itemLabel ?debian ?debianLabel ?itemDescription ?website
WHERE
{
  # Has a website
  ?item wdt:P856 ?website.

  #?item wdt:P3442|wdt:P3473|wdt:P3463 ?debian.

  ?item wdt:P306 ?linux.
  VALUES(?linux) {
   (wd:Q388)(wd:Q174666)(wd:Q3251801)(wd:Q14656)(wd:Q11368)
  }

  # ?item p:P31/ps:P31/wdt:P279* wd:Q7397.
  # ?item wdt:P275 ?licens.
  # ?licens p:P31/ps:P31/(wdt:P31|wdt:P279)* ?kind.
  # VALUES ?kind { wd:Q196294 wd:Q1156659 }.
  # FILTER NOT EXISTS {
  #     ?item p:P31/ps:P31/wdt:P279* wd:Q35127.
  # }.

  # Without Arch-Package given
  FILTER NOT EXISTS {
      ?item wdt:P3454|wdt:P3473|wdt:P3463 ?arch.
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
    if url != "" and url[-1] == '/':
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
    archclaim = pywikibot.Claim(repo, 'P3454', datatype='external-id')
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
    debianname = getvalue(software, 'debianLabel').lower()
    if name == "":
        print("Item without name: ", qid)
        continue
    website = normurl(getvalue(software, 'website'))
    description = normurl(getvalue(software, 'itemDescription'))
    searchres = runquery(archurl.format(name))
    if len(searchres) == 1:
        website2 = normurl(searchres[0]['url'])
        name2 = normurl(searchres[0]['pkgname'])
        if not (qid in done):
            print("")
            print(Style.BRIGHT + "Potential Match: ", end="")
            print(Fore.GREEN + name + " - " + name2)
            print(Fore.RED + website)
            if (website != website2):
                print(Fore.RED + website2 + Style.RESET_ALL)
            print(Style.RESET_ALL + description)
            print(searchres[0]['pkgdesc'])
            securematch = website == website2 and name == name2
            if securematch or ask("Write?"):
                addRepoToItem(qid, name2)
                done.append(qid)
