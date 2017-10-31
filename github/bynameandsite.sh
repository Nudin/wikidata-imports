#!/bin/bash

Query="
SELECT Distinct ?item ?itemLabel ?website
WHERE
{

  ?item wdt:P856 ?website.
  FILTER REGEX(STR(?website), \"github\") .
  
  FILTER NOT EXISTS {
    ?item wdt:P1324 ?repo.
  }.

  SERVICE wikibase:label { bd:serviceParam wikibase:language \"[AUTO_LANGUAGE],en\". }
}
"

#set -x

t=$(basename $0)
resultfile="${t%%.*}-results.csv"
echo "Writing to $resultfile"

echo > $resultfile

counter=0
echo "Stating…" >&2
curl -s -H "Accept: text/csv" \
      --data-urlencode "query=${Query}" \
      https://query.wikidata.org/sparql \
 | tr -d '\015' \
 | tail -n +2 \
 | while IFS=, read qid name website; do
    echo -e "\e[A\e[KSearching for ${name}…\e[40GFound so far: ${counter}" >&2
    repo="https://github.com/${name// /_}/${name// /_}"
    httpcode=$(curl -Is -o /dev/null -w "%{http_code}" "${repo}")
    if [[ $httpcode == "200" ]]; then
      echo -e "${qid}, ${name}, $repo\e[A"
      echo "${qid}, ${name}, $repo" >> $resultfile
      ((counter++))
    fi
   done

