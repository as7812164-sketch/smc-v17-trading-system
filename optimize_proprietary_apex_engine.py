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

def run_self_improvement_trials():
    coins_15m = [os.path.basename(f).replace("_15m.json", "") for f in glob.glob("market_data_cache_15m/*_15m.json")]
    coins_1h = [os.path.basename(f).replace("_1h.json", "") for f in glob.glob("historical_data/*_1h.json")]
    common_symbols = sorted(list(set(coins_15m).intersection(set(coins_1h))))
    
    print(f"================================================================================")
    print(f"🧠 SELF-IMPROVEMENT BATTLE TRIALS: ENGINEERING 80%+ PROPRIETARY CRYPTO ENGINE")
    print(f"Testing on {len(common_symbols)} institutional pairs")
    print(f"================================================================================")

    # Let's test 4 Iterations of the Proprietary Strategy:
    # Gen 1: Ultra-Strict Unicorn & Extreme (Tested: PF 4.05, 54.5% WR, 17 trades)
    # Gen 2: Calibrated Asymmetric Harvest (TP at +2.0R, BE at +1.0R, 20-bar Sweep Lookback)
    # Gen 3: Dual-Target Stepped Scalp (TP at +1.6R, BE at +0.8R, Dynamic ATR SL)
    # Gen 4: The Apex Hybrid (Extreme OB + Unicorn + 50% Discount + 15m Absorption Gate + +2.2% Sweetspot Harvest)

    trials = {
        "GEN_2_ASYMMETRIC_2R": {"tp_mult": 2.0, "be_trigger_mult": 1.0, "sweep_lookback": 20, "trades": 0, "wins": 0, "losses": 0, "be_cuts": 0, "pnl_roe": 0.0, "gross_win": 0.0, "gross_loss": 0.0},
        "GEN_3_CALIBRATED_1.6R": {"tp_mult": 1.6, "be_trigger_mult": 0.9, "sweep_lookback": 20, "trades": 0, "wins": 0, "losses": 0, "be_cuts": 0, "pnl_roe": 0.0, "gross_win": 0.0, "gross_loss": 0.0},
        "GEN_4_APEX_SWEETSPOT": {"fixed_tp_pct": 0.0240, "fixed_sl_pct": 0.0240, "be_pct": 0.0120, "sweep_lookback": 25, "trades": 0, "wins": 0, "losses": 0, "be_cuts": 0, "pnl_roe": 0.0, "gross_win": 0.0, "gross_loss": 0.0}
    }

    for sym in common_symbols:
        f_1h = f"historical_data/{sym}_1h.json"
        f_15m = f"market_data_cache_15m/{sym}_15m.json"
        with open(f_1h, "r") as fp: raw_1h = json.load(fp)
        with open(f_15m, "r") as fp: raw_15m = json.load(fp)
            
        c_1h = [{"t": c.get("time") or c.get("open_time"), "o": float(c["open"]), "h": float(c["high"]), "l": float(c["low"]), "c": float(c["close"])} for c in raw_1h]
        c_15m = [{"t": c.get("time") or c.get("open_time"), "o": float(c["open"]), "h": float(c["high"]), "l": float(c["low"]), "c": float(c["close"])} for c in raw_15m]
        t_15m_times = [c["t"] for c in c_15m]
        n = len(c_1h)

        for i in range(15, n - 40):
            c3 = c_1h[i]
            c2 = c_1h[i+1]
            c1 = c_1h[i+2]
            
            imp_h = max(c1["h"], c2["h"])
            is_red = c3["c"] < c3["o"]
            fvg = c1["l"] > c3["h"]
            disp = (imp_h - c3["l"]) / c3["l"] if c3["l"] > 0 else 0.0

            if not (is_red and fvg and disp >= 0.040):
                continue

            # 50% Equilibrium Discount Check (Lookback 40 bars)
            lookback_h = max(c["h"] for c in c_1h[max(0, i-40):i+1])
            lookback_l = min(c["l"] for c in c_1h[max(0, i-40):i+1])
            equilibrium_50 = (lookback_h + lookback_l) / 2.0
            if c3["l"] > equilibrium_50:
                continue # Disqualify Premium purchases!

            # Liquidity Sweep Lookback Check (20-25 bars)
            prior_lows = [c["l"] for c in c_1h[max(0, i-25):i]]
            min_prior_low = min(prior_lows) if prior_lows else c3["l"]
            has_swept_liquidity = (c3["l"] <= min_prior_low * 1.002)

            ob_high = c3["h"]
            ob_low = c3["l"]
            ob_range = ob_high - ob_low
            boundary_5pct = ob_high - (0.05 * ob_range)

            # Virgin tap search
            peak_runway = imp_h
            tap_1h_idx = -1
            for k in range(i + 3, min(i + 300, n)):
                bar = c_1h[k]
                peak_runway = max(peak_runway, bar["h"])
                if bar["c"] < ob_low: break
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

            # 15m Absorption Wick Gate
            c_rng = tap_c_15m["h"] - tap_c_15m["l"]
            l_wick = min(tap_c_15m["o"], tap_c_15m["c"]) - tap_c_15m["l"]
            wick_ratio = (l_wick / c_rng) if c_rng > 0 else 0.0
            is_green = tap_c_15m["c"] >= tap_c_15m["o"]

            # Must have absorption reaction
            if not (wick_ratio >= 0.15 or is_green):
                continue

            entry_p = boundary_5pct
            micro_sl = min(ob_low, tap_c_15m["l"]) * 0.998
            risk_dist = entry_p - micro_sl
            if risk_dist <= 0 or (risk_dist / entry_p) > 0.035:
                risk_dist = entry_p * 0.022
                micro_sl = entry_p * 0.978

            # --- RUN TRIALS ---
            # Trial 1: GEN_2 (2.0R Target)
            t2 = trials["GEN_2_ASYMMETRIC_2R"]
            tp_2 = entry_p + (t2["tp_mult"] * risk_dist)
            be_2 = entry_p + (t2["be_trigger_mult"] * risk_dist)
            be_act = False; won = False; lost = False
            for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                sc = c_15m[s]
                if sc["h"] >= be_2: be_act = True
                if sc["h"] >= tp_2: won = True; break
                if be_act and sc["l"] <= entry_p * 1.001: break
                if sc["l"] <= micro_sl: lost = True; break
            t2["trades"] += 1
            if won:
                t2["wins"] += 1
                gain = (t2["tp_mult"] * risk_dist / entry_p) * 5.0
                t2["pnl_roe"] += gain
                t2["gross_win"] += gain
            elif lost:
                t2["losses"] += 1
                loss = (risk_dist / entry_p) * 5.0
                t2["pnl_roe"] -= loss
                t2["gross_loss"] += loss
            else:
                t2["be_cuts"] += 1

            # Trial 2: GEN_3 (1.6R Target)
            t3 = trials["GEN_3_CALIBRATED_1.6R"]
            tp_3 = entry_p + (t3["tp_mult"] * risk_dist)
            be_3 = entry_p + (t3["be_trigger_mult"] * risk_dist)
            be_act = False; won = False; lost = False
            for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                sc = c_15m[s]
                if sc["h"] >= be_3: be_act = True
                if sc["h"] >= tp_3: won = True; break
                if be_act and sc["l"] <= entry_p * 1.001: break
                if sc["l"] <= micro_sl: lost = True; break
            t3["trades"] += 1
            if won:
                t3["wins"] += 1
                gain = (t3["tp_mult"] * risk_dist / entry_p) * 5.0
                t3["pnl_roe"] += gain
                t3["gross_win"] += gain
            elif lost:
                t3["losses"] += 1
                loss = (risk_dist / entry_p) * 5.0
                t3["pnl_roe"] -= loss
                t3["gross_loss"] += loss
            else:
                t3["be_cuts"] += 1

            # Trial 3: GEN_4 (APEX SWEETSPOT: Fixed +2.4% TP, Dynamic Micro-SL, +1.2% BE)
            t4 = trials["GEN_4_APEX_SWEETSPOT"]
            tp_4 = entry_p * (1.0 + t4["fixed_tp_pct"])
            sl_4 = min(micro_sl, entry_p * (1.0 - t4["fixed_sl_pct"]))
            be_4 = entry_p * (1.0 + t4["be_pct"])
            be_act = False; won = False; lost = False
            for s in range(tap_15m_idx + 1, min(tap_15m_idx + 400, len(c_15m))):
                sc = c_15m[s]
                if sc["h"] >= be_4: be_act = True
                if sc["h"] >= tp_4: won = True; break
                if be_act and sc["l"] <= entry_p * 1.001: break
                if sc["l"] <= sl_4: lost = True; break
            t4["trades"] += 1
            if won:
                t4["wins"] += 1
                gain = t4["fixed_tp_pct"] * 5.0
                t4["pnl_roe"] += gain
                t4["gross_win"] += gain
            elif lost:
                t4["losses"] += 1
                loss = (entry_p - sl_4) / entry_p * 5.0
                t4["pnl_roe"] -= loss
                t4["gross_loss"] += loss
            else:
                t4["be_cuts"] += 1

    # Output metrics
    for k in trials:
        t = trials[k]
        decided = t["wins"] + t["losses"]
        t["win_rate"] = round((t["wins"] / decided * 100.0), 2) if decided > 0 else 0.0
        t["profit_factor"] = round((t["gross_win"] / t["gross_loss"]), 2) if t["gross_loss"] > 0 else 99.0
        t["pnl_roe"] = round(t["pnl_roe"] * 100.0, 2)

    print("\n========================= SELF-IMPROVEMENT BATTLE RESULTS =========================")
    print(json.dumps(trials, indent=2))

if __name__ == "__main__":
    run_self_improvement_trials()
