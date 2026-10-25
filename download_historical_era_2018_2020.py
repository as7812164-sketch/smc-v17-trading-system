import urllib.request
import json
import time
import os
import sys
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COINS_2018 = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT", "LTCUSDT",
    "TRXUSDT", "ETCUSDT", "EOSUSDT", "NEOUSDT", "VETUSDT"
]

COINS_2019 = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT", "LTCUSDT",
    "TRXUSDT", "ETCUSDT", "EOSUSDT", "NEOUSDT", "VETUSDT", "LINKUSDT",
    "THETAUSDT", "ALGOUSDT", "DOGEUSDT"
]

DIR_2018 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2018_2019")
DIR_2019 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2019_2020")
os.makedirs(DIR_2018, exist_ok=True)
os.makedirs(DIR_2019, exist_ok=True)

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
    print(" 📥 DOWNLOADING HISTORICAL BINANCE DATA FOR 2018-2019 AND 2019-2020 ERAS")
    print("=" * 90)

    # Era 1: 2018-01-01 00:00:00 UTC (1514764800000) to 2019-01-01 00:00:00 UTC (1546300800000)
    start_2018 = 1514764800000
    end_2018 = 1546300800000

    # Era 2: 2019-01-01 00:00:00 UTC (1546300800000) to 2020-01-01 00:00:00 UTC (1577836800000)
    start_2019 = 1546300800000
    end_2019 = 1577836800000

    tasks = []
    # 2018 tasks
    for sym in COINS_2018:
        for itv in ["1h", "4h"]:
            tasks.append((sym, itv, start_2018, end_2018, DIR_2018, "2018-2019"))

    # 2019 tasks
    for sym in COINS_2019:
        for itv in ["1h", "4h"]:
            tasks.append((sym, itv, start_2019, end_2019, DIR_2019, "2019-2020"))

    total_candles = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {
            executor.submit(download_era_history, sym, itv, s_ms, e_ms, d_dir): (sym, itv, era)
            for sym, itv, s_ms, e_ms, d_dir, era in tasks
        }
        for future in concurrent.futures.as_completed(future_map):
            sym, itv, era = future_map[future]
            try:
                s, i, count, status = future.result()
                total_candles += count
                print(f"  • [{era}] [{status:<10}] {s:<10} ({i}): {count:>5} candles")
            except Exception as e:
                print(f"  • [{era}] [ERROR]      {sym:<10} ({itv}): {e}")

    print("=" * 90)
    print(f"✅ Download Complete! Total Historical Candlesticks: {total_candles:,}")

if __name__ == "__main__":
    main()
