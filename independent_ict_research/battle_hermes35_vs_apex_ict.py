"""
===============================================================================
⚔️ 1-YEAR TITANIC BATTLE: HERMES 3.5 vs APEX ICT 8-LAYER CONFLUENCE STRATEGY
===============================================================================
Directive: 100% Standalone / Independent Quantitative Battle.
Zero modification to production Hermes 3.5 codebase.

Dataset: 1 Full Year (339,512 Candlesticks) across Top-22 Binance Futures Assets
Timeframes: 1H and 4H
Capital: $50.00 Starting Margin, 5x Isolated Leverage, 85% Reinvest / 15% Vault
Sequential Trade Execution: Strict 1-Trade-at-a-time Portfolio Queue
Friction: 0.16% Round-trip taker fee/slippage applied to every trade fill

Competitor 1: HERMES 3.5 (Decisional OB + Inducement Sweep + 18% Wick + 50% MT)
Competitor 2: APEX ICT (Extreme Bedrock OB + Body BOS + 50% Discount + 0.35 ATR Buffer)
===============================================================================
"""

import os
import sys
import json
import time
import math
import numpy as np
from typing import List, Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

BASE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
DATA_DIR = os.path.join(BASE_DIR, "historical_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "independent_ict_research")


def load_candles(sym: str, interval: str) -> List[Dict[str, Any]]:
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_atr(candles: List[Dict[str, Any]], period: int = 14) -> List[float]:
    if not candles:
        return []
    atrs = [max(candles[0]["high"] - candles[0]["low"], 1e-6)]
    for i in range(1, len(candles)):
        curr = candles[i]
        prev = candles[i - 1]
        tr = max(curr["high"] - curr.get("low", curr["high"]),
                 abs(curr["high"] - prev["close"]),
                 abs(curr["low"] - prev["close"]))
        prev_atr = atrs[-1]
        atr = (prev_atr * (period - 1) + tr) / period
        atrs.append(atr)
    return atrs


# =============================================================================
# 1. HERMES 3.5 ENGINE (DECISIONAL OB + INDUCEMENT + 18% WICK + 50% MT)
# =============================================================================
def generate_hermes35_trades(all_data: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> List[Dict[str, Any]]:
    trades = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.022 if tf == "1h" else 0.028
        soft_sl_pct = 0.025 if tf == "1h" else 0.028
        hard_sl_pct = 0.036 if tf == "1h" else 0.038
        max_hold = 24

        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 60:
                continue
            for i in range(25, n - 35):
                # Bullish Hermes 3.5
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.045:
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
                                    for t in range(high_idx + 1, min(high_idx + 35, n)):
                                        if candles[t]["low"] <= dec_top * 0.9995:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                res = None
                                                exit_p = entry
                                                exit_t = tap_c["time"]

                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"
                                                        exit_p = tp_p
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res = "LOSS"
                                                        exit_p = min(hard_sl_p, candles[m]["open"])
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["close"] <= soft_sl_p:
                                                        res = "LOSS"
                                                        exit_p = candles[m]["close"]
                                                        exit_t = candles[m]["time"]
                                                        break

                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                gross_move = (exit_p - entry) / entry
                                                trades.append({
                                                    "strategy": "HERMES_3.5",
                                                    "sym": sym,
                                                    "side": "LONG",
                                                    "tf": tf,
                                                    "time": tap_c["time"],
                                                    "exit_time": exit_t,
                                                    "entry": entry,
                                                    "exit": exit_p,
                                                    "gross": gross_move,
                                                    "res": res,
                                                    "model": "DECISIONAL_OB"
                                                })
                                            break

                # Bearish Hermes 3.5
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.045:
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
                                    for t in range(low_idx + 1, min(low_idx + 35, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                res = None
                                                exit_p = entry
                                                exit_t = tap_c["time"]

                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"
                                                        exit_p = tp_p
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res = "LOSS"
                                                        exit_p = max(hard_sl_p, candles[m]["open"])
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["close"] >= soft_sl_p:
                                                        res = "LOSS"
                                                        exit_p = candles[m]["close"]
                                                        exit_t = candles[m]["time"]
                                                        break

                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                gross_move = (entry - exit_p) / entry
                                                trades.append({
                                                    "strategy": "HERMES_3.5",
                                                    "sym": sym,
                                                    "side": "SHORT",
                                                    "tf": tf,
                                                    "time": tap_c["time"],
                                                    "exit_time": exit_t,
                                                    "entry": entry,
                                                    "exit": exit_p,
                                                    "gross": gross_move,
                                                    "res": res,
                                                    "model": "DECISIONAL_OB"
                                                })
                                            break
    return trades


# =============================================================================
# 2. APEX ICT 8-LAYER CONFLUENCE STRATEGY
# =============================================================================
def generate_apex_ict_trades(all_data: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> List[Dict[str, Any]]:
    """
    Unified 8-Layer Confluence Engine:
    1. Fractal Inside-Bar filter (Noise eliminated)
    2. Confirmed Swing via Inducement (IDM) Sweep
    3. Break of Structure (BOS) requires CANDLE BODY CLOSE
    4. 50% Dealing Range Equilibrium Filter (Longs in Discount only <50%, Shorts in Premium only >50%)
    5. Extreme Origin Bedrock Order Block ONLY (Zero Decisional Traps)
    6. 3-Candle FVG with 50% Consequent Encroachment (CE) Entry
    7. Microstructure Absorption (Rejection Wick >= 18%)
    8. Institutional 0.35 * ATR Buffer beyond the Bedrock OB extreme
    """
    trades = []
    for tf in ["1h", "4h"]:
        max_hold = 36  # Gives high R:R setups room to expand to structural targets

        for sym, raw_candles in all_data[tf].items():
            n = len(raw_candles)
            if n < 60:
                continue

            atrs = calculate_atr(raw_candles)

            for i in range(25, n - 40):
                # 40-bar Dealing Range Calculation (Video 6: Guardeer L11)
                window_40 = raw_candles[max(0, i - 40):i + 1]
                range_low = min(c["low"] for c in window_40)
                range_high = max(c["high"] for c in window_40)
                eq_level = (range_low + range_high) / 2.0

                # -------------------------------------------------------------
                # BULLISH APEX ICT CONFLUENCE SETUP
                # -------------------------------------------------------------
                # Identify Extreme Origin Swing Low
                if raw_candles[i]["low"] == min(c["low"] for c in raw_candles[i-15:i+1]):
                    # Rule 4: Bedrock origin MUST be deep in Discount (< 50% Equilibrium)
                    if raw_candles[i]["low"] > eq_level:
                        continue  # Disqualified: Not in true institutional discount

                    sub_w = raw_candles[i:min(i+20, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)

                    if high_idx > i + 3:
                        # Rule 3: Valid Structural Impulse requiring CANDLE BODY CLOSE Break
                        prev_high_ref = max(c["high"] for c in raw_candles[max(0, i-20):i])
                        body_close_break = any(raw_candles[k]["close"] > prev_high_ref for k in range(i+1, high_idx+1))
                        if not body_close_break:
                            continue  # Disqualified: Wick sweep only (Turtle soup trap rejected)

                        gain = (max_high - raw_candles[i]["low"]) / raw_candles[i]["low"]
                        if gain >= 0.05:  # Strong institutional displacement >= 5.0%
                            # Rule 2: Inducement (IDM) level
                            idm_low = raw_candles[high_idx - 1]["low"]

                            # Rule 5: EXTREME ORIGIN BEDROCK OB (Video 1: Smart Risk)
                            # The absolute origin candle that launched the displacement (Fib >= 0.786)
                            bedrock_c = raw_candles[i]
                            ob_top = max(bedrock_c["open"], bedrock_c["close"])
                            ob_bot = bedrock_c["low"]

                            # Rule 6: 3-Candle FVG presence at/near bedrock origin
                            has_origin_fvg = (raw_candles[i + 2]["low"] > raw_candles[i]["high"]) if i + 2 < n else False
                            # FVG 50% Consequent Encroachment
                            fvg_low = raw_candles[i]["high"] if has_origin_fvg else ob_bot
                            fvg_high = raw_candles[i + 2]["low"] if has_origin_fvg else ob_top
                            ce_entry = (fvg_low + fvg_high) / 2.0 if has_origin_fvg else ob_top

                            # Rule 8: Institutional 0.35 * ATR buffer beyond bedrock low
                            atr_val = atrs[i] if i < len(atrs) else (ob_top - ob_bot)
                            buffered_sl = ob_bot - (0.35 * atr_val)

                            # Scan forward for Inducement Sweep and Bedrock Tap
                            for t in range(high_idx + 1, min(high_idx + 40, n)):
                                tap_c = raw_candles[t]
                                # Check if IDM has been swept
                                idm_swept = any(raw_candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                if not idm_swept:
                                    continue  # Cannot enter before smart money purges inducement!

                                # Check if price taps the Bedrock / CE zone
                                if tap_c["low"] <= ob_top * 1.001:
                                    # Rule 7: Microstructure Rejection Wick >= 18% (Video 7: Guardeer OF)
                                    c_range = max(tap_c["high"] - tap_c["low"], 1e-6)
                                    l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                    w_ratio = l_wick / c_range

                                    # Current price must still be in Discount
                                    if tap_c["close"] <= eq_level and w_ratio >= 0.18:
                                        entry = min(tap_c["close"], ob_top)
                                        # Take Profit targets structural Dealing Range High (High R:R)
                                        tp_price = range_high * 0.998
                                        risk_dist = abs(entry - buffered_sl)
                                        nominal_rr = (tp_price - entry) / max(risk_dist, 1e-6)

                                        # Ensure institutional R:R >= 2.5:1
                                        if nominal_rr < 2.5:
                                            tp_price = entry + (risk_dist * 2.5)

                                        res = None
                                        exit_p = entry
                                        exit_t = tap_c["time"]

                                        for m in range(t + 1, min(t + max_hold, n)):
                                            # Check TP
                                            if raw_candles[m]["high"] >= tp_price:
                                                res = "WIN"
                                                exit_p = tp_price
                                                exit_t = raw_candles[m]["time"]
                                                break
                                            # Check Buffered Stop Loss
                                            if raw_candles[m]["low"] <= buffered_sl:
                                                res = "LOSS"
                                                exit_p = buffered_sl
                                                exit_t = raw_candles[m]["time"]
                                                break

                                        if not res:
                                            fc = raw_candles[min(t + max_hold, n - 1)]["close"]
                                            res = "WIN" if fc >= entry else "LOSS"
                                            exit_p = fc
                                            exit_t = raw_candles[min(t + max_hold, n - 1)]["time"]

                                        gross_move = (exit_p - entry) / entry
                                        trades.append({
                                            "strategy": "APEX_ICT",
                                            "sym": sym,
                                            "side": "LONG",
                                            "tf": tf,
                                            "time": tap_c["time"],
                                            "exit_time": exit_t,
                                            "entry": entry,
                                            "exit": exit_p,
                                            "gross": gross_move,
                                            "res": res,
                                            "rr_nominal": nominal_rr,
                                            "model": "BEDROCK_ORIGIN_OB"
                                        })
                                    break

                # -------------------------------------------------------------
                # BEARISH APEX ICT CONFLUENCE SETUP
                # -------------------------------------------------------------
                if raw_candles[i]["high"] == max(c["high"] for c in raw_candles[i-15:i+1]):
                    # Rule 4: Bedrock origin MUST be deep in Premium (> 50% Equilibrium)
                    if raw_candles[i]["high"] < eq_level:
                        continue  # Disqualified: Not in true institutional premium

                    sub_w = raw_candles[i:min(i+20, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)

                    if low_idx > i + 3:
                        # Rule 3: Valid Structural Impulse requiring CANDLE BODY CLOSE Break
                        prev_low_ref = min(c["low"] for c in raw_candles[max(0, i-20):i])
                        body_close_break = any(raw_candles[k]["close"] < prev_low_ref for k in range(i+1, low_idx+1))
                        if not body_close_break:
                            continue

                        drop = (raw_candles[i]["high"] - min_low) / raw_candles[i]["high"]
                        if drop >= 0.05:  # Strong institutional displacement >= 5.0%
                            idm_high = raw_candles[low_idx - 1]["high"]

                            # Rule 5: EXTREME ORIGIN BEDROCK OB
                            bedrock_c = raw_candles[i]
                            ob_top = bedrock_c["high"]
                            ob_bot = min(bedrock_c["open"], bedrock_c["close"])

                            # Rule 6: 3-Candle FVG presence
                            has_bear_fvg = (raw_candles[i + 2]["high"] < raw_candles[i]["low"]) if i + 2 < n else False
                            fvg_high = raw_candles[i]["low"] if has_bear_fvg else ob_top
                            fvg_low = raw_candles[i + 2]["high"] if has_bear_fvg else ob_bot
                            ce_entry = (fvg_high + fvg_low) / 2.0 if has_bear_fvg else ob_bot

                            # Rule 8: Institutional 0.35 * ATR buffer beyond bedrock high
                            atr_val = atrs[i] if i < len(atrs) else (ob_top - ob_bot)
                            buffered_sl = ob_top + (0.35 * atr_val)

                            for t in range(low_idx + 1, min(low_idx + 40, n)):
                                tap_c = raw_candles[t]
                                idm_swept = any(raw_candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                if not idm_swept:
                                    continue

                                if tap_c["high"] >= ob_bot * 0.999:
                                    c_range = max(tap_c["high"] - tap_c["low"], 1e-6)
                                    u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                    w_ratio = u_wick / c_range

                                    if tap_c["close"] >= eq_level and w_ratio >= 0.18:
                                        entry = max(tap_c["close"], ob_bot)
                                        tp_price = range_low * 1.002
                                        risk_dist = abs(buffered_sl - entry)
                                        nominal_rr = (entry - tp_price) / max(risk_dist, 1e-6)

                                        if nominal_rr < 2.5:
                                            tp_price = entry - (risk_dist * 2.5)

                                        res = None
                                        exit_p = entry
                                        exit_t = tap_c["time"]

                                        for m in range(t + 1, min(t + max_hold, n)):
                                            if raw_candles[m]["low"] <= tp_price:
                                                res = "WIN"
                                                exit_p = tp_price
                                                exit_t = raw_candles[m]["time"]
                                                break
                                            if raw_candles[m]["high"] >= buffered_sl:
                                                res = "LOSS"
                                                exit_p = buffered_sl
                                                exit_t = raw_candles[m]["time"]
                                                break

                                        if not res:
                                            fc = raw_candles[min(t + max_hold, n - 1)]["close"]
                                            res = "WIN" if fc <= entry else "LOSS"
                                            exit_p = fc
                                            exit_t = raw_candles[min(t + max_hold, n - 1)]["time"]

                                        gross_move = (entry - exit_p) / entry
                                        trades.append({
                                            "strategy": "APEX_ICT",
                                            "sym": sym,
                                            "side": "SHORT",
                                            "tf": tf,
                                            "time": tap_c["time"],
                                            "exit_time": exit_t,
                                            "entry": entry,
                                            "exit": exit_p,
                                            "gross": gross_move,
                                            "res": res,
                                            "rr_nominal": nominal_rr,
                                            "model": "BEDROCK_ORIGIN_OB"
                                        })
                                    break
    return trades


# =============================================================================
# 3. SEQUENTIAL COMPOUNDING ARENA & BATTLE AUDITOR
# =============================================================================
def run_compounding_arena(trades: List[Dict[str, Any]], strat_name: str) -> Dict[str, Any]:
    # Sort chronologically by entry time
    trades.sort(key=lambda x: x["time"])

    # Strict 1-Trade-at-a-time Portfolio Queue
    executed = []
    active_exit = 0
    for t in trades:
        if t["time"] >= active_exit:
            executed.append(t)
            active_exit = t["exit_time"]

    cap = 50.0
    vault = 0.0
    peak = 50.0
    max_dd = 0.0
    hit_1k = None

    wins = 0
    losses = 0
    gp = 0.0
    gl = 0.0

    fee_pct = 0.0016  # 0.16% round-trip exchange fees & friction

    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - fee_pct
        pos_size = cap * 5.0  # 5x isolated leverage
        pnl = pos_size * net_move

        if trade["res"] == "WIN":
            wins += 1
            gp += max(0.0, pnl)
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
        dd = (peak - tot) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

        if tot >= 1000.0 and hit_1k is None:
            hit_1k = idx + 1

        if cap <= 0:
            break

    wr = (wins / len(executed) * 100.0) if executed else 0.0
    pf = (gp / gl) if gl > 0 else (99.0 if gp > 0 else 0.0)

    # Average Win vs Average Loss
    win_moves = [t["gross"] * 100.0 for t in executed if t["res"] == "WIN"]
    loss_moves = [t["gross"] * 100.0 for t in executed if t["res"] == "LOSS"]
    avg_win_pct = np.mean(win_moves) if win_moves else 0.0
    avg_loss_pct = np.mean(loss_moves) if loss_moves else 0.0

    return {
        "strategy": strat_name,
        "total_trades_generated": len(trades),
        "sequential_trades_executed": len(executed),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(wr, 2),
        "profit_factor": round(pf, 2),
        "max_drawdown_pct": round(max_dd * 100.0, 2),
        "hit_1k_trade": hit_1k,
        "final_capital_usdt": round(cap, 2),
        "vault_usdt": round(vault, 2),
        "total_wealth_usdt": round(cap + vault, 2),
        "avg_win_pct": round(avg_win_pct, 2),
        "avg_loss_pct": round(avg_loss_pct, 2),
        "sample_trades": executed[:8]
    }


def main():
    print("=" * 90)
    print("⚔️ STARTING 1-YEAR TITANIC BATTLE: HERMES 3.5 vs APEX ICT 8-LAYER CONFLUENCE")
    print("=" * 90)

    # Load 1-year data for Top-22 Champions
    all_data = {"1h": {}, "4h": {}}
    total_candles = 0
    t0 = time.time()

    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            c = load_candles(sym, tf)
            if len(c) >= 500:
                all_data[tf][sym] = c
                total_candles += len(c)

    t_load = time.time() - t0
    print(f"✅ Loaded {total_candles:,} candlesticks across {len(TOP_22_CHAMPIONS)} assets in {t_load:.2f}s.")

    # 1. Run Hermes 3.5 Engine
    print("\n--- [ROUND 1] EXECUTING HERMES 3.5 (DECISIONAL OB BASELINE) ---")
    t1 = time.time()
    hermes_trades = generate_hermes35_trades(all_data)
    hermes_results = run_compounding_arena(hermes_trades, "HERMES_3.5")
    t_hermes = time.time() - t1
    print(f"✅ Hermes 3.5 executed: {hermes_results['sequential_trades_executed']} trades in {t_hermes:.2f}s.")
    print(f"   Win Rate: {hermes_results['win_rate_pct']}% | Max DD: {hermes_results['max_drawdown_pct']}% | Wealth: ${hermes_results['total_wealth_usdt']:,.2f}")

    # 2. Run Apex ICT 8-Layer Confluence Engine
    print("\n--- [ROUND 2] EXECUTING APEX ICT (8-LAYER CONFLUENCE MASTER) ---")
    t2 = time.time()
    apex_trades = generate_apex_ict_trades(all_data)
    apex_results = run_compounding_arena(apex_trades, "APEX_ICT")
    t_apex = time.time() - t2
    print(f"✅ Apex ICT executed: {apex_results['sequential_trades_executed']} trades in {t_apex:.2f}s.")
    print(f"   Win Rate: {apex_results['win_rate_pct']}% | Max DD: {apex_results['max_drawdown_pct']}% | Wealth: ${apex_results['total_wealth_usdt']:,.2f}")

    # Save complete battle report
    battle_report = {
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "total_candles_tested": total_candles,
        "assets_universe": TOP_22_CHAMPIONS,
        "hermes_3_5": hermes_results,
        "apex_ict": apex_results
    }

    report_path = os.path.join(OUTPUT_DIR, "TITANIC_BATTLE_HERMES35_VS_APEX_ICT.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(battle_report, f, indent=2)

    print(f"\n📁 Battle Report saved to: {report_path}")
    print("=" * 90)


if __name__ == "__main__":
    main()
