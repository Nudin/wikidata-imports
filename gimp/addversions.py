#!/bin/env python3
import pywikibot

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

gimp = 'Q8038'

# Quelle – eine für alle Einträge
statedin = pywikibot.Claim(repo, 'P854')
statedin.setTarget("https://www.gimp.org/about/history.html")
title = pywikibot.Claim(repo, 'P1476')
title.setTarget(pywikibot.WbMonolingualText("GIMP History", "en"))
retrieved = pywikibot.Claim(repo, 'P813')
date = pywikibot.WbTime(year=2017, month=11, day=11)        # TODO: set today
retrieved.setTarget(date)


for line in open('gimp-versions'):
    [date, _, version] = line.split()
    item = pywikibot.ItemPage(repo, gimp)
    item.get()
    # Check if version is already there
    if version in map(lambda x: x.getTarget(), item.claims['P348']):
        continue
    print("Adding version %s" % version)

    claim = pywikibot.Claim(repo, 'P348', datatype='string')
    claim.setTarget(version)
    item.addClaim(claim, summary=u'Adding version-number')

    qualifier = pywikibot.Claim(repo, 'P577')
    [year, month, day] = date.split('-')
    pdate = pywikibot.WbTime(int(year), int(month), int(day))
    qualifier.setTarget(pdate)
    claim.addQualifier(qualifier, summary='Adding a date of release.')

    claim.addSources([statedin, title, retrieved], summary='Adding source.')
    exit
