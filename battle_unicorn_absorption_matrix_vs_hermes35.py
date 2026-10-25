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

def run_battle():
    # Gather pairs with 1h and 15m data
    coins_15m = [os.path.basename(f).replace("_15m.json", "") for f in glob.glob("market_data_cache_15m/*_15m.json")]
    coins_1h = [os.path.basename(f).replace("_1h.json", "") for f in glob.glob("historical_data/*_1h.json")]
    common_symbols = sorted(list(set(coins_15m).intersection(set(coins_1h))))
    
    print(f"================================================================================")
    print(f"⚔️ STRATEGY BATTLE: HERMES 3.5 BASELINE vs PROPRIETARY UNICORN ABSORPTION ENGINE")
    print(f"Testing on {len(common_symbols)} institutional crypto pairs across real microstructure data")
    print(f"================================================================================")

    results = {
        "HERMES_3.5_BASELINE": {
            "trades": 0, "wins": 0, "losses": 0, "be_cuts": 0,
            "win_rate": 0.0, "total_roe": 0.0, "total_r": 0.0, "profit_factor": 0.0,
            "gross_profit": 0.0, "gross_loss": 0.0
        },
        "PROPRIETARY_UNICORN_ABSORPTION": {
            "trades": 0, "wins": 0, "losses": 0, "be_cuts": 0,
            "win_rate": 0.0, "total_roe": 0.0, "total_r": 0.0, "profit_factor": 0.0,
            "gross_profit": 0.0, "gross_loss": 0.0,
            "unicorn_models_hit": 0, "extreme_ob_hit": 0
        }
    }

    # Parameters for Baseline Hermes 3.5:
    # Fixed TP 2.2%, SL 2.8%, BE at 1.5%
    h35_tp = 0.0220
    h35_sl = 0.0280
    h35_be = 0.0150

    for sym in common_symbols:
        f_1h = f"historical_data/{sym}_1h.json"
        f_15m = f"market_data_cache_15m/{sym}_15m.json"
        
        with open(f_1h, "r") as fp: raw_1h = json.load(fp)
        with open(f_15m, "r") as fp: raw_15m = json.load(fp)
            
        c_1h = [{"t": c.get("time") or c.get("open_time"), "o": float(c["open"]), "h": float(c["high"]), "l": float(c["low"]), "c": float(c["close"]), "v": float(c.get("volume", 0.0))} for c in raw_1h]
        c_15m = [{"t": c.get("time") or c.get("open_time"), "o": float(c["open"]), "h": float(c["high"]), "l": float(c["low"]), "c": float(c["close"]), "v": float(c.get("volume", 0.0))} for c in raw_15m]
        
        t_15m_times = [c["t"] for c in c_15m]
        n = len(c_1h)

        for i in range(15, n - 40):
            c3 = c_1h[i]
            c2 = c_1h[i+1]
            c1 = c_1h[i+2]
            
            imp_h = max(c1["h"], c2["h"])
            imp_l = min(c1["l"], c2["l"])
            
            # --- STRUCTURE SCANNING ---
            is_red = c3["c"] < c3["o"]
            fvg = c1["l"] > c3["h"]
            disp = (imp_h - c3["l"]) / c3["l"] if c3["l"] > 0 else 0.0
            
            # 50% Equilibrium Context on 1H:
            # Measure prior 40-bar range to see if c3 is in DISCOUNT (< 50%)
            lookback_h = max(c["h"] for c in c_1h[max(0, i-40):i+1])
            lookback_l = min(c["l"] for c in c_1h[max(0, i-40):i+1])
            equilibrium_50 = (lookback_h + lookback_l) / 2.0
            is_in_discount = c3["l"] <= equilibrium_50
            
            # Liquidity Sweep Pre-condition:
            # Did c3 or c3-1 sweep a prior swing low in the previous 10 bars?
            prior_lows = [c["l"] for c in c_1h[max(0, i-10):i]]
            min_prior_low = min(prior_lows) if prior_lows else c3["l"]
            has_swept_liquidity = (c3["l"] < min_prior_low) or (c_1h[i-1]["l"] < min_prior_low)
            
            # Breaker Block (Unicorn) Check:
            # Did price sweep a low, violently break previous minor high, and leave an FVG?
            is_unicorn = has_swept_liquidity and fvg and (imp_h > max(c["h"] for c in c_1h[max(0, i-8):i]))

            if is_red and fvg and disp >= 0.045:
                ob_high = c3["h"]
                ob_low = c3["l"]
                ob_range = ob_high - ob_low
                mt_50 = (ob_high + ob_low) / 2.0
                boundary_5pct = ob_high - (0.05 * ob_range)

                # Virgin Tap Search
                peak_runway = imp_h
                tap_1h_idx = -1
                for k in range(i + 3, min(i + 300, n)):
                    bar = c_1h[k]
                    peak_runway = max(peak_runway, bar["h"])
                    if bar["c"] < ob_low: break
                    runway_pct = (peak_runway - ob_high) / ob_high if ob_high > 0 else 0.0
                    if runway_pct < 0.040: continue
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
                
                tap_c_15m = c_15m[tap_15m_idx]
                
                # 15m Absorption Wick Check:
                c_rng = tap_c_15m["h"] - tap_c_15m["l"]
                l_wick = min(tap_c_15m["o"], tap_c_15m["c"]) - tap_c_15m["l"]
                wick_ratio = (l_wick / c_rng) if c_rng > 0 else 0.0
                is_green = tap_c_15m["c"] >= tap_c_15m["o"]
                
                # --- EVALUATION 1: BASELINE HERMES 3.5 ---
                h35_eligible = (wick_ratio >= 0.15 or is_green) and (tap_c_15m["c"] >= mt_50)
                if h35_eligible:
                    entry_p = boundary_5pct
                    tp_p = entry_p * (1.0 + h35_tp)
                    sl_p = entry_p * (1.0 - h35_sl)
                    be_p = entry_p * (1.0 + h35_be)
                    
                    be_act = False
                    won = False
                    lost = False
                    
                    for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                        sc = c_15m[s]
                        if sc["h"] >= be_p: be_act = True
                        if sc["h"] >= tp_p: won = True; break
                        if be_act and sc["l"] <= entry_p * 1.001: break
                        if sc["l"] <= sl_p: lost = True; break
                        
                    res_h = results["HERMES_3.5_BASELINE"]
                    res_h["trades"] += 1
                    if won:
                        res_h["wins"] += 1
                        res_h["total_roe"] += h35_tp * 5.0
                        res_h["gross_profit"] += h35_tp * 5.0
                        res_h["total_r"] += (h35_tp / h35_sl)
                    elif lost:
                        res_h["losses"] += 1
                        res_h["total_roe"] -= h35_sl * 5.0
                        res_h["gross_loss"] += h35_sl * 5.0
                        res_h["total_r"] -= 1.0
                    else:
                        res_h["be_cuts"] += 1

                # --- EVALUATION 2: PROPRIETARY UNICORN ABSORPTION ENGINE ---
                # Criteria:
                # 1. Must be in Discount Zone (< 50% Equilibrium)
                # 2. Must have prior Liquidity Sweep or be a Unicorn Breaker Model
                # 3. 15m Absorption Wick must be strictly >= 18% OR (Wick >= 12% AND Green Close)
                # 4. Asymmetric Target: Target is Next Draw on Liquidity (Peak Runway High) -> 1:3 to 1:4 RR!
                # 5. Micro-SL: Tight under tap reaction low (0.3% buffer)
                
                prop_eligible = is_in_discount and (has_swept_liquidity or is_unicorn) and (wick_ratio >= 0.18 or (wick_ratio >= 0.12 and is_green))
                
                if prop_eligible:
                    entry_p = boundary_5pct
                    # Structural Micro-SL: Just under the tap reaction low + small buffer
                    micro_sl = min(ob_low, tap_c_15m["l"]) * 0.998
                    risk_dist = entry_p - micro_sl
                    
                    # Target is the Peak Runway (Draw on Liquidity / BSL) or 1:3.0 RR
                    target_dol = max(entry_p + (3.0 * risk_dist), peak_runway)
                    target_dol = min(target_dol, entry_p * 1.060) # Cap at +6% move (+30% ROE @ 5x)
                    
                    # Risk validation
                    if risk_dist <= 0 or (risk_dist / entry_p) > 0.030:
                        risk_dist = entry_p * 0.020 # Standard 2% risk
                        micro_sl = entry_p * 0.980
                        target_dol = entry_p * 1.060 # 1:3 RR
                        
                    reward_dist = target_dol - entry_p
                    trade_rr = reward_dist / risk_dist if risk_dist > 0 else 3.0
                    
                    be_1r_trigger = entry_p + (1.2 * risk_dist) # BE armor at +1.2R
                    be_act = False
                    won = False
                    lost = False
                    
                    for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                        sc = c_15m[s]
                        if sc["h"] >= be_1r_trigger: be_act = True
                        if sc["h"] >= target_dol: won = True; break
                        if be_act and sc["l"] <= entry_p * 1.0015: break
                        if sc["l"] <= micro_sl: lost = True; break
                        
                    res_p = results["PROPRIETARY_UNICORN_ABSORPTION"]
                    res_p["trades"] += 1
                    if is_unicorn: res_p["unicorn_models_hit"] += 1
                    else: res_p["extreme_ob_hit"] += 1
                    
                    if won:
                        res_p["wins"] += 1
                        r_gain = trade_rr
                        roe_gain = (reward_dist / entry_p) * 5.0
                        res_p["total_r"] += r_gain
                        res_p["total_roe"] += roe_gain
                        res_p["gross_profit"] += roe_gain
                    elif lost:
                        res_p["losses"] += 1
                        r_loss = 1.0
                        roe_loss = (risk_dist / entry_p) * 5.0
                        res_p["total_r"] -= r_loss
                        res_p["total_roe"] -= roe_loss
                        res_p["gross_loss"] += roe_loss
                    else:
                        res_p["be_cuts"] += 1

    # Final calculations
    for k in results:
        d = results[k]
        decided = d["wins"] + d["losses"]
        d["win_rate"] = round((d["wins"] / decided * 100.0), 2) if decided > 0 else 0.0
        d["profit_factor"] = round((d["gross_profit"] / d["gross_loss"]), 2) if d["gross_loss"] > 0 else 99.0
        d["total_roe"] = round(d["total_roe"] * 100.0, 2)
        d["total_r"] = round(d["total_r"], 2)

    print("\n========================= BATTLE ROYALE AUDIT SUMMARY =========================")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_battle()
