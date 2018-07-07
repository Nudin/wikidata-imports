#!/bin/bash

mkdir -p versionlists
cd versionlists

curl -s https://feh.finalrewind.org/archive/  | \
   grep -e '<h1>' -e '<span class="date">' | \
   cut -d\> -f3 | \
   cut -d\< -f1 | \
   tr '\n' \#   | \
   sed 's/#\?feh v/\n/g;s/#/\t/g' > feh &

curl -s https://libvirt.org/news.html | \
   grep -o -e '[0-9.]* ([0-9-]*)'  | \
   tr -d '[()]' > libvirt &

curl -s http://www.qcad.org/en/changelog | \
   grep -P '<h2>.*</h2>' | \
   grep -oP '\b\d(\.\d+)+ +\(\d{4}/\d{2}/\d{2}\)' | \
   tr -d '[()]' > qcad &

curl -s https://pidgin.im/ChangeLog | \
   grep '^version' | \
   grep -oP '\b\d(\.\d+)+ +\(\d{2}/\d{2}/\d{4}\)' | \
   tr -d '[()]' > pidgin &

curl -s https://weechat.org/files/changelog/ChangeLog-stable.html | \
   grep -o '[0-9.]\+ +([0-9-]\+)' | \
   tr -d '[()]' > weechat &

lynx --dump https://sqlite.org/chronology.html | \
   awk '/\[[0-9]+\]20[0-9-]+ *(\[[0-9]+\])?[0-9.]+/ {
	    gsub(/\[[0-9]+\]/, "");
	    print $2,$1
	 }' | \
   uniq > sqlite &

curl -s "https://sourceforge.net/p/clisp/clisp/ci/default/tree/src/NEWS?format=raw" | \
   grep -P '^\d+(.\d+)+ \(\d{4}-\d{2}-\d{2}\)$' | \
   tr -d '[()]' > clisp &

curl -s ftp://sources.redhat.com/pub/lvm2/WHATS_NEW | \
   awk -F\  '/^Version [0-9.]+ - [0-9]+\w\w \w+ [0-9]+/ {
	 print $2" "gensub(/[a-z]{2}/, "", "g", $4)"."$5"."$6
      }' > lvm2 &

curl -s https://raw.githubusercontent.com/file/file/master/ChangeLog | \
   grep -B2 '* release 5\...' | \
   grep -o -E '^20..-..-..|release 5\...' | \
   sed 's/release //' | \
   paste - - | \
   awk '{print $2,$1}' > file &

curl -s https://download.qemu.org/ | \
   grep -E 'qemu-[0-9]\.[0-9]+\.[0-9]+\.tar.xz.sig' | \
   grep -o -E '"qemu-[0-9]\.[0-9]+\.[0-9]+\.tar.xz.sig"|20[0-9]{2}-[0-9]{2}-[0-9]{2}' | \
   sed 's/"qemu-\(.*\).tar.xz.sig"/\1/' | \
   paste - - > qemu &

curl -s https://mupdf.com/news.html | \
   grep -P '^MuPDF \d.\d \(20\d\d-\d\d-\d\d\)$' | \
   tr -d '[()]' | \
   cut -d\  -f2,3 > mupdf &

curl -s https://raw.githubusercontent.com/hashicorp/vagrant/master/CHANGELOG.md | \
   grep -P '## \d(.\d+)+ (.*)$' | \
   sed 's/## //;s/ (/\t/;s/,\? /-/g;s/)//' > vagrant &

curl -s http://links.twibright.com/download/ChangeLog | \
   grep -A2 '^=== RELEASE [0-9.]\+ ===$' | \
   sed -E 's/=== RELEASE (.*) ===/\1/;s/^(\S+ \S+ +\S+) \S+ \S+[A-Z ]*([0-9]{4}).*$/\1 \2/' | \
   grep -v '^-*$' | \
   tr -s ' ' | tr ' ' '-' | \
   paste - - > links &

curl -s https://www.fossil-scm.org/index.html/doc/trunk/www/changes.wiki | \
   grep -i "Changes For Version" | \
   tr '[()]' ' ' | \
   cut -d\  -f4,6 > fossil &

echo "Waiting for downloads to complete…"
wait

# TODO:
# gimp
# pacman
# sqlitebrowser
