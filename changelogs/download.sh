#!/bin/bash

curl https://feh.finalrewind.org/archive/  | \
   grep -e '<h1>' -e '<span class="date">' | \
   cut -d\> -f3 | \
   cut -d\< -f1 | \
   tr '\n' \#   | \
   sed 's/#\?feh v/\n/g;s/#/\t/g' > feh

curl https://libvirt.org/news.html | \
   grep -o -e '[0-9.]* ([0-9-]*)'  | \
   tr -d '[()]' > libvirt

curl http://www.qcad.org/en/changelog | \
   grep -P '<h2>.*</h2>' | \
   grep -oP '\b\d(\.\d+)+ +\(\d{4}/\d{2}/\d{2}\)' | \
   tr -d '[()]' > qcad

curl https://pidgin.im/ChangeLog | \
   grep '^version' | \
   grep -oP '\b\d(\.\d+)+ +\(\d{2}/\d{2}/\d{4}\)' | \
   tr -d '[()]' > pidgin

curl https://weechat.org/files/changelog/ChangeLog-stable.html | \
   grep -o '[0-9.]\+ +([0-9-]\+)' | \
   tr -d '[()]' > weechat

lynx --dump https://sqlite.org/chronology.html | \
   awk '/\[[0-9]+\]20[0-9-]+ *(\[[0-9]+\])?[0-9.]+/ {
	    gsub(/\[[0-9]+\]/, "");
	    print $2,$1
	 }' | \
   uniq > sqlite

curl "https://sourceforge.net/p/clisp/clisp/ci/default/tree/src/NEWS?format=raw" | \
   grep -P '^\d+(.\d+)+ \(\d{4}-\d{2}-\d{2}\)$' | \
   tr -d '[()]' > clisp

curl ftp://sources.redhat.com/pub/lvm2/WHATS_NEW | \
   awk -F\  '/^Version [0-9.]+ - [0-9]+\w\w \w+ [0-9]+/ {
	 print $2" "gensub(/[a-z]{2}/, "", "g", $4)"."$5"."$6
      }' > lvm2

# TODO:
# gimp
# pacman
# sqlitebrowser
