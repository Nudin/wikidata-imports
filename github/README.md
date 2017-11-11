Scripts to add data to Wikidata
===============================

Folder 'github': Add links to Github-repositories to wikidata-items

Script:
 - website.py (pywikibot)
   - Search for items where a github-repo is given as official website
     and add it to the item as repo
 - byname.sh
   - A lot of Software-projects on Github have there Repo named <name>/<name>
     Search for these by brute force.


Ideas:
 - Search and replace http://github.com with https://github.com
