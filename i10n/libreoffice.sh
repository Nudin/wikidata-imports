#!/bin/bash

while read lang; do
  result=$(curl -s -d "query=$(sed "s/German/$lang/" lookupname.rq)" \
                   -d "format=json" https://query.wikidata.org/sparql)
  if [[ $(echo "$result" | wc -l) -eq 18 ]]; then
    echo "$result" \
       | jq '.results.bindings[0].item.value' \
       | tr -d \" | cut -d/ -f5
  else
    echo "Unambiguous language $lang"
    continue
  fi
done < libreoffice 
