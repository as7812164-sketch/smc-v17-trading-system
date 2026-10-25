with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
sw = re.findall(r'serviceWorker[^\n;]*', text)
print("ServiceWorker occurrences:", sw)
sw_reg = re.findall(r'navigator\.serviceWorker\.register[^\n;]*', text)
print("ServiceWorker registrations:", sw_reg)

# Check manifest.json
print("Manifest link in HTML:", "manifest.json" in text)
