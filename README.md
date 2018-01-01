Scripts to add data to Wikidata
===============================
These is my collection of scripts mining data from different places,
to add them to Wikidata – automatically or half-automatically.

# Folders
 - archlinux
    - Search for data in the archlinux repositories and/or connect
      wikidata-items with archlinux-packages.
 - github
    - Add links to Github-repositories to wikidata-items
 - changlogs
    - Import Changlogs of various software projects to wikidata

# How to use
To run the scripts marked with (pywikibot) you need to have pywikibot installed
and an configuration-file in the working directory. To install pywikibot you
can use
```
pip install pywikibot
```
the configuration-file has to be named `user-config.py` and should contain your
user credentials:
```
mylang = "wikidata"
family = "wikidata"
usernames["wikidata"]["wikidata"] = "YourUserName"
```
