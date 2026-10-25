import sys
import os
import json
from datetime import datetime, timezone, timedelta

def test_ensemble_and_combinations():
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

    # Run Hermes 3.0 simulation with Body Close SL
    # Returns month dict: { "July 2026": final_bal, ... }
    def run_h30_sim(start_capital=50.0):
        # Extract H30 setups
        h30_candidates = []
        for m in months:
            m_start, m_end = m["start_ms"], m["end_ms"]
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
                                                        h30_candidates.append({
                                                            "month": m["name"], "symbol": c, "side": "LONG", "tf": tf,
                                                            "entry_time": tap_c["time"], "idx": t, "dataset": dataset, "ep": mt
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
                                                        h30_candidates.append({
                                                            "month": m["name"], "symbol": c, "side": "SHORT", "tf": tf,
                                                            "entry_time": tap_c["time"], "idx": t, "dataset": dataset, "ep": mt
                                                        })
                                                    break
        seen = set()
        uniq = []
        for ev in h30_candidates:
            k = (ev["symbol"], ev["entry_time"])
            if k not in seen:
                seen.add(k)
                uniq.append(ev)
        uniq.sort(key=lambda x: x["entry_time"])
        
        results = {}
        for m in months:
            m_events = [x for x in uniq if x["month"] == m["name"]]
            balance = start_capital
            busy_until = 0
            tps, sls, bes = 0, 0, 0
            for ev in m_events:
                if ev["entry_time"] < busy_until: continue
                ds = ev["dataset"]
                idx = ev["idx"]
                ep = ev["ep"]
                side = ev["side"]
                tp = round(ep * 1.0300, 8) if side == "LONG" else round(ep * 0.9700, 8)
                sl = round(ep * 0.9850, 8) if side == "LONG" else round(ep * 1.0150, 8)
                be_trig = round(ep * 1.0150, 8) if side == "LONG" else round(ep * 0.9850, 8)
                em_sl = round(ep * 0.9700, 8) if side == "LONG" else round(ep * 1.0300, 8)
                
                active_sl = sl
                be_locked = False
                outcome = None
                exit_time = ev["entry_time"]
                for bar in ds[idx+1:]:
                    b_h, b_l, b_c, b_t = float(bar["high"]), float(bar["low"]), float(bar["close"]), bar["time"]
                    if side == "LONG":
                        if not be_locked and b_h >= be_trig: be_locked, active_sl = True, ep
                        if b_h >= tp: outcome, exit_time = "TP", b_t; break
                        if be_locked:
                            if b_l <= active_sl: outcome, exit_time = "BE", b_t; break
                        else:
                            if b_l <= em_sl: outcome, exit_time = "SL", b_t; break
                            elif b_c <= sl: outcome, exit_time = "SL", b_t; break
                    else:
                        if not be_locked and b_l <= be_trig: be_locked, active_sl = True, ep
                        if b_l <= tp: outcome, exit_time = "TP", b_t; break
                        if be_locked:
                            if b_h >= active_sl: outcome, exit_time = "BE", b_t; break
                        else:
                            if b_h >= em_sl: outcome, exit_time = "SL", b_t; break
                            elif b_c >= sl: outcome, exit_time = "SL", b_t; break
                if not outcome: continue
                busy_until = exit_time
                if outcome == "TP": balance *= 1.15; tps += 1
                elif outcome == "SL": balance *= 0.925; sls += 1
                else: bes += 1
            results[m["name"]] = {"balance": balance, "tp": tps, "sl": sls, "be": bes}
        return results

    # Run Hermes 3.5 simulation with Body Close SL
    def run_h35_sim(start_capital=50.0):
        h35_candidates = []
        for m in months:
            m_start, m_end = m["start_ms"], m["end_ms"]
            for c in coins:
                for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
                    n = len(dataset)
                    if n < 40: continue
                    effective_min_bars = 18 if tf == "1h" else 8
                    effective_max_bars = 720 if tf == "1h" else 360
                    for i in range(5, n - 3):
                        c3, c2, c1 = dataset[i], dataset[i+1], dataset[i+2]
                        impulse_h = max(c1["high"], c2["high"])
                        impulse_l = min(c1["low"], c2["low"])
                        bull_fvg = (c1["low"] > c3["high"])
                        bull_disp = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                        if (c3["close"] < c3["open"]) and bull_fvg and (bull_disp >= 0.050):
                            ob_high, ob_low = c3["high"], c3["low"]
                            ob_rng = ob_high - ob_low
                            entry_p = round(ob_high - (ob_rng * 0.05), 8)
                            tp_p = round(entry_p * 1.0300, 8)
                            sl_p = round(entry_p * 0.9850, 8)
                            be_p = round(entry_p * 1.0150, 8)
                            em_sl = round(entry_p * 0.9700, 8)
                            peak_runway = impulse_h
                            for t in range(i + 3, n):
                                bar = dataset[t]
                                peak_runway = max(peak_runway, bar["high"])
                                runway_pct = ((peak_runway - ob_high) / ob_high) * 100.0
                                bars_alive = t - i
                                if bars_alive > effective_max_bars: break
                                if bar["close"] < ob_low: break
                                if bar["time"] < m_start: continue
                                if bar["time"] > m_end: break
                                if bar["low"] <= entry_p and bar["high"] >= entry_p:
                                    if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                        h35_candidates.append({
                                            "month": m["name"], "symbol": c, "side": "LONG", "tf": tf,
                                            "entry_time": bar["time"], "idx": t, "dataset": dataset,
                                            "ep": entry_p, "tp": tp_p, "sl": sl_p, "be": be_p, "em_sl": em_sl
                                        })
                                    break
                        bear_fvg = (c1["high"] < c3["low"])
                        bear_disp = (c3["high"] - impulse_l) / c3["high"] if c3["high"] > 0 else 0.0
                        if (c3["close"] > c3["open"]) and bear_fvg and (bear_disp >= 0.050):
                            ob_high, ob_low = c3["high"], c3["low"]
                            ob_rng = ob_high - ob_low
                            entry_p = round(ob_low + (ob_rng * 0.05), 8)
                            tp_p = round(entry_p * 0.9700, 8)
                            sl_p = round(entry_p * 1.0150, 8)
                            be_p = round(entry_p * 0.9850, 8)
                            em_sl = round(entry_p * 1.0300, 8)
                            peak_runway = impulse_l
                            for t in range(i + 3, n):
                                bar = dataset[t]
                                peak_runway = min(peak_runway, bar["low"])
                                runway_pct = ((ob_low - peak_runway) / ob_low) * 100.0
                                bars_alive = t - i
                                if bars_alive > effective_max_bars: break
                                if bar["close"] > ob_high: break
                                if bar["time"] < m_start: continue
                                if bar["time"] > m_end: break
                                if bar["high"] >= entry_p and bar["low"] <= entry_p:
                                    if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                        h35_candidates.append({
                                            "month": m["name"], "symbol": c, "side": "SHORT", "tf": tf,
                                            "entry_time": bar["time"], "idx": t, "dataset": dataset,
                                            "ep": entry_p, "tp": tp_p, "sl": sl_p, "be": be_p, "em_sl": em_sl
                                        })
                                    break
        seen = set()
        uniq = []
        for ev in h35_candidates:
            k = (ev["symbol"], ev["entry_time"])
            if k not in seen:
                seen.add(k)
                uniq.append(ev)
        uniq.sort(key=lambda x: x["entry_time"])
        results = {}
        for m in months:
            m_events = [x for x in uniq if x["month"] == m["name"]]
            balance = start_capital
            busy_until = 0
            tps, sls, bes = 0, 0, 0
            for ev in m_events:
                if ev["entry_time"] < busy_until: continue
                ds = ev["dataset"]
                idx = ev["idx"]
                ep, tp, sl, be_trig, em_sl = ev["ep"], ev["tp"], ev["sl"], ev["be"], ev["em_sl"]
                side = ev["side"]
                active_sl = sl
                be_locked = False
                outcome = None
                exit_time = ev["entry_time"]
                for bar in ds[idx+1:]:
                    b_h, b_l, b_c, b_t = float(bar["high"]), float(bar["low"]), float(bar["close"]), bar["time"]
                    if side == "LONG":
                        if not be_locked and b_h >= be_trig: be_locked, active_sl = True, ep
                        if b_h >= tp: outcome, exit_time = "TP", b_t; break
                        if be_locked:
                            if b_l <= active_sl: outcome, exit_time = "BE", b_t; break
                        else:
                            if b_l <= em_sl: outcome, exit_time = "SL", b_t; break
                            elif b_c <= sl: outcome, exit_time = "SL", b_t; break
                    else:
                        if not be_locked and b_l <= be_trig: be_locked, active_sl = True, ep
                        if b_l <= tp: outcome, exit_time = "TP", b_t; break
                        if be_locked:
                            if b_h >= active_sl: outcome, exit_time = "BE", b_t; break
                        else:
                            if b_h >= em_sl: outcome, exit_time = "SL", b_t; break
                            elif b_c >= sl: outcome, exit_time = "SL", b_t; break
                if not outcome: continue
                busy_until = exit_time
                if outcome == "TP": balance *= 1.15; tps += 1
                elif outcome == "SL": balance *= 0.925; sls += 1
                else: bes += 1
            results[m["name"]] = {"balance": balance, "tp": tps, "sl": sls, "be": bes}
        return results

    # Compute Ensemble ($50 allocated to H30 + $50 allocated to H35)
    r30 = run_h30_sim(50.0)
    r35 = run_h35_sim(50.0)
    
    print("\n" + "="*80)
    print("DUAL-ENGINE ENSEMBLE COMBINATION ($100 TOTAL: $50 H3.0 + $50 H3.5)")
    print("Both Powered by Candle Body Close SL (Dual-Threshold Defense)")
    print("="*80)
    
    for m in months:
        m_name = m["name"]
        b30 = r30[m_name]["balance"]
        b35 = r35[m_name]["balance"]
        total_bal = b30 + b35
        growth = ((total_bal - 100.0) / 100.0) * 100.0
        tot_tp = r30[m_name]["tp"] + r35[m_name]["tp"]
        tot_sl = r30[m_name]["sl"] + r35[m_name]["sl"]
        tot_be = r30[m_name]["be"] + r35[m_name]["be"]
        tot_trades = tot_tp + tot_sl + tot_be
        wr = ((tot_tp + tot_be) / tot_trades * 100.0) if tot_trades > 0 else 0.0
        
        print(f"[{m_name}] Combined Balance: ${total_bal:.2f} ({growth:+.2f}%) | H30: ${b30:.2f} | H35: ${b35:.2f}")
        print(f"       Trades: {tot_trades} | TP: {tot_tp} | BE: {tot_be} | SL: {tot_sl} | Eff Win Rate: {wr:.1f}%\n")

if __name__ == "__main__":
    test_ensemble_and_combinations()
