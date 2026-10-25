import urllib.request
import json

url = "http://127.0.0.1:8000/api/klines?symbol=FLOWUSDT&interval=1h&limit=500"
with urllib.request.urlopen(url) as resp:
    data = json.loads(resp.read().decode())
    print("FLOWUSDT 1H CURRENT PRICE:", data.get("current_price"))
    zones = data.get("zones", [])
    print(f"TOTAL RETURNED ZONES: {len(zones)}")
    for i, z in enumerate(zones):
        print(f"Zone {i+1}: Side={z.get('side')} | Range={z.get('ob_low'):.6f} - {z.get('ob_high'):.6f} | Status={z.get('status')} | 2nd={z.get('is_2nd_ob')} | Prob={z.get('prob_score')}%")
