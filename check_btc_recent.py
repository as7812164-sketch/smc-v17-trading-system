import urllib.request
import json
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=30"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode())

for r in data:
    dt = datetime.fromtimestamp(r[0]/1000, tz=IST).strftime("%Y-%m-%d %H:%M")
    o, h, l, c, v = float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])
    color = "GREEN" if c > o else "RED"
    body_pct = abs(c - o) / o * 100
    print(f"{dt} | {color:5s} | Open:{o:8.2f} High:{h:8.2f} Low:{l:8.2f} Close:{c:8.2f} | Body:{body_pct:.2f}%")
