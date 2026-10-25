import re

with open(r'C:\Users\power\.gemini\antigravity\brain\2f7c1ce3-13e3-479c-ae9a-e1cdceb7d3f7\.system_generated\steps\10358\content.md', 'r', encoding='utf-8') as f:
    text = f.read()

matches = set(re.findall(r'href="([^"]*smart-money-concepts[^"]*)"', text))
for m in sorted(matches):
    if 'tree' in m or 'blob' in m:
        print(m)
