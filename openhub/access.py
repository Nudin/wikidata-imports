#!/usr/bin/env python3
import xml

import pywikibot
from tqdm import tqdm

import oloho
from wikidata import (create_andor_source, create_claim, create_target,
                      createsource, get_counters, get_mapping, runquery,
                      wikidata)

query = """
SELECT DISTINCT ?item ?itemLabel ?openhubname WHERE
{
  ?item wdt:P1972 ?openhubname.
  MINUS { ?item wdt:P31*/wdt:P279* wd:Q9135 }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
"""

lang_dict = get_mapping("P277")
lang_dict["c"] = "Q15777"
lang_dict["java"] = "Q251"
lang_dict["perl"] = "Q42478"

license_dict = get_mapping("P275")
license_dict['bsd 3-clause "new" or "revised" license'] = "Q18491847"
license_dict["gnu general public license v3.0 only"] = "Q10513445"
license_dict['gnu library or "lesser" gpl (lgpl)'] = "Q192897"
license_dict["bsd 4-clause (university of california-specific)"] = "Q21503790"
license_dict["gnu general public license v2.0 only"] = "Q10513450"
license_dict["creative commons attribution-sharealike 2.5"] = "Q19113751"
license_dict["mit license"] = "Q334661"
license_dict["eclipse public license 1.0"] = "Q55633170"
license_dict["gnu affero general public license 3.0 or later"] = "Q27020062"
license_dict["gpl 2"] = "Q10513450"
license_dict['bsd 2-clause "freebsd" license'] = "Q18517294"
license_dict["zlib license (aka zlib/libpng)"] = "Q207243"
license_dict["gnu lesser general public license v2.1 only"] = "Q18534390"


f = open("unmatched_license_lang", "w")

# Get list of wikidata-items to edit
wdlist = runquery(query)

with tqdm(wdlist, postfix="Api calls: ") as t:
    for software in t:
        qid = software["item"]["value"][31:]
        softwarename = software["itemLabel"]["value"]
        openhubname = software["openhubname"]["value"]

        t.write("\n= {} – {} =".format(softwarename, openhubname))
        try:
            project = oloho.getprojectdata(openhubname)
            enlistments = oloho.getenlistments(openhubname)
        except LookupError as e:
            t.write(str(e))
            continue
        except xml.etree.ElementTree.ParseError:
            t.write("No valid XML found, project was probably deleted")
            continue
        except PermissionError:
            t.write("API Limit Exceeded")
            break
        t.postfix = "Api calls: %i" % oloho.cache_miss
        item = pywikibot.ItemPage(wikidata, qid)
        item.get()

        # openhub_url = project.find("html_url")

        if len(enlistments) == 1:
            repo_url = enlistments[0].findtext("code_location/url")
            repo_type = enlistments[0].findtext("code_location/type")
            if repo_type != "git":
                continue
            t.write(" {} - {}".format(repo_url, repo_type))
            source = createsource(
                "https://www.openhub.net/p/{}/enlistments".format(openhubname),
                "The {} Open Source Project on Open Hub: Code Locations Page".format(
                    openhubname
                ),
            )
            target = create_target("string", repo_url)
            qualifier = create_claim("P2700", create_target("item", "Q186055"))
            create_andor_source(item, "P1324", target, qualifier, source, t.write)

        main_lang = project.findtext("analysis/main_language_name")
        if main_lang is not None:
            main_lang = main_lang.lower()
            if main_lang in lang_dict:
                lqid = lang_dict[main_lang]
                t.write(" {} - {}".format(main_lang, lqid))
                source = createsource(
                    "https://www.openhub.net/p/{}/analyses/latest/languages_summary".format(
                        openhubname
                    ),
                    "The {} Open Source Project on Open Hub: Languages Page".format(
                        openhubname
                    ),
                )
                target = create_target("item", lqid)
                create_andor_source(item, "P277", target, None, source, t.write)
            else:
                f.write(main_lang + "\n")
                f.flush()
                pass

        licensename = project.findtext("licenses/license/name")
        if licensename is not None:
            licensename = licensename.lower()
            if licensename in license_dict:
                lqid = license_dict[licensename]
                t.write(" {} - {}".format(licensename, lqid))
                source = createsource(
                    "https://www.openhub.net/p/{}/licenses".format(openhubname),
                    "The {} Open Source Project on Open Hub: Licenses Page".format(
                        openhubname
                    ),
                )
                target = create_target("item", lqid)
                create_andor_source(item, "P275", target, None, source, t.write)
            else:
                f.write(licensename + "\n")
                f.flush()
                pass

        # forum = project.findtext("links/link[category='Forums']/url")
        # if forum is not None:
        #     t.write(forum)
        #     pass  # Wikidata-Editing


t.write("Added {} statements & sourced {} existing statements".format(*get_counters()))
