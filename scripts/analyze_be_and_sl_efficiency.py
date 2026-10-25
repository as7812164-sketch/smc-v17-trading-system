import sys
import os
import json
from datetime import datetime, timezone, timedelta

def analyze_be_and_sl_forensics():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    
    # We load datasets for the 3 months
    months = [
        {"name": "July 2026", "start_ms": 1782864000000, "end_ms": 1785542399000},
        {"name": "August 2026", "start_ms": 1785542400000, "end_ms": 1788220799000},
        {"name": "September 2026", "start_ms": 1788220800000, "end_ms": 1790294400000}
    ]
    
    # Preload all 1h and 4h data
    data_1h = {}
    data_4h = {}
    for c in coins:
        f1 = os.path.join(hist_dir, f"{c}_1h.json")
        f4 = os.path.join(hist_dir, f"{c}_4h.json")
        if os.path.exists(f1):
            with open(f1, "r", encoding="utf-8") as f:
                data_1h[c] = json.load(f)
        if os.path.exists(f4):
            with open(f4, "r", encoding="utf-8") as f:
                data_4h[c] = json.load(f)
                
    btc_4h = data_4h.get("BTCUSDT", [])
    max_tap_window = 28
    
    total_trades_all = []
    
    for m in months:
        m_start = m["start_ms"]
        m_end = m["end_ms"]
        candidates = []
        
        for c in coins:
            for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
                n = len(dataset)
                if n < 40: continue
                
                for i in range(20, n - 2):
                    # LONG
                    prior_lows = [float(x["low"]) for x in dataset[max(0, i-15):i+1]]
                    if float(dataset[i]["low"]) == min(prior_lows):
                        sub_w = dataset[i:min(i+16, n)]
                        highs = [float(x["high"]) for x in sub_w]
                        max_high = max(highs)
                        high_idx = i + highs.index(max_high)
                        if high_idx > i + 2:
                            origin_l = float(dataset[i]["low"])
                            gain = (max_high - origin_l) / origin_l if origin_l > 0 else 0.0
                            if gain >= 0.050:
                                idm_low = float(dataset[high_idx - 1]["low"])
                                best_mid = -1
                                max_bg = 0.0
                                for mid in range(i + 1, high_idx):
                                    m_h = float(dataset[mid]["high"])
                                    m_l = float(dataset[mid]["low"])
                                    bg = (m_h - m_l) / m_l if m_l > 0 else 0.0
                                    fib = (m_l - origin_l) / (max_high - origin_l) if max_high > origin_l else 0.0
                                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                                        max_bg = bg
                                        best_mid = mid
                                if best_mid != -1:
                                    dec_c = dataset[best_mid - 1]
                                    dec_top = max(float(dec_c["open"]), float(dec_c["close"]))
                                    dec_bot = float(dec_c["low"])
                                    has_fvg = (float(dataset[best_mid + 1]["low"]) > float(dataset[best_mid - 1]["high"])) if best_mid + 1 < n else False
                                    if has_fvg:
                                        mt = round((dec_top + dec_bot) / 2.0, 8)
                                        for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                            tap_c = dataset[t]
                                            t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                            if tap_c["time"] < m_start: continue
                                            if tap_c["time"] > m_end: break
                                            
                                            # Strict physical
                                            if t_l <= mt and t_c >= mt:
                                                c_range = t_h - t_l
                                                swept = any(float(dataset[k]["low"]) < idm_low for k in range(high_idx, t + 1))
                                                l_wick = min(t_o, t_c) - t_l
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                                
                                                btc_clean = True
                                                if btc_4h:
                                                    prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                    if len(prior_btc) >= 2:
                                                        last_b = prior_btc[-1]
                                                        o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                        if ((o_b - c_b) / o_b) >= 0.020: btc_clean = False
                                                if btc_clean and swept and w_ratio >= 0.18:
                                                    ep = mt
                                                    tp = round(ep * 1.0300, 8)
                                                    sl = round(ep * 0.9850, 8)
                                                    be = round(ep * 1.0150, 8)
                                                    candidates.append({
                                                        "month": m["name"], "symbol": c, "side": "LONG", "tf": tf,
                                                        "entry_time": tap_c["time"], "idx": t, "dataset": dataset,
                                                        "ep": ep, "tp": tp, "sl": sl, "be": be
                                                    })
                                                break
                                                
                    # SHORT
                    prior_highs = [float(x["high"]) for x in dataset[max(0, i-15):i+1]]
                    if float(dataset[i]["high"]) == max(prior_highs):
                        sub_w = dataset[i:min(i+16, n)]
                        lows = [float(x["low"]) for x in sub_w]
                        min_low = min(lows)
                        low_idx = i + lows.index(min_low)
                        if low_idx > i + 2:
                            origin_h = float(dataset[i]["high"])
                            drop = (origin_h - min_low) / origin_h if origin_h > 0 else 0.0
                            if drop >= 0.050:
                                idm_high = float(dataset[low_idx - 1]["high"])
                                best_mid = -1
                                max_bg = 0.0
                                for mid in range(i + 1, low_idx):
                                    m_h = float(dataset[mid]["high"])
                                    m_l = float(dataset[mid]["low"])
                                    bg = (m_h - m_l) / m_h if m_h > 0 else 0.0
                                    fib = (origin_h - m_h) / (origin_h - min_low) if origin_h > min_low else 0.0
                                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                                        max_bg = bg
                                        best_mid = mid
                                if best_mid != -1:
                                    dec_c = dataset[best_mid - 1]
                                    dec_top = float(dec_c["high"])
                                    dec_bot = min(float(dec_c["open"]), float(dec_c["close"]))
                                    has_bear_fvg = (float(dataset[best_mid + 1]["high"]) < float(dataset[best_mid - 1]["low"])) if best_mid + 1 < n else False
                                    if has_bear_fvg:
                                        mt = round((dec_top + dec_bot) / 2.0, 8)
                                        for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                            tap_c = dataset[t]
                                            t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                            if tap_c["time"] < m_start: continue
                                            if tap_c["time"] > m_end: break
                                            
                                            if t_h >= mt and t_c <= mt:
                                                c_range = t_h - t_l
                                                swept = any(float(dataset[k]["high"]) > idm_high for k in range(low_idx, t + 1))
                                                u_wick = t_h - max(t_o, t_c)
                                                w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                                
                                                btc_clean_short = True
                                                if btc_4h:
                                                    prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                    if len(prior_btc) >= 2:
                                                        last_b = prior_btc[-1]
                                                        o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                        if ((c_b - o_b) / o_b) >= 0.020: btc_clean_short = False
                                                if btc_clean_short and swept and w_ratio >= 0.18:
                                                    ep = mt
                                                    tp = round(ep * 0.9700, 8)
                                                    sl = round(ep * 1.0150, 8)
                                                    be = round(ep * 0.9850, 8)
                                                    candidates.append({
                                                        "month": m["name"], "symbol": c, "side": "SHORT", "tf": tf,
                                                        "entry_time": tap_c["time"], "idx": t, "dataset": dataset,
                                                        "ep": ep, "tp": tp, "sl": sl, "be": be
                                                    })
                                                break
                                                
        # Deduplicate
        seen = set()
        uniq = []
        for ev in candidates:
            k = (ev["symbol"], ev["entry_time"])
            if k not in seen:
                seen.add(k)
                uniq.append(ev)
        uniq.sort(key=lambda x: x["entry_time"])
        
        # Simulate sequential execution
        busy_until = 0
        for ev in uniq:
            if ev["entry_time"] < busy_until: continue
            ds = ev["dataset"]
            idx = ev["idx"]
            ep, tp, sl, be_trig = ev["ep"], ev["tp"], ev["sl"], ev["be"]
            side = ev["side"]
            
            active_sl = sl
            be_locked = False
            outcome = None
            exit_time = ev["entry_time"]
            be_exit_bar_idx = -1
            
            # Normal run with BE Armor
            for b_i, bar in enumerate(ds[idx+1:], start=idx+1):
                b_h, b_l, b_t = float(bar["high"]), float(bar["low"]), bar["time"]
                if side == "LONG":
                    if not be_locked and b_h >= be_trig:
                        be_locked = True
                        active_sl = ep
                    if b_h >= tp:
                        outcome = "TP_HIT"
                        exit_time = b_t
                        break
                    elif b_l <= active_sl:
                        outcome = "BE_SAVE" if be_locked else "SL_HIT"
                        exit_time = b_t
                        be_exit_bar_idx = b_i
                        break
                else:
                    if not be_locked and b_l <= be_trig:
                        be_locked = True
                        active_sl = ep
                    if b_l <= tp:
                        outcome = "TP_HIT"
                        exit_time = b_t
                        break
                    elif b_h >= active_sl:
                        outcome = "BE_SAVE" if be_locked else "SL_HIT"
                        exit_time = b_t
                        be_exit_bar_idx = b_i
                        break
                        
            if not outcome: continue
            busy_until = exit_time
            
            # NOW: If outcome was BE_SAVE, what would have happened if we NEVER moved SL to BE?
            post_be_result = "N/A"
            if outcome == "BE_SAVE":
                # Check from be_exit_bar_idx onwards
                for bar in ds[be_exit_bar_idx:]:
                    b_h, b_l = float(bar["high"]), float(bar["low"])
                    if side == "LONG":
                        if b_h >= tp:
                            post_be_result = "EVENTUAL_TP" # Premature exit: went to TP later!
                            break
                        elif b_l <= sl:
                            post_be_result = "EVENTUAL_SL" # Life saver: would have hit real SL!
                            break
                    else:
                        if b_l <= tp:
                            post_be_result = "EVENTUAL_TP"
                            break
                        elif b_h >= sl:
                            post_be_result = "EVENTUAL_SL"
                            break
                if post_be_result == "N/A":
                    post_be_result = "UNDECIDED_CHOP"
                    
            total_trades_all.append({
                "month": ev["month"],
                "symbol": ev["symbol"],
                "side": side,
                "tf": ev["tf"],
                "outcome": outcome,
                "post_be_result": post_be_result
            })
            
    # Compile Statistics
    print(f"\n=================================================================")
    print(f"STOP LOSS & BREAK-EVEN FORENSIC AUTOPSY (JULY, AUGUST, SEPT 2026)")
    print(f"=================================================================\n")
    
    total_count = len(total_trades_all)
    sl_count = len([t for t in total_trades_all if t["outcome"] == "SL_HIT"])
    be_count = len([t for t in total_trades_all if t["outcome"] == "BE_SAVE"])
    tp_count = len([t for t in total_trades_all if t["outcome"] == "TP_HIT"])
    
    be_saved_from_sl = len([t for t in total_trades_all if t["post_be_result"] == "EVENTUAL_SL"])
    be_missed_tp = len([t for t in total_trades_all if t["post_be_result"] == "EVENTUAL_TP"])
    be_undecided = len([t for t in total_trades_all if t["post_be_result"] == "UNDECIDED_CHOP"])
    
    print(f"TOTAL EXECUTED TRADES: {total_count}")
    print(f"-----------------------------------------------------------------")
    print(f"1. Real SL Hits:          {sl_count} trades ({sl_count/total_count*100:.2f}%)")
    print(f"2. Pure TP Hits:          {tp_count} trades ({tp_count/total_count*100:.2f}%)")
    print(f"3. Break-Even Closures:   {be_count} trades ({be_count/total_count*100:.2f}%)")
    print(f"-----------------------------------------------------------------")
    print(f"BREAK-EVEN POST-MORTEM (Out of {be_count} BE Closures):")
    print(f"  * SAVED FROM REAL SL (Price dropped to hit SL):  {be_saved_from_sl} ({be_saved_from_sl/be_count*100:.1f}%)")
    print(f"  * MISSED TP (Price reversed back to hit TP):    {be_missed_tp} ({be_missed_tp/be_count*100:.1f}%)")
    print(f"  * UNDECIDED / CHOPPY RANGE:                     {be_undecided} ({be_undecided/be_count*100:.1f}%)")
    print(f"-----------------------------------------------------------------")
    
    # Month by month breakdown
    for m in ["July 2026", "August 2026", "September 2026"]:
        m_trades = [t for t in total_trades_all if t["month"] == m]
        m_tot = len(m_trades)
        m_sl = len([t for t in m_trades if t["outcome"] == "SL_HIT"])
        m_tp = len([t for t in m_trades if t["outcome"] == "TP_HIT"])
        m_be = len([t for t in m_trades if t["outcome"] == "BE_SAVE"])
        m_be_sl = len([t for t in m_trades if t["post_be_result"] == "EVENTUAL_SL"])
        m_be_tp = len([t for t in m_trades if t["post_be_result"] == "EVENTUAL_TP"])
        print(f"[{m}] Total: {m_tot} | TP: {m_tp} ({m_tp/m_tot*100:.1f}%) | Real SL: {m_sl} ({m_sl/m_tot*100:.1f}%) | BE: {m_be} ({m_be/m_tot*100:.1f}%)")
        print(f"   -> BE Analysis: Saved from SL = {m_be_sl} ({m_be_sl/m_be*100:.1f}%), Missed TP = {m_be_tp} ({m_be_tp/m_be*100:.1f}%)")
    print(f"=================================================================\n")
    
    # Save results to json
    res = {
        "total_trades": total_count,
        "pure_tp_hits": tp_count,
        "real_sl_hits": sl_count,
        "be_closures": be_count,
        "be_saved_from_sl": be_saved_from_sl,
        "be_missed_tp": be_missed_tp,
        "be_undecided": be_undecided,
        "trades": total_trades_all
    }
    with open(os.path.join(os.path.dirname(__file__), "..", "be_and_sl_ratio_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

if __name__ == "__main__":
    analyze_be_and_sl_forensics()
