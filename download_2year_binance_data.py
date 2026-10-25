import urllib.request
import json
import time
import os
import sys
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")
os.makedirs(DATA_DIR_2Y, exist_ok=True)

def fetch_chunk(sym, interval, start_time, end_time=None, limit=1000):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&startTime={start_time}&limit={limit}"
    if end_time:
        url += f"&endTime={end_time}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = json.loads(resp.read().decode())
                return raw
        except Exception:
            time.sleep(0.3 * (attempt + 1))
    return []

def download_symbol_history(sym, interval="1h", days=730):
    filepath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
    
    # Check if already downloaded with enough bars
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
                expected_min = 15000 if interval == "1h" else 3800
                # If coin is newer than 2 years (like SUI, PYTH), len(existing) might be smaller but still complete
                if len(existing) >= expected_min or (len(existing) >= 5000 and interval == "1h"):
                    return sym, interval, len(existing), "CACHED"
        except Exception:
            pass

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
        next_t = last_t + (3600 * 1000 if interval == "1h" else 4 * 3600 * 1000)
        if next_t <= curr_start:
            break
        curr_start = next_t
        time.sleep(0.04)
        
    # Deduplicate and sort
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
    print(" 📥 DOWNLOADING 2 FULL YEARS (730 DAYS) OF BINANCE FUTURES DATA")
    print(f" Targets: Top-22 Champions | Intervals: 1h & 4h | Directory: {DATA_DIR_2Y}")
    print("=" * 90)
    
    tasks = []
    for sym in TOP_22_CHAMPIONS:
        tasks.append((sym, "1h"))
        tasks.append((sym, "4h"))
        
    total_downloaded = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {executor.submit(download_symbol_history, sym, interval): (sym, interval) for sym, interval in tasks}
        for future in concurrent.futures.as_completed(future_map):
            sym, interval = future_map[future]
            try:
                s, itv, count, status = future.result()
                total_downloaded += count
                print(f"  • [{status:<10}] {s:<10} ({itv}): {count:>5} candles")
            except Exception as e:
                print(f"  • [ERROR]      {sym:<10} ({interval}): {e}")
                
    print("=" * 90)
    print(f"✅ Download Complete! Total Historical Candlesticks: {total_downloaded:,}")

if __name__ == "__main__":
    main()
