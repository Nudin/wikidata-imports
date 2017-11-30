#!/usr/bin/env python3
import requests
import urllib.parse
import xml.etree.ElementTree as ET


wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT ?item ?itemLabel ?openhubname WHERE 
{
  ?item wdt:P1972 ?openhubname.
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
    openhubname = software['itemLabel']['value']
    softwarename = software['openhubname']['value']

    url = apiurl % (softwarename, key)
    r = requests.get(url)
    if r.status_code != 200:
        print("Error")
        exit
    root = ET.fromstring(r.text)
    openhub_url=root.find("result/project/html_url")
    main_lang=root.find("result/project/analysis/main_language_name").text

    print(softwarename)
    print(openhubname)
    print(main_lang)
    print("")

