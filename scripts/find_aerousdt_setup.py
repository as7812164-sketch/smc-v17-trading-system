import json
import urllib.request
import datetime
import sys
import os

sys.path.append(os.getcwd())
from engine.hermes30_apex_live import hermes30_live_engine

url = "https://fapi.binance.com/fapi/v1/klines?symbol=AEROUSDT&interval=4h&limit=100"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    raw_klines = json.loads(resp.read().decode('utf-8'))

candles = []
for k in raw_klines:
    candles.append({
        "time": k[0],
        "open": float(k[1]),
        "high": float(k[2]),
        "low": float(k[3]),
        "close": float(k[4]),
        "volume": float(k[5]),
    })

btc_sentry = {"long_veto": False, "short_veto": False}
for end_idx in range(len(candles)-15, len(candles)+1):
    sub = candles[:end_idx]
    setups = hermes30_live_engine.detect_apex_setups_on_candles("AEROUSDT", sub, "4h", btc_sentry)
    for s in setups:
        if abs(s['entry_price'] - 0.8435) < 0.05:
            print(f"AERO MATCH at end_idx={end_idx}! Setup: {s}")
            break
