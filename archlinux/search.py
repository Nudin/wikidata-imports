#!/bin/env python3
import requests
import urllib.parse
import pywikibot


archurl = 'https://www.archlinux.org/packages/search/json/?name={}'
wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT DISTINCT ?item ?itemLabel ?website
WHERE
{
  {
    ?item wdt:P856 ?website.
  } UNION {
      ?item wdt:P1324 ?website.
  }

  #{
      ?item wdt:P306 ?linux.
      VALUES(?linux) {
          (wd:Q388)(wd:Q174666)(wd:Q3251801)(wd:Q14656)(wd:Q11368)
      }
  #} UNION {
  #    ?item wdt:P3499 ?gentoo.
  #}

  FILTER NOT EXISTS {
      ?item wdt:P3454 ?arch.
  }.
  ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = "en") .
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
    # special treatment for kde – they often have more than one site
    # and theres never more than one kde-application with the same name
    if "kde.org" in url:
        return "kde.org"
    url = url.replace("https:", "http:")
    url = url.replace("://www.", "://")
    url = url.replace("index.html", "")
    url = url.replace("index.htm", "")
    url = url.replace("index.php", "")
    if url[-1] == '/':
        url = url[0:-1]
    return url


# Ask a user a yes/no-question
def ask(question):
    answer = input(question + " [Y/n] ")
    return (answer == "" or str.lower(answer[0]) == "y")


site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

wdlist = runquery(wdqurl + urllib.parse.quote_plus(query))
softwarelist = {}
qidlist = {}
done = []
blacklist = ["python", "twine", "Q1107192"]
for software in wdlist['bindings']:
    qid = software['item']['value'][31:]
    name = software['itemLabel']['value'].replace(" ", "").lower()
    website = normurl(software['website']['value'])
    if name in blacklist or qid in blacklist:
        continue
    searchres = runquery(archurl.format(name))
    if searchres != []:
        if qid in done:
            continue
        website2 = normurl(searchres[0]['url'])
        match = website == website2
        if not match:
            print("Website not matching for %s" % name)
            print("\t%s vs %s" % (website, website2))
            if not ask("Write?"):
                continue
        print("Match " + name)
        item = pywikibot.ItemPage(repo, qid)
        archclaim = pywikibot.Claim(repo, 'P3454', datatype='external-id')
        archclaim.setTarget(name)
        item.addClaim(archclaim, summary=u'Adding arch-package name')
        done.append(qid)
