#!/bin/bash

curl https://libvirt.org/news.html | grep -o -e '[0-9.]* ([0-9-]*)' | tr -d '[()]' | tr ' ' '\t' > libvirt
