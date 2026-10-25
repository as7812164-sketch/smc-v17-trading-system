import urllib.request
import json
from datetime import datetime

url = 'https://fapi.binance.com/fapi/v1/klines?symbol=LDOUSDT&interval=4h&limit=50'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req)
raw = json.loads(resp.read().decode())
candles = [{"time": int(d[0]), "open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4]), "vol": float(d[5])} for d in raw]

print("Last 15 candles on LDO 4H:")
for idx, c in enumerate(candles[-15:]):
    t = datetime.fromtimestamp(c['time']/1000).strftime('%Y-%m-%d %H:%M')
    print(f"[{idx}] {t} | O: {c['open']:.4f} | H: {c['high']:.4f} | L: {c['low']:.4f} | C: {c['close']:.4f}")
