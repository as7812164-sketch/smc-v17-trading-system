import sys
import os
import json
from datetime import datetime, timezone, timedelta

def run_hermes35_comparison():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    
    months = [
        {"name": "July 2026", "start_ms": 1782864000000, "end_ms": 1785542399000},
        {"name": "August 2026", "start_ms": 1785542400000, "end_ms": 1788220799000},
        {"name": "September 2026", "start_ms": 1788220800000, "end_ms": 1790294400000}
    ]
    
    data_1h = {}
    data_4h = {}
    for c in coins:
        f1 = os.path.join(hist_dir, f"{c}_1h.json")
        f4 = os.path.join(hist_dir, f"{c}_4h.json")
        if os.path.exists(f1):
            with open(f1, "r", encoding="utf-8") as f: data_1h[c] = json.load(f)
        if os.path.exists(f4):
            with open(f4, "r", encoding="utf-8") as f: data_4h[c] = json.load(f)

    # 1. Extract base Hermes 3.5 candidates
    all_month_candidates = {}
    for m in months:
        m_start = m["start_ms"]
        m_end = m["end_ms"]
        candidates = []
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
                    
                    # Bullish OB
                    bull_fvg = (c1["low"] > c3["high"])
                    bull_disp = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                    if (c3["close"] < c3["open"]) and bull_fvg and (bull_disp >= 0.050):
                        ob_high, ob_low = c3["high"], c3["low"]
                        ob_rng = ob_high - ob_low
                        entry_p = round(ob_high - (ob_rng * 0.05), 8)
                        tp_p = round(entry_p * 1.0300, 8)
                        sl_p = round(entry_p * 0.9850, 8)
                        be_p = round(entry_p * 1.0150, 8)
                        emergency_sl = round(entry_p * 0.9700, 8)
                        
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
                                    candidates.append({
                                        "month": m["name"], "symbol": c, "side": "LONG", "tf": tf,
                                        "entry_time": bar["time"], "idx": t, "dataset": dataset,
                                        "ep": entry_p, "tp": tp_p, "sl": sl_p, "be": be_p, "em_sl": emergency_sl
                                    })
                                break
                    
                    # Bearish OB
                    bear_fvg = (c1["high"] < c3["low"])
                    bear_disp = (c3["high"] - impulse_l) / c3["high"] if c3["high"] > 0 else 0.0
                    if (c3["close"] > c3["open"]) and bear_fvg and (bear_disp >= 0.050):
                        ob_high, ob_low = c3["high"], c3["low"]
                        ob_rng = ob_high - ob_low
                        entry_p = round(ob_low + (ob_rng * 0.05), 8)
                        tp_p = round(entry_p * 0.9700, 8)
                        sl_p = round(entry_p * 1.0150, 8)
                        be_p = round(entry_p * 0.9850, 8)
                        emergency_sl = round(entry_p * 1.0300, 8)
                        
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
                                    candidates.append({
                                        "month": m["name"], "symbol": c, "side": "SHORT", "tf": tf,
                                        "entry_time": bar["time"], "idx": t, "dataset": dataset,
                                        "ep": entry_p, "tp": tp_p, "sl": sl_p, "be": be_p, "em_sl": emergency_sl
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
        all_month_candidates[m["name"]] = uniq

    # Now run two simulations on the EXACT same candidates:
    # 1. Baseline: Limit SL touch
    # 2. Body-Close: SL only on candle body close (or -3% emergency hard stop)
    for mode in ["BASELINE_LIMIT", "BODY_CLOSE_SL"]:
        print(f"\n{'='*75}")
        print(f"HERMES 3.5 MODE: {mode}")
        print(f"{'='*75}")
        total_3m_tp = 0
        total_3m_sl = 0
        total_3m_be = 0
        total_3m_trades = 0
        
        for m in months:
            m_candidates = all_month_candidates[m["name"]]
            balance = 100.00
            peak_balance = 100.00
            max_drawdown = 0.0
            busy_until = 0
            
            tps, sls, bes = 0, 0, 0
            
            for ev in m_candidates:
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
                        # BE Lock trigger
                        if not be_locked and b_h >= be_trig:
                            be_locked = True
                            active_sl = ep
                            
                        # TP hit
                        if b_h >= tp:
                            outcome = "TP"
                            exit_time = b_t
                            break
                            
                        if mode == "BASELINE_LIMIT":
                            if b_l <= active_sl:
                                outcome = "BE" if be_locked else "SL"
                                exit_time = b_t
                                break
                        else: # BODY_CLOSE_SL
                            if be_locked:
                                # BE lock: if touches breakeven entry price
                                if b_l <= active_sl:
                                    outcome = "BE"
                                    exit_time = b_t
                                    break
                            else:
                                # Emergency hard stop (-3%) touch
                                if b_l <= em_sl:
                                    outcome = "SL"
                                    exit_time = b_t
                                    break
                                # Soft SL: Candle Body Closes below -1.5%
                                elif b_c <= sl:
                                    outcome = "SL"
                                    exit_time = b_t
                                    break
                    else: # SHORT
                        # BE Lock trigger
                        if not be_locked and b_l <= be_trig:
                            be_locked = True
                            active_sl = ep
                            
                        # TP hit
                        if b_l <= tp:
                            outcome = "TP"
                            exit_time = b_t
                            break
                            
                        if mode == "BASELINE_LIMIT":
                            if b_h >= active_sl:
                                outcome = "BE" if be_locked else "SL"
                                exit_time = b_t
                                break
                        else: # BODY_CLOSE_SL
                            if be_locked:
                                if b_h >= active_sl:
                                    outcome = "BE"
                                    exit_time = b_t
                                    break
                            else:
                                # Emergency hard stop (-3%) touch
                                if b_h >= em_sl:
                                    outcome = "SL"
                                    exit_time = b_t
                                    break
                                # Soft SL: Candle Body Closes above +1.5%
                                elif b_c >= sl:
                                    outcome = "SL"
                                    exit_time = b_t
                                    break
                                    
                if not outcome: continue
                busy_until = exit_time
                
                # Compounding PnL (5x leverage, 100% equity sequential compounding)
                if outcome == "TP":
                    balance *= (1.0 + 0.150)
                    tps += 1
                elif outcome == "SL":
                    balance *= (1.0 - 0.075)
                    sls += 1
                else: # BE
                    bes += 1
                    
                if balance > peak_balance:
                    peak_balance = balance
                dd = (peak_balance - balance) / peak_balance if peak_balance > 0 else 0.0
                if dd > max_drawdown:
                    max_drawdown = dd
                    
            n_t = tps + sls + bes
            eff_wr = ((tps + bes) / n_t * 100.0) if n_t > 0 else 0.0
            print(f"[{m['name']}] Final: ${balance:.2f} ({balance-100:+.2f}%) | Trades: {n_t} | TP: {tps} | BE: {bes} | SL: {sls} | Eff WR: {eff_wr:.1f}% | Max DD: {max_drawdown*100:.2f}%")
            total_3m_tp += tps
            total_3m_sl += sls
            total_3m_be += bes
            total_3m_trades += n_t
            
        print(f"--> 3-MONTH TOTALS: Trades: {total_3m_trades} | TP: {total_3m_tp} ({(total_3m_tp/total_3m_trades)*100:.1f}%) | SL: {total_3m_sl} ({(total_3m_sl/total_3m_trades)*100:.1f}%) | BE: {total_3m_be}")

if __name__ == "__main__":
    run_hermes35_comparison()
