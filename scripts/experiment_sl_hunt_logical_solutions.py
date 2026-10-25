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

def run_experiment_suite():
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
    
    # Extract Base Setups (Hermes 3.0 Setup rules)
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
                                                l_wick = min(t_o, t_c) - t_l
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
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
                                                        "ep": mt, "atr": atr_val, "ob_low": dec_bot, "ob_high": dec_top,
                                                        "origin_level": origin_l
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
                                                        "ep": mt, "atr": atr_val, "ob_low": dec_bot, "ob_high": dec_top,
                                                        "origin_level": origin_h
                                                    })
                                                break
        seen = set()
        uniq = []
        for ev in candidates:
            k = (ev["symbol"], ev["entry_time"])
            if k not in seen:
                seen.add(k)
                uniq.append(ev)
        uniq.sort(key=lambda x: x["entry_time"])
        all_events.extend(uniq)

    print(f"Total Base Setups Loaded: {len(all_events)}")
    
    # ---------------------------------------------------------------------------------
    # EXPERIMENTAL ENGINE SIMULATOR
    # ---------------------------------------------------------------------------------
    def simulate_hypothesis(hypothesis_name, sl_mode="FIXED_15", exit_mode="WICK_TOUCH"):
        """
        sl_mode:
          - 'FIXED_15': Fixed -1.50% spot move
          - 'CANDLE_BODY_CLOSE': SL is triggered ONLY on candle body close beyond SL level!
          - 'STRUCTURAL_ORIGIN': SL placed below Origin Low/High
          - 'TF_VOLATILITY_SCALED': 1H uses 1.50% SL / 3.0% TP, 4H uses 2.50% SL / 5.0% TP (maintaining 1:2 R:R!)
        exit_mode:
          - 'WICK_TOUCH': Standard limit touch
          - 'BODY_CLOSE': Candle body close confirmation
        """
        months_grouped = {}
        for ev in all_events:
            months_grouped.setdefault(ev["month"], []).append(ev)
            
        summary_by_month = {}
        all_trades_count = 0
        all_tp = 0
        all_be = 0
        all_sl = 0
        total_growth_compound = 1.0
        
        for m_name in ["July 2026", "August 2026", "September 2026"]:
            ev_list = months_grouped.get(m_name, [])
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
                tf = ev["tf"]
                
                # Calibrate TP / SL according to hypothesis
                if sl_mode == "FIXED_15" or sl_mode == "CANDLE_BODY_CLOSE":
                    tp = round(ep * 1.0300, 8) if side == "LONG" else round(ep * 0.9700, 8)
                    sl = round(ep * 0.9850, 8) if side == "LONG" else round(ep * 1.0150, 8)
                    be_trig = round(ep * 1.0150, 8) if side == "LONG" else round(ep * 0.9850, 8)
                    roe_tp = 15.0
                    roe_sl = -7.5
                elif sl_mode == "TF_VOLATILITY_SCALED":
                    # 1H uses 1.5% SL / 3.0% TP (15% ROE)
                    # 4H uses 2.5% SL / 5.0% TP (25% ROE / 12.5% Loss @ 5x) - true 4H volatility room!
                    if tf == "1h":
                        tp = round(ep * 1.0300, 8) if side == "LONG" else round(ep * 0.9700, 8)
                        sl = round(ep * 0.9850, 8) if side == "LONG" else round(ep * 1.0150, 8)
                        be_trig = round(ep * 1.0150, 8) if side == "LONG" else round(ep * 0.9850, 8)
                        roe_tp = 15.0
                        roe_sl = -7.5
                    else:
                        tp = round(ep * 1.0500, 8) if side == "LONG" else round(ep * 0.9500, 8)
                        sl = round(ep * 0.9750, 8) if side == "LONG" else round(ep * 1.0250, 8)
                        be_trig = round(ep * 1.0250, 8) if side == "LONG" else round(ep * 0.9750, 8)
                        roe_tp = 25.0
                        roe_sl = -12.5
                elif sl_mode == "STRUCTURAL_ORIGIN":
                    orig = ev["origin_level"]
                    if side == "LONG":
                        sl = round(orig * 0.998, 8)
                        risk_pct = (ep - sl) / ep
                        # Cap risk at 3.0% spot move
                        if risk_pct > 0.035 or risk_pct < 0.010:
                            sl = round(ep * 0.9850, 8)
                            risk_pct = 0.015
                        tp = round(ep * (1.0 + (risk_pct * 2.0)), 8)
                        be_trig = round(ep * (1.0 + risk_pct), 8)
                    else:
                        sl = round(orig * 1.002, 8)
                        risk_pct = (sl - ep) / ep
                        if risk_pct > 0.035 or risk_pct < 0.010:
                            sl = round(ep * 1.0150, 8)
                            risk_pct = 0.015
                        tp = round(ep * (1.0 - (risk_pct * 2.0)), 8)
                        be_trig = round(ep * (1.0 - risk_pct), 8)
                    roe_tp = round(risk_pct * 2.0 * 500.0, 1)
                    roe_sl = round(-risk_pct * 500.0, 1)
                    
                active_sl = sl
                be_locked = False
                outcome = None
                exit_time = ev["entry_time"]
                
                for bar in ds[idx+1:]:
                    b_h, b_l, b_c, b_t = float(bar["high"]), float(bar["low"]), float(bar["close"]), bar["time"]
                    
                    if side == "LONG":
                        if not be_locked and b_h >= be_trig:
                            be_locked = True
                            active_sl = ep
                        if b_h >= tp:
                            outcome = "TP_HIT"
                            exit_time = b_t
                            break
                        
                        # SL Check
                        if sl_mode == "CANDLE_BODY_CLOSE":
                            # Only exits if candle body closes below SL
                            if b_c <= active_sl:
                                outcome = "BE_SAVE" if be_locked else "SL_HIT"
                                exit_time = b_t
                                break
                        else:
                            if b_l <= active_sl:
                                outcome = "BE_SAVE" if be_locked else "SL_HIT"
                                exit_time = b_t
                                break
                    else:
                        if not be_locked and b_l <= be_trig:
                            be_locked = True
                            active_sl = ep
                        if b_l <= tp:
                            outcome = "TP_HIT"
                            exit_time = b_t
                            break
                        
                        if sl_mode == "CANDLE_BODY_CLOSE":
                            if b_c >= active_sl:
                                outcome = "BE_SAVE" if be_locked else "SL_HIT"
                                exit_time = b_t
                                break
                        else:
                            if b_h >= active_sl:
                                outcome = "BE_SAVE" if be_locked else "SL_HIT"
                                exit_time = b_t
                                break
                                
                if not outcome: continue
                
                margin = bal
                pos_size = margin * 5.0
                curr_roe = roe_tp if outcome == "TP_HIT" else (0.0 if outcome == "BE_SAVE" else roe_sl)
                gross = round(margin * (curr_roe / 100.0), 2)
                fee = round(pos_size * 0.0016, 2)
                net = round(gross - fee, 2)
                bal = round(max(5.0, bal + net), 2)
                if bal > peak: peak = bal
                dd = (peak - bal) / peak * 100.0 if peak > 0 else 0.0
                if dd > max_dd: max_dd = dd
                busy_until = exit_time
                trades.append(outcome)
                
            w = len([t for t in trades if t == "TP_HIT"])
            b = len([t for t in trades if t == "BE_SAVE"])
            l = len([t for t in trades if t == "SL_HIT"])
            tot = len(trades)
            all_trades_count += tot
            all_tp += w
            all_be += b
            all_sl += l
            
            summary_by_month[m_name] = {
                "bal": bal, "growth": round((bal - 100.0)/100.0 * 100.0, 2),
                "total": tot, "tp": w, "be": b, "sl": l,
                "eff_wr": round((w + b)/tot * 100.0, 2) if tot else 0.0,
                "max_dd": round(max_dd, 2)
            }
            
        print(f"\n=========================================================================")
        print(f"HYPOTHESIS EXPERIMENT: {hypothesis_name}")
        print(f"=========================================================================")
        for m_name, res in summary_by_month.items():
            print(f"[{m_name}] Final: ${res['bal']:.2f} ({res['growth']:+.2f}%) | Trades: {res['total']} | TP: {res['tp']} | BE: {res['be']} | SL: {res['sl']} | Eff WR: {res['eff_wr']}% | Max DD: {res['max_dd']}%")
        
        overall_sl_rate = (all_sl / all_trades_count * 100.0) if all_trades_count else 0.0
        overall_tp_rate = (all_tp / all_trades_count * 100.0) if all_trades_count else 0.0
        print(f"--> 3-MONTH AGGREGATE: Total: {all_trades_count} | TP: {all_tp} ({overall_tp_rate:.1f}%) | SL: {all_sl} ({overall_sl_rate:.1f}%) | BE: {all_be}")
        print("-------------------------------------------------------------------------")
        return summary_by_month

    # Run the 4 experiments
    res1 = simulate_hypothesis("1. BASELINE (Fixed 1.5% SL Limit Touch)", sl_mode="FIXED_15")
    res2 = simulate_hypothesis("2. CANDLE BODY CLOSE SL (Wick Sweep Immune)", sl_mode="CANDLE_BODY_CLOSE")
    res3 = simulate_hypothesis("3. 4H VOLATILITY-SCALED SL/TP (Room for 4H Normal ATR)", sl_mode="TF_VOLATILITY_SCALED")
    res4 = simulate_hypothesis("4. STRUCTURAL ORIGIN SL (Protected Behind Wave Origin)", sl_mode="STRUCTURAL_ORIGIN")

if __name__ == "__main__":
    run_experiment_suite()
