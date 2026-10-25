import urllib.request
import json
import datetime

url = "https://fapi.binance.com/fapi/v1/klines?symbol=SNXUSDT&interval=5m&limit=30"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    klines = json.loads(resp.read().decode('utf-8'))

print("=== SNX 5m CANDLES (From ~14:15 to 16:35 IST) ===")
touched = False
lowest_ever = 999.0
for k in klines:
    t = datetime.datetime.fromtimestamp(k[0]/1000.0)
    o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    lowest_ever = min(lowest_ever, l)
    is_touch = l <= 0.2151
    if is_touch:
        touched = True
    print(f"{t.strftime('%H:%M')} | O:{o:.4f} H:{h:.4f} L:{l:.4f} C:{c:.4f} | Touched 0.2151? {'YES' if is_touch else 'NO'}")

print(f"\nLowest price reached in this entire window: {lowest_ever:.4f}")
print(f"Did price ever touch 0.2151? {'YES' if touched else 'NO'}")
