import re

with open('static/mobile.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Checking viewport:")
for line in text.splitlines()[:20]:
    if 'viewport' in line:
        print("VIEWPORT:", line)

print("\nInline width styles:")
for m in re.findall(r'style="([^"]+)"', text):
    if any(k in m for k in ['width', 'min-width', 'max-width']):
        print("  -", m)
