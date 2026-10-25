with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

start = text.find('id="tab-home"')
end = text.find('id="tab-markets"')

home_content = text[start:end]
print("Home content length:", len(home_content))

# Look for headers in home tab
import re
headers = re.findall(r'<div[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>(.*?)</div>', home_content)
print("Headers in home tab:", headers)

# Check if there is an active positions strip on home tab
print("Has activePositionsStrip container?", "activePositionsStrip" in home_content)
for m in re.finditer(r'id=["\']([^"\']*pos[^"\']*)["\']', home_content):
    print("Found pos ID in home tab:", m.group(1))
