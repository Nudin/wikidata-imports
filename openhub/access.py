#!/usr/bin/env python3
import requests
import urllib.parse
import xml.etree.ElementTree as ET
import pywikibot
import datetime


wdqurl = 'https://query.wikidata.org/sparql?format=json&query='
query = """
SELECT DISTINCT ?item ?itemLabel ?openhubname WHERE
{
  ?item wdt:P1972 ?openhubname.
  MINUS { ?item wdt:P31*/wdt:P279* wd:Q9135 }.
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
license_query = """
SELECT DISTINCT ?license ?licenseLabel WHERE
{
  ?item wdt:P275 ?license.
  ?license rdfs:label|skos:altLabel ?licenseLabel.
  FILTER (lang(?licenseLabel) = "en")
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

licenses = runquery(license_query)
bad = []
license_dict = {}
for l in licenses:
    key = l['licenseLabel']['value']
    if key in license_dict:
        del license_dict[key]
        bad.append(key)
    elif key not in bad:
        license_dict[key] = l['license']['value'][31:]
del bad

f = open("unmatched_license", "a")

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
    try:
        root = ET.fromstring(r.text)
        openhub_url = root.find("result/project/html_url")
    except Exception:
        print("Error parsing xml")
        continue

    print("\n{} – {}".format(softwarename, openhubname))
    item = pywikibot.ItemPage(repo, qid)
    item.get()

    statedin = pywikibot.Claim(repo, 'P854')
    statedin.setTarget("https://www.openhub.net/p/{}/analyses/latest/languages_summary"
                       .format(openhubname))
    title = pywikibot.Claim(repo, 'P1476')
    title.setTarget(pywikibot.WbMonolingualText(
        "The {} Open Source Project on Open Hub: Languages Page".format(openhubname), "en"))
    retrieved = pywikibot.Claim(repo, 'P813')
    today = datetime.date.today()
    date = pywikibot.WbTime(year=today.year, month=today.month, day=today.day)
    retrieved.setTarget(date)

    main_lang = root.findtext("result/project/analysis/main_language_name")
    if main_lang is not None and 'P277' not in item.claims:
        try:
            lqid = lang_dict[main_lang]
            print(main_lang, lqid)
            claim = pywikibot.Claim(repo, 'P277')
            target = pywikibot.ItemPage(repo, lqid)
            claim.setTarget(target)
            item.addClaim(claim, summary=u'Adding language')
            claim.addSources([statedin, title, retrieved], summary='Adding source.')
            print('Added language')
        except Exception:
            pass

    statedin = pywikibot.Claim(repo, 'P854')
    statedin.setTarget("https://www.openhub.net/p/{}/licenses"
                       .format(openhubname))
    title = pywikibot.Claim(repo, 'P1476')
    title.setTarget(pywikibot.WbMonolingualText(
        "The {} Open Source Project on Open Hub: Licenses Page".format(openhubname), "en"))
    retrieved = pywikibot.Claim(repo, 'P813')
    today = datetime.date.today()
    date = pywikibot.WbTime(year=today.year, month=today.month, day=today.day)
    retrieved.setTarget(date)

    licensename = root.findtext("result/project/licenses/license/name")
    if licensename is not None and 'P275' not in item.claims:
        print(licensename)
        try:
            lqid = license_dict[licensename]
            print(licensename, lqid)
            claim = pywikibot.Claim(repo, 'P275')
            target = pywikibot.ItemPage(repo, lqid)
            claim.setTarget(target)
            item.addClaim(claim, summary=u'Adding license')
            claim.addSources([statedin, title, retrieved], summary='Adding source.')
            print('Added language')
        except Exception:
            f.write(licensename)
            pass

    # forum = root.findtext("result/project/links/link[category='Forums']/url")
    # if forum is not None:
    #     print(forum)
    #     pass  # Wikidata-Editing
