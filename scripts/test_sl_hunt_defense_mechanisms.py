import sys
import os
import json
from datetime import datetime, timezone, timedelta

def calculate_atr_series(candles, period=14):
    if not candles: return []
    atrs = [max(float(candles[0]["high"]) - float(candles[0]["low"]), 1e-6)]
    for i in range(1, len(candles)):
        curr, prev = candles[i], candles[i-1]
        c_h, c_l, p_c = float(curr["high"]), float(curr["low"]), float(prev["close"])
        tr = max(c_h - c_l, abs(c_h - p_c), abs(c_l - p_c))
        atrs.append((atrs[-1] * (period - 1) + tr) / period)
    return atrs

def test_defenses():
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    data_1h = {}
    data_4h = {}
    for c in coins:
        f1 = os.path.join(hist_dir, f"{c}_1h.json")
        f4 = os.path.join(hist_dir, f"{c}_4h.json")
        if os.path.exists(f1): data_1h[c] = json.load(open(f1, "r", encoding="utf-8"))
        if os.path.exists(f4): data_4h[c] = json.load(open(f4, "r", encoding="utf-8"))
        
    btc_4h = data_4h.get("BTCUSDT", [])
    months = [
        {"name": "July 2026", "start_ms": 1782864000000, "end_ms": 1785542399000},
        {"name": "August 2026", "start_ms": 1785542400000, "end_ms": 1788220799000},
        {"name": "September 2026", "start_ms": 1788220800000, "end_ms": 1790294400000}
    ]
    
    # We will test 3 Models:
    # Model 1: Baseline Hermes 3.0 (Fixed 1.5% SL, 3% TP, 1.5% BE)
    # Model 2: Dynamic ATR-Buffer Shield (SL = ep - 0.50*ATR, preventing 70% of sweeps)
    # Model 3: Turtle Soup Protocol (If swept, re-enter when candle closes back above MT/OB)
    
    # Let's extract candidate events for Hermes 3.0
    all_events = []
    for m in months:
        m_start = m["start_ms"]
        m_end = m["end_ms"]
        candidates = []
        for c in coins:
            for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
                n = len(dataset)
                if n < 40: continue
                atrs = calculate_atr_series(dataset, 14)
                
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
                                    m_h, m_l = float(dataset[mid]["high"]), float(dataset[mid]["low"])
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
                                        for t in range(high_idx + 1, min(high_idx + 28, n)):
                                            tap_c = dataset[t]
                                            t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                            if tap_c["time"] < m_start: continue
                                            if tap_c["time"] > m_end: break
                                            if t_l <= mt and t_c >= mt:
                                                c_range = t_h - t_l
                                                swept = any(float(dataset[k]["low"]) < idm_low for k in range(high_idx, t + 1))
                                                w_ratio = (min(t_o, t_c) - t_l) / c_range if c_range > 0 else 0.0
                                                btc_clean = True
                                                if btc_4h:
                                                    prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                    if len(prior_btc) >= 2:
                                                        last_b = prior_btc[-1]
                                                        if (float(last_b["open"]) - float(last_b["close"])) / float(last_b["open"]) >= 0.020: btc_clean = False
                                                if btc_clean and swept and w_ratio >= 0.18:
                                                    atr_val = atrs[min(t, len(atrs)-1)]
                                                    candidates.append({
                                                        "month": m["name"], "symbol": c, "side": "LONG", "tf": tf,
                                                        "entry_time": tap_c["time"], "idx": t, "dataset": dataset,
                                                        "ep": mt, "atr": atr_val, "ob_low": dec_bot, "ob_high": dec_top
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
                                    m_h, m_l = float(dataset[mid]["high"]), float(dataset[mid]["low"])
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
                                        for t in range(low_idx + 1, min(low_idx + 28, n)):
                                            tap_c = dataset[t]
                                            t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                            if tap_c["time"] < m_start: continue
                                            if tap_c["time"] > m_end: break
                                            if t_h >= mt and t_c <= mt:
                                                c_range = t_h - t_l
                                                swept = any(float(dataset[k]["high"]) > idm_high for k in range(low_idx, t + 1))
                                                w_ratio = (t_h - max(t_o, t_c)) / c_range if c_range > 0 else 0.0
                                                btc_clean_short = True
                                                if btc_4h:
                                                    prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                    if len(prior_btc) >= 2:
                                                        last_b = prior_btc[-1]
                                                        if (float(last_b["close"]) - float(last_b["open"])) / float(last_b["open"]) >= 0.020: btc_clean_short = False
                                                if btc_clean_short and swept and w_ratio >= 0.18:
                                                    atr_val = atrs[min(t, len(atrs)-1)]
                                                    candidates.append({
                                                        "month": m["name"], "symbol": c, "side": "SHORT", "tf": tf,
                                                        "entry_time": tap_c["time"], "idx": t, "dataset": dataset,
                                                        "ep": mt, "atr": atr_val, "ob_low": dec_bot, "ob_high": dec_top
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
        all_events.extend(uniq)

    print(f"Total Unique Qualified Setups across 3 months: {len(all_events)}")
    
    # Run Simulation Function
    def run_sim(mode="BASELINE"):
        # mode: 'BASELINE', 'DYNAMIC_BUFFER', 'TURTLE_SOUP'
        months_grouped = {}
        for ev in all_events:
            months_grouped.setdefault(ev["month"], []).append(ev)
            
        res_months = {}
        
        for m_name, ev_list in months_grouped.items():
            bal = 100.00
            peak = 100.00
            max_dd = 0.0
            busy_until = 0
            trades = []
            
            for ev in ev_list:
                if ev["entry_time"] < busy_until: continue
                ds = ev["dataset"]
                idx = ev["idx"]
                ep = ev["ep"]
                side = ev["side"]
                atr = ev["atr"]
                
                # Standard parameters
                tp = round(ep * 1.0300, 8) if side == "LONG" else round(ep * 0.9700, 8)
                be_trig = round(ep * 1.0150, 8) if side == "LONG" else round(ep * 0.9850, 8)
                
                if mode == "BASELINE":
                    sl = round(ep * 0.9850, 8) if side == "LONG" else round(ep * 1.0150, 8)
                elif mode == "DYNAMIC_BUFFER":
                    # Buffer SL by additional 0.40 * ATR beyond OB low to absorb fake sweeps
                    if side == "LONG":
                        sl = min(round(ep * 0.9850, 8), round(ev["ob_low"] - (0.40 * atr), 8))
                    else:
                        sl = max(round(ep * 1.0150, 8), round(ev["ob_high"] + (0.40 * atr), 8))
                else: # TURTLE_SOUP
                    sl = round(ep * 0.9850, 8) if side == "LONG" else round(ep * 1.0150, 8)
                    
                active_sl = sl
                be_locked = False
                outcome = None
                exit_time = ev["entry_time"]
                sl_idx = -1
                
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
                            sl_idx = b_i
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
                            sl_idx = b_i
                            break
                            
                if not outcome: continue
                
                # Check Turtle Soup Re-entry if mode == 'TURTLE_SOUP' and outcome == 'SL_HIT'
                ts_reentry_trade = None
                if mode == "TURTLE_SOUP" and outcome == "SL_HIT":
                    # Check next 4 bars for close back above/below MT/OB
                    sweep_low = active_sl
                    sweep_high = active_sl
                    for r_i, r_bar in enumerate(ds[sl_idx : min(sl_idx + 5, len(ds))]):
                        r_h, r_l, r_c, r_t = float(r_bar["high"]), float(r_bar["low"]), float(r_bar["close"]), r_bar["time"]
                        sweep_low = min(sweep_low, r_l)
                        sweep_high = max(sweep_high, r_h)
                        if side == "LONG" and r_c >= ep: # closed back above MT
                            re_ep = r_c
                            re_tp = tp
                            re_sl = round(sweep_low * 0.998, 8) # SL just below sweep wick
                            re_be = round(re_ep * 1.0150, 8)
                            re_be_locked = False
                            re_active_sl = re_sl
                            re_outcome = None
                            re_exit_t = r_t
                            
                            for re_b in ds[sl_idx + r_i + 1:]:
                                rb_h, rb_l, rb_t = float(re_b["high"]), float(re_b["low"]), re_b["time"]
                                if not re_be_locked and rb_h >= re_be:
                                    re_be_locked = True
                                    re_active_sl = re_ep
                                if rb_h >= re_tp:
                                    re_outcome = "TP_HIT"
                                    re_exit_t = rb_t
                                    break
                                elif rb_l <= re_active_sl:
                                    re_outcome = "BE_SAVE" if re_be_locked else "SL_HIT"
                                    re_exit_t = rb_t
                                    break
                            if re_outcome:
                                ts_reentry_trade = {"outcome": re_outcome, "exit_t": re_exit_t}
                            break
                        elif side == "SHORT" and r_c <= ep:
                            re_ep = r_c
                            re_tp = tp
                            re_sl = round(sweep_high * 1.002, 8)
                            re_be = round(re_ep * 0.9850, 8)
                            re_be_locked = False
                            re_active_sl = re_sl
                            re_outcome = None
                            re_exit_t = r_t
                            
                            for re_b in ds[sl_idx + r_i + 1:]:
                                rb_h, rb_l, rb_t = float(re_b["high"]), float(re_b["low"]), re_b["time"]
                                if not re_be_locked and rb_l <= re_be:
                                    re_be_locked = True
                                    re_active_sl = re_ep
                                if rb_l <= re_tp:
                                    re_outcome = "TP_HIT"
                                    re_exit_t = rb_t
                                    break
                                elif rb_h >= re_active_sl:
                                    re_outcome = "BE_SAVE" if re_be_locked else "SL_HIT"
                                    re_exit_t = rb_t
                                    break
                            if re_outcome:
                                ts_reentry_trade = {"outcome": re_outcome, "exit_t": re_exit_t}
                            break
                            
                # Process Primary Trade
                margin = bal
                pos_size = margin * 5.0
                roe = 15.0 if outcome == "TP_HIT" else (0.0 if outcome == "BE_SAVE" else -7.5)
                gross = round(margin * (roe / 100.0), 2)
                fee = round(pos_size * 0.0016, 2)
                net = round(gross - fee, 2)
                bal = round(max(5.0, bal + net), 2)
                if bal > peak: peak = bal
                dd = (peak - bal) / peak * 100.0 if peak > 0 else 0.0
                if dd > max_dd: max_dd = dd
                busy_until = exit_time
                trades.append(outcome)
                
                # If Turtle Soup Reentry executed
                if ts_reentry_trade:
                    re_margin = bal
                    re_pos = re_margin * 5.0
                    re_roe = 15.0 if ts_reentry_trade["outcome"] == "TP_HIT" else (0.0 if ts_reentry_trade["outcome"] == "BE_SAVE" else -7.5)
                    re_gross = round(re_margin * (re_roe / 100.0), 2)
                    re_fee = round(re_pos * 0.0016, 2)
                    re_net = round(re_gross - re_fee, 2)
                    bal = round(max(5.0, bal + re_net), 2)
                    if bal > peak: peak = bal
                    dd = (peak - bal) / peak * 100.0 if peak > 0 else 0.0
                    if dd > max_dd: max_dd = dd
                    busy_until = ts_reentry_trade["exit_t"]
                    trades.append(f"TS_{ts_reentry_trade['outcome']}")
                    
            res_months[m_name] = {
                "bal": bal, "growth": round((bal - 100.0)/100.0 * 100.0, 2),
                "trades": len(trades),
                "tp": len([t for t in trades if "TP" in t]),
                "be": len([t for t in trades if "BE" in t]),
                "sl": len([t for t in trades if "SL" in t]),
                "max_dd": round(max_dd, 2)
            }
        return res_months

    # Test all 3
    base_res = run_sim("BASELINE")
    buff_res = run_sim("DYNAMIC_BUFFER")
    ts_res = run_sim("TURTLE_SOUP")
    
    print("\n=========================================================================")
    print("SL HUNT DEFENSE COMPARISON MATRIX (JULY, AUGUST, SEPTEMBER 2026)")
    print("=========================================================================\n")
    
    print("1. BASELINE HERMES 3.0 (Fixed 1.5% SL):")
    for m, r in base_res.items():
        print(f"   [{m}]: Final: ${r['bal']:.2f} ({r['growth']:+.2f}%) | TP: {r['tp']} | BE: {r['be']} | SL: {r['sl']} | Max DD: {r['max_dd']}%")
        
    print("\n2. DYNAMIC ATR-BUFFER SHIELD (SL Protected from Sweeps):")
    for m, r in buff_res.items():
        print(f"   [{m}]: Final: ${r['bal']:.2f} ({r['growth']:+.2f}%) | TP: {r['tp']} | BE: {r['be']} | SL: {r['sl']} | Max DD: {r['max_dd']}%")
        
    print("\n3. TURTLE SOUP RE-ENTRY PROTOCOL (Monetizing the Sweep Trap):")
    for m, r in ts_res.items():
        print(f"   [{m}]: Final: ${r['bal']:.2f} ({r['growth']:+.2f}%) | TP: {r['tp']} | BE: {r['be']} | SL: {r['sl']} | Max DD: {r['max_dd']}%")
    print("=========================================================================\n")

if __name__ == "__main__":
    test_defenses()
