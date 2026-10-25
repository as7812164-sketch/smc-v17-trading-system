with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
m = re.findall(r'function refreshAllData[^{]*\{[^}]*\}', text)
print("refreshAllData function:", m)

for btn in re.finditer(r'class=["\'][^"\']*refresh[^"\']*["\'][^>]*>', text):
    print("Refresh button in HTML:", btn.group(0))
