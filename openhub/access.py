#!/usr/bin/env python3
import requests
import urllib.parse
import xml.etree.ElementTree as ET


wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT ?item ?itemLabel ?openhubname WHERE 
{
  ?item wdt:P1972 ?openhubname.
  MINUS { ?item wdt:P31*/wdt:P279* wd:Q9135 }.
  FILTER NOT EXISTS { ?item wdt:P277 ?lang }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
"""

def runquery(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["results"]
    else:
        return None


key = open("mykey").readline()[:-1]
apiurl = "https://www.openhub.net/p/%s.xml?api_key=%s"

wdlist = runquery(wdqurl + urllib.parse.quote_plus(query))

for software in wdlist['bindings']:
    qid = software['item']['value'][31:]
    softwarename = software['itemLabel']['value']
    openhubname = software['openhubname']['value']

    url = apiurl % (openhubname, key)
    r = requests.get(url)
    if r.status_code != 200:
        print("Error\n")
        continue
    root = ET.fromstring(r.text)
    openhub_url=root.find("result/project/html_url")
    #import code
    #code.interact(local=locals())

    print(softwarename)
    print(openhubname)
    main_lang=root.findtext("result/project/analysis/main_language_name")
    if main_lang is not None:
        print(main_lang)
        pass # Wikidata-Editing

    licensename=root.findtext("result/project/licenses/license/name")
    if licensename is not None:
        print(licensename)
        pass # Wikidata-Editing

    forum=root.findtext("result/project/links/link[category='Forums']/url")
    if forum is not None:
        print(forum)
        pass # Wikidata-Editing

    print("")

