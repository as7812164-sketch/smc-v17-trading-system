import urllib.request
import re

url = 'https://www.youtube.com/watch?v=IOBoaM71MUA'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

desc_m = re.search(r'"shortDescription":"(.*?)"', html)
if desc_m:
    raw_desc = desc_m.group(1).encode('utf-8').decode('unicode_escape', errors='ignore')
    with open('scripts/video_description.txt', 'w', encoding='utf-8') as f:
        f.write(raw_desc)
    print('Wrote video_description.txt!')
else:
    print('Description not found')
