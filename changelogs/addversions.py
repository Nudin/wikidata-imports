#!/bin/env python3
import pywikibot
import datetime
import csv
import sys
import signal
import re

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

selected = None
if len(sys.argv) > 1:
    selected = sys.argv[1]
doexit = False


def signal_handler(signal, frame):
    global doexit
    print('You pressed Ctrl+C! - stopping')
    doexit = True


signal.signal(signal.SIGINT, signal_handler)

with open('conf.csv', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        qid = row[0]
        filename = row[1]
        dateformat = row[2]
        srcurl = row[3]
        srctitle = row[4]
        if doexit:
            break
        if selected is not None and filename != selected:
            continue
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

        # Stable Version
        stablev = pywikibot.Claim(repo, 'P548')
        stablev.setTarget(pywikibot.ItemPage(repo, 'Q2804309'))

        # Get item
        item = pywikibot.ItemPage(repo, qid)
        item.get()

        for line in reversed(list(open(filename))):
            if doexit:
                break
            if len(line.split()) != 2:
                print("WARNING: line does not contain right amount of values!")
                continue
            [version, datestr] = line.split()

            # Check if version is already there
            if 'P348' in item.claims:
                if version in map(lambda x: x.getTarget(), item.claims['P348']):
                    continue
            date = datetime.datetime.strptime(datestr, dateformat)
            assert(date.date() <= today)
            assert(date.date() > datetime.date(1990, 1, 1))
            print("Adding version %s (date: %s)" % (version, date))

            claim = pywikibot.Claim(repo, 'P348', datatype='string')
            claim.setTarget(version)
            assert(re.fullmatch(r'^\d+(\.\d+)*$', version))
            item.addClaim(claim, summary=u'Adding version-number')

            qualifier = pywikibot.Claim(repo, 'P577')
            pdate = pywikibot.WbTime(date.year, date.month, date.day)
            qualifier.setTarget(pdate)
            claim.addQualifier(qualifier, summary='Adding a date of release.')

            claim.addQualifier(stablev, summary='Set stable version')

            claim.addSources([statedin, title, retrieved], summary='Adding source.')
