import os
import sys
import json
import time
import ssl
import urllib.request
from datetime import datetime, timezone

CACHE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\market_data_cache_15m"
CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT",
    "DOGEUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT",
    "OPUSDT", "RENDERUSDT", "SUIUSDT", "TIAUSDT", "UNIUSDT",
    "XRPUSDT", "1000PEPEUSDT", "APTUSDT", "ARBUSDT", "FETUSDT"
]

def fetch_klines(symbol: str, start_time_ms: int) -> list:
    ctx = ssl._create_unverified_context()
    spot_symbol = symbol[4:] if symbol.startswith("1000") else symbol
    multiplier = 1000.0 if symbol.startswith("1000") else 1.0

    all_candles = []
    curr_start = start_time_ms

    for _ in range(5): # Up to 5000 candles
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={spot_symbol}&interval=15m&limit=1000&startTime={curr_start}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not data or not isinstance(data, list):
                    break
                for row in data:
                    all_candles.append({
                        "time": int(row[0]),
                        "open": float(row[1]) * multiplier,
                        "high": float(row[2]) * multiplier,
                        "low": float(row[3]) * multiplier,
                        "close": float(row[4]) * multiplier,
                        "volume": float(row[5])
                    })
                if len(data) < 1000:
                    break
                curr_start = int(data[-1][0]) + (15 * 60 * 1000)
                time.sleep(0.1)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            break

    return all_candles

print("Updating 15m cache for Sep-Oct 2026...")
for sym in CHAMPIONS:
    fpath = os.path.join(CACHE_DIR, f"{sym}_15m.json")
    existing = []
    last_ts = 0
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            existing = json.load(f)
            if existing:
                last_ts = existing[-1]["time"]

    if last_ts > 0:
        new_candles = fetch_klines(sym, last_ts + 900000)
    else:
        # Fetch from Sep 1, 2026: timestamp 1788220800000
        new_candles = fetch_klines(sym, 1788220800000)

    if new_candles:
        # Merge and deduplicate
        seen = set()
        merged = []
        for c in existing + new_candles:
            if c["time"] not in seen:
                seen.add(c["time"])
                merged.append(c)
        merged.sort(key=lambda x: x["time"])
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(merged, f)
        print(f"  [OK] {sym}: Added {len(new_candles)} new candles. Total: {len(merged)} bars (ends {datetime.fromtimestamp(merged[-1]['time']/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')})")
    else:
        print(f"  [UP-TO-DATE] {sym}: Total {len(existing)} bars")

print("\nCache update complete!")
