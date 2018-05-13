#!/bin/env python3
import requests
import urllib.parse
import pywikibot
import functools
from colorama import Fore, Style

exactsearch = True
doask = False


if exactsearch:
    archurl = 'https://www.archlinux.org/packages/search/json/?name={}&arch=any&arch=x86_64'
else:
    archurl = 'https://www.archlinux.org/packages/search/json/?q={}&arch=any&arch=x86_64'
wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT DISTINCT ?item ?itemLabel ?itemDescription ?website
WHERE
{
  # Has a website/repo
  #?item wdt:P856|wdt:P1324 ?website.
  ?item wdt:P856 ?website.


  {
      ?item wdt:P306 ?linux.
      VALUES(?linux) {
          (wd:Q388)(wd:Q174666)(wd:Q3251801)(wd:Q14656)(wd:Q11368)
      }
  }
  #{
  #    ?item wdt:P3499 ?gentoo.
  #}

  # Without Arch-Package given
  FILTER NOT EXISTS {
      ?item wdt:P3454 ?arch.
  }.

  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
"""


# Run a Query and get the results block of the returned json
@functools.lru_cache()
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
    # special treatment for kde – they often have more than one site
    # and theres never more than one kde-application with the same name
    if "kde.org" in url:
        return "kde.org"
    url = url.replace("https:", "http:")
    url = url.replace("://www.", "://")
    url = url.replace("index.html", "")
    url = url.replace("index.htm", "")
    url = url.replace("index.php", "")
    if url != "" and url[-1] == '/':
        url = url[0:-1]
    return url


# Ask a user a yes/no-question
def ask(question):
    if not doask:
        print(Fore.RED + "Doesn't match! Skipping" + Style.RESET_ALL)
        return False
    answer = input(question + " [Y/n] ")
    return (answer == "" or str.lower(answer[0]) == "y")


def getvalue(software, key):
    if key in software:
        return software[key]['value']
    else:
        return ""


def addPkgToItem(qid, name):
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
blacklist = ["python", "twine", "Q1107192", "Q28975307"]
for software in wdlist['bindings']:
    print('.', end='', flush=True)
    qid = getvalue(software, 'item')[31:]
    name = getvalue(software, 'itemLabel').lower()
    website = normurl(getvalue(software, 'website'))
    description = normurl(getvalue(software, 'itemDescription'))
    if name == "":
        print("Item without name: ", qid)
        continue
    if name in blacklist or qid in blacklist:
        continue
    searchres = runquery(archurl.format(name))
    if len(searchres) == 1:
        if qid in done:
            continue
        pkgwebsite = normurl(searchres[0]['url'])
        pkgname = normurl(searchres[0]['pkgname'])
        pkgdesc = searchres[0]['pkgdesc']
        match = website == pkgwebsite and name == pkgname
        print("")
        print(Style.BRIGHT + "Potential Match: ", end="")
        print(Fore.GREEN + name + " - " + pkgname)
        print(Fore.RED + website)
        if (website != pkgwebsite):
            print(Fore.RED + pkgwebsite + Style.RESET_ALL)
        print(Style.RESET_ALL + description)
        print(pkgdesc)
        if match or ask("Write?"):
            addPkgToItem(qid, pkgname)
            done.append(qid)
