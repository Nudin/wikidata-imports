Scripts to add data to Wikidata
===============================

Folder 'archlinux' – searching in the repositories of Arch Linux.

Script:
- match.py (pywikibot)
   - Search for matchings between Wikidata-items and packages in the Arch Linux
     repositories: if name and webadress match the arch-packagename is added
     to the wikidata item.
- checkversion.py
   - Compares the newest version-number set on Wikidata to the version
     available in the Arch Linux-Repositories. Prints out a Wikitext-table with
     all matches where Arch Linux has a newer version than Wikidata.
