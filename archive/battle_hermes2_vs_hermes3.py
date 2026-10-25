import json
import time
import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_local_data(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def run_simulation(model_name, signals, fee_rate=0.0016):
    signals.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for s in signals:
        if s["time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    cap = 50.0
    vault = 0.0
    peak = 50.0
    max_dd = 0.0
    hit_1k = None
    hit_2k = None
    wins = 0
    losses = 0
    gp = 0.0
    gl = 0.0

    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - fee_rate
        pos_size = cap * 5.0
        pnl = pos_size * net_move

        if trade["res"] == "WIN":
            wins += 1
            gp += pnl
            cap += (pnl * 0.85)
            vault += (pnl * 0.15)
        else:
            losses += 1
            gl += abs(pnl)
            cap += pnl
            if cap < 2.0:
                cap = 0.0

        tot = cap + vault
        if tot > peak:
            peak = tot
        dd = (peak - tot) / peak * 100.0 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

        if tot >= 1000.0 and hit_1k is None:
            hit_1k = idx + 1
        if tot >= 2000.0 and hit_2k is None:
            hit_2k = idx + 1

    tot_trades = wins + losses
    wr = (wins / tot_trades * 100.0) if tot_trades > 0 else 0.0
    pf = (gp / gl) if gl > 0 else 99.0

    return {
        "model": model_name,
        "total_trades": tot_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "profit_factor": round(pf, 2),
        "max_drawdown": round(max_dd, 2),
        "hit_1k": hit_1k or "N/A",
        "hit_2k": hit_2k or "N/A",
        "final_capital": round(cap, 2),
        "final_vault": round(vault, 2),
        "total_equity": round(cap + vault, 2)
    }

def main():
    print("=" * 115)
    print(" 👑 QUANTITATIVE BATTLE: HERMES 2.0 APEX vs HERMES 3.0 EXPERIMENTAL")
    print(" Complete Dataset: 1 Full Year (339,512 Candlesticks) across Top-22 Champions")
    print(" Baseline: $50 Start | 5x Isolated Leverage | 1-Trade Sequential Compounding (85/15 Split)")
    print("=" * 115)

    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    btc_4h = load_local_data("BTCUSDT", "4h")
    btc_map_4h = {c["time"]: c for c in btc_4h}

    # Signals collectors
    hermes2_signals = []
    hermes3_variants = {
        "HERMES 3.0-A (Dynamic Armor)": [],
        "HERMES 3.0-B (FVG Quality >= 0.5%)": [],
        "HERMES 3.0-C (Full Quantum Suite)": []
    }

    max_hold = 24

    for tf in ["1h", "4h"]:
        std_tp_pct = 0.022 if tf == "1h" else 0.028
        soft_sl_pct = 0.025 if tf == "1h" else 0.028
        hard_sl_pct = 0.036 if tf == "1h" else 0.038
        max_tap_window = 28

        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                # -------------------------------------------------------------
                # 1. BULLISH EVALUATION
                # -------------------------------------------------------------
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050: # Sentry 2: 5% Displacement
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
                                fvg_pct = (candles[best_mid + 1]["low"] - candles[best_mid - 1]["high"]) / candles[best_mid - 1]["high"] if has_fvg else 0.0

                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        if candles[t]["low"] <= dec_top * 0.9995:
                                            tap_c = candles[t]

                                            # Sentry 1: Macro BTC Check
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0

                                            # Sentry 1 Standard (Dump >= 2.0%)
                                            sentry1_clean = btc_dump < 0.020

                                            # Sentry 1 Enhanced (2-bar cumulative dump >= 3.0%)
                                            prev_prev_4h_ts = prev_4h_ts - (4 * 3600 * 1000)
                                            btc_c_prev = btc_map_4h.get(prev_prev_4h_ts)
                                            cum_dump = (btc_c_prev["open"] - btc_c["close"]) / btc_c_prev["open"] if btc_c and btc_c_prev else btc_dump
                                            sentry1_quantum = (btc_dump < 0.020) and (cum_dump < 0.030)

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            # Sentry 3: IDM Sweep + >=18% Wick + 50% MT
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top

                                                # --- EVALUATE MODEL A: HERMES 2.0 APEX ---
                                                if sentry1_clean:
                                                    tp_p = entry * (1.0 + std_tp_pct)
                                                    soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                    res = None; exit_p = entry; exit_t = tap_c["time"]
                                                    for m in range(t, min(t + max_hold, n)):
                                                        if candles[m]["high"] >= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["low"] <= hard_sl_p:
                                                            res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] <= soft_sl_p:
                                                            res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc >= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    hermes2_signals.append({
                                                        "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (exit_p - entry) / entry, "res": res
                                                    })

                                                # --- EVALUATE MODEL B: HERMES 3.0-A (Dynamic Armor) ---
                                                if sentry1_clean:
                                                    tp_p = entry * (1.0 + std_tp_pct)
                                                    soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                    res = None; exit_p = entry; exit_t = tap_c["time"]
                                                    curr_soft_sl = soft_sl_p

                                                    for m in range(t, min(t + max_hold, n)):
                                                        high_so_far = candles[m]["high"]
                                                        # Dynamic profit lock:
                                                        if high_so_far >= entry * 1.016:
                                                            curr_soft_sl = max(curr_soft_sl, entry * 1.002) # Fee breakeven
                                                        if high_so_far >= entry * 1.022:
                                                            curr_soft_sl = max(curr_soft_sl, entry * 1.012) # +1.2% locked profit

                                                        if candles[m]["high"] >= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["low"] <= hard_sl_p:
                                                            res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] <= curr_soft_sl:
                                                            res = "WIN" if curr_soft_sl > entry else "LOSS"
                                                            exit_p = candles[m]["close"]
                                                            exit_t = candles[m]["time"]
                                                            break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc >= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    hermes3_variants["HERMES 3.0-A (Dynamic Armor)"].append({
                                                        "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (exit_p - entry) / entry, "res": res
                                                    })

                                                # --- EVALUATE MODEL B: HERMES 3.0-B (FVG Quality >= 0.50%) ---
                                                if sentry1_clean and fvg_pct >= 0.005:
                                                    tp_p = entry * (1.0 + std_tp_pct)
                                                    soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                    res = None; exit_p = entry; exit_t = tap_c["time"]
                                                    for m in range(t, min(t + max_hold, n)):
                                                        if candles[m]["high"] >= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["low"] <= hard_sl_p:
                                                            res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] <= soft_sl_p:
                                                            res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc >= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    hermes3_variants["HERMES 3.0-B (FVG Quality >= 0.5%)"].append({
                                                        "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (exit_p - entry) / entry, "res": res
                                                    })

                                                # --- EVALUATE MODEL B: HERMES 3.0-C (Full Quantum Suite) ---
                                                if sentry1_quantum and fvg_pct >= 0.004:
                                                    # Adaptive TP: Expand to 3.4% if displacement >= 10%
                                                    adv_tp_pct = 0.034 if (gain >= 0.10 and tf == "4h") else std_tp_pct
                                                    tp_p = entry * (1.0 + adv_tp_pct)
                                                    soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                    res = None; exit_p = entry; exit_t = tap_c["time"]
                                                    curr_soft_sl = soft_sl_p
                                                    for m in range(t, min(t + max_hold, n)):
                                                        high_so_far = candles[m]["high"]
                                                        if high_so_far >= entry * 1.016:
                                                            curr_soft_sl = max(curr_soft_sl, entry * 1.002)
                                                        if high_so_far >= entry * 1.024:
                                                            curr_soft_sl = max(curr_soft_sl, entry * 1.014)

                                                        if candles[m]["high"] >= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["low"] <= hard_sl_p:
                                                            res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] <= curr_soft_sl:
                                                            res = "WIN" if curr_soft_sl > entry else "LOSS"
                                                            exit_p = candles[m]["close"]
                                                            exit_t = candles[m]["time"]
                                                            break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc >= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    hermes3_variants["HERMES 3.0-C (Full Quantum Suite)"].append({
                                                        "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (exit_p - entry) / entry, "res": res
                                                    })

                                            break

                # -------------------------------------------------------------
                # 2. BEARISH EVALUATION
                # -------------------------------------------------------------
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050: # Sentry 2: 5% Displacement
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
                                fvg_pct = (candles[best_mid - 1]["low"] - candles[best_mid + 1]["high"]) / candles[best_mid - 1]["low"] if has_bear_fvg else 0.0

                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]

                                            # Sentry 1: Macro BTC Check
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0

                                            sentry1_clean = btc_pump < 0.020

                                            prev_prev_4h_ts = prev_4h_ts - (4 * 3600 * 1000)
                                            btc_c_prev = btc_map_4h.get(prev_prev_4h_ts)
                                            cum_pump = (btc_c["close"] - btc_c_prev["open"]) / btc_c_prev["open"] if btc_c and btc_c_prev else btc_pump
                                            sentry1_quantum = (btc_pump < 0.020) and (cum_pump < 0.030)

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            # Sentry 3: IDM Sweep + >=18% Wick + 50% MT
                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot

                                                # --- MODEL A: HERMES 2.0 APEX ---
                                                if sentry1_clean:
                                                    tp_p = entry * (1.0 - std_tp_pct)
                                                    soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                    res = None; exit_p = entry; exit_t = tap_c["time"]
                                                    for m in range(t, min(t + max_hold, n)):
                                                        if candles[m]["low"] <= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["high"] >= hard_sl_p:
                                                            res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] >= soft_sl_p:
                                                            res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc <= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    hermes2_signals.append({
                                                        "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (entry - exit_p) / entry, "res": res
                                                    })

                                                # --- MODEL B: HERMES 3.0-A (Dynamic Armor) ---
                                                if sentry1_clean:
                                                    tp_p = entry * (1.0 - std_tp_pct)
                                                    soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                    res = None; exit_p = entry; exit_t = tap_c["time"]
                                                    curr_soft_sl = soft_sl_p

                                                    for m in range(t, min(t + max_hold, n)):
                                                        low_so_far = candles[m]["low"]
                                                        if low_so_far <= entry * 0.984:
                                                            curr_soft_sl = min(curr_soft_sl, entry * 0.998)
                                                        if low_so_far <= entry * 0.978:
                                                            curr_soft_sl = min(curr_soft_sl, entry * 0.988)

                                                        if candles[m]["low"] <= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["high"] >= hard_sl_p:
                                                            res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] >= curr_soft_sl:
                                                            res = "WIN" if curr_soft_sl < entry else "LOSS"
                                                            exit_p = candles[m]["close"]
                                                            exit_t = candles[m]["time"]
                                                            break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc <= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    hermes3_variants["HERMES 3.0-A (Dynamic Armor)"].append({
                                                        "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (entry - exit_p) / entry, "res": res
                                                    })

                                                # --- MODEL B: HERMES 3.0-B (FVG Quality >= 0.50%) ---
                                                if sentry1_clean and fvg_pct >= 0.005:
                                                    tp_p = entry * (1.0 - std_tp_pct)
                                                    soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                    res = None; exit_p = entry; exit_t = tap_c["time"]
                                                    for m in range(t, min(t + max_hold, n)):
                                                        if candles[m]["low"] <= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["high"] >= hard_sl_p:
                                                            res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] >= soft_sl_p:
                                                            res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc <= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    hermes3_variants["HERMES 3.0-B (FVG Quality >= 0.5%)"].append({
                                                        "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (entry - exit_p) / entry, "res": res
                                                    })

                                                # --- MODEL B: HERMES 3.0-C (Full Quantum Suite) ---
                                                if sentry1_quantum and fvg_pct >= 0.004:
                                                    adv_tp_pct = 0.034 if (drop >= 0.10 and tf == "4h") else std_tp_pct
                                                    tp_p = entry * (1.0 - adv_tp_pct)
                                                    soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                    res = None; exit_p = entry; exit_t = tap_c["time"]
                                                    curr_soft_sl = soft_sl_p
                                                    for m in range(t, min(t + max_hold, n)):
                                                        low_so_far = candles[m]["low"]
                                                        if low_so_far <= entry * 0.984:
                                                            curr_soft_sl = min(curr_soft_sl, entry * 0.998)
                                                        if low_so_far <= entry * 0.976:
                                                            curr_soft_sl = min(curr_soft_sl, entry * 0.986)

                                                        if candles[m]["low"] <= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["high"] >= hard_sl_p:
                                                            res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] >= curr_soft_sl:
                                                            res = "WIN" if curr_soft_sl < entry else "LOSS"
                                                            exit_p = candles[m]["close"]
                                                            exit_t = candles[m]["time"]
                                                            break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc <= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    hermes3_variants["HERMES 3.0-C (Full Quantum Suite)"].append({
                                                        "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (entry - exit_p) / entry, "res": res
                                                    })

                                            break

    # Run simulations
    print("\n⚔️  RUNNING HEAD-TO-HEAD BATTLE SIMULATIONS...")
    res_hermes2 = run_simulation("HERMES 2.0 APEX (Production Standard)", hermes2_signals)
    results = [res_hermes2]

    for name, sigs in hermes3_variants.items():
        results.append(run_simulation(name, sigs))

    # Print Table
    print("\n" + "=" * 125)
    print(f"{'Strategy Model':<38} | {'Trades':<7} | {'Win Rate':<9} | {'PF':<5} | {'Max DD':<7} | {'$1K Hit':<8} | {'$2K Hit':<8} | {'Total Equity':<18}")
    print("-" * 125)
    for r in results:
        eq_str = f"${r['total_equity']:,.2f} USDT"
        hit_1k_str = f"T#{r['hit_1k']}" if isinstance(r['hit_1k'], int) else r['hit_1k']
        hit_2k_str = f"T#{r['hit_2k']}" if isinstance(r['hit_2k'], int) else r['hit_2k']
        print(f"{r['model']:<38} | {r['total_trades']:<7} | {r['win_rate']:>6.2f}%   | {r['profit_factor']:>4.2f} | {r['max_drawdown']:>5.2f}% | {hit_1k_str:<8} | {hit_2k_str:<8} | {eq_str:<18}")
    print("=" * 125)

    # Save battle report json
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hermes2_vs_hermes3_battle_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n📊 Detailed results saved to: {out_path}")

if __name__ == "__main__":
    main()
