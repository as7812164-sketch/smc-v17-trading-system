# Let's inspect the exact prices of BTC, ETH, SOL, XRP right now and calculate the full SMC V17.5 state
import urllib.request
import json
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
results = {}

for sym in pairs:
    url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=100"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    
    candles = []
    for r in data:
        candles.append({
            "time": int(r[0]),
            "datetime": datetime.fromtimestamp(r[0]/1000, tz=IST).strftime("%Y-%m-%d %H:%M"),
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4]),
            "vol": float(r[5])
        })
    
    curr = candles[-1]
    results[sym] = {
        "current_price": curr["close"],
        "high_24h": max(c["high"] for c in candles[-24:]),
        "low_24h": min(c["low"] for c in candles[-24:]),
        "candles": candles
    }

print("Live Market Snapshots (IST):")
for sym, d in results.items():
    print(f"{sym}: Price={d['current_price']}, 24h High={d['high_24h']}, 24h Low={d['low_24h']}")
