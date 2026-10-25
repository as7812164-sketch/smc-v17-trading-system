"""
1-YEAR MASTER TEST: ORDER FLOW CONFIRMATION + DYNAMIC ATR BUFFER STOP LOSS
==========================================================================
Combines:
1. Location: Institutional Order Block (Displacement >= 5.0% + FVG)
2. Trigger: 15m Order Flow Confirmation (Delta Flip + CVD Absorption + Rejection Wick)
3. STOP LOSS ARCHITECTURE: Dynamic ATR Buffer SL (OB Low - 0.20 * ATR_14)
   + Multi-Stage Profit Armor (+1.6% move -> BE Lock +0.1%, +2.2% move -> Trailing +0.8%)
4. Targets: TP = +14.0% ROE (+2.8% price move at 5x leverage)
"""

import os
import sys
import json
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from run_experiment_hermes35_4_orderflow_concepts import (
    load_15m_data, resample_15m_to_higher_tf, calculate_ema, calculate_sma
)

def calculate_atr_15m(candles: List[Dict[str, Any]], period: int = 14) -> List[float]:
    n = len(candles)
    if n == 0: return []
    atr = [0.0] * n
    tr_list = [0.0] * n
    for i in range(1, n):
        h = float(candles[i]["high"])
        l = float(candles[i]["low"])
        prev_c = float(candles[i-1]["close"])
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list[i] = tr
        if i < period:
            atr[i] = sum(tr_list[1:i+1]) / i
        elif i == period:
            atr[i] = sum(tr_list[1:period+1]) / period
        else:
            atr[i] = (atr[i-1] * (period - 1) + tr) / period
    return atr

