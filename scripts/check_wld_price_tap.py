import urllib.request
import json
import datetime

# 1. Fetch 1m candles for WLDUSDT between 14:00 and 14:35
url = "https://fapi.binance.com/fapi/v1/klines?symbol=WLDUSDT&interval=1m&limit=40"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    klines = json.loads(resp.read().decode('utf-8'))

print("=== WLD 1m CANDLES (Around 14:07 to 14:32 IST) ===")
for k in klines:
    t = datetime.datetime.fromtimestamp(k[0]/1000.0)
    o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    print(f"{t.strftime('%H:%M:%S')} | O:{o:.4f} H:{h:.4f} L:{l:.4f} C:{c:.4f} | Touched 0.5364? {'YES' if l <= 0.5364 else 'NO'}")
