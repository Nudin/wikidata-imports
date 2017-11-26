#!/bin/env python3
import requests
import xml.etree.ElementTree as ET


apiurl = "https://www.openhub.net/p/%s.xml?api_key=%s"
url = apiurl % ("inkscape", open("mykey").readline()[:-1])
r = requests.get(url)
if r.status_code != 200:
    print("Error")
    exit
root = ET.fromstring(r.text)
print(root.find("result/project/analysis/main_language_name").text)

