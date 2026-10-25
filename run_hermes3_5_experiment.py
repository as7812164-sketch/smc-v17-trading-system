import os
import sys
import json
import time
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

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
    
    running_cvd = 0.0
    vol_window = []
    
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        v = float(c.get("volume", 0.0))
        c["volume"] = v
        
        # Order Flow Metrics
        rng = c["high"] - c["low"]
        if rng > 0:
            d_ratio = (c["close"] - c["low"]) / rng
            delta = v * (2.0 * d_ratio - 1.0)
        else:
            d_ratio = 0.50
            delta = 0.0
            
        running_cvd += delta
        c["delta"] = delta
        c["delta_ratio"] = d_ratio
        c["cvd"] = running_cvd
        
        vol_window.append(v)
        if len(vol_window) > 20:
            vol_window.pop(0)
        c["vol_sma20"] = sum(vol_window) / len(vol_window)
        
    CANDLE_CACHE[key] = data
    return data

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_1h = load_candles("BTCUSDT", "1h")
    return {c["time"]: c for c in btc_4h}, {c["time"]: c for c in btc_1h}

def run_hermes_experiment():
    print("=" * 85)
    print("🔬 EXPERIMENT: HERMES 2.5 vs HERMES 3.0 vs HERMES 3.5 (CVD DELTA & OI)")
    print("=" * 85)
    print(f"Dataset: 2 Continuous Years across Top-22 Champions (historical_data_2year)")
    
    btc_map_4h, btc_map_1h = build_btc_map()
    
    raw_setups = []
    
    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        max_tap_window = 28
        max_hold = 30 if tf == "4h" else 40
        
        for sym in TOP_22_CHAMPIONS:
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
                # -------------------------------------------------------------
                # 1. LONG / BUY CANDIDATE SETUP
                # -------------------------------------------------------------
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
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
                                                # Sentry 5 (CVD Delta & OI) Check for Hermes 3.5
                                                cvd_3_ago = candles[t-3]["cvd"] if t >= 3 else candles[0]["cvd"]
                                                cvd_slope = tap_c["cvd"] - cvd_3_ago
                                                # Long pass: buyers absorbing at OB (Delta ratio >= 0.49 or delta > 0) + CVD curling up
                                                cvd_pass = (tap_c["delta_ratio"] >= 0.49 or tap_c["delta"] > 0) and (cvd_slope > 0)
                                                # OI volume check: volume >= 0.85x SMA20
                                                oi_pass = (tap_c["volume"] >= 0.85 * tap_c["vol_sma20"]) if tap_c["vol_sma20"] > 0 else True
                                                sentry5_pass = cvd_pass and oi_pass
                                                
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold,
                                                    "sentry5_pass": sentry5_pass
                                                })
                                                break
                
                # -------------------------------------------------------------
                # 2. SHORT / SELL CANDIDATE SETUP
                # -------------------------------------------------------------
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
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
                                                # Sentry 5 (CVD Delta & OI) Check for Hermes 3.5
                                                cvd_3_ago = candles[t-3]["cvd"] if t >= 3 else candles[0]["cvd"]
                                                cvd_slope = tap_c["cvd"] - cvd_3_ago
                                                # Short pass: sellers hitting bids (Delta ratio <= 0.51 or delta < 0) + CVD curling down
                                                cvd_pass = (tap_c["delta_ratio"] <= 0.51 or tap_c["delta"] < 0) and (cvd_slope < 0)
                                                oi_pass = (tap_c["volume"] >= 0.85 * tap_c["vol_sma20"]) if tap_c["vol_sma20"] > 0 else True
                                                sentry5_pass = cvd_pass and oi_pass
                                                
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold,
                                                    "sentry5_pass": sentry5_pass
                                                })
                                                break

    raw_setups.sort(key=lambda x: x["time"])
    print(f"Total candidate setups detected across 2 years: {len(raw_setups)}")
    
    models = ["HERMES_2.5_APEX_HYBRID", "HERMES_3.0_QUANTUM", "HERMES_3.5_ORDER_FLOW"]
    results = {}
    
    fee_rate = 0.0016  # 0.16% round-trip taker fees
    
    for model_name in models:
        slot_busy_until = {
            "4h_slot1": 0,
            "4h_slot2": 0,
            "1h_slot1": 0,
            "1h_slot2": 0
        }
        
        executed_trades = []
        balance = 50.0
        vault = 0.0
        peak = 50.0
        max_drawdown = 0.0
        milestone_500 = None
        milestone_1k = None
        milestone_2k = None
        
        for setup in raw_setups:
            # If Model is HERMES 3.5, enforce Sentry 5 (CVD Delta & OI)
            if model_name == "HERMES_3.5_ORDER_FLOW":
                if not setup["sentry5_pass"]:
                    continue  # Sentry 5 VETOED!
                    
            sym = setup["sym"]
            tf = setup["tf"]
            t = setup["t_idx"]
            candles = load_candles(sym, tf)
            n = len(candles)
            side = setup["side"]
            s_time = setup["time"]
            
            # Select available slot
            target_slot = None
            if tf == "4h":
                if s_time >= slot_busy_until["4h_slot1"]:
                    target_slot = "4h_slot1"
                elif s_time >= slot_busy_until["4h_slot2"]:
                    target_slot = "4h_slot2"
            else: # 1h
                if s_time >= slot_busy_until["1h_slot1"]:
                    target_slot = "1h_slot1"
                elif s_time >= slot_busy_until["1h_slot2"]:
                    target_slot = "1h_slot2"
            
            if not target_slot:
                continue
                
            # ENTRY & STOP LOSS LOGIC
            if model_name == "HERMES_2.5_APEX_HYBRID":
                if side == "LONG":
                    entry = setup["dec_top"]
                    tp_p = entry * (1.0 + setup["std_tp_pct"])
                    soft_sl_p = entry * (1.0 - setup["soft_sl_pct"])
                    hard_sl_p = entry * (1.0 - setup["hard_sl_pct"])
                else:
                    entry = setup["dec_bot"]
                    tp_p = entry * (1.0 - setup["std_tp_pct"])
                    soft_sl_p = entry * (1.0 + setup["soft_sl_pct"])
                    hard_sl_p = entry * (1.0 + setup["hard_sl_pct"])
            else: # HERMES 3.0 & HERMES 3.5 (50% Mean Threshold + Structural Armor)
                mt = setup["mt"]
                if side == "LONG":
                    entry = mt if setup["tap_low"] <= mt else (setup["dec_top"] + mt) / 2.0
                    tp_p = entry * (1.0 + setup["std_tp_pct"])
                    struct_sl = min(setup["dec_bot"], setup["tap_low"]) - 0.20 * setup["atr"]
                    hard_sl_p = min(struct_sl, entry * (1.0 - setup["hard_sl_pct"]))
                    hard_sl_p = max(hard_sl_p, entry * 0.962)
                    soft_sl_p = (entry + hard_sl_p) / 2.0
                else: # SHORT
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
            sl_reason = None
            
            for m in range(t, min(t + setup["max_hold"], n)):
                c_m = candles[m]
                m_time = c_m["time"]
                
                # In-trade BTC Emergency Shield for Hermes 3.0 & 3.5
                if model_name in ["HERMES_3.0_QUANTUM", "HERMES_3.5_ORDER_FLOW"]:
                    btc_ts = m_time - (m_time % (3600 * 1000))
                    btc_1h_c = btc_map_1h.get(btc_ts)
                    if btc_1h_c:
                        btc_chg = (btc_1h_c["close"] - btc_1h_c["open"]) / btc_1h_c["open"]
                        if side == "LONG" and btc_chg < -0.010:
                            if not be_locked:
                                curr_sl = max(curr_sl, entry * 0.995)
                        elif side == "SHORT" and btc_chg > 0.010:
                            if not be_locked:
                                curr_sl = min(curr_sl, entry * 1.005)
                
                if side == "LONG":
                    # Profit Armor
                    if model_name in ["HERMES_3.0_QUANTUM", "HERMES_3.5_ORDER_FLOW"]:
                        if c_m["high"] >= entry * 1.022:
                            curr_sl = max(curr_sl, entry * 1.012)
                            be_locked = True
                        elif c_m["high"] >= entry * 1.016:
                            curr_sl = max(curr_sl, entry * 1.002)
                            be_locked = True
                    elif c_m["high"] >= entry * 1.016:
                        curr_sl = max(curr_sl, entry * 1.002)
                        be_locked = True
                        
                    if c_m["high"] >= tp_p:
                        res = "WIN"
                        exit_price = tp_p
                        exit_time = m_time
                        break
                    if c_m["low"] <= hard_sl_p:
                        res = "LOSS"
                        exit_price = hard_sl_p
                        exit_time = m_time
                        sl_reason = "HARD_SL"
                        break
                    if c_m["close"] <= curr_sl:
                        res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                        exit_price = c_m["close"]
                        exit_time = m_time
                        sl_reason = "BE_EXIT" if be_locked and curr_sl > entry else "SOFT_SL"
                        break
                else: # SHORT
                    if model_name in ["HERMES_3.0_QUANTUM", "HERMES_3.5_ORDER_FLOW"]:
                        if c_m["low"] <= entry * 0.978:
                            curr_sl = min(curr_sl, entry * 0.988)
                            be_locked = True
                        elif c_m["low"] <= entry * 0.984:
                            curr_sl = min(curr_sl, entry * 0.998)
                            be_locked = True
                    elif c_m["low"] <= entry * 0.984:
                        curr_sl = min(curr_sl, entry * 0.998)
                        be_locked = True
                        
                    if c_m["low"] <= tp_p:
                        res = "WIN"
                        exit_price = tp_p
                        exit_time = m_time
                        break
                    if c_m["high"] >= hard_sl_p:
                        res = "LOSS"
                        exit_price = hard_sl_p
                        exit_time = m_time
                        sl_reason = "HARD_SL"
                        break
                    if c_m["close"] >= curr_sl:
                        res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                        exit_price = c_m["close"]
                        exit_time = m_time
                        sl_reason = "BE_EXIT" if be_locked and curr_sl < entry else "SOFT_SL"
                        break
            
            if not res:
                fc = candles[min(t + setup["max_hold"], n - 1)]["close"]
                if side == "LONG":
                    res = "WIN" if fc > entry else "LOSS"
                else:
                    res = "WIN" if fc < entry else "LOSS"
                exit_price = fc
                exit_time = candles[min(t + setup["max_hold"], n - 1)]["time"]
                sl_reason = "MAX_HOLD_TIMEOUT"
                
            slot_busy_until[target_slot] = exit_time
            
            if side == "LONG":
                gross_pct = (exit_price - entry) / entry
            else:
                gross_pct = (entry - exit_price) / entry
                
            net_pct = gross_pct - fee_rate
            pos_size = balance * 5.0
            pnl_usdt = pos_size * net_pct
            
            if res == "WIN":
                balance += (pnl_usdt * 0.85)
                vault += (pnl_usdt * 0.15)
            else:
                balance += pnl_usdt
                if balance < 5.0:
                    balance = 5.0  # Safe floor
                    
            tot_equity = balance + vault
            if tot_equity > peak:
                peak = tot_equity
            dd = (peak - tot_equity) / peak if peak > 0 else 0
            if dd > max_drawdown:
                max_drawdown = dd
                
            t_num = len(executed_trades) + 1
            if tot_equity >= 500.0 and milestone_500 is None:
                milestone_500 = t_num
            if tot_equity >= 1000.0 and milestone_1k is None:
                milestone_1k = t_num
            if tot_equity >= 2000.0 and milestone_2k is None:
                milestone_2k = t_num
                
            executed_trades.append({
                "num": t_num, "sym": sym, "tf": tf, "side": side,
                "res": res, "net_pct": net_pct, "pnl": pnl_usdt,
                "tot_equity": tot_equity, "sl_reason": sl_reason
            })
            
        wins = sum(1 for t in executed_trades if t["res"] == "WIN")
        losses = sum(1 for t in executed_trades if t["res"] == "LOSS")
        tot = len(executed_trades)
        win_rate = (wins / tot * 100.0) if tot > 0 else 0
        
        long_w = sum(1 for t in executed_trades if t["side"] == "LONG" and t["res"] == "WIN")
        long_tot = sum(1 for t in executed_trades if t["side"] == "LONG")
        long_wr = (long_w / long_tot * 100.0) if long_tot > 0 else 0
        
        short_w = sum(1 for t in executed_trades if t["side"] == "SHORT" and t["res"] == "WIN")
        short_tot = sum(1 for t in executed_trades if t["side"] == "SHORT")
        short_wr = (short_w / short_tot * 100.0) if short_tot > 0 else 0
        
        tf_4h_w = sum(1 for t in executed_trades if t["tf"] == "4h" and t["res"] == "WIN")
        tf_4h_tot = sum(1 for t in executed_trades if t["tf"] == "4h")
        tf_4h_wr = (tf_4h_w / tf_4h_tot * 100.0) if tf_4h_tot > 0 else 0
        
        tf_1h_w = sum(1 for t in executed_trades if t["tf"] == "1h" and t["res"] == "WIN")
        tf_1h_tot = sum(1 for t in executed_trades if t["tf"] == "1h")
        tf_1h_wr = (tf_1h_w / tf_1h_tot * 100.0) if tf_1h_tot > 0 else 0
        
        gp = sum(t["pnl"] for t in executed_trades if t["pnl"] > 0)
        gl = abs(sum(t["pnl"] for t in executed_trades if t["pnl"] < 0))
        pf = (gp / gl) if gl > 0 else 999.0
        
        results[model_name] = {
            "total_trades": tot,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "long_win_rate": round(long_wr, 2),
            "long_trades": long_tot,
            "short_win_rate": round(short_wr, 2),
            "short_trades": short_tot,
            "4h_win_rate": round(tf_4h_wr, 2),
            "4h_trades": tf_4h_tot,
            "1h_win_rate": round(tf_1h_wr, 2),
            "1h_trades": tf_1h_tot,
            "profit_factor": round(pf, 2),
            "max_drawdown": round(max_drawdown * 100.0, 2),
            "milestone_500": milestone_500,
            "milestone_1k": milestone_1k,
            "milestone_2k": milestone_2k,
            "final_compounded_equity": round(tot_equity, 2),
            "vault_stashed": round(vault, 2)
        }
        
    print("\n" + "=" * 85)
    print("🏆 FINAL HEAD-TO-HEAD BATTLE AUDIT RESULTS:")
    print("=" * 85)
    print(f"{'Metric':<30} | {'HERMES 2.5 (Apex)':<18} | {'HERMES 3.0 (Quantum)':<20} | {'HERMES 3.5 (CVD & OI)':<22}")
    print("-" * 100)
    for m in [
        ("Total Trades", "total_trades"),
        ("Wins / Losses", lambda r: f"{r['wins']}W / {r['losses']}L"),
        ("OVERALL WIN RATE", lambda r: f"{r['win_rate']}%"),
        ("Long Win Rate", lambda r: f"{r['long_win_rate']}%"),
        ("Short Win Rate", lambda r: f"{r['short_win_rate']}%"),
        ("4H Macro Accuracy", lambda r: f"{r['4h_win_rate']}%"),
        ("1H Scalp Accuracy", lambda r: f"{r['1h_win_rate']}%"),
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
        v25 = get_val(results["HERMES_2.5_APEX_HYBRID"])
        v30 = get_val(results["HERMES_3.0_QUANTUM"])
        v35 = get_val(results["HERMES_3.5_ORDER_FLOW"])
        print(f"{lbl:<30} | {v25:<18} | {v30:<20} | {v35:<22}")
        
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hermes3_5_experiment_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed JSON report saved to: {out_file}")
    return results

if __name__ == "__main__":
    run_hermes_experiment()
