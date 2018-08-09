#!/usr/bin/env python3

import re

import pywikibot
import unidecode
from tqdm import tqdm

from oloho import get_cache_miss, oloho_getdata
from wikidata import create_claim, create_target, runquery, wikidata

query = """
SELECT DISTINCT ?item ?itemLabel ?website WHERE
{
  ?item wdt:P275 ?freelicense.
  ?freelicense (wdt:P31/wdt:P279*) wd:Q3943414.
  ?item wdt:P856 ?website.
  MINUS {?item wdt:P1972 ?openhubname}.
  MINUS { ?item wdt:P31*/wdt:P279* wd:Q9135 }.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
"""


# Normalise URL
# so that two urls with probably identical target result are identical
def normurl(url):
    if url is None:
        return ""
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
    if url != "" and url[-1] == "/":
        url = url[0:-1]
    return url


oh_api_key = open("mykey").readline()[:-1]
mainapi = "p/{}.xml"


# Get list of wikidata-items to edit
wdlist = runquery(query)

done = []
with tqdm(wdlist, postfix="Api calls: ") as t:
    for software in t:
        qid = software["item"]["value"][31:]
        softwarename = software["itemLabel"]["value"]
        website = software["website"]["value"]
        guessed_name = re.sub(r"[ .]", "_", softwarename).lower()
        guessed_name = unidecode.unidecode(guessed_name)
        guessed_name = re.sub(r"[^a-z_-]", "", guessed_name)
        if softwarename in done:
            continue

        try:
            root = oloho_getdata(mainapi, guessed_name)
            cachemiss = get_cache_miss()
            t.postfix = "Api calls: %i" % cachemiss
            item = pywikibot.ItemPage(wikidata, qid)
        except Exception as e:
            if e.args[0] == "API-Error" and e.args[1] == 401:
                t.write("API Limit Exceeded")
                break
            t.write("\n%s %s" % (guessed_name, e))
            continue
        t.write("\n={}=".format(softwarename))

        website_oh = root.findtext("result/project/homepage_url")
        if normurl(website) == normurl(website_oh):
            t.write("match!")
            item.get()
            done.append(softwarename)
            if "P1972" in item.claims:
                continue
            target = create_target("string", guessed_name)
            claim = create_claim("P1972", target)
            item.addClaim(claim)
        else:
            print(
                "URLs not matching: {} - {}".format(
                    normurl(website), normurl(website_oh)
                )
            )

        if get_cache_miss() > 950:
            t.write("Warning %s api-calls made. Exiting" % cachemiss)
            break
