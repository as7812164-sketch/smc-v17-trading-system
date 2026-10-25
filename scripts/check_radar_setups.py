import sys
import os
import json
import urllib.request

url = "https://smc-ai-agent.onrender.com/api/deca/setups"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Setups fetched from Render: {len(data)}")
        for s in data[:5]:
            print(f"{s.get('symbol')} {s.get('side')} ({s.get('interval')}) | Entry: {s.get('entry_price')} | Dist: {s.get('proximity_pct', s.get('distance_pct', 'N/A'))}% | Status: {s.get('status')}")
except Exception as e:
    print(f"Error: {e}")
