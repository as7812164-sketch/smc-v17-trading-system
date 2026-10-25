import urllib.request
import json
import time
import os
import sys
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COINS_2020 = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT", "LTCUSDT",
    "TRXUSDT", "ETCUSDT", "EOSUSDT", "NEOUSDT", "VETUSDT", "LINKUSDT",
    "THETAUSDT", "ALGOUSDT", "DOGEUSDT"
]

DIR_2020 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2020_2021")
os.makedirs(DIR_2020, exist_ok=True)

def fetch_chunk(sym, interval, start_time, end_time, limit=1000):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&startTime={start_time}&endTime={end_time}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = json.loads(resp.read().decode())
                return raw
        except Exception:
            time.sleep(0.3 * (attempt + 1))
    return []

def download_era_history(sym, interval, start_ms, end_ms, out_dir):
    filepath = os.path.join(out_dir, f"{sym}_{interval}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                d = json.load(f)
                if len(d) >= 1500:
                    return sym, interval, len(d), "CACHED"
        except Exception:
            pass

    all_candles = []
    curr_start = start_ms
    
    while curr_start < end_ms:
        chunk = fetch_chunk(sym, interval, curr_start, end_ms, limit=1000)
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
        next_t = last_t + (3600 * 1000 if interval == "1h" else 4 * 3600 * 1000)
        if next_t <= curr_start:
            break
        curr_start = next_t
        time.sleep(0.04)

    seen = set()
    clean = []
    for c in all_candles:
        if c["time"] not in seen:
            seen.add(c["time"])
            clean.append(c)
    clean.sort(key=lambda x: x["time"])

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(clean, f)

    return sym, interval, len(clean), "DOWNLOADED"

def main():
    print("=" * 90)
    print(" 📥 DOWNLOADING HISTORICAL BINANCE DATA FOR 2020-2021 (COVID CRASH & RECOVERY)")
    print("=" * 90)

    # Era 2020: 2020-01-01 00:00:00 UTC (1577836800000) to 2021-01-01 00:00:00 UTC (1609459200000)
    start_2020 = 1577836800000
    end_2020 = 1609459200000

    tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for sym in COINS_2020:
            tasks.append(executor.submit(download_era_history, sym, "4h", start_2020, end_2020, DIR_2020))
            tasks.append(executor.submit(download_era_history, sym, "1h", start_2020, end_2020, DIR_2020))

        total_candles = 0
        for future in concurrent.futures.as_completed(tasks):
            sym, interval, count, status = future.result()
            total_candles += count
            print(f"  • [2020-2021] [{status}] {sym:<10} ({interval}): {count:>5} candles")

    print("=" * 90)
    print(f"✅ 2020-2021 Download Complete! Total Historical Candlesticks: {total_candles:,}")

if __name__ == "__main__":
    main()
