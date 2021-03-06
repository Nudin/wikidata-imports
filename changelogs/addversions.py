#!/bin/env python3
import csv
import datetime
import hashlib
import re
import signal
import sys
from os.path import join

import pywikibot

site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()
today = datetime.date.today()
wbtoday = pywikibot.WbTime(year=today.year, month=today.month, day=today.day)

selected = None
if len(sys.argv) > 1:
    selected = sys.argv[1]
doexit = False


def signal_handler(signal, frame):
    global doexit
    print('You pressed Ctrl+C! - stopping')
    doexit = True


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def check_md5file(fname):
    md5fname = fname + '.md5'
    md5sum = md5(fname)
    try:
        with open(md5fname, "r+") as f:
            if f.read() == md5sum:
                return True
            else:
                f.seek(0)
                f.write(md5sum)
    except FileNotFoundError:
        with open(md5fname, "w") as f:
            f.write(md5sum)
    return False


signal.signal(signal.SIGINT, signal_handler)

with open('conf.csv', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        qid = row[0]
        filename = join("versionlists", row[1])
        dateformat = row[2]
        srcurl = row[3]
        srctitle = row[4]
        if doexit:
            break
        if selected is not None and filename != selected:
            continue
        if check_md5file(filename):
            print("Passing {}, due to no change".format(filename))
            continue
        print("==", qid, filename, "==")

        # Quelle – eine für alle Einträge
        statedin = pywikibot.Claim(repo, 'P854')
        statedin.setTarget(srcurl)
        title = pywikibot.Claim(repo, 'P1476')
        title.setTarget(pywikibot.WbMonolingualText(srctitle, "en"))
        retrieved = pywikibot.Claim(repo, 'P813')
        retrieved.setTarget(wbtoday)

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
            try:
                date = datetime.datetime.strptime(datestr, dateformat).date()
            except ValueError:
                print("Wrong dateformat %s %s" % (datestr, dateformat))
                continue
            assert(date <= today)
            assert(date > datetime.date(1990, 1, 1))
            print("Adding version %s (date: %s)" % (version, date))

            claim = pywikibot.Claim(repo, 'P348', datatype='string')
            claim.setTarget(version)
            assert(re.fullmatch(r'^\d+(\.\d+)*$', version))
            item.addClaim(claim, summary=u'Adding version-number')

            qualifier = pywikibot.Claim(repo, 'P577')
            pdate = pywikibot.WbTime(date.year, date.month, date.day)
            qualifier.setTarget(pdate)
            claim.addQualifier(qualifier, summary='Adding a date of release.')

            # FIXME
            if version[0] != '0':
                claim.addQualifier(stablev, summary='Set stable version')

            claim.addSources([statedin, title, retrieved], summary='Adding source.')
