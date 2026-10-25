import urllib.request
import json
import time
import os
import sys
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

APPROVED_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "APTUSDT",
    "ARBUSDT", "OPUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", "RUNEUSDT", "RENDERUSDT",
    "INJUSDT", "FETUSDT", "THETAUSDT", "ALGOUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT", "ICPUSDT",
    "PYTHUSDT", "PEPEUSDT", "SHIBUSDT", "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOGEUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")
os.makedirs(DATA_DIR, exist_ok=True)

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
        except Exception as e:
            time.sleep(0.3 * (attempt + 1))
    return []

def download_symbol_history(sym, interval="1h", days=365):
    filepath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    
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
        # If we got fewer than 1000 or the last timestamp didn't advance, we're at the present
        if len(chunk) < 1000 or last_t <= curr_start:
            break
        curr_start = last_t + 1
        time.sleep(0.04) # Mild polite throttle
        
    # Deduplicate by timestamp in case of boundary overlaps
    seen = set()
    deduped = []
    for c in all_candles:
        if c["time"] not in seen:
            seen.add(c["time"])
            deduped.append(c)
    deduped.sort(key=lambda x: x["time"])
    
    # Save to disk
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(deduped, f)
        
    start_str = time.strftime("%Y-%m-%d", time.gmtime(deduped[0]["time"]/1000)) if deduped else "N/A"
    end_str = time.strftime("%Y-%m-%d", time.gmtime(deduped[-1]["time"]/1000)) if deduped else "N/A"
    
    return sym, interval, len(deduped), start_str, end_str

def main():
    print("=" * 85)
    print(" 📥 INSTITUTIONAL 1-YEAR HISTORICAL DATA DOWNLOADER (BINANCE 1H & 4H)")
    print(f" Target Directory: {DATA_DIR}")
    print(f" Total Symbols:    {len(APPROVED_COINS)} pairs")
    print(f" History Span:     365 Days (1 Full Year)")
    print("=" * 85)
    
    tasks = []
    for s in APPROVED_COINS:
        tasks.append((s, "1h"))
        tasks.append((s, "4h"))
        
    print(f"Total Download Tasks: {len(tasks)} (1H and 4H streams)\n")
    start_time = time.time()
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_symbol_history, s, tf): (s, tf) for s, tf in tasks}
        for f in concurrent.futures.as_completed(futures):
            sym, tf = futures[f]
            try:
                sym, interval, count, s_date, e_date = f.result()
                results.append((sym, interval, count, s_date, e_date))
                print(f"  [SAVED] {sym:10s} ({interval}) | {count:5d} candles | {s_date} ➔ {e_date}", flush=True)
            except Exception as e:
                print(f"  [ERROR] {sym:10s} ({tf}): {e}")
                
    elapsed = time.time() - start_time
    total_candles = sum(r[2] for r in results)
    
    print("\n" + "=" * 85)
    print(" ✅ 1-YEAR HISTORICAL DATA INGESTION COMPLETE")
    print("=" * 85)
    print(f"Total Files Saved to Disk:  {len(results)} JSON files")
    print(f"Total Candlesticks Stored:  {total_candles:,} bars")
    print(f"Total Elapsed Time:         {elapsed:.1f} seconds")
    print(f"Storage Location:           {DATA_DIR}")
    print("=====================================================================================")

if __name__ == "__main__":
    main()
