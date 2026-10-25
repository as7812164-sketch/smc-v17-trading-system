import os
import sys
import json
import time
import urllib.request
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "historical_data")
os.makedirs(DATA_DIR, exist_ok=True)

MISSING = [
    "ATOMUSDT", "CAPUSDT", "ENAUSDT", "BZUSDT", "INTCUSDT", 
    "ORCAUSDT", "MSTRUSDT", "NMRUSDT", "TAOUSDT", "1000PEPEUSDT", "USUSDT"
]

def fetch_chunk(sym: str, interval: str, start_time: int, end_time: int = None, limit: int = 1000) -> List[Any]:
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={interval}&startTime={start_time}&limit={limit}"
    if end_time:
        url += f"&endTime={end_time}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            time.sleep(0.3 * (attempt + 1))
    return []

def download_coin(sym: str, interval: str, days: int = 365):
    filepath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if os.path.exists(filepath):
        print(f"  [EXISTS] {sym}_{interval}.json")
        return

    now_ms = int(time.time() * 1000)
    target_start_ms = now_ms - (days * 24 * 3600 * 1000)

    all_candles = []
    curr_start = target_start_ms

    while curr_start < now_ms:
        chunk = fetch_chunk(sym, interval, curr_start, end_time=now_ms, limit=1000)
        if not chunk:
            break
        for k in chunk:
            all_candles.append({
                "time": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": int(k[6])
            })
        last_t = int(chunk[-1][0])
        if last_t <= curr_start:
            break
        curr_start = last_t + 1
        if len(chunk) < 1000:
            break
        time.sleep(0.05)

    if all_candles:
        # Deduplicate
        seen = set()
        deduped = []
        for c in all_candles:
            if c["time"] not in seen:
                seen.add(c["time"])
                deduped.append(c)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(deduped, f)
        print(f"  [SAVED] {sym}_{interval}.json: {len(deduped)} candles")
    else:
        print(f"  [FAILED/EMPTY] {sym}_{interval}")

print(f"Downloading 1-year data for {len(MISSING)} missing coins...")
for sym in MISSING:
    for interval in ["4h", "1h"]:
        download_coin(sym, interval, days=365)
print("Download complete!")
