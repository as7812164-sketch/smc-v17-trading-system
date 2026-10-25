"""
HERMES 3.5 SINGLE TIER: EXPERIMENTAL TIMEFRAME EXPLORATION
==========================================================
Tests Hermes 3.5 Single Tier across non-standard and custom timeframes:
- 3H (3 Hours / 180 Minutes)
- 1.5H (1.5 Hours / 90 Minutes)
- 45min (45 Minutes)
Compared against baseline:
- 4H (Standard Macro Champion)
- 1H (Standard Intraday Champion)

Runs across 2 datasets:
Dataset 1: Continuous 6-Month High-Resolution 15m Dataset (20 Champions, 18,000 candles/coin)
Dataset 2: 2-Year Continuous Dataset (22 Champions, 17,520 candles/coin) for 3H vs 4H vs 1H
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def calculate_ema(values: List[float], period: int = 50) -> List[float]:
    if not values: return []
    ema = [values[0]] * len(values)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(values)):
        ema[i] = values[i] * k + ema[i-1] * (1.0 - k)
    return ema

def resample_candles(candles: List[Dict[str, Any]], target_minutes: int) -> List[Dict[str, Any]]:
    if not candles: return []
    interval_ms = target_minutes * 60 * 1000
    resampled = []
    current_bucket = None
    b_open = b_high = b_low = b_close = b_vol = b_start_time = None
    
    for c in candles:
        t = c["time"]
        bucket_key = t - (t % interval_ms)
        if current_bucket is None:
            current_bucket = bucket_key
            b_open = float(c["open"])
            b_high = float(c["high"])
            b_low = float(c["low"])
            b_close = float(c["close"])
            b_vol = float(c.get("volume", 0.0))
            b_start_time = bucket_key
        elif bucket_key == current_bucket:
            b_high = max(b_high, float(c["high"]))
            b_low = min(b_low, float(c["low"]))
            b_close = float(c["close"])
            b_vol += float(c.get("volume", 0.0))
        else:
            resampled.append({
                "time": b_start_time,
                "open": b_open,
                "high": b_high,
                "low": b_low,
                "close": b_close,
                "volume": b_vol
            })
            current_bucket = bucket_key
            b_open = float(c["open"])
            b_high = float(c["high"])
            b_low = float(c["low"])
            b_close = float(c["close"])
            b_vol = float(c.get("volume", 0.0))
            b_start_time = bucket_key
            
    if current_bucket is not None:
        resampled.append({
            "time": b_start_time,
            "open": b_open,
            "high": b_high,
            "low": b_low,
            "close": b_close,
            "volume": b_vol
        })
    return resampled

def harvest_hermes35_setups(
    candles: List[Dict[str, Any]],
    sym: str,
    tf_label: str,
    tf_minutes: int,
    btc_4h_ema50_map: Dict[int, bool],
    btc_map_4h: Dict[int, Any],
    disp_threshold: float = 0.050,
    tp_pct: float = 0.028,
    soft_sl_pct: float = 0.028,
    hard_sl_pct: float = 0.038
) -> List[Dict[str, Any]]:
    n = len(candles)
    if n < 40: return []
    
    atr = [0.0] * n
    for k in range(1, n):
        tr = max(
            candles[k]["high"] - candles[k]["low"],
            abs(candles[k]["high"] - candles[k-1]["close"]),
            abs(candles[k]["low"] - candles[k-1]["close"])
        )
        atr[k] = tr if k < 14 else (atr[k-1] * 13 + tr) / 14.0

    max_tap_window = 28
    hours_per_bar = tf_minutes / 60.0
    max_hold_bars = max(20, min(60, int(100.0 / hours_per_bar)))
    
    setups = []
    
    for i in range(20, n - 2):
        # 1. LONG / DEMAND ORDER BLOCK
        if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
            sub_w = candles[i:min(i+16, n)]
            highs = [c["high"] for c in sub_w]
            max_high = max(highs)
            high_idx = i + highs.index(max_high)
            if high_idx > i + 2:
                gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                if gain >= disp_threshold:
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
                                    
                                    btc_is_bull = btc_4h_ema50_map.get(prev_4h_ts, True)
                                    
                                    if btc_clean and btc_is_bull and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                        setups.append({
                                            "sym": sym,
                                            "tf": tf_label,
                                            "tf_minutes": tf_minutes,
                                            "t_idx": t,
                                            "side": "LONG",
                                            "time": tap_c["time"],
                                            "dec_top": dec_top,
                                            "dec_bot": dec_bot,
                                            "mt": mt,
                                            "tap_low": tap_c["low"],
                                            "tap_high": tap_c["high"],
                                            "atr": atr[t],
                                            "std_tp_pct": tp_pct,
                                            "soft_sl_pct": soft_sl_pct,
                                            "hard_sl_pct": hard_sl_pct,
                                            "max_hold": max_hold_bars
                                        })
                                        break

        # 2. SHORT / SUPPLY ORDER BLOCK
        if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
            sub_w = candles[i:min(i+16, n)]
            lows = [c["low"] for c in sub_w]
            min_low = min(lows)
            low_idx = i + lows.index(min_low)
            if low_idx > i + 2:
                drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                if drop >= disp_threshold:
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
                                    
                                    btc_is_bull = btc_4h_ema50_map.get(prev_4h_ts, True)
                                    short_allowed = (not btc_is_bull) or (sym == "BTCUSDT")
                                    
                                    if btc_clean_short and short_allowed and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                        setups.append({
                                            "sym": sym,
                                            "tf": tf_label,
                                            "tf_minutes": tf_minutes,
                                            "t_idx": t,
                                            "side": "SHORT",
                                            "time": tap_c["time"],
                                            "dec_top": dec_top,
                                            "dec_bot": dec_bot,
                                            "mt": mt,
                                            "tap_low": tap_c["low"],
                                            "tap_high": tap_c["high"],
                                            "atr": atr[t],
                                            "std_tp_pct": tp_pct,
                                            "soft_sl_pct": soft_sl_pct,
                                            "hard_sl_pct": hard_sl_pct,
                                            "max_hold": max_hold_bars
                                        })
                                        break
    return setups

def evaluate_setup_outcome(
    s: Dict[str, Any],
    candles: List[Dict[str, Any]],
    btc_map_1h: Dict[int, Any]
) -> Dict[str, Any]:
    n = len(candles)
    t = s["t_idx"]
    side = s["side"]
    s_time = s["time"]
    mt = s["mt"]
    
    if side == "LONG":
        entry = mt if s["tap_low"] <= mt else (s["dec_top"] + mt) / 2.0
        tp_p = entry * (1.0 + s["std_tp_pct"])
        struct_sl = min(s["dec_bot"], s["tap_low"]) - 0.20 * s["atr"]
        hard_sl_p = max(min(struct_sl, entry * (1.0 - s["hard_sl_pct"])), entry * 0.962)
        soft_sl_p = (entry + hard_sl_p) / 2.0
    else:
        entry = mt if s["tap_high"] >= mt else (s["dec_bot"] + mt) / 2.0
        tp_p = entry * (1.0 - s["std_tp_pct"])
        struct_sl = max(s["dec_top"], s["tap_high"]) + 0.20 * s["atr"]
        hard_sl_p = min(max(struct_sl, entry * (1.0 + s["hard_sl_pct"])), entry * 1.038)
        soft_sl_p = (entry + hard_sl_p) / 2.0
        
    res = None
    exit_price = entry
    exit_time = s_time
    curr_sl = soft_sl_p
    be_locked = False
    
    be_thresh = entry * 1.016 if side == "LONG" else entry * 0.984
    trail_thresh = entry * 1.022 if side == "LONG" else entry * 0.978
    
    for m in range(t, min(t + s["max_hold"], n)):
        c_m = candles[m]
        m_time = c_m["time"]
        
        # 1H BTC Emergency Shield
        btc_ts = m_time - (m_time % (3600 * 1000))
        btc_1h_c = btc_map_1h.get(btc_ts)
        if btc_1h_c:
            btc_chg = (btc_1h_c["close"] - btc_1h_c["open"]) / btc_1h_c["open"]
            if side == "LONG" and btc_chg < -0.010 and not be_locked:
                curr_sl = max(curr_sl, entry * 0.995)
            elif side == "SHORT" and btc_chg > 0.010 and not be_locked:
                curr_sl = min(curr_sl, entry * 1.005)
                
        if side == "LONG":
            if c_m["high"] >= trail_thresh:
                curr_sl = max(curr_sl, entry * 1.012)
                be_locked = True
            elif c_m["high"] >= be_thresh:
                curr_sl = max(curr_sl, entry * 1.002)
                be_locked = True
                
            if c_m["high"] >= tp_p:
                res = "WIN"; exit_price = tp_p; exit_time = m_time; break
            if c_m["low"] <= hard_sl_p:
                res = "LOSS"; exit_price = hard_sl_p; exit_time = m_time; break
            if c_m["close"] <= curr_sl:
                res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                exit_price = c_m["close"]; exit_time = m_time; break
        else:
            if c_m["low"] <= trail_thresh:
                curr_sl = min(curr_sl, entry * 0.988)
                be_locked = True
            elif c_m["low"] <= be_thresh:
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
        fc = candles[min(t + s["max_hold"], n - 1)]["close"]
        exit_price = fc
        exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]
        res = "WIN" if ((side == "LONG" and fc > entry) or (side == "SHORT" and fc < entry)) else "LOSS"
        
    pnl_pct = (exit_price - entry) / entry if side == "LONG" else (entry - exit_price) / entry
    raw_ret = pnl_pct * 5.0
    fee = 0.0016 * 5.0
    net_ret = raw_ret - fee
    dur_h = (exit_time - s_time) / (3600.0 * 1000.0)
    
    return {
        "sym": s["sym"],
        "side": side,
        "entry_time": s_time,
        "exit_time": exit_time,
        "res": res,
        "entry": entry,
        "exit": exit_price,
        "pnl_pct": pnl_pct,
        "net_ret": net_ret,
        "dur_h": dur_h
    }

def evaluate_raw_signals(
    setups: List[Dict[str, Any]],
    candles_dict: Dict[str, List[Dict[str, Any]]],
    btc_map_1h: Dict[int, Any]
) -> Dict[str, Any]:
    outcomes = []
    for s in setups:
        candles = candles_dict.get(s["sym"], [])
        if candles:
            outcomes.append(evaluate_setup_outcome(s, candles, btc_map_1h))
            
    tot = len(outcomes)
    wins = sum(1 for o in outcomes if o["res"] == "WIN")
    losses = sum(1 for o in outcomes if o["res"] == "LOSS")
    wr = (wins / tot * 100.0) if tot > 0 else 0.0
    
    pos_ret = sum(o["net_ret"] for o in outcomes if o["net_ret"] > 0)
    neg_ret = abs(sum(o["net_ret"] for o in outcomes if o["net_ret"] < 0))
    pf = (pos_ret / neg_ret) if neg_ret > 0 else 999.0
    avg_dur = sum(o["dur_h"] for o in outcomes) / tot if tot > 0 else 0.0
    avg_net_ret = (sum(o["net_ret"] for o in outcomes) / tot * 100.0) if tot > 0 else 0.0
    
    return {
        "total_signals": tot,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "profit_factor": round(pf, 2),
        "avg_duration_h": round(avg_dur, 1),
        "avg_net_return_pct": round(avg_net_ret, 2)
    }

def simulate_compounding(
    setups: List[Dict[str, Any]],
    candles_dict: Dict[str, List[Dict[str, Any]]],
    btc_map_1h: Dict[int, Any],
    max_slots: int = 5,
    initial_balance: float = 50.0
) -> Dict[str, Any]:
    setups_sorted = sorted(setups, key=lambda x: x["time"])
    slots_busy_until = [0] * max_slots
    executed = []
    
    bal = initial_balance
    vault = 0.0
    max_equity = initial_balance
    max_dd = 0.0
    m1k_trade = None
    m2k_trade = None
    
    for s in setups_sorted:
        s_time = s["time"]
        candles = candles_dict.get(s["sym"], [])
        if not candles: continue
        
        free_slot = -1
        for idx in range(max_slots):
            if s_time >= slots_busy_until[idx]:
                free_slot = idx
                break
        if free_slot == -1:
            continue
            
        out = evaluate_setup_outcome(s, candles, btc_map_1h)
        slots_busy_until[free_slot] = out["exit_time"]
        
        # Isolated 5x compounding math
        pos_size = bal * 5.0
        trade_pnl = (pos_size * out["pnl_pct"]) - (pos_size * 0.0016)
        
        if trade_pnl > 0:
            bal += trade_pnl * 0.85
            vault += trade_pnl * 0.15
        else:
            bal += trade_pnl
            if bal < 10.0: bal = 10.0
            
        total_eq = bal + vault
        if total_eq > max_equity:
            max_equity = total_eq
        dd = ((max_equity - total_eq) / max_equity * 100.0) if max_equity > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
            
        if not m1k_trade and total_eq >= 1000.0:
            m1k_trade = len(executed) + 1
        if not m2k_trade and total_eq >= 2000.0:
            m2k_trade = len(executed) + 1
            
        executed.append({
            "sym": out["sym"],
            "side": out["side"],
            "res": out["res"],
            "pnl_usdt": round(trade_pnl, 2),
            "bal": round(bal, 2),
            "vault": round(vault, 2),
            "total_eq": round(total_eq, 2),
            "dur_h": round(out["dur_h"], 1)
        })
        
    tot = len(executed)
    wins = sum(1 for e in executed if e["res"] == "WIN")
    losses = sum(1 for e in executed if e["res"] == "LOSS")
    wr = (wins / tot * 100.0) if tot > 0 else 0.0
    
    gross_win = sum(e["pnl_usdt"] for e in executed if e["pnl_usdt"] > 0)
    gross_loss = abs(sum(e["pnl_usdt"] for e in executed if e["pnl_usdt"] < 0))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
    avg_dur = sum(e["dur_h"] for e in executed) / tot if tot > 0 else 0.0
    
    return {
        "executed_trades": tot,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "profit_factor": round(pf, 2),
        "final_bal": round(bal, 2),
        "final_vault": round(vault, 2),
        "total_equity": round(bal + vault, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "avg_duration_h": round(avg_dur, 1),
        "m1k_trade": m1k_trade,
        "m2k_trade": m2k_trade
    }

def run_all_experiments():
    start_time = time.time()
    results = {
        "experiment_meta": {
            "strategy": "HERMES 3.5 SINGLE TIER",
            "tested_timeframes": ["45m", "1.5H (90m)", "3H (180m)", "1H (60m)", "4H (240m)"],
            "timestamp": datetime.utcnow().isoformat()
        },
        "dataset_6month_15m": {},
        "dataset_2year_longterm": {}
    }
    
    print("\n" + "=" * 90)
    print("🚀 HERMES 3.5 MULTI-TIMEFRAME QUANT LABORATORY EXPERIMENT")
    print("Testing Custom Timeframes: 3H (180m), 1.5H (90m), 45m vs Standard 4H & 1H")
    print("=" * 90)
    
    # -------------------------------------------------------------
    # EXPERIMENT 1: 6-Month High-Resolution 15m Dataset (20 Champions)
    # -------------------------------------------------------------
    dir_15m = "market_data_cache_15m"
    if not os.path.exists(dir_15m):
        print(f"❌ Error: {dir_15m} not found!")
        return
        
    files_15m = [f for f in os.listdir(dir_15m) if f.endswith("_15m.json")]
    print(f"📊 Loading 15m data for {len(files_15m)} coins from {dir_15m}...")
    
    raw_15m_data = {}
    for f in files_15m:
        sym = f.replace("_15m.json", "")
        with open(os.path.join(dir_15m, f), "r", encoding="utf-8") as fp:
            raw_15m_data[sym] = json.load(fp)
            
    # BTC Maps derived from BTC 15m
    btc_15m = raw_15m_data.get("BTCUSDT", [])
    btc_4h = resample_candles(btc_15m, 240)
    btc_1h = resample_candles(btc_15m, 60)
    
    btc_map_4h = {c["time"]: c for c in btc_4h}
    btc_map_1h = {c["time"]: c for c in btc_1h}
    
    btc_closes_4h = [c["close"] for c in btc_4h]
    btc_ema50_4h = calculate_ema(btc_closes_4h, 50)
    btc_4h_ema50_map = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_ema50_4h[i]) for i in range(len(btc_4h))}
    
    print(f"✅ Precomputed BTC 4H ({len(btc_4h)} bars) & BTC 1H ({len(btc_1h)} bars) causal maps.")
    
    # Definitions of Timeframes to test
    timeframes_to_test = [
        {"label": "45m", "minutes": 45, "tp": 0.022, "soft_sl": 0.024, "hard_sl": 0.034, "calib_disp": 0.038},
        {"label": "1.5H (90m)", "minutes": 90, "tp": 0.025, "soft_sl": 0.026, "hard_sl": 0.036, "calib_disp": 0.044},
        {"label": "3H (180m)", "minutes": 180, "tp": 0.028, "soft_sl": 0.028, "hard_sl": 0.038, "calib_disp": 0.048},
        {"label": "1H (60m)", "minutes": 60, "tp": 0.022, "soft_sl": 0.025, "hard_sl": 0.036, "calib_disp": 0.050},
        {"label": "4H (240m)", "minutes": 240, "tp": 0.028, "soft_sl": 0.028, "hard_sl": 0.038, "calib_disp": 0.050}
    ]
    
    print("\n" + "-" * 90)
    print("TEST SUITE 1: 6-Month Dataset (March 2026 - September 2026 | 20 Coins)")
    print("EVALUATING BOTH STRICT 5.0% DISPLACEMENT AND CALIBRATED DISPLACEMENT")
    print("-" * 90)
    
    suite1_results = {}
    
    for tf_cfg in timeframes_to_test:
        lbl = tf_cfg["label"]
        mins = tf_cfg["minutes"]
        print(f"\n🔄 Resampling 20 coins to {lbl} ({mins} mins)...", end="", flush=True)
        
        candles_resampled = {}
        for sym, c_list in raw_15m_data.items():
            candles_resampled[sym] = resample_candles(c_list, mins)
        print(" Done.")
        
        # Test 1A: Strict 5.0% Displacement across all TFs
        setups_strict = []
        for sym, c_list in candles_resampled.items():
            s = harvest_hermes35_setups(
                c_list, sym, lbl, mins,
                btc_4h_ema50_map, btc_map_4h,
                disp_threshold=0.050,
                tp_pct=0.028, soft_sl_pct=0.028, hard_sl_pct=0.038
            )
            setups_strict.extend(s)
            
        raw_eval_strict = evaluate_raw_signals(setups_strict, candles_resampled, btc_map_1h)
        comp_eval_strict = simulate_compounding(setups_strict, candles_resampled, btc_map_1h, max_slots=5)
        
        # Test 1B: Calibrated Displacement & TP/SL per TF
        setups_calib = []
        for sym, c_list in candles_resampled.items():
            s = harvest_hermes35_setups(
                c_list, sym, lbl, mins,
                btc_4h_ema50_map, btc_map_4h,
                disp_threshold=tf_cfg["calib_disp"],
                tp_pct=tf_cfg["tp"], soft_sl_pct=tf_cfg["soft_sl"], hard_sl_pct=tf_cfg["hard_sl"]
            )
            setups_calib.extend(s)
            
        raw_eval_calib = evaluate_raw_signals(setups_calib, candles_resampled, btc_map_1h)
        comp_eval_calib = simulate_compounding(setups_calib, candles_resampled, btc_map_1h, max_slots=5)
        
        suite1_results[lbl] = {
            "strict_5pct": {
                "setups": len(setups_strict),
                "raw_signals": raw_eval_strict,
                "compounding_5slots": comp_eval_strict
            },
            "calibrated": {
                "disp_threshold": tf_cfg["calib_disp"],
                "tp_pct": tf_cfg["tp"],
                "setups": len(setups_calib),
                "raw_signals": raw_eval_calib,
                "compounding_5slots": comp_eval_calib
            }
        }
        
        print(f"   [{lbl} STRICT 5%]   Signals: {raw_eval_strict['total_signals']:3d} | WinRate: {raw_eval_strict['win_rate']:5.1f}% | PF: {raw_eval_strict['profit_factor']:5.2f} | Eq: ${comp_eval_strict['total_equity']:,.2f} | MaxDD: {comp_eval_strict['max_drawdown_pct']:.1f}%")
        print(f"   [{lbl} CALIBRATED] Signals: {raw_eval_calib['total_signals']:3d} | WinRate: {raw_eval_calib['win_rate']:5.1f}% | PF: {raw_eval_calib['profit_factor']:5.2f} | Eq: ${comp_eval_calib['total_equity']:,.2f} | MaxDD: {comp_eval_calib['max_drawdown_pct']:.1f}%")

    results["dataset_6month_15m"] = suite1_results
    
    # -------------------------------------------------------------
    # EXPERIMENT 2: 2-Year Continuous Long-Term Dataset (22 Champions)
    # -------------------------------------------------------------
    dir_2yr = "historical_data_2year"
    if os.path.exists(dir_2yr):
        print("\n" + "-" * 90)
        print("TEST SUITE 2: 2-YEAR CONTINUOUS MACRO DATASET (Sep 2024 - Sep 2026 | 22 Coins)")
        print("LONG-TERM COMPARISON: 3H (180m) vs 4H (240m) vs 1H (60m)")
        print("-" * 90)
        
        # Load 1h files and 4h files
        coins_2yr = [
            "AAVEUSDT", "ALGOUSDT", "APTUSDT", "AVAXUSDT", "BTCUSDT",
            "DOGEUSDT", "FETUSDT", "FILUSDT", "GALAUSDT", "ICPUSDT",
            "LDOUSDT", "MKRUSDT", "NEARUSDT", "OPUSDT", "PYTHUSDT",
            "RENDERUSDT", "RUNEUSDT", "SANDUSDT", "SHIBUSDT", "SUIUSDT",
            "THETAUSDT", "UNIUSDT"
        ]
        
        raw_1h_2yr = {}
        raw_4h_2yr = {}
        for c in coins_2yr:
            f1h = os.path.join(dir_2yr, f"{c}_1h.json")
            f4h = os.path.join(dir_2yr, f"{c}_4h.json")
            if os.path.exists(f1h):
                with open(f1h, "r", encoding="utf-8") as fp: raw_1h_2yr[c] = json.load(fp)
            if os.path.exists(f4h):
                with open(f4h, "r", encoding="utf-8") as fp: raw_4h_2yr[c] = json.load(fp)
                
        # BTC Maps for 2-year
        btc_4h_2yr = raw_4h_2yr.get("BTCUSDT", [])
        btc_1h_2yr = raw_1h_2yr.get("BTCUSDT", [])
        btc_map_4h_2yr = {c["time"]: c for c in btc_4h_2yr}
        btc_map_1h_2yr = {c["time"]: c for c in btc_1h_2yr}
        
        btc_closes_4h_2yr = [c["close"] for c in btc_4h_2yr]
        btc_ema50_4h_2yr = calculate_ema(btc_closes_4h_2yr, 50)
        btc_4h_ema50_map_2yr = {btc_4h_2yr[i]["time"]: (btc_4h_2yr[i]["close"] >= btc_ema50_4h_2yr[i]) for i in range(len(btc_4h_2yr))}
        
        # Create 3H by resampling 1H
        print("🔄 Resampling 22 coins from 1H to 3H (180m)...", end="", flush=True)
        raw_3h_2yr = {}
        for sym, c_list in raw_1h_2yr.items():
            raw_3h_2yr[sym] = resample_candles(c_list, 180)
        print(" Done.")
        
        longterm_tests = [
            {"tf": "3H (180m)", "data": raw_3h_2yr, "mins": 180, "tp": 0.028, "disp": 0.050},
            {"tf": "4H (240m)", "data": raw_4h_2yr, "mins": 240, "tp": 0.028, "disp": 0.050},
            {"tf": "1H (60m)", "data": raw_1h_2yr, "mins": 60, "tp": 0.022, "disp": 0.050}
        ]
        
        suite2_results = {}
        for lt in longterm_tests:
            lbl = lt["tf"]
            mins = lt["mins"]
            c_dict = lt["data"]
            
            setups = []
            for sym, c_list in c_dict.items():
                s = harvest_hermes35_setups(
                    c_list, sym, lbl, mins,
                    btc_4h_ema50_map_2yr, btc_map_4h_2yr,
                    disp_threshold=lt["disp"],
                    tp_pct=lt["tp"], soft_sl_pct=lt["tp"], hard_sl_pct=0.038
                )
                setups.extend(s)
                
            raw_eval = evaluate_raw_signals(setups, c_dict, btc_map_1h_2yr)
            comp_eval = simulate_compounding(setups, c_dict, btc_map_1h_2yr, max_slots=5)
            
            # Split In-Sample (Year 1) vs Out-of-Sample (Year 2)
            # Midpoint timestamp: Sep 2025 (~1758800000000)
            split_ts = 1758800000000
            setups_is = [s for s in setups if s["time"] < split_ts]
            setups_oos = [s for s in setups if s["time"] >= split_ts]
            
            raw_is = evaluate_raw_signals(setups_is, c_dict, btc_map_1h_2yr)
            raw_oos = evaluate_raw_signals(setups_oos, c_dict, btc_map_1h_2yr)
            
            suite2_results[lbl] = {
                "full_2year": {
                    "total_setups": len(setups),
                    "raw_signals": raw_eval,
                    "compounding_5slots": comp_eval
                },
                "in_sample_year1": raw_is,
                "out_of_sample_year2": raw_oos
            }
            
            print(f"\n   [{lbl} 2-YEAR MASTER REPORT]")
            print(f"   Signals: {raw_eval['total_signals']} | WinRate: {raw_eval['win_rate']:.2f}% | PF: {raw_eval['profit_factor']:.2f} | AvgDur: {raw_eval['avg_duration_h']}h")
            print(f"   In-Sample Yr 1 WinRate: {raw_is['win_rate']:.2f}% ({raw_is['wins']}W / {raw_is['losses']}L)")
            print(f"   Out-of-Sample Yr 2 WinRate: {raw_oos['win_rate']:.2f}% ({raw_oos['wins']}W / {raw_oos['losses']}L)")
            print(f"   Compounding Equity: ${comp_eval['total_equity']:,.2f} | MaxDD: {comp_eval['max_drawdown_pct']:.2f}% | M1K: Trade #{comp_eval['m1k_trade']} | M2K: Trade #{comp_eval['m2k_trade']}")
            
        results["dataset_2year_longterm"] = suite2_results
        
    out_file = "hermes35_custom_timeframes_results.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(results, fp, indent=2)
        
    elapsed = time.time() - start_time
    print("\n" + "=" * 90)
    print(f"✅ EXPERIMENT COMPLETE IN {elapsed:.2f}s! Results saved to {out_file}")
    print("=" * 90)

if __name__ == "__main__":
    run_all_experiments()
