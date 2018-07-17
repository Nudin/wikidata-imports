import datetime
import urllib.parse

import pywikibot
import requests

wdqurl = "https://query.wikidata.org/sparql?format=json&query="

site = pywikibot.Site("wikidata", "wikidata")
wikidata = site.data_repository()

_today = datetime.date.today()
today = pywikibot.WbTime(year=_today.year, month=_today.month, day=_today.day)
openhub = pywikibot.ItemPage(wikidata, "Q124688")


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


def createsource(url_str, title_str):
    statedin = create_claim("P248", openhub)
    url = create_claim("P854", url_str)
    title = create_claim("P1476", create_target("entext", title_str))
    retrieved = create_claim("P813", today)
    return [statedin, url, title, retrieved]


def create_claim(prop, target):
    claim = pywikibot.Claim(wikidata, prop)
    claim.setTarget(target)
    return claim


def create_target(ptype, target_str):
    if ptype == "item":
        target = pywikibot.ItemPage(wikidata, target_str)
    elif ptype == "string":
        target = target_str
    elif ptype == "entext":
        target = pywikibot.WbMonolingualText(target_str, "en")
    else:
        raise NotImplementedError(ptype)
    return target


def search_sources(sources, string):
    return any([string in c.getTarget() for s in sources for c in s["P854"]])


def create_andor_source(item, prop, target, qualifier, source, logger=print):
    source_summary = "Adding Open-Hub as source"
    if prop not in item.claims:
        claim = create_claim(prop, target)
        item.addClaim(claim)
        if qualifier is not None:
            claim.addQualifier(qualifier)
        claim.addSources(source, summary=source_summary)
        logger("  Successfully added")
    else:
        for claim in item.claims[prop]:
            if claim.getTarget() == target and not search_sources(
                claim.sources, "openhub"
            ):
                claim.addSources(source, summary=source_summary)
                logger("  Successfully sourced")
