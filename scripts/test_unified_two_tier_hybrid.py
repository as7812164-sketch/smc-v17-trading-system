import sys
import os
import json

def test_unified_two_tier():
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    data_1h, data_4h = {}, {}
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

    # Two-Tier Adaptive Execution:
    # Tier 1 fills at 5% Boundary.
    # Tier 2 fills if price reaches 50% Mean Threshold.
    # If only Tier 1 fills, size is 0.5x, entry is Tier 1.
    # If both fill, size is 1.0x, blended entry = (T1 + T2)/2.
    # Both use Candle Body Close SL (-1.50%) + Emergency Circuit Breaker (-3.00%) + BE Armor (+1.50%).
    
    candidates = []
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
                    
                    # LONG OB
                    bull_fvg = (c1["low"] > c3["high"])
                    bull_disp = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                    if (c3["close"] < c3["open"]) and bull_fvg and (bull_disp >= 0.050):
                        ob_high, ob_low = c3["high"], c3["low"]
                        ob_rng = ob_high - ob_low
                        t1_price = round(ob_high - (ob_rng * 0.05), 8)
                        t2_price = round((ob_high + ob_low) / 2.0, 8)
                        
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
                            
                            # First tap check
                            if bar["low"] <= t1_price and bar["high"] >= t1_price:
                                if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                    candidates.append({
                                        "month": m["name"], "symbol": c, "side": "LONG", "tf": tf,
                                        "entry_time": bar["time"], "idx": t, "dataset": dataset,
                                        "t1_price": t1_price, "t2_price": t2_price
                                    })
                                break
                                
                    # SHORT OB
                    bear_fvg = (c1["high"] < c3["low"])
                    bear_disp = (c3["high"] - impulse_l) / c3["high"] if c3["high"] > 0 else 0.0
                    if (c3["close"] > c3["open"]) and bear_fvg and (bear_disp >= 0.050):
                        ob_high, ob_low = c3["high"], c3["low"]
                        ob_rng = ob_high - ob_low
                        t1_price = round(ob_low + (ob_rng * 0.05), 8)
                        t2_price = round((ob_high + ob_low) / 2.0, 8)
                        
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
                            
                            if bar["high"] >= t1_price and bar["low"] <= t1_price:
                                if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                    candidates.append({
                                        "month": m["name"], "symbol": c, "side": "SHORT", "tf": tf,
                                        "entry_time": bar["time"], "idx": t, "dataset": dataset,
                                        "t1_price": t1_price, "t2_price": t2_price
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

    print("\n" + "="*80)
    print("UNIFIED TWO-TIER ADAPTIVE HYBRID (Tier 1 @ Boundary + Tier 2 @ Mean Threshold)")
    print("Armed with Dual-Threshold Candle Body Close SL & BE Armor")
    print("="*80)
    
    for m in months:
        m_events = [x for x in uniq if x["month"] == m["name"]]
        balance = 100.00
        peak_balance = 100.00
        max_drawdown = 0.0
        busy_until = 0
        tps, sls, bes = 0, 0, 0
        both_fills = 0
        
        for ev in m_events:
            if ev["entry_time"] < busy_until: continue
            ds = ev["dataset"]
            idx = ev["idx"]
            t1, t2 = ev["t1_price"], ev["t2_price"]
            side = ev["side"]
            
            # Start with Tier 1 filled
            blended_ep = t1
            tier2_filled = False
            
            # Check if entry bar already tapped t2
            entry_bar = ds[idx]
            if side == "LONG" and float(entry_bar["low"]) <= t2:
                tier2_filled = True
                blended_ep = (t1 + t2) / 2.0
                both_fills += 1
            elif side == "SHORT" and float(entry_bar["high"]) >= t2:
                tier2_filled = True
                blended_ep = (t1 + t2) / 2.0
                both_fills += 1
                
            tp = round(blended_ep * 1.0300, 8) if side == "LONG" else round(blended_ep * 0.9700, 8)
            sl = round(blended_ep * 0.9850, 8) if side == "LONG" else round(blended_ep * 1.0150, 8)
            be_trig = round(blended_ep * 1.0150, 8) if side == "LONG" else round(blended_ep * 0.9850, 8)
            em_sl = round(blended_ep * 0.9700, 8) if side == "LONG" else round(blended_ep * 1.0300, 8)
            
            active_sl = sl
            be_locked = False
            outcome = None
            exit_time = ev["entry_time"]
            
            for bar in ds[idx+1:]:
                b_h, b_l, b_c, b_t = float(bar["high"]), float(bar["low"]), float(bar["close"]), bar["time"]
                
                # Check if tier 2 fills subsequently if not yet filled
                if not tier2_filled:
                    if (side == "LONG" and b_l <= t2) or (side == "SHORT" and b_h >= t2):
                        tier2_filled = True
                        blended_ep = (t1 + t2) / 2.0
                        both_fills += 1
                        # Recalibrate TP/SL based on improved blended price
                        tp = round(blended_ep * 1.0300, 8) if side == "LONG" else round(blended_ep * 0.9700, 8)
                        sl = round(blended_ep * 0.9850, 8) if side == "LONG" else round(blended_ep * 1.0150, 8)
                        be_trig = round(blended_ep * 1.0150, 8) if side == "LONG" else round(blended_ep * 0.9850, 8)
                        em_sl = round(blended_ep * 0.9700, 8) if side == "LONG" else round(blended_ep * 1.0300, 8)
                        if not be_locked: active_sl = sl
                
                if side == "LONG":
                    if not be_locked and b_h >= be_trig:
                        be_locked, active_sl = True, blended_ep
                    if b_h >= tp:
                        outcome, exit_time = "TP", b_t
                        break
                    if be_locked:
                        if b_l <= active_sl:
                            outcome, exit_time = "BE", b_t
                            break
                    else:
                        if b_l <= em_sl:
                            outcome, exit_time = "SL", b_t
                            break
                        elif b_c <= sl:
                            outcome, exit_time = "SL", b_t
                            break
                else: # SHORT
                    if not be_locked and b_l <= be_trig:
                        be_locked, active_sl = True, blended_ep
                    if b_l <= tp:
                        outcome, exit_time = "TP", b_t
                        break
                    if be_locked:
                        if b_h >= active_sl:
                            outcome, exit_time = "BE", b_t
                            break
                    else:
                        if b_h >= em_sl:
                            outcome, exit_time = "SL", b_t
                            break
                        elif b_c >= sl:
                            outcome, exit_time = "SL", b_t
                            break
                            
            if not outcome: continue
            busy_until = exit_time
            
            # Position sizing: If both filled -> 100% size (15% TP, -7.5% SL). If only Tier 1 filled -> 50% size (7.5% TP, -3.75% SL)
            multiplier = 1.0 if tier2_filled else 0.5
            if outcome == "TP":
                balance *= (1.0 + (0.150 * multiplier))
                tps += 1
            elif outcome == "SL":
                balance *= (1.0 - (0.075 * multiplier))
                sls += 1
            else:
                bes += 1
                
            if balance > peak_balance: peak_balance = balance
            dd = (peak_balance - balance) / peak_balance * 100.0 if peak_balance > 0 else 0.0
            if dd > max_drawdown: max_drawdown = dd
            
        n_t = tps + sls + bes
        eff_wr = ((tps + bes) / n_t * 100.0) if n_t > 0 else 0.0
        growth = ((balance - 100.0) / 100.0) * 100.0
        print(f"[{m['name']}] Final Balance: ${balance:.2f} ({growth:+.2f}%) | Trades: {n_t} (Both Filled: {both_fills})")
        print(f"       TP: {tps} | BE: {bes} | SL: {sls} | Eff WR: {eff_wr:.1f}% | Max DD: {max_drawdown:.2f}%\n")

if __name__ == "__main__":
    test_unified_two_tier()
