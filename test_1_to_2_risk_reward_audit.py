import os
import sys
import json
import glob

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def run_test():
    coins_15m = [os.path.basename(f).replace("_15m.json", "") for f in glob.glob("market_data_cache_15m/*_15m.json")]
    coins_1h = [os.path.basename(f).replace("_1h.json", "") for f in glob.glob("historical_data/*_1h.json")]
    common_symbols = sorted(list(set(coins_15m).intersection(set(coins_1h))))
    
    print(f"Running 1:2 Risk-to-Reward Audit across {len(common_symbols)} institutional pairs:")
    print(common_symbols)

    # We will test 3 Models under Strict 1:2 Risk to Reward:
    # Model 1: HERMES 3.5 Baseline (18% Rejection Wick + 50% MT Defense) with 1:2 R:R
    # Model 2: USER Rule A (15m close inside OB) with 1:2 R:R
    # Model 3: USER Rule B (15m close >= OB Low, no wick) with 1:2 R:R
    
    # We will evaluate both:
    # (A) Pure 1:2 R:R (No BE armor, only TP or SL)
    # (B) 1:2 R:R with 1R Breakeven Armor (When price reaches +1R, SL moves to Breakeven)

    modes = ["HERMES_3.5_BASELINE", "USER_15M_INSIDE_OB", "USER_15M_DEFENDED_NO_WICK"]
    
    results = {
        m: {
            "pure_1_to_2": {"trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "total_r": 0.0},
            "with_1r_be": {"trades": 0, "wins": 0, "losses": 0, "be_cuts": 0, "win_rate": 0.0, "total_r": 0.0}
        }
        for m in modes
    }

    min_runway = 0.040
    min_displacement = 0.050

    for sym in common_symbols:
        f_1h = f"historical_data/{sym}_1h.json"
        f_15m = f"market_data_cache_15m/{sym}_15m.json"
        
        with open(f_1h, "r") as fp: raw_1h = json.load(fp)
        with open(f_15m, "r") as fp: raw_15m = json.load(fp)
            
        c_1h = [{"t": c.get("time") or c.get("open_time"), "o": float(c["open"]), "h": float(c["high"]), "l": float(c["low"]), "c": float(c["close"])} for c in raw_1h]
        c_15m = [{"t": c.get("time") or c.get("open_time"), "o": float(c["open"]), "h": float(c["high"]), "l": float(c["low"]), "c": float(c["close"])} for c in raw_15m]
        
        t_15m_times = [c["t"] for c in c_15m]
        n = len(c_1h)

        for i in range(10, n - 40):
            c3 = c_1h[i]
            c2 = c_1h[i+1]
            c1 = c_1h[i+2]
            
            imp_h = max(c1["h"], c2["h"])
            is_red = c3["c"] < c3["o"]
            fvg = c1["l"] > c3["h"]
            disp = (imp_h - c3["l"]) / c3["l"] if c3["l"] > 0 else 0.0
            
            if is_red and fvg and disp >= min_displacement:
                ob_high = c3["h"]
                ob_low = c3["l"]
                ob_range = ob_high - ob_low
                mt_50 = (ob_high + ob_low) / 2.0
                boundary_5pct = ob_high - (0.05 * ob_range)

                peak_runway = imp_h
                tap_1h_idx = -1
                for k in range(i + 3, min(i + 300, n)):
                    bar = c_1h[k]
                    peak_runway = max(peak_runway, bar["h"])
                    if bar["c"] < ob_low: break
                    runway_pct = (peak_runway - ob_high) / ob_high if ob_high > 0 else 0.0
                    if runway_pct < min_runway: continue
                    if bar["l"] <= boundary_5pct:
                        tap_1h_idx = k
                        break
                
                if tap_1h_idx == -1: continue
                
                tap_time_1h = c_1h[tap_1h_idx]["t"]
                matching_15m = [idx for idx, t_m in enumerate(t_15m_times) if tap_time_1h <= t_m < tap_time_1h + 3600000]
                if not matching_15m: continue
                
                tap_15m_idx = -1
                for idx_15 in matching_15m:
                    if c_15m[idx_15]["l"] <= boundary_5pct:
                        tap_15m_idx = idx_15
                        break
                if tap_15m_idx == -1: tap_15m_idx = matching_15m[0]
                
                tap_candle_15m = c_15m[tap_15m_idx]
                
                # Eligibility checks for the 3 modes:
                c_rng = tap_candle_15m["h"] - tap_candle_15m["l"]
                l_wick = min(tap_candle_15m["o"], tap_candle_15m["c"]) - tap_candle_15m["l"]
                w_ratio = (l_wick / c_rng) if c_rng > 0 else 0.0
                is_green = tap_candle_15m["c"] >= tap_candle_15m["o"]
                
                elig = {
                    "HERMES_3.5_BASELINE": (w_ratio >= 0.15 or is_green) and (tap_candle_15m["c"] >= mt_50),
                    "USER_15M_INSIDE_OB": (ob_low <= tap_candle_15m["c"] <= ob_high),
                    "USER_15M_DEFENDED_NO_WICK": (tap_candle_15m["c"] >= ob_low)
                }

                for m in modes:
                    if not elig[m]: continue
                    
                    entry_p = boundary_5pct if m == "HERMES_3.5_BASELINE" else tap_candle_15m["c"]
                    
                    # Structural SL: Just below OB low (0.2% buffer)
                    struct_sl = ob_low * 0.998
                    risk_amount = entry_p - struct_sl
                    
                    if risk_amount <= 0 or (risk_amount / entry_p) > 0.05:
                        # Unrealistic risk, cap SL at 2.5%
                        risk_pct = 0.025
                        sl_p = entry_p * (1.0 - risk_pct)
                        tp_p = entry_p * (1.0 + (2.0 * risk_pct)) # 1:2 R:R (TP = +5.0%)
                        risk_r = 1.0
                    else:
                        sl_p = struct_sl
                        tp_p = entry_p + (2.0 * risk_amount) # Exact 1:2 R:R
                        risk_r = 1.0

                    be_1r_trigger = entry_p + (1.0 * (entry_p - sl_p)) # +1R mark

                    # Simulation 1: Pure 1:2 (No BE Armor)
                    pure_won = False
                    pure_lost = False
                    for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                        sc = c_15m[s]
                        if sc["h"] >= tp_p:
                            pure_won = True
                            break
                        if sc["l"] <= sl_p:
                            pure_lost = True
                            break
                            
                    res_pure = results[m]["pure_1_to_2"]
                    res_pure["trades"] += 1
                    if pure_won:
                        res_pure["wins"] += 1
                        res_pure["total_r"] += 2.0
                    elif pure_lost:
                        res_pure["losses"] += 1
                        res_pure["total_r"] -= 1.0

                    # Simulation 2: 1:2 with 1R Breakeven Armor
                    be_active = False
                    be_won = False
                    be_lost = False
                    be_cut = False
                    for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                        sc = c_15m[s]
                        if sc["h"] >= be_1r_trigger:
                            be_active = True
                        if sc["h"] >= tp_p:
                            be_won = True
                            break
                        if be_active and sc["l"] <= entry_p * 1.001:
                            be_cut = True
                            break
                        if sc["l"] <= sl_p:
                            be_lost = True
                            break
                            
                    res_be = results[m]["with_1r_be"]
                    res_be["trades"] += 1
                    if be_won:
                        res_be["wins"] += 1
                        res_be["total_r"] += 2.0
                    elif be_lost:
                        res_be["losses"] += 1
                        res_be["total_r"] -= 1.0
                    elif be_cut:
                        res_be["be_cuts"] += 1

    # Calculate Win Rates
    for m in modes:
        for sub in ["pure_1_to_2", "with_1r_be"]:
            d = results[m][sub]
            t = d["trades"]
            w = d["wins"]
            l = d["losses"]
            decided = w + l
            wr = (w / decided * 100.0) if decided > 0 else 0.0
            d["win_rate"] = round(wr, 2)
            d["total_r"] = round(d["total_r"], 2)

    print("\n--- 1:2 RISK TO REWARD AUDIT RESULTS ---")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_test()
