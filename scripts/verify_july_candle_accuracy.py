import json
import os
from datetime import datetime, timezone, timedelta

def verify_all_july_trades():
    json_path = os.path.join(os.path.dirname(__file__), "..", "hermes30_july_oos_results.json")
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    
    with open(json_path, "r", encoding="utf-8") as f:
        res = json.load(f)
        
    trades = res["trades"]
    print(f"Auditing {len(trades)} July trades against raw historical candlestick files...\n")
    
    passed = 0
    failed = 0
    
    for t in trades:
        sym = t["symbol"]
        tf = t["timeframe"].lower()
        fpath = os.path.join(hist_dir, f"{sym}_{tf}.json")
        
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
            print(f"[FAIL] Trade #{t['trade_id']} ({sym}): Entry candle at {entry_ist} not found in {fpath}!")
            failed += 1
            continue
            
        ep = t["entry_price"]
        c_low = float(entry_c["low"])
        c_high = float(entry_c["high"])
        
        if not (c_low <= ep <= c_high):
            print(f"[FAIL] Trade #{t['trade_id']} ({sym}): Entry {ep} outside candle [{c_low}, {c_high}]!")
            failed += 1
            continue
            
        side = t["side"]
        tp = t["tp_price"]
        sl = t["sl_price"]
        be_trig = (ep * 1.0150) if side == "LONG" else (ep * 0.9850)
        
        be_locked = False
        audit_outcome = None
        audit_exit_time = None
        audit_exit_price = None
        
        for bar in klines[entry_idx+1:]:
            b_h, b_l = float(bar["high"]), float(bar["low"])
            dt_bar_ist = (datetime.fromtimestamp(bar["time"] / 1000, tz=timezone.utc) + timedelta(hours=5, minutes=30)).strftime("%d %b %Y %I:%M %p IST")
            
            if side == "LONG":
                if not be_locked and b_h >= be_trig:
                    be_locked = True
                if b_h >= tp:
                    audit_outcome = "TP_HIT"
                    audit_exit_time = dt_bar_ist
                    audit_exit_price = tp
                    break
                elif b_l <= (ep if be_locked else sl):
                    audit_outcome = "BE_SAVE" if be_locked else "SL_HIT"
                    audit_exit_time = dt_bar_ist
                    audit_exit_price = ep if be_locked else sl
                    break
            else: # SHORT
                if not be_locked and b_l <= be_trig:
                    be_locked = True
                if b_l <= tp:
                    audit_outcome = "TP_HIT"
                    audit_exit_time = dt_bar_ist
                    audit_exit_price = tp
                    break
                elif b_h >= (ep if be_locked else sl):
                    audit_outcome = "BE_SAVE" if be_locked else "SL_HIT"
                    audit_exit_time = dt_bar_ist
                    audit_exit_price = ep if be_locked else sl
                    break
                    
        match_outcome = (audit_outcome == t["outcome"])
        match_exit_time = (audit_exit_time == exit_ist)
        match_exit_price = (abs(audit_exit_price - t["exit_price"]) < 1e-5)
        
        if match_outcome and match_exit_time and match_exit_price:
            passed += 1
            print(f"[VERIFIED 100%] Trade #{t['trade_id']} | {sym} {side} {t['timeframe']} | Entry: {entry_ist} @ {ep} | Exit: {exit_ist} ({t['outcome']}) | Matched!")
        else:
            print(f"[MISMATCH] Trade #{t['trade_id']} | Recorded: {t['outcome']} at {exit_ist} vs Audited: {audit_outcome} at {audit_exit_time}")
            failed += 1
            
    print(f"\n==========================================")
    print(f"AUDIT SUMMARY: {passed} PASSED / {failed} FAILED (Total {len(trades)})")
    print(f"Accuracy: {passed / len(trades) * 100:.2f}%")
    print(f"==========================================")

if __name__ == "__main__":
    verify_all_july_trades()
