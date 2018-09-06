Query Open Hub for data for Wikidata
====================================

access.py
    Read all items with an Open Hub identifier and search Open Hub for information.
    Currently the following informations get imported:
     - Code repository
     - license
     - main programing language

match.py
    Search for items missing an Open Hub identifier. Match items when theire
    names and websited match.

TODO:
 - Log failed API calls
 - match:
     - Write Game-API for matches with different URLs https://bitbucket.org/magnusmanske/wikidata-game/src/master/public_html/distributed/?at=master
 - access:
     - If one of the two API calls fails, don't skip it the item entirely
     - Count added repos
     - Handle multiple licenses
     - Handle multiple repositories
     - Add Issue Trackers, Forum, etc.
     - Handle cases when data on wikidata and open hub disagrees

