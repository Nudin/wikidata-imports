#!/usr/bin/env python3
import requests
import urllib.parse
import xml.etree.ElementTree as ET
import pywikibot


wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT DISTINCT ?item ?itemLabel ?openhubname WHERE
{
  ?item wdt:P1972 ?openhubname.
  MINUS { ?item wdt:P31*/wdt:P279* wd:Q9135 }.
  FILTER NOT EXISTS { ?item wdt:P277 ?lang }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
"""
lang_query = """
SELECT DISTINCT ?lang ?langLabel WHERE
{
  ?lang wdt:P31/wdt:P279* wd:Q9143.
  ?lang rdfs:label ?langLabel.
  FILTER (lang(?langLabel) = "en")
}
"""


def runquery(query):
    url = wdqurl + urllib.parse.quote_plus(query)
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["results"]['bindings']
    else:
        return None


oh_api_key = open("mykey").readline()[:-1]
apiurl = "https://www.openhub.net/p/%s.xml?api_key=%s"

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

languages = runquery(lang_query)
# short version in valid: remove duplicates!
# lang_dict = {l['langLabel']['value']: l['lang']['value'][31:] for l in languages}
bad = []
lang_dict = {}
for l in languages:
    key = l['langLabel']['value']
    if key in lang_dict:
        del lang_dict[key]
        bad.append(key)
    elif key not in bad:
        lang_dict[key] = l['lang']['value'][31:]
del bad


# Get list of wikidata-items to edit
wdlist = runquery(query)

for software in wdlist:
    qid = software['item']['value'][31:]
    softwarename = software['itemLabel']['value']
    openhubname = software['openhubname']['value']

    url = apiurl % (openhubname, oh_api_key)
    r = requests.get(url)
    if r.status_code != 200:
        print("Error\n")
        continue
    root = ET.fromstring(r.text)
    openhub_url = root.find("result/project/html_url")
    # import code
    # code.interact(local=locals())

    print(softwarename)
    print(openhubname)
    item = pywikibot.ItemPage(repo, qid)
    item.get()

    main_lang = root.findtext("result/project/analysis/main_language_name")
    if main_lang is not None:
        print(main_lang)
        if 'P277' in item.claims:
            print('is schon da')
            continue
        try:
            lqid = lang_dict[main_lang]
            print(lqid)
            claim = pywikibot.Claim(repo, 'P277')
            target = pywikibot.ItemPage(repo, lqid)
            claim.setTarget(target)
            item.addClaim(claim, summary=u'Adding language')
            print('done')
        except:
            pass

    # licensename = root.findtext("result/project/licenses/license/name")
    # if licensename is not None:
    #     print(licensename)
    #     pass  # Wikidata-Editing

    # forum = root.findtext("result/project/links/link[category='Forums']/url")
    # if forum is not None:
    #     print(forum)
    #     pass  # Wikidata-Editing

    print("")
