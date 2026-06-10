from time import sleep
import os
import requests
import json
import re

### exemple donné pour vatlat4756

MANIFEST_URL = "https://digi.vatlib.it/iiif/MSS_Vat.lat.4756/manifest.json"

r = requests.get(MANIFEST_URL)
manifest = r.json()

base = "https://digi.vatlib.it/pub/digit/MSS_Vat.lat.4756/iiif"

urls=[]

canvases = manifest["sequences"][0]["canvases"]

for canvas in canvases:
  img_url = canvas['images'][0]['resource']['service']['@id']
  m = re.search(r"Vat\.lat\.4756_(\d+)_fa_([0-9rv]+)\.jp2", img_url)
  if m is None:
    print(img_url)
    continue
  num, folio = m.groups()
  final_url = f"{base}/Vat.lat.4756_{num}_fa_{folio}.jp2/full/full/0/native.jpg"
  urls.append({'url':final_url, 'name':folio})
for url in urls:
  os.system("wget -O "+url['name']+".jpg "+url['url'])
  sleep(2)