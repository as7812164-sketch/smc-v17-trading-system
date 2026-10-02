import os
import sys
import json
import time
import urllib.request
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TARGET_COINS = ["ORDIUSDT", "ETCUSDT", "MANAUSDT", "TIAUSDT", "AXSUSDT"]
BINANCE_BASE = "https://data-api.binance.vision/api/v3/klines"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")
os.makedirs(CACHE_DIR, exist_ok=True)

NOW_TS = int(time.time() * 1000)
ONE_YEAR_MS = 365 * 24 * 3600 * 1000
START_1Y_TS = NOW_TS - ONE_YEAR_MS

def download_full_year(symbol: str, interval: str) -> List[Dict[str, Any]]:
    cache_path = os.path.join(CACHE_DIR, f"{symbol}_{interval}.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if len(data) > 500:
                print(f"✅ [CACHE] Already exists: {symbol} {interval} ({len(data)} candles)")
                return data

    print(f"📥 [DOWNLOADING] 1-Year data for {symbol} ({interval})...")
    all_candles = []
    curr_start = START_1Y_TS

    while curr_start < NOW_TS:
        url = f"{BINANCE_BASE}?symbol={symbol}&interval={interval}&startTime={curr_start}&limit=1000"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                batch = json.loads(resp.read().decode("utf-8"))
                if not batch:
                    break
                for c in batch:
                    all_candles.append({
                        "time": int(c[0]),
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": float(c[5])
                    })
                last_ts = int(batch[-1][0])
                if last_ts <= curr_start:
                    break
                curr_start = last_ts + (3600000 if interval == "1h" else 14400000)
                time.sleep(0.08)
        except Exception as e:
            print(f"Error fetching batch: {e}")
            break

    # Deduplicate by timestamp
    seen = set()
    clean_candles = []
    for c in all_candles:
        if c["time"] not in seen:
            seen.add(c["time"])
            clean_candles.append(c)

    clean_candles.sort(key=lambda x: x["time"])
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(clean_candles, f)

    print(f"💾 [SAVED] {symbol} {interval}: {len(clean_candles)} candles.")
    return clean_candles

for sym in TARGET_COINS:
    download_full_year(sym, "1h")
    download_full_year(sym, "4h")

print("🎉 ALL 5 MISSING COINS DOWNLOADED SUCCESSFULLY!")
