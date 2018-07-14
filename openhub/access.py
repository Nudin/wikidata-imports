#!/usr/bin/env python3
import datetime
import urllib.parse
import xml.etree.ElementTree as ET

import pywikibot
import requests

wdqurl = "https://query.wikidata.org/sparql?format=json&query="
query = """
SELECT DISTINCT ?item ?itemLabel ?openhubname WHERE
{
  ?item wdt:P1972 ?openhubname.
  MINUS { ?item wdt:P31*/wdt:P279* wd:Q9135 }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
"""

oh_api_key = open("mykey").readline()[:-1]
apiurl = "https://www.openhub.net/p/{}.xml?api_key={}"

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

today = datetime.date.today()


def createsource(url_str, title_str):
    url = pywikibot.Claim(repo, "P854")
    url.setTarget(url_str)

    title = pywikibot.Claim(repo, "P1476")
    title.setTarget(pywikibot.WbMonolingualText(title_str, "en"))

    retrieved = pywikibot.Claim(repo, "P813")
    date = pywikibot.WbTime(year=today.year, month=today.month, day=today.day)
    retrieved.setTarget(date)

    return [url, title, retrieved]


def create_andor_source(item, prop, qid, summary, source):
    source_summary = "Adding Open-Hub as source"
    if prop not in item.claims:
        claim = pywikibot.Claim(repo, prop)
        target = pywikibot.ItemPage(repo, qid)
        claim.setTarget(target)
        item.addClaim(claim, summary=summary)
        claim.addSources(source_language, summary=source_summary)
        print("Successfully added")
    elif (
        len(item.claims[prop]) == 1
        and item.claims[prop][0].getTarget().getID() == qid
        and len(item.claims[prop][0].sources) == 0
    ):
        claim = item.claims[prop][0]
        claim.addSources(source, summary=source_summary)
        print("Successfully sourced")


def runquery(query):
    url = wdqurl + urllib.parse.quote_plus(query)
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["results"]["bindings"]
    else:
        return None


def get_mapping(prop):
    query = (
        """
    SELECT DISTINCT ?object ?label WHERE
    {
      ?item wdt:%s ?object.
      ?object rdfs:label|skos:altLabel ?label.
      FILTER (lang(?label) = "en")
    }
    """
        % prop
    )
    results = runquery(query)
    bad = []
    mapping = {}
    for l in results:
        key = l["label"]["value"]
        if key in mapping:
            del mapping[key]
            bad.append(key)
        elif key not in bad:
            mapping[key] = l["object"]["value"][31:]
    del bad
    return mapping


lang_dict = get_mapping("P277")
license_dict = get_mapping("P275")

f = open("unmatched_license", "w")

# Get list of wikidata-items to edit
wdlist = runquery(query)

for software in wdlist:
    qid = software["item"]["value"][31:]
    softwarename = software["itemLabel"]["value"]
    openhubname = software["openhubname"]["value"]

    url = apiurl.format(openhubname, oh_api_key)
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

    main_lang = root.findtext("result/project/analysis/main_language_name")
    if main_lang is not None:
        if main_lang in lang_dict:
            lqid = lang_dict[main_lang]
            print(main_lang, lqid)
            source_language = createsource(
                "https://www.openhub.net/p/{}/analyses/latest/languages_summary".format(
                    openhubname
                ),
                "The {} Open Source Project on Open Hub: Languages Page".format(
                    openhubname
                ),
            )
            create_andor_source(item, "P277", lqid, "Adding language", source_language)
        else:
            pass

    licensename = root.findtext("result/project/licenses/license/name")
    if licensename is not None:
        if licensename in license_dict:
            lqid = license_dict[licensename]
            print(licensename, lqid)
            source_license = createsource(
                "https://www.openhub.net/p/{}/licenses".format(openhubname),
                "The {} Open Source Project on Open Hub: Licenses Page".format(
                    openhubname
                ),
            )
            create_andor_source(item, "P275", lqid, "Adding license", source_license)
        else:
            f.write(licensename)
            pass

    # forum = root.findtext("result/project/links/link[category='Forums']/url")
    # if forum is not None:
    #     print(forum)
    #     pass  # Wikidata-Editing
