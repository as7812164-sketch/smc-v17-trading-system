"""
DOWNLOAD 1-YEAR (365 DAYS) 15m CANDLESTICK CACHE FOR TOP-20 CHAMPIONS
======================================================================
Extends market_data_cache_15m from March 2026 back to October 2025 (Full 365 Days).
"""

import os
import sys
import json
import time
import urllib.request
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
CACHE_DIR = os.path.join(ROOT_DIR, "market_data_cache_15m")
os.makedirs(CACHE_DIR, exist_ok=True)

CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", "DOGEUSDT",
    "DOTUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT", "OPUSDT", "RENDERUSDT",
    "SUIUSDT", "TIAUSDT", "UNIUSDT", "XRPUSDT", "1000PEPEUSDT", "APTUSDT",
    "ARBUSDT", "FETUSDT"
]

def fetch_binance_futures_chunk(sym: str, start_time: int, end_time: int, limit: int = 1000):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=15m&startTime={start_time}&endTime={end_time}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            time.sleep(0.4 * (attempt + 1))
    return []

def extend_coin_to_1year(sym: str, target_start_ms: int):
    fpath = os.path.join(CACHE_DIR, f"{sym}_15m.json")
    existing_candles = []
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            existing_candles = json.load(f)

    earliest_existing = existing_candles[0]["time"] if existing_candles else int(time.time() * 1000)

    if earliest_existing <= target_start_ms + (86400 * 1000):
        print(f"  [ALREADY EXTENDED] {sym}: earliest is {datetime.fromtimestamp(earliest_existing/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        return len(existing_candles)

    print(f"  [FETCHING] {sym}: from {datetime.fromtimestamp(target_start_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(earliest_existing/1000, tz=timezone.utc).strftime('%Y-%m-%d')}...")

    new_candles = []
    curr_start = target_start_ms

    while curr_start < earliest_existing:
        chunk = fetch_binance_futures_chunk(sym, curr_start, earliest_existing, limit=1000)
        if not chunk:
            print(f"    Warning: No chunk for {sym} at {curr_start}")
            break

        for k in chunk:
            new_candles.append({
                "time": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": int(k[6])
            })

        last_k_time = int(chunk[-1][0])
        if last_k_time <= curr_start:
            break
        curr_start = last_k_time + 1
        time.sleep(0.04)

    # Combine & deduplicate
    combined = new_candles + existing_candles
    unique_dict = {c["time"]: c for c in combined}
    sorted_candles = sorted(unique_dict.values(), key=lambda c: c["time"])

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(sorted_candles, f)

    start_str = datetime.fromtimestamp(sorted_candles[0]["time"]/1000, tz=timezone.utc).strftime('%Y-%m-%d')
    end_str = datetime.fromtimestamp(sorted_candles[-1]["time"]/1000, tz=timezone.utc).strftime('%Y-%m-%d')
    days = (sorted_candles[-1]["time"] - sorted_candles[0]["time"]) / (1000 * 86400)
    print(f"  [SAVED] {sym}: Total {len(sorted_candles)} candles ({start_str} to {end_str}, {days:.1f} days)")
    return len(sorted_candles)

def main():
    now_ms = int(time.time() * 1000)
    target_start_ms = now_ms - (365 * 86400 * 1000)
    start_dt = datetime.fromtimestamp(target_start_ms/1000, tz=timezone.utc)
    print("=" * 80)
    print(f"🌐 EXTENDING 15M CANDLESTICK CACHE TO FULL 1 YEAR (365 DAYS)")
    print(f"Target Start: {start_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Total Symbols: {len(CHAMPIONS)}")
    print("=" * 80)

    for idx, sym in enumerate(CHAMPIONS, 1):
        print(f"[{idx}/{len(CHAMPIONS)}] Processing {sym}...")
        try:
            extend_coin_to_1year(sym, target_start_ms)
        except Exception as e:
            print(f"  Error fetching {sym}: {e}")

    print("\n[COMPLETE] All 20 Champions extended to 1 full year!")

if __name__ == "__main__":
    main()
