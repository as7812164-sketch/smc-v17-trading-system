import os
import sys
import json
import glob

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def run_test():
    # 1. Gather symbols that have both 1h and 15m data
    coins_15m = [os.path.basename(f).replace("_15m.json", "") for f in glob.glob("market_data_cache_15m/*_15m.json")]
    coins_1h = [os.path.basename(f).replace("_1h.json", "") for f in glob.glob("historical_data/*_1h.json")]
    common_symbols = sorted(list(set(coins_15m).intersection(set(coins_1h))))
    
    print(f"Testing on {len(common_symbols)} institutional pairs with exact 15m microstructure:")
    print(common_symbols)
    
    # Let's run backtests for both models:
    # Model 1: BASELINE HERMES 3.5 (18% Rejection Wick + 15m Sniper Gate)
    # Model 2: USER PROPOSED (15m close strictly inside OB zone, no wick required)

    results = {
        "HERMES_3.5_BASELINE": {
            "trades": 0, "wins": 0, "losses": 0, "be_armors": 0, "win_rate": 0.0, "total_pnl": 0.0, "max_dd": 0.0,
            "avg_r": 0.0, "falling_knives_avoided": 0
        },
        "USER_15M_INSIDE_OB": {
            "trades": 0, "wins": 0, "losses": 0, "be_armors": 0, "win_rate": 0.0, "total_pnl": 0.0, "max_dd": 0.0,
            "avg_r": 0.0, "fakeouts_caught": 0
        },
        "USER_15M_DEFENDED_NO_WICK": {
            "trades": 0, "wins": 0, "losses": 0, "be_armors": 0, "win_rate": 0.0, "total_pnl": 0.0, "max_dd": 0.0,
            "avg_r": 0.0
        }
    }

    # Parameters
    tp_pct = 0.0220       # +11.0% ROE @ 5x
    sl_pct = 0.0280       # -14.0% ROE @ 5x
    be_trigger = 0.0150   # BE Armor
    min_runway = 0.040    # 4.0% Airspace
    min_displacement = 0.050

    for sym in common_symbols:
        f_1h = f"historical_data/{sym}_1h.json"
        f_15m = f"market_data_cache_15m/{sym}_15m.json"
        
        with open(f_1h, "r") as fp:
            raw_1h = json.load(fp)
        with open(f_15m, "r") as fp:
            raw_15m = json.load(fp)
            
        c_1h = [{"t": c.get("time") or c.get("open_time"), "o": float(c["open"]), "h": float(c["high"]), "l": float(c["low"]), "c": float(c["close"])} for c in raw_1h]
        c_15m = [{"t": c.get("time") or c.get("open_time"), "o": float(c["open"]), "h": float(c["high"]), "l": float(c["low"]), "c": float(c["close"])} for c in raw_15m]
        
        # Build 15m timestamp lookup
        t_15m_map = {c["t"]: idx for idx, c in enumerate(c_15m)}
        t_15m_times = [c["t"] for c in c_15m]

        n = len(c_1h)
        for i in range(10, n - 40):
            c3 = c_1h[i]
            c2 = c_1h[i+1]
            c1 = c_1h[i+2]
            
            imp_h = max(c1["h"], c2["h"])
            # Bullish OB detection
            is_red = c3["c"] < c3["o"]
            fvg = c1["l"] > c3["h"]
            disp = (imp_h - c3["l"]) / c3["l"] if c3["l"] > 0 else 0.0
            
            if is_red and fvg and disp >= min_displacement:
                ob_high = c3["h"]
                ob_low = c3["l"]
                ob_range = ob_high - ob_low
                mt_50 = (ob_high + ob_low) / 2.0
                boundary_5pct = ob_high - (0.05 * ob_range)

                # Check forward for virgin tap
                peak_runway = imp_h
                tap_1h_idx = -1
                for k in range(i + 3, min(i + 300, n)):
                    bar = c_1h[k]
                    peak_runway = max(peak_runway, bar["h"])
                    
                    # Broken before tap
                    if bar["c"] < ob_low:
                        break
                    
                    # Airspace check
                    runway_pct = (peak_runway - ob_high) / ob_high if ob_high > 0 else 0.0
                    if runway_pct < min_runway:
                        continue
                        
                    # 5% boundary tap
                    if bar["l"] <= boundary_5pct:
                        tap_1h_idx = k
                        break
                
                if tap_1h_idx == -1:
                    continue
                
                tap_time_1h = c_1h[tap_1h_idx]["t"]
                
                # Find matching 15m candles during this 1h bar
                # Find the 15m candle where the tap first occurred
                matching_15m = [idx for idx, t_m in enumerate(t_15m_times) if tap_time_1h <= t_m < tap_time_1h + 3600000]
                if not matching_15m:
                    continue
                
                tap_15m_idx = -1
                for idx_15 in matching_15m:
                    if c_15m[idx_15]["l"] <= boundary_5pct:
                        tap_15m_idx = idx_15
                        break
                        
                if tap_15m_idx == -1:
                    tap_15m_idx = matching_15m[0]
                
                tap_candle_15m = c_15m[tap_15m_idx]
                
                # --- MODEL 1: BASELINE HERMES 3.5 ---
                # Requires >= 18% rejection wick (or 15m micro-gate lower wick >= 15% / green close)
                c_rng = tap_candle_15m["h"] - tap_candle_15m["l"]
                l_wick = min(tap_candle_15m["o"], tap_candle_15m["c"]) - tap_candle_15m["l"]
                w_ratio = (l_wick / c_rng) if c_rng > 0 else 0.0
                is_green = tap_candle_15m["c"] >= tap_candle_15m["o"]
                
                h35_pass = (w_ratio >= 0.15 or is_green) and (tap_candle_15m["c"] >= mt_50)
                
                if h35_pass:
                    # Execute at boundary / close
                    entry_p = boundary_5pct
                    tp_p = entry_p * (1.0 + tp_pct)
                    sl_p = entry_p * (1.0 - sl_pct)
                    be_p = entry_p * (1.0 + be_trigger)
                    
                    be_active = False
                    won = False
                    lost = False
                    
                    # Forward simulation on 15m
                    for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                        sc = c_15m[s]
                        if sc["h"] >= be_p:
                            be_active = True
                        if sc["h"] >= tp_p:
                            won = True
                            break
                        if be_active and sc["l"] <= entry_p * 1.001:
                            # BE exit
                            break
                        if sc["l"] <= sl_p:
                            lost = True
                            break
                    
                    results["HERMES_3.5_BASELINE"]["trades"] += 1
                    if won:
                        results["HERMES_3.5_BASELINE"]["wins"] += 1
                        results["HERMES_3.5_BASELINE"]["total_pnl"] += tp_pct * 5.0
                    elif lost:
                        results["HERMES_3.5_BASELINE"]["losses"] += 1
                        results["HERMES_3.5_BASELINE"]["total_pnl"] -= sl_pct * 5.0
                    else:
                        results["HERMES_3.5_BASELINE"]["be_armors"] += 1
                        results["HERMES_3.5_BASELINE"]["total_pnl"] += 0.005 # Small BE buffer
                else:
                    results["HERMES_3.5_BASELINE"]["falling_knives_avoided"] += 1

                # --- MODEL 2A: USER STRICT INSIDE OB (ob_low <= c <= ob_high) ---
                user_a_pass = (ob_low <= tap_candle_15m["c"] <= ob_high)
                
                # --- MODEL 2B: USER DEFENDED OB (c >= ob_low) - no wick requirement ---
                user_b_pass = (tap_candle_15m["c"] >= ob_low)

                # Process 2A
                if user_a_pass:
                    entry_p = tap_candle_15m["c"]
                    tp_p = entry_p * (1.0 + tp_pct)
                    sl_p = entry_p * (1.0 - sl_pct)
                    be_p = entry_p * (1.0 + be_trigger)
                    
                    be_active = False
                    won = False
                    lost = False
                    
                    for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                        sc = c_15m[s]
                        if sc["h"] >= be_p: be_active = True
                        if sc["h"] >= tp_p: won = True; break
                        if be_active and sc["l"] <= entry_p * 1.001: break
                        if sc["l"] <= sl_p: lost = True; break
                            
                    results["USER_15M_INSIDE_OB"]["trades"] += 1
                    if won:
                        results["USER_15M_INSIDE_OB"]["wins"] += 1
                        results["USER_15M_INSIDE_OB"]["total_pnl"] += tp_pct * 5.0
                    elif lost:
                        results["USER_15M_INSIDE_OB"]["losses"] += 1
                        results["USER_15M_INSIDE_OB"]["total_pnl"] -= sl_pct * 5.0
                    else:
                        results["USER_15M_INSIDE_OB"]["be_armors"] += 1
                        results["USER_15M_INSIDE_OB"]["total_pnl"] += 0.005

                # Process 2B (If in results)
                if "USER_15M_DEFENDED_NO_WICK" in results and user_b_pass:
                    entry_p = tap_candle_15m["c"]
                    tp_p = entry_p * (1.0 + tp_pct)
                    sl_p = entry_p * (1.0 - sl_pct)
                    be_p = entry_p * (1.0 + be_trigger)
                    
                    be_active = False
                    won = False
                    lost = False
                    
                    for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                        sc = c_15m[s]
                        if sc["h"] >= be_p: be_active = True
                        if sc["h"] >= tp_p: won = True; break
                        if be_active and sc["l"] <= entry_p * 1.001: break
                        if sc["l"] <= sl_p: lost = True; break
                            
                    results["USER_15M_DEFENDED_NO_WICK"]["trades"] += 1
                    if won:
                        results["USER_15M_DEFENDED_NO_WICK"]["wins"] += 1
                        results["USER_15M_DEFENDED_NO_WICK"]["total_pnl"] += tp_pct * 5.0
                    elif lost:
                        results["USER_15M_DEFENDED_NO_WICK"]["losses"] += 1
                        results["USER_15M_DEFENDED_NO_WICK"]["total_pnl"] -= sl_pct * 5.0
                    else:
                        results["USER_15M_DEFENDED_NO_WICK"]["be_armors"] += 1
                        results["USER_15M_DEFENDED_NO_WICK"]["total_pnl"] += 0.005

    # Compute win rates
    for k in results:
        t = results[k]["trades"]
        w = results[k]["wins"]
        l = results[k]["losses"]
        b = results[k]["be_armors"]
        decided = w + l
        wr = (w / decided * 100.0) if decided > 0 else 0.0
        results[k]["win_rate"] = round(wr, 2)
        results[k]["total_pnl"] = round(results[k]["total_pnl"] * 100.0, 2) # in ROE %
        
    print("\n--- FINAL QUANT RESULTS ---")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_test()
