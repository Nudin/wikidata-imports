Query Open Hub for data for Wikidata
====================================

access.py
    Read all items with an Open Hub identifier and search Open Hub for information.
    Currently the following informations get imported:
     - Code repository
     - license
     - programing language

match.py
    Search for items missing an Open Hub identifier. Match items when theire
    names and websited match.

TODO:
 - If one of the two API calls fails, don't skip it the item entirely
 - Log failed API calls
 - Count added repos
 - Handle cases when data on wikidata and open hub disagrees
 - Handle multible repositories
 - Write Game-API for matches with different URLs https://bitbucket.org/magnusmanske/wikidata-game/src/master/public_html/distributed/?at=master
