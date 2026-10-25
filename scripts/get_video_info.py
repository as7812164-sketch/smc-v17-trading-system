import urllib.request
import re
import json

url = 'https://www.youtube.com/watch?v=IOBoaM71MUA'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    # Look for author
    author_m = re.search(r'"author":"([^"]+)"', html)
    print("Author:", author_m.group(1) if author_m else "Not found")

    # Look for title
    title_m = re.search(r'<title>(.*?)</title>', html)
    print("Title:", title_m.group(1) if title_m else "Not found")

    # Look for shortDescription
    desc_m = re.search(r'"shortDescription":"(.*?)"', html)
    if desc_m:
        raw_desc = desc_m.group(1)
        # unescape
        clean_desc = raw_desc.encode('utf-8').decode('unicode_escape', errors='ignore')
        print("\n--- Description ---")
        print(clean_desc)

except Exception as e:
    print("Error:", e)
