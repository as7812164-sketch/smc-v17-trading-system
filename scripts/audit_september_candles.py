import json
import os
from datetime import datetime, timezone, timedelta

def audit_september():
    json_path = os.path.join(os.path.dirname(__file__), "..", "hermes30_1to2_oos_results.json")
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    
    with open(json_path, "r", encoding="utf-8") as f:
        res = json.load(f)
        
    trades = res["trades"]
    print(f"Auditing {len(trades)} September trades...")
    
    passed = 0
    failed_candle_not_found = 0
    failed_entry_outside = 0
    failed_resolution = 0
    
    for t in trades:
        sym = t["symbol"]
        tf = t["timeframe"].lower()
        fpath = os.path.join(hist_dir, f"{sym}_{tf}.json")
        if not os.path.exists(fpath):
            print(f"File {fpath} not found")
            continue
            
        with open(fpath, "r", encoding="utf-8") as kf:
            klines = json.load(kf)
            
        entry_ist = t["entry_time_str"]
        exit_ist = t["exit_time_str"]
        
        entry_c = None
        entry_idx = -1
        for idx, k in enumerate(klines):
            dt_ist = (datetime.fromtimestamp(k["time"] / 1000, tz=timezone.utc) + timedelta(hours=5, minutes=30)).strftime("%d %b %Y %I:%M %p IST")
            if dt_ist == entry_ist:
                entry_c = k
                entry_idx = idx
                break
                
        if not entry_c:
            # Maybe the timeframe was 1h but trade says 4h, or vice versa?
            failed_candle_not_found += 1
            continue
            
        ep = t["entry_price"]
        c_low = float(entry_c["low"])
        c_high = float(entry_c["high"])
        
        if not (c_low <= ep <= c_high):
            failed_entry_outside += 1
            print(f"Trade #{t['trade_id']} ({sym} {t['side']} {t['timeframe']}): Entry {ep} outside candle [{c_low}, {c_high}] at {entry_ist}")
            continue
            
        passed += 1

    print(f"\nSeptember Audit Summary:")
    print(f"Passed candle bounds: {passed}")
    print(f"Failed (entry outside candle): {failed_entry_outside}")
    print(f"Failed (candle not found): {failed_candle_not_found}")

if __name__ == "__main__":
    audit_september()
