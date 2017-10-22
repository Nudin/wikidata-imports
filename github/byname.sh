#!/bin/bash

Query="
SELECT Distinct ?floss ?flossLabel
WHERE
{
  {
    ?floss p:P31/ps:P31/wdt:P279* wd:Q506883.
  } Union {
    ?floss p:P31/ps:P31/wdt:P279* wd:Q341.
  } Union {
    ?floss p:P31/ps:P31/wdt:P279* wd:Q1130645.
  } Union {
    ?floss p:P31/ps:P31/wdt:P279* wd:Q19652.
    ?floss p:P31/ps:P31/wdt:P279* wd:Q7397.
  } Union {
    ?floss p:P31/ps:P31/wdt:P279* wd:Q7397.
    ?floss wdt:P275 ?licens.
    ?licens p:P31/ps:P31/(wdt:P31|wdt:P279)* ?kind.
    VALUES ?kind { wd:Q196294 wd:Q1156659 }.
  }
  
  FILTER NOT EXISTS {
    ?floss wdt:P1324 ?repo.
  }.

  SERVICE wikibase:label { bd:serviceParam wikibase:language \"[AUTO_LANGUAGE],en\". }
}
"

#set -x

resultfile="${0##*.}-results.csv"

echo > $resultfile

counter=0
echo "Stating…" >&2
curl -s -H "Accept: text/csv" \
      --data-urlencode "query=${Query}" \
      https://query.wikidata.org/sparql \
 | tr -d '\015' \
 | tail -n +2 \
 | while IFS=, read qid name; do
    echo -e "\e[A\e[KSearching for ${name}…\e[40GFound so far: ${counter}" >&2
    repo="https://github.com/${name// /_}/${name// /_}"
    httpcode=$(curl -Is -o /dev/null -w "%{http_code}" "${repo}")
    if [[ $httpcode == "200" ]]; then
      echo "${qid},${name},$repo" >> $resultfile
      ((counter++))
    fi
   done

