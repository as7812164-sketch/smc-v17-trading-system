import urllib.request
import json

url = "http://127.0.0.1:8000/api/klines?symbol=UNIUSDT&interval=1h&limit=500"
with urllib.request.urlopen(url) as resp:
    data = json.loads(resp.read().decode())
    print("CURRENT PRICE:", data.get("current_price"))
    print("TOTAL ZONES:", len(data.get("zones", [])))
    for i, z in enumerate(data.get("zones", [])):
        print(f"Zone {i+1}: {z.get('side')} | {z.get('ob_low')} - {z.get('ob_high')} | Status: {z.get('status')} | 2nd: {z.get('is_2nd_ob')} | Tags: {z.get('tags')}")
