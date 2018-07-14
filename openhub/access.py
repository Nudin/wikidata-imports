#!/usr/bin/env python3
import pywikibot

from oloho import oloho_getdata
from wikidata import (create_andor_source, create_claim, create_target,
                      createsource, get_mapping, runquery, wikidata)

query = """
SELECT DISTINCT ?item ?itemLabel ?openhubname WHERE
{
  ?item wdt:P1972 ?openhubname.
  MINUS { ?item wdt:P31*/wdt:P279* wd:Q9135 }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
"""

mainapi = "p/{}.xml"
enlistmentsapi = "p/{}/enlistments.xml"


lang_dict = get_mapping("P277")
lang_dict["C"] = "Q15777"
lang_dict["Java"] = "Q251"

license_dict = get_mapping("P275")
license_dict['BSD 3-clause "New" or "Revised" License'] = "Q18491847"
license_dict["GNU General Public License v3.0 only"] = "Q10513445"

f = open("unmatched_license_lang", "w")

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
        print("", repo_url, repo_type)
        source = createsource(
            "https://www.openhub.net/p/{}/enlistments".format(openhubname),
            "The {} Open Source Project on Open Hub: Code Locations Page".format(
                openhubname
            ),
        )
        target = create_target("string", repo_url)
        qualifier = create_claim("P2700", create_target("item", "Q186055"))
        create_andor_source(item, "P1324", target, qualifier, source)

    main_lang = root.findtext("result/project/analysis/main_language_name")
    if main_lang is not None:
        if main_lang in lang_dict:
            lqid = lang_dict[main_lang]
            print("", main_lang, lqid)
            source = createsource(
                "https://www.openhub.net/p/{}/analyses/latest/languages_summary".format(
                    openhubname
                ),
                "The {} Open Source Project on Open Hub: Languages Page".format(
                    openhubname
                ),
            )
            target = create_target("item", lqid)
            create_andor_source(item, "P277", target, None, source)
        else:
            f.write(main_lang + "\n")
            pass

    licensename = root.findtext("result/project/licenses/license/name")
    if licensename is not None:
        if licensename in license_dict:
            lqid = license_dict[licensename]
            print("", licensename, lqid)
            source = createsource(
                "https://www.openhub.net/p/{}/licenses".format(openhubname),
                "The {} Open Source Project on Open Hub: Licenses Page".format(
                    openhubname
                ),
            )
            target = create_target("item", lqid)
            create_andor_source(item, "P275", target, None, source)
        else:
            f.write(licensename + "\n")
            pass

    # forum = root.findtext("result/project/links/link[category='Forums']/url")
    # if forum is not None:
    #     print(forum)
    #     pass  # Wikidata-Editing