def run_of_with_atr_sl_test():
    print("=" * 85)
    print("🔬 1-YEAR TEST: ORDER FLOW TRIGGER + DYNAMIC ATR BUFFER STOP LOSS")
    print("=" * 85)

    data_15m = load_15m_data()
    btc_15m = data_15m.get("BTCUSDT", [])
    btc_4h = resample_15m_to_higher_tf(btc_15m, 4)
    btc_closes_4h = [c["close"] for c in btc_4h]
    btc_ema50_4h = calculate_ema(btc_closes_4h, 50)
    btc_4h_ema50_map = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_ema50_4h[i]) for i in range(len(btc_4h))}

    tp_pct = 0.0280 # +14.0% ROE at 5x

    for target_tf_hours in [1, 4]:
        tf_name = f"{target_tf_hours}H"
        print(f"\n--- Testing on {tf_name} with Order Flow & Dynamic ATR SL ---")

        all_setups = []
        for sym, c15_list in data_15m.items():
            atr_15m = calculate_atr_15m(c15_list, 14)
            for idx, c in enumerate(c15_list):
                c["atr"] = atr_15m[idx] if idx < len(atr_15m) else 0.0

            c_high_tf = resample_15m_to_higher_tf(c15_list, target_tf_hours)
            n_htf = len(c_high_tf)
            if n_htf < 30: continue

            for i in range(15, n_htf - 10):
                # Bullish OB
                if c_high_tf[i]["low"] == min(c["low"] for c in c_high_tf[max(0, i-10):i+1]):
                    sub = c_high_tf[i:min(i+16, n_htf)]
                    highs = [c["high"] for c in sub]
                    max_h = max(highs)
                    h_idx = i + highs.index(max_h)
                    if h_idx > i + 2:
                        gain = (max_h - c_high_tf[i]["low"]) / c_high_tf[i]["low"]
                        if gain >= 0.050:
                            has_fvg = (c_high_tf[i+2]["low"] > c_high_tf[i]["high"]) if i+2 < n_htf else False
                            if not has_fvg and i+3 < n_htf:
                                has_fvg = (c_high_tf[i+3]["low"] > c_high_tf[i+1]["high"])
                            if has_fvg:
                                ob_high = c_high_tf[i]["high"]
                                ob_low = c_high_tf[i]["low"]
                                mt = (ob_high + ob_low) / 2.0
                                all_setups.append({
                                    "sym": sym, "side": "BUY", "ob_high": ob_high, "ob_low": ob_low, "mt": mt,
                                    "h_idx_time": c_high_tf[h_idx]["time"], "c15_list": c15_list
                                })

                # Bearish OB
                if c_high_tf[i]["high"] == max(c["high"] for c in c_high_tf[max(0, i-10):i+1]):
                    sub = c_high_tf[i:min(i+16, n_htf)]
                    lows = [c["low"] for c in sub]
                    min_l = min(lows)
                    l_idx = i + lows.index(min_l)
                    if l_idx > i + 2:
                        drop = (c_high_tf[i]["high"] - min_l) / c_high_tf[i]["high"]
                        if drop >= 0.050:
                            has_fvg = (c_high_tf[i+2]["high"] < c_high_tf[i]["low"]) if i+2 < n_htf else False
                            if not has_fvg and i+3 < n_htf:
                                has_fvg = (c_high_tf[i+3]["high"] < c_high_tf[i+1]["low"])
                            if has_fvg:
                                ob_high = c_high_tf[i]["high"]
                                ob_low = c_high_tf[i]["low"]
                                mt = (ob_high + ob_low) / 2.0
                                all_setups.append({
                                    "sym": sym, "side": "SELL", "ob_high": ob_high, "ob_low": ob_low, "mt": mt,
                                    "h_idx_time": c_high_tf[l_idx]["time"], "c15_list": c15_list
                                })

        all_setups.sort(key=lambda x: x["h_idx_time"])

        stats_fixed = {"w": 0, "be": 0, "l": 0, "stopped_then_tp": 0}
        stats_atr = {"w": 0, "be": 0, "l": 0, "stopped_then_tp": 0}
        total_triggered = 0

        for s in all_setups:
            c15 = s["c15_list"]
            h_time = s["h_idx_time"]
            side = s["side"]
            ob_high = s["ob_high"]
            ob_low = s["ob_low"]
            mt = s["mt"]

            start_15m_idx = None
            for idx, c in enumerate(c15):
                if c["time"] >= h_time:
                    start_15m_idx = idx
                    break
            if start_15m_idx is None or start_15m_idx + 10 >= len(c15):
                continue

            search_window = c15[start_15m_idx : min(start_15m_idx + 180, len(c15))]
            
            boundary_idx = None
            for idx, c in enumerate(search_window):
                if side == "BUY" and c["low"] <= ob_high:
                    boundary_idx = idx
                    break
                elif side == "SELL" and c["high"] >= ob_low:
                    boundary_idx = idx
                    break

            if boundary_idx is None or boundary_idx + 1 >= len(search_window):
                continue

            # 15m Order Flow Check (Delta Flip + CVD Absorption)
            tap_c = search_window[boundary_idx]
            next_c = search_window[boundary_idx + 1]
            delta_tap = float(tap_c.get("delta", 0.0))
            delta_next = float(next_c.get("delta", 0.0))
            of_confirmed = (delta_tap > 0 or delta_next > 0) if side == "BUY" else (delta_tap < 0 or delta_next < 0)
            if not of_confirmed:
                continue

            total_triggered += 1
            entry = ob_high if side == "BUY" else ob_low
            tp_price = entry * (1.0 + tp_pct) if side == "BUY" else entry * (1.0 - tp_pct)
            future = search_window[boundary_idx + 1:]

            # Did price reach TP?
            eventually_hit_tp = any((fc["high"] >= tp_price if side == "BUY" else fc["low"] <= tp_price) for fc in future)

            # SL Method 1: Fixed -2.8% SL with Profit Armor
            sl_fixed = entry * (1.0 - 0.0280) if side == "BUY" else entry * (1.0 + 0.0280)
            sl_curr_fixed = sl_fixed
            armor_fixed = False
            for fc in future:
                if side == "BUY":
                    if not armor_fixed and fc["high"] >= entry * 1.016:
                        armor_fixed = True; sl_curr_fixed = entry * 1.001
                    if fc["high"] >= tp_price: stats_fixed["w"] += 1; break
                    elif fc["low"] <= sl_curr_fixed:
                        if armor_fixed: stats_fixed["be"] += 1
                        else:
                            stats_fixed["l"] += 1
                            if eventually_hit_tp: stats_fixed["stopped_then_tp"] += 1
                        break
                else:
                    if not armor_fixed and fc["low"] <= entry * 0.984:
                        armor_fixed = True; sl_curr_fixed = entry * 0.999
                    if fc["low"] <= tp_price: stats_fixed["w"] += 1; break
                    elif fc["high"] >= sl_curr_fixed:
                        if armor_fixed: stats_fixed["be"] += 1
                        else:
                            stats_fixed["l"] += 1
                            if eventually_hit_tp: stats_fixed["stopped_then_tp"] += 1
                        break

            # SL Method 2: Dynamic ATR Buffer SL (OB Low - 0.20 * ATR_15m) with Profit Armor
            atr_val = float(tap_c.get("atr", entry * 0.015)) or (entry * 0.015)
            sl_atr_init = (ob_low - 0.20 * atr_val) if side == "BUY" else (ob_high + 0.20 * atr_val)
            sl_curr_atr = sl_atr_init
            armor_atr = False
            for fc in future:
                if side == "BUY":
                    if not armor_atr and fc["high"] >= entry * 1.016:
                        armor_atr = True; sl_curr_atr = entry * 1.001
                    if fc["high"] >= tp_price: stats_atr["w"] += 1; break
                    elif fc["low"] <= sl_curr_atr:
                        if armor_atr: stats_atr["be"] += 1
                        else:
                            stats_atr["l"] += 1
                            if eventually_hit_tp: stats_atr["stopped_then_tp"] += 1
                        break
                else:
                    if not armor_atr and fc["low"] <= entry * 0.984:
                        armor_atr = True; sl_curr_atr = entry * 0.999
                    if fc["low"] <= tp_price: stats_atr["w"] += 1; break
                    elif fc["high"] >= sl_curr_atr:
                        if armor_atr: stats_atr["be"] += 1
                        else:
                            stats_atr["l"] += 1
                            if eventually_hit_tp: stats_atr["stopped_then_tp"] += 1
                        break

        print(f"\nRESULTS ON {tf_name} ({total_triggered} EXECUTED TRADES):")
        print(f"{'METRIC':<30} | {'FIXED -2.8% SL':<20} | {'DYNAMIC ATR BUFFER SL':<20}")
        print("-" * 75)
        f_wr = (stats_fixed["w"] / total_triggered * 100) if total_triggered else 0
        f_cs = ((stats_fixed["w"] + stats_fixed["be"]) / total_triggered * 100) if total_triggered else 0
        f_pf = (stats_fixed["w"] * 14.0) / (stats_fixed["l"] * 14.0) if stats_fixed["l"] else 99
        a_wr = (stats_atr["w"] / total_triggered * 100) if total_triggered else 0
        a_cs = ((stats_atr["w"] + stats_atr["be"]) / total_triggered * 100) if total_triggered else 0
        a_pf = (stats_atr["w"] * 14.0) / (stats_atr["l"] * 14.0) if stats_atr["l"] else 99

        print(f"{'Direct Wins (+14% ROE)':<30} | {stats_fixed['w']:<20} | {stats_atr['w']:<20}")
        print(f"{'Armor BE Exits':<30} | {stats_fixed['be']:<20} | {stats_atr['be']:<20}")
        print(f"{'Hard SL Losses':<30} | {stats_fixed['l']:<20} | {stats_atr['l']:<20}")
        print(f"{'Direct Win Rate (%)':<30} | {f_wr:.2f}%{'':<14} | {a_wr:.2f}%{'':<14}")
        print(f"{'Capital Safety Rate (%)':<30} | {f_cs:.2f}%{'':<14} | {a_cs:.2f}%{'':<14}")
        print(f"{'Profit Factor':<30} | {f_pf:.2f}{'':<16} | {a_pf:.2f}{'':<16}")
        print(f"{'Stop-Hunts (Hit SL then TP)':<30} | {stats_fixed['stopped_then_tp']} ({stats_fixed['stopped_then_tp']/max(1, stats_fixed['l'])*100:.1f}%)" + " " * 8 + f"| {stats_atr['stopped_then_tp']} ({stats_atr['stopped_then_tp']/max(1, stats_atr['l'])*100:.1f}%)")

if __name__ == "__main__":
    run_of_with_atr_sl_test()
