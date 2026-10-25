import sys
import os
import json
from datetime import datetime, timezone, timedelta

def format_duration(ms):
    secs = int(ms / 1000)
    hrs = secs // 3600
    mins = (secs % 3600) // 60
    if hrs > 0:
        return f"{hrs}h {mins}m"
    return f"{mins}m"

def format_ist(ts_ms):
    if not ts_ms:
        return "N/A"
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) + timedelta(hours=5, minutes=30)
    return dt.strftime("%d %b %Y %I:%M %p IST")

def analyze_sl_hunts():
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    
    # Load 1h and 4h data
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
                
    months = [
        {"name": "July 2026", "start_ms": 1782864000000, "end_ms": 1785542399000},
        {"name": "August 2026", "start_ms": 1785542400000, "end_ms": 1788220799000},
        {"name": "September 2026", "start_ms": 1788220800000, "end_ms": 1790294400000}
    ]
    btc_4h = data_4h.get("BTCUSDT", [])
    
    # We will run SL hunt analysis for all 3 strategies:
    # 1. Hermes 3.0 Quantum
    # 2. Hermes 3.5 Single Tier
    # 3. Hermes 4.0 Council
    
    strategies = ["Hermes 3.0 Quantum", "Hermes 3.5 Single Tier", "Hermes 4.0 Council"]
    report_data = {}
    
    for strat in strategies:
        sl_events = []
        
        for m in months:
            m_start = m["start_ms"]
            m_end = m["end_ms"]
            candidates = []
            
            for c in coins:
                for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
                    n = len(dataset)
                    if n < 40: continue
                    
                    if strat == "Hermes 3.0 Quantum":
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
                                                for t in range(high_idx + 1, min(high_idx + 28, n)):
                                                    tap_c = dataset[t]
                                                    t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                                    if tap_c["time"] < m_start: continue
                                                    if tap_c["time"] > m_end: break
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
                                                                "symbol": c, "side": "LONG", "tf": tf, "entry_time": tap_c["time"],
                                                                "idx": t, "dataset": dataset, "ep": ep, "tp": tp, "sl": sl, "be": be, "month": m["name"]
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
                                                for t in range(low_idx + 1, min(low_idx + 28, n)):
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
                                                                "symbol": c, "side": "SHORT", "tf": tf, "entry_time": tap_c["time"],
                                                                "idx": t, "dataset": dataset, "ep": ep, "tp": tp, "sl": sl, "be": be, "month": m["name"]
                                                            })
                                                        break

                    elif strat == "Hermes 3.5 Single Tier":
                        effective_min_bars = 18 if tf == "1h" else 8
                        effective_max_bars = 720 if tf == "1h" else 360
                        for i in range(5, n - 3):
                            c3, c2, c1 = dataset[i], dataset[i+1], dataset[i+2]
                            impulse_h = max(c1["high"], c2["high"])
                            impulse_l = min(c1["low"], c2["low"])
                            # Bullish
                            if (c3["close"] < c3["open"]) and (c1["low"] > c3["high"]) and ((impulse_h - c3["low"])/c3["low"] >= 0.050):
                                ob_high, ob_low = c3["high"], c3["low"]
                                entry_p = round(ob_high - ((ob_high - ob_low) * 0.05), 8)
                                tp_p = round(entry_p * 1.0300, 8)
                                sl_p = round(entry_p * 0.9850, 8)
                                be_p = round(entry_p * 1.0150, 8)
                                peak_runway = impulse_h
                                for t in range(i + 3, n):
                                    bar = dataset[t]
                                    peak_runway = max(peak_runway, bar["high"])
                                    runway_pct = ((peak_runway - ob_high) / ob_high) * 100.0
                                    bars_alive = t - i
                                    if bars_alive > effective_max_bars or bar["close"] < ob_low: break
                                    if bar["time"] < m_start: continue
                                    if bar["time"] > m_end: break
                                    if bar["low"] <= entry_p and bar["high"] >= entry_p:
                                        if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                            candidates.append({
                                                "symbol": c, "side": "LONG", "tf": tf, "entry_time": bar["time"],
                                                "idx": t, "dataset": dataset, "ep": entry_p, "tp": tp_p, "sl": sl_p, "be": be_p, "month": m["name"]
                                            })
                                        break
                            # Bearish
                            if (c3["close"] > c3["open"]) and (c1["high"] < c3["low"]) and ((c3["high"] - impulse_l)/c3["high"] >= 0.050):
                                ob_high, ob_low = c3["high"], c3["low"]
                                entry_p = round(ob_low + ((ob_high - ob_low) * 0.05), 8)
                                tp_p = round(entry_p * 0.9700, 8)
                                sl_p = round(entry_p * 1.0150, 8)
                                be_p = round(entry_p * 0.9850, 8)
                                peak_runway = impulse_l
                                for t in range(i + 3, n):
                                    bar = dataset[t]
                                    peak_runway = min(peak_runway, bar["low"])
                                    runway_pct = ((ob_low - peak_runway) / ob_low) * 100.0
                                    bars_alive = t - i
                                    if bars_alive > effective_max_bars or bar["close"] > ob_high: break
                                    if bar["time"] < m_start: continue
                                    if bar["time"] > m_end: break
                                    if bar["high"] >= entry_p and bar["low"] <= entry_p:
                                        if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                            candidates.append({
                                                "symbol": c, "side": "SHORT", "tf": tf, "entry_time": bar["time"],
                                                "idx": t, "dataset": dataset, "ep": entry_p, "tp": tp_p, "sl": sl_p, "be": be_p, "month": m["name"]
                                            })
                                        break

                    elif strat == "Hermes 4.0 Council":
                        for i in range(20, n - 4):
                            c1, c2 = dataset[i-1], dataset[i]
                            c1_l, c1_h = float(c1["low"]), float(c1["high"])
                            c2_o, c2_c, c2_l, c2_h = float(c2["open"]), float(c2["close"]), float(c2["low"]), float(c2["high"])
                            if c2_c <= c2_o and c2_l < c1_l:
                                prior_lows = [float(x["low"]) for x in dataset[max(0, i-15):i+1]]
                                if c2_l == min(prior_lows):
                                    sub_w = dataset[i:min(i+20, n)]
                                    highs = [float(x["high"]) for x in sub_w]
                                    m_high = max(highs)
                                    h_idx = i + highs.index(m_high)
                                    if h_idx > i + 2:
                                        if (m_high - c2_l) / c2_l >= 0.035:
                                            has_fvg = any(float(dataset[d+1]["low"]) > float(dataset[d-1]["high"]) for d in range(i+1, min(h_idx, n-1)) if d+1 < n)
                                            prev_swing_high = max(float(x["high"]) for x in dataset[max(0, i-15):i])
                                            body_bos = any(float(x["close"]) > prev_swing_high for x in dataset[i+1:h_idx+1])
                                            if has_fvg and body_bos:
                                                mt = round((c2_h + c2_l) / 2.0, 8)
                                                idm_low = float(dataset[h_idx-1]["low"])
                                                ep = mt
                                                tp = round(ep * 1.0300, 8)
                                                sl = round(ep * 0.9850, 8)
                                                be = round(ep * 1.0150, 8)
                                                for t in range(h_idx+1, min(h_idx+28, n)):
                                                    tap_c = dataset[t]
                                                    t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                                    if tap_c["time"] < m_start: continue
                                                    if tap_c["time"] > m_end: break
                                                    if t_l <= mt and t_c >= mt:
                                                        c_range = t_h - t_l
                                                        swept = any(float(dataset[k]["low"]) < idm_low for k in range(h_idx, t+1))
                                                        w_ratio = (min(t_o, t_c) - t_l) / c_range if c_range > 0 else 0.0
                                                        btc_clean = True
                                                        if btc_4h:
                                                            prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                            if len(prior_btc) >= 2:
                                                                last_b = prior_btc[-1]
                                                                o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                                if ((o_b - c_b) / o_b) >= 0.010: btc_clean = False
                                                        if btc_clean and swept and w_ratio >= 0.18:
                                                            candidates.append({
                                                                "symbol": c, "side": "LONG", "tf": tf, "entry_time": tap_c["time"],
                                                                "idx": t, "dataset": dataset, "ep": ep, "tp": tp, "sl": sl, "be": be, "month": m["name"]
                                                            })
                                                        break
                            # Short
                            if c2_c >= c2_o and c2_h > c1_h:
                                prior_highs = [float(x["high"]) for x in dataset[max(0, i-15):i+1]]
                                if c2_h == max(prior_highs):
                                    sub_w = dataset[i:min(i+20, n)]
                                    lows = [float(x["low"]) for x in sub_w]
                                    min_low = min(lows)
                                    low_idx = i + lows.index(min_low)
                                    if low_idx > i + 2:
                                        if (c2_h - min_low) / c2_h >= 0.035:
                                            has_fvg = any(float(dataset[d+1]["high"]) < float(dataset[d-1]["low"]) for d in range(i+1, min(low_idx, n-1)) if d+1 < n)
                                            prev_swing_low = min(float(x["low"]) for x in dataset[max(0, i-15):i])
                                            body_bos = any(float(x["close"]) < prev_swing_low for x in dataset[i+1:low_idx+1])
                                            if has_fvg and body_bos:
                                                mt = round((c2_h + c2_l) / 2.0, 8)
                                                idm_high = float(dataset[low_idx-1]["high"])
                                                ep = mt
                                                tp = round(ep * 0.9700, 8)
                                                sl = round(ep * 1.0150, 8)
                                                be = round(ep * 0.9850, 8)
                                                for t in range(low_idx+1, min(low_idx+28, n)):
                                                    tap_c = dataset[t]
                                                    t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                                    if tap_c["time"] < m_start: continue
                                                    if tap_c["time"] > m_end: break
                                                    if t_h >= mt and t_c <= mt:
                                                        c_range = t_h - t_l
                                                        swept = any(float(dataset[k]["high"]) > idm_high for k in range(low_idx, t+1))
                                                        w_ratio = (t_h - max(t_o, t_c)) / c_range if c_range > 0 else 0.0
                                                        btc_clean_short = True
                                                        if btc_4h:
                                                            prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                            if len(prior_btc) >= 2:
                                                                last_b = prior_btc[-1]
                                                                o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                                if ((c_b - o_b) / o_b) >= 0.015: btc_clean_short = False
                                                        if btc_clean_short and swept and w_ratio >= 0.18:
                                                            candidates.append({
                                                                "symbol": c, "side": "SHORT", "tf": tf, "entry_time": tap_c["time"],
                                                                "idx": t, "dataset": dataset, "ep": ep, "tp": tp, "sl": sl, "be": be, "month": m["name"]
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
            
            # Simulate Sequential Execution
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
                sl_hit_bar_idx = -1
                
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
                            sl_hit_bar_idx = b_i
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
                            sl_hit_bar_idx = b_i
                            break
                            
                if not outcome: continue
                busy_until = exit_time
                
                # Check for SL Hunt -> Reversal to TP!
                if outcome == "SL_HIT":
                    sl_duration_ms = exit_time - ev["entry_time"]
                    
                    # Look at candles AFTER the SL was hit (up to 72 hours / 72 bars)
                    hit_tp_after_sl = False
                    tp_after_sl_time = 0
                    time_to_tp_after_sl_ms = 0
                    max_adverse_price = sl
                    
                    future_window = ds[sl_hit_bar_idx+1 : min(sl_hit_bar_idx + 73, len(ds))]
                    for f_bar in future_window:
                        f_h, f_l, f_t = float(f_bar["high"]), float(f_bar["low"]), f_bar["time"]
                        if side == "LONG":
                            max_adverse_price = min(max_adverse_price, f_l)
                            if f_h >= tp:
                                hit_tp_after_sl = True
                                tp_after_sl_time = f_t
                                time_to_tp_after_sl_ms = f_t - exit_time
                                break
                        else:
                            max_adverse_price = max(max_adverse_price, f_h)
                            if f_l <= tp:
                                hit_tp_after_sl = True
                                tp_after_sl_time = f_t
                                time_to_tp_after_sl_ms = f_t - exit_time
                                break
                                
                    sl_events.append({
                        "month": ev["month"],
                        "symbol": ev["symbol"],
                        "side": side,
                        "tf": ev["tf"].upper(),
                        "entry_time_str": format_ist(ev["entry_time"]),
                        "sl_time_str": format_ist(exit_time),
                        "time_to_sl_str": format_duration(sl_duration_ms),
                        "time_to_sl_hrs": round(sl_duration_ms / 3600000.0, 2),
                        "ep": ep,
                        "sl": sl,
                        "tp": tp,
                        "hit_tp_after_sl": hit_tp_after_sl,
                        "tp_after_sl_time_str": format_ist(tp_after_sl_time) if hit_tp_after_sl else "NEVER",
                        "time_from_sl_to_tp_str": format_duration(time_to_tp_after_sl_ms) if hit_tp_after_sl else "N/A",
                        "time_from_sl_to_tp_hrs": round(time_to_tp_after_sl_ms / 3600000.0, 2) if hit_tp_after_sl else 0.0
                    })
                    
        report_data[strat] = sl_events

    # Compiling Full Analysis
    print("\n=========================================================================================")
    print("FORENSIC AUTOPSY: SL HUNT & POST-STOP LOSS TAKE PROFIT REVERSAL (3 MONTHS)")
    print("=========================================================================================\n")
    
    summary_table = []
    
    for strat, events in report_data.items():
        tot_sl = len(events)
        fake_sl_hunts = [e for e in events if e["hit_tp_after_sl"]]
        true_failures = [e for e in events if not e["hit_tp_after_sl"]]
        
        fake_count = len(fake_sl_hunts)
        fake_pct = (fake_count / tot_sl * 100.0) if tot_sl else 0.0
        
        avg_time_to_sl = (sum(e["time_to_sl_hrs"] for e in events) / tot_sl) if tot_sl else 0.0
        avg_time_sl_to_tp = (sum(e["time_from_sl_to_tp_hrs"] for e in fake_sl_hunts) / fake_count) if fake_count else 0.0
        
        print(f"[{strat.upper()}]")
        print(f"  * Total Real Stop Losses:               {tot_sl} Trades")
        print(f"  * FAKE SL HUNTS (Swept SL, then HIT TP): {fake_count} Trades ({fake_pct:.2f}%)")
        print(f"  * TRUE STRUCTURAL FAILURES (Never hit TP): {len(true_failures)} Trades ({100.0 - fake_pct:.2f}%)")
        print(f"  * Average Time taken to Hunt SL:        {avg_time_to_sl:.1f} Hours ({int(avg_time_to_sl*60)} mins)")
        if fake_count:
            print(f"  * Average Time from SL Hunt to Target TP: {avg_time_sl_to_tp:.1f} Hours ({int(avg_time_sl_to_tp*60)} mins)")
        print("-----------------------------------------------------------------------------------------")
        
        summary_table.append({
            "strategy": strat,
            "total_sl": tot_sl,
            "fake_sl_hunts": fake_count,
            "fake_sl_pct": round(fake_pct, 2),
            "true_failures": len(true_failures),
            "true_failures_pct": round(100.0 - fake_pct, 2),
            "avg_time_to_sl_hrs": round(avg_time_to_sl, 2),
            "avg_time_sl_to_tp_hrs": round(avg_time_sl_to_tp, 2)
        })

    # Save detailed JSON
    with open(os.path.join(os.path.dirname(__file__), "..", "sl_hunt_post_mortem_results.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary_table, "details": report_data}, f, indent=2)

if __name__ == "__main__":
    analyze_sl_hunts()
