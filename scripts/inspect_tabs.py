import re

with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

# Find all tab panels
panels = re.findall(r'<main[^>]*id=["\'](tab-[^"\']+)["\'][^>]*>', text)
print("All tab panels:", panels)

# Check which panel has 'active' class
for p in re.finditer(r'<main[^>]*id=["\'](tab-[^"\']+)["\'][^>]*>', text):
    tag = p.group(0)
    print("Panel:", tag)

# Check bottom nav items
for nav in re.finditer(r'<button[^>]*class=["\']([^"\']*nav-item[^"\']*)["\'][^>]*>', text):
    print("Nav item:", nav.group(0))
