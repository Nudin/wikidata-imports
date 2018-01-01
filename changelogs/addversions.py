#!/bin/env python3
import pywikibot
import datetime
import csv

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

with open('conf.csv', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        qid = row[0]
        filename = row[1]
        dateformat = row[2]
        srcurl = row[3]
        srctitle = row[4]
        print("==", qid, filename, "==")

        # Quelle – eine für alle Einträge
        statedin = pywikibot.Claim(repo, 'P854')
        statedin.setTarget(srcurl)
        title = pywikibot.Claim(repo, 'P1476')
        title.setTarget(pywikibot.WbMonolingualText(srctitle, "en"))
        retrieved = pywikibot.Claim(repo, 'P813')
        today = datetime.date.today()
        date = pywikibot.WbTime(year=today.year, month=today.month, day=today.day)
        retrieved.setTarget(date)

        for line in open(filename):
            [version, datestr] = line.split()
            date = datetime.datetime.strptime(datestr, dateformat)

            item = pywikibot.ItemPage(repo, qid)
            item.get()
            # Check if version is already there
            if version in map(lambda x: x.getTarget(), item.claims['P348']):
                continue
            print("Adding version %s" % version)

            claim = pywikibot.Claim(repo, 'P348', datatype='string')
            claim.setTarget(version)
            item.addClaim(claim, summary=u'Adding version-number')

            qualifier = pywikibot.Claim(repo, 'P577')
            pdate = pywikibot.WbTime(date.year, date.month, date.day)
            qualifier.setTarget(pdate)
            claim.addQualifier(qualifier, summary='Adding a date of release.')

            qualifier = pywikibot.Claim(repo, 'P548')
            qualifier.setTarget(pywikibot.ItemPage(repo, 'Q2804309'))
            claim.addQualifier(qualifier, summary='Set stable version')

            claim.addSources([statedin, title, retrieved], summary='Adding source.')
