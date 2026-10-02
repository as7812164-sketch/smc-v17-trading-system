import os
import sys
import json
import time
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from engine.hermes3_5_apex import TOP_45_CHAMPIONS, hermes35_engine

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")

CANDLE_CACHE = {}

def load_candles(sym, interval):
    key = f"{sym}_{interval}"
    if key in CANDLE_CACHE:
        return CANDLE_CACHE[key]
    fpath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        c["volume"] = float(c.get("volume", 0.0))
    CANDLE_CACHE[key] = data
    return data

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_1h = load_candles("BTCUSDT", "1h")
    return {c["time"]: c for c in btc_4h}, {c["time"]: c for c in btc_1h}

def run_dualtier_experiment():
    print("=" * 95)
    print("🚀 QUANT BENCHMARK: HERMES 3.0 vs HERMES 3.5 STRICT vs HERMES 3.5 DUAL-TIER & 15M SNIPER")
    print("=" * 95)
    
    btc_map_4h, btc_map_1h = build_btc_map()
    
    # Harvest all candidate setups across available 2-year dataset
    available_symbols = [s for s in TOP_45_CHAMPIONS if os.path.exists(os.path.join(DATA_DIR_2Y, f"{s}_1h.json"))]
    print(f"Auditing across {len(available_symbols)} Champions with complete 2-Year Continuous Data...")
    
    raw_setups = []
    
    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        max_tap_window = 28
        max_hold = 30 if tf == "4h" else 40
        
        for sym in available_symbols:
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < 40:
                continue
                
            atr = [0.0] * n
            for k in range(1, n):
                tr = max(candles[k]["high"] - candles[k]["low"],
                         abs(candles[k]["high"] - candles[k-1]["close"]),
                         abs(candles[k]["low"] - candles[k-1]["close"]))
                atr[k] = tr if k < 14 else (atr[k-1] * 13 + tr) / 14
                
            for i in range(20, n - 2):
                # LONG SETUP
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1; max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        if candles[t]["low"] <= dec_top * 1.0005:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean = btc_dump < 0.020
                                            
                                            if btc_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                # Classify Tier and 15m Sniper Gate
                                                tier_info = hermes35_engine.classify_dual_tier_setup(candles, t, "LONG")
                                                sniper_pass, sniper_reason = hermes35_engine.evaluate_15m_micro_sniper_gate(tap_c, "LONG")
                                                
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold,
                                                    "tier_info": tier_info,
                                                    "sniper_pass": sniper_pass,
                                                    "is_tier_1": tier_info["tier"] == "TIER_1_INSTITUTIONAL"
                                                })
                                                break
                
                # SHORT SETUP
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1; max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        if candles[t]["high"] >= dec_bot * 0.9995:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean_short = btc_pump < 0.020
                                            
                                            if btc_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                tier_info = hermes35_engine.classify_dual_tier_setup(candles, t, "SHORT")
                                                sniper_pass, sniper_reason = hermes35_engine.evaluate_15m_micro_sniper_gate(tap_c, "SHORT")
                                                
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold,
                                                    "tier_info": tier_info,
                                                    "sniper_pass": sniper_pass,
                                                    "is_tier_1": tier_info["tier"] == "TIER_1_INSTITUTIONAL"
                                                })
                                                break

    raw_setups.sort(key=lambda x: x["time"])
    print(f"Total raw setups detected: {len(raw_setups)}")
    
    models = [
        "HERMES_3.0_QUANTUM",
        "HERMES_3.5_STRICT_VETO",
        "HERMES_3.5_DUAL_TIER_SNIPER"
    ]
    results = {}
    fee_rate = 0.0016
    
    for model_name in models:
        slot_busy_until = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
        executed = []
        balance = 50.0
        vault = 0.0
        peak = 50.0
        max_dd = 0.0
        milestone_500 = None
        milestone_1k = None
        milestone_2k = None
        
        for setup in raw_setups:
            if model_name == "HERMES_3.5_STRICT_VETO":
                if not setup["is_tier_1"]:
                    continue # Strict veto kills all Tier 2
            elif model_name == "HERMES_3.5_DUAL_TIER_SNIPER":
                # Sniper Gate: must pass 15m micro-structure reaction!
                if not setup["sniper_pass"]:
                    continue # Rejects runaway knife or rocket!
                    
            sym = setup["sym"]
            tf = setup["tf"]
            t = setup["t_idx"]
            candles = load_candles(sym, tf)
            n = len(candles)
            side = setup["side"]
            s_time = setup["time"]
            
            target_slot = None
            if tf == "4h":
                if s_time >= slot_busy_until["4h_1"]: target_slot = "4h_1"
                elif s_time >= slot_busy_until["4h_2"]: target_slot = "4h_2"
            else:
                if s_time >= slot_busy_until["1h_1"]: target_slot = "1h_1"
                elif s_time >= slot_busy_until["1h_2"]: target_slot = "1h_2"
                
            if not target_slot:
                continue
                
            mt = setup["mt"]
            tier_data = setup["tier_info"]
            
            # Position size & Armor configuration
            if model_name == "HERMES_3.5_DUAL_TIER_SNIPER":
                margin_mult = tier_data["margin_mult"]
                be_thresh = tier_data["be_lock_pct"]
                trail_thresh = tier_data["trail_lock_pct"]
            else:
                margin_mult = 1.0
                be_thresh = 0.016
                trail_thresh = 0.022
                
            if side == "LONG":
                entry = mt if setup["tap_low"] <= mt else (setup["dec_top"] + mt) / 2.0
                tp_p = entry * (1.0 + setup["std_tp_pct"])
                struct_sl = min(setup["dec_bot"], setup["tap_low"]) - 0.20 * setup["atr"]
                hard_sl_p = min(struct_sl, entry * (1.0 - setup["hard_sl_pct"]))
                hard_sl_p = max(hard_sl_p, entry * 0.962)
                soft_sl_p = (entry + hard_sl_p) / 2.0
            else:
                entry = mt if setup["tap_high"] >= mt else (setup["dec_bot"] + mt) / 2.0
                tp_p = entry * (1.0 - setup["std_tp_pct"])
                struct_sl = max(setup["dec_top"], setup["tap_high"]) + 0.20 * setup["atr"]
                hard_sl_p = max(struct_sl, entry * (1.0 + setup["hard_sl_pct"]))
                hard_sl_p = min(hard_sl_p, entry * 1.038)
                soft_sl_p = (entry + hard_sl_p) / 2.0
                
            res = None
            exit_price = entry
            exit_time = s_time
            curr_sl = soft_sl_p
            be_locked = False
            
            for m in range(t, min(t + setup["max_hold"], n)):
                c_m = candles[m]
                m_time = c_m["time"]
                
                # Active BTC Shield
                btc_ts = m_time - (m_time % (3600 * 1000))
                btc_1h_c = btc_map_1h.get(btc_ts)
                if btc_1h_c:
                    btc_chg = (btc_1h_c["close"] - btc_1h_c["open"]) / btc_1h_c["open"]
                    if side == "LONG" and btc_chg < -0.010 and not be_locked:
                        curr_sl = max(curr_sl, entry * 0.995)
                    elif side == "SHORT" and btc_chg > 0.010 and not be_locked:
                        curr_sl = min(curr_sl, entry * 1.005)
                        
                if side == "LONG":
                    if c_m["high"] >= entry * (1.0 + trail_thresh):
                        curr_sl = max(curr_sl, entry * 1.012)
                        be_locked = True
                    elif c_m["high"] >= entry * (1.0 + be_thresh):
                        curr_sl = max(curr_sl, entry * 1.002)
                        be_locked = True
                        
                    if c_m["high"] >= tp_p:
                        res = "WIN"; exit_price = tp_p; exit_time = m_time; break
                    if c_m["low"] <= hard_sl_p:
                        res = "LOSS"; exit_price = hard_sl_p; exit_time = m_time; break
                    if c_m["close"] <= curr_sl:
                        res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                        exit_price = c_m["close"]; exit_time = m_time; break
                else: # SHORT
                    if c_m["low"] <= entry * (1.0 - trail_thresh):
                        curr_sl = min(curr_sl, entry * 0.988)
                        be_locked = True
                    elif c_m["low"] <= entry * (1.0 - be_thresh):
                        curr_sl = min(curr_sl, entry * 0.998)
                        be_locked = True
                        
                    if c_m["low"] <= tp_p:
                        res = "WIN"; exit_price = tp_p; exit_time = m_time; break
                    if c_m["high"] >= hard_sl_p:
                        res = "LOSS"; exit_price = hard_sl_p; exit_time = m_time; break
                    if c_m["close"] >= curr_sl:
                        res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                        exit_price = c_m["close"]; exit_time = m_time; break
                        
            if not res:
                fc = candles[min(t + setup["max_hold"], n - 1)]["close"]
                res = "WIN" if (fc > entry if side == "LONG" else fc < entry) else "LOSS"
                exit_price = fc
                exit_time = candles[min(t + setup["max_hold"], n - 1)]["time"]
                
            slot_busy_until[target_slot] = exit_time
            
            gross_pct = ((exit_price - entry) / entry) if side == "LONG" else ((entry - exit_price) / entry)
            net_pct = gross_pct - fee_rate
            
            # Position margin sized dynamically
            pos_margin = balance * margin_mult
            pos_size = pos_margin * 5.0
            pnl_usdt = pos_size * net_pct
            
            if res == "WIN":
                balance += (pnl_usdt * 0.85)
                vault += (pnl_usdt * 0.15)
            else:
                balance += pnl_usdt
                if balance < 5.0: balance = 5.0
                
            tot_eq = balance + vault
            if tot_eq > peak: peak = tot_eq
            dd = (peak - tot_eq) / peak if peak > 0 else 0
            if dd > max_dd: max_dd = dd
            
            t_num = len(executed) + 1
            if tot_eq >= 500.0 and milestone_500 is None: milestone_500 = t_num
            if tot_eq >= 1000.0 and milestone_1k is None: milestone_1k = t_num
            if tot_eq >= 2000.0 and milestone_2k is None: milestone_2k = t_num
            
            executed.append({
                "num": t_num, "sym": sym, "tf": tf, "side": side,
                "res": res, "tier": tier_data["tier"], "pnl": pnl_usdt, "tot_eq": tot_eq
            })
            
        wins = sum(1 for e in executed if e["res"] == "WIN")
        losses = sum(1 for e in executed if e["res"] == "LOSS")
        tot = len(executed)
        wr = (wins / tot * 100.0) if tot > 0 else 0
        gp = sum(e["pnl"] for e in executed if e["pnl"] > 0)
        gl = abs(sum(e["pnl"] for e in executed if e["pnl"] < 0))
        pf = (gp / gl) if gl > 0 else 999.0
        
        results[model_name] = {
            "total_trades": tot,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wr, 2),
            "profit_factor": round(pf, 2),
            "max_drawdown": round(max_dd * 100.0, 2),
            "milestone_500": milestone_500,
            "milestone_1k": milestone_1k,
            "milestone_2k": milestone_2k,
            "final_equity": round(tot_eq, 2)
        }
        
    print("\n" + "=" * 95)
    print("🏆 FINAL COMPARISON RESULTS (2 FULL CONTINUOUS YEARS):")
    print("=" * 95)
    print(f"{'Metric':<30} | {'HERMES 3.0 (Quantum)':<20} | {'HERMES 3.5 (Strict Veto)':<22} | {'HERMES 3.5 (Dual-Tier Sniper)':<28}")
    print("-" * 105)
    for m in [
        ("Total Trades Executed", "total_trades"),
        ("Wins / Losses", lambda r: f"{r['wins']}W / {r['losses']}L"),
        ("OVERALL WIN RATE", lambda r: f"{r['win_rate']}%"),
        ("Profit Factor", "profit_factor"),
        ("Max Drawdown", lambda r: f"{r['max_drawdown']}%"),
        ("Hit $500 Milestone", "milestone_500"),
        ("Hit $1,000 Milestone", "milestone_1k"),
        ("Hit $2,000 Target", "milestone_2k"),
    ]:
        lbl, key = m
        def get_val(r):
            if callable(key): return str(key(r))
            return str(r[key])
        v30 = get_val(results["HERMES_3.0_QUANTUM"])
        v35s = get_val(results["HERMES_3.5_STRICT_VETO"])
        v35dt = get_val(results["HERMES_3.5_DUAL_TIER_SNIPER"])
        print(f"{lbl:<30} | {v30:<20} | {v35s:<22} | {v35dt:<28}")

    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hermes3_5_dualtier_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved dual-tier results to: {out_file}")

if __name__ == "__main__":
    run_dualtier_experiment()
