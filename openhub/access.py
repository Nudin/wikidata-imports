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
mainapi = "p/{}.xml"
enlistmentsapi = "p/{}/enlistments.xml"

site = pywikibot.Site("wikidata", "wikidata")
wikidata = site.data_repository()

today = datetime.date.today()
openhub = pywikibot.ItemPage(wikidata, "Q124688")


def createsource(url_str, title_str):
    statedin = pywikibot.Claim(wikidata, "P248")
    statedin.setTarget(openhub)

    url = pywikibot.Claim(wikidata, "P854")
    url.setTarget(url_str)

    title = pywikibot.Claim(wikidata, "P1476")
    title.setTarget(pywikibot.WbMonolingualText(title_str, "en"))

    retrieved = pywikibot.Claim(wikidata, "P813")
    date = pywikibot.WbTime(year=today.year, month=today.month, day=today.day)
    retrieved.setTarget(date)

    return [statedin, url, title, retrieved]


def create_andor_source(item, prop, ptype, target, summary, source):
    source_summary = "Adding Open-Hub as source"
    if ptype == "item":
        target = pywikibot.ItemPage(wikidata, target)
    elif ptype == "string":
        target = target
    else:
        raise NotImplementedError(ptype)
    if prop not in item.claims:
        claim = pywikibot.Claim(wikidata, prop)
        claim.setTarget(target)
        item.addClaim(claim, summary=summary)
        claim.addSources(source, summary=source_summary)
        print("Successfully added")
    elif (
        len(item.claims[prop]) == 1
        and item.claims[prop][0].getTarget() == target
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


def oloho_getdata(query, olohoname):
    baseurl = "https://www.openhub.net/{}?api_key={}"
    url = baseurl.format(query.format(olohoname), oh_api_key)
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("API-Error", r.status_code)
    return ET.fromstring(r.text)


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

    print("\n{} – {}".format(softwarename, openhubname))
    try:
        root = oloho_getdata(mainapi, openhubname)
        root_enlistments = oloho_getdata(enlistmentsapi, openhubname)
        item = pywikibot.ItemPage(wikidata, qid)
        item.get()
    except Exception as e:
        print(e)
        continue

    # openhub_url = root.find("result/project/html_url")

    repos = root_enlistments.findall("result/enlistment/code_location")
    if len(repos) == 1:
        repo_url = repos[0].findtext("url")
        repo_type = repos[0].findtext("type")
        if repo_type != "git":
            continue
        print(repo_url, repo_type)
        source = createsource(
            "https://www.openhub.net/p/{}/enlistments".format(openhubname),
            "The {} Open Source Project on Open Hub: Code Locations Page".format(
                openhubname
            ),
        )
        # TODO add repo_type as qualifier
        create_andor_source(item, "P1324", "string", repo_url, "Adding repo", source)

    main_lang = root.findtext("result/project/analysis/main_language_name")
    if main_lang is not None:
        if main_lang in lang_dict:
            lqid = lang_dict[main_lang]
            print(main_lang, lqid)
            source = createsource(
                "https://www.openhub.net/p/{}/analyses/latest/languages_summary".format(
                    openhubname
                ),
                "The {} Open Source Project on Open Hub: Languages Page".format(
                    openhubname
                ),
            )
            create_andor_source(item, "P277", "item", lqid, "Adding language", source)
        else:
            pass

    licensename = root.findtext("result/project/licenses/license/name")
    if licensename is not None:
        if licensename in license_dict:
            lqid = license_dict[licensename]
            print(licensename, lqid)
            source = createsource(
                "https://www.openhub.net/p/{}/licenses".format(openhubname),
                "The {} Open Source Project on Open Hub: Licenses Page".format(
                    openhubname
                ),
            )
            create_andor_source(item, "P275", "item", lqid, "Adding license", source)
        else:
            f.write(licensename)
            pass

    # forum = root.findtext("result/project/links/link[category='Forums']/url")
    # if forum is not None:
    #     print(forum)
    #     pass  # Wikidata-Editing
