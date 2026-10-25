import re

with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

lines = text.splitlines()
for i, line in enumerate(lines, 1):
    matches = re.findall(r'font-size:\s*([0-9\.]+px)', line)
    for m in matches:
        val = float(m.replace('px', ''))
        if val < 12.0:
            print(f"Line {i}: {line.strip()[:120]}")
