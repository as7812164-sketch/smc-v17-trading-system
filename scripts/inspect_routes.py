"""Inspect routes in app.py"""
import re

with open('app.py', encoding='utf-8') as f:
    text = f.read()

routes = [m.group(1) for m in re.finditer(r'@app\.(?:get|post)\([\'"]([^\'"]+)[\'"]', text)]
for r in routes:
    if any(k in r for k in ['ticker', 'kline', 'market', 'trade', 'order']):
        print('Route:', r)
