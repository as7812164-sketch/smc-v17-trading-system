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

DATA_DIR_4Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_4year")
os.makedirs(DATA_DIR_4Y, exist_ok=True)

def fetch_chunk(sym, interval, start_time, end_time=None, limit=1000):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&startTime={start_time}&limit={limit}"
    if end_time:
        url += f"&endTime={end_time}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                raw = json.loads(resp.read().decode())
                return raw
        except Exception:
            time.sleep(0.3 * (attempt + 1))
    return []

def download_symbol_history(sym, interval="1h", days=1460): # 4 years = 1460 days
    filepath = os.path.join(DATA_DIR_4Y, f"{sym}_{interval}.json")
    
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
                expected_min = 32000 if interval == "1h" else 8000
                if len(existing) >= expected_min or (len(existing) >= 8000 and interval == "1h"):
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
            c_dict = {
                "time": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": int(k[6])
            }
            if not all_candles or c_dict["time"] > all_candles[-1]["time"]:
                all_candles.append(c_dict)
                
        last_t = int(chunk[-1][0])
        next_t = last_t + (3600 * 1000 if interval == "1h" else 4 * 3600 * 1000)
        if next_t <= curr_start:
            break
        curr_start = next_t
        time.sleep(0.05)
        
    if all_candles:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(all_candles, f)
        return sym, interval, len(all_candles), "DOWNLOADED"
    return sym, interval, 0, "FAILED"

def main():
    print("=" * 80)
    print("🚀 DOWNLOADING 4 FULL YEARS (2022-2026) CANDLESTICK DATA FOR TOP-22 CHAMPIONS")
    print(f"Target Directory: {DATA_DIR_4Y}")
    print("=" * 80)
    
    tasks = []
    for sym in TOP_22_CHAMPIONS:
        tasks.append((sym, "1h"))
        tasks.append((sym, "4h"))
        
    start_t = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(download_symbol_history, sym, interval): (sym, interval) for sym, interval in tasks}
        for fut in concurrent.futures.as_completed(futures):
            sym, interval = futures[fut]
            try:
                s, iv, count, status = fut.result()
                print(f"[{status}] {s:<12} {iv:<4} -> {count:>6} candles")
            except Exception as e:
                print(f"[ERROR] {sym} {interval}: {e}")
                
    elapsed = time.time() - start_t
    print(f"\n✅ All 4-Year data tasks completed in {elapsed:.1f}s.")

if __name__ == "__main__":
    main()
