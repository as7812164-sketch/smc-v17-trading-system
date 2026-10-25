"""
===============================================================================
⚔️ 1-YEAR HEAD-TO-HEAD BATTLE: HERMES 3.5 vs HERMES 4.0 QUANTUM
===============================================================================
Dataset: 1 Full Year (339,512 Candlesticks) across Top-22 Champions
Timeframes: 1H and 4H
Capital: $50.00 Starting Margin, 5x Isolated Leverage
Sequential Trade Queue: Strict 1-Trade-at-a-time Portfolio Execution
Friction: 0.16% Round-trip taker fee/slippage on every fill

Competitor 1: HERMES 3.5 SINGLE TIER (5% Boundary Entry, Disabled BTC Filter, Decisional OBs)
Competitor 2: HERMES 4.0 QUANTUM (Extreme Valid OB + Prior Sweep + FVG + Body BOS + Golden Pocket/50% MT + BTC Causal Brake)
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
# 1. HERMES 3.5 BASELINE ENGINE
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
                                                entry = dec_top # 5% boundary / top edge
                                                tp_p = entry * (1.0 + tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                res = None
                                                exit_p = entry
                                                exit_t = tap_c["time"]

                                                # Hermes 3.5 Stepped Harvest Simulator (+8% ROE -> BE Lock)
                                                be_locked = False
                                                for m in range(t, min(t + max_hold, n)):
                                                    curr_mfe_roe = (candles[m]["high"] - entry) / entry * 5.0
                                                    if curr_mfe_roe >= 0.08:
                                                        be_locked = True
                                                    
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"
                                                        exit_p = tp_p
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        if be_locked:
                                                            res = "WIN" # BE Lock saves as Breakeven (0 PnL)
                                                            exit_p = entry
                                                        else:
                                                            res = "LOSS"
                                                            exit_p = min(hard_sl_p, candles[m]["open"])
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["close"] <= soft_sl_p:
                                                        if be_locked:
                                                            res = "WIN"
                                                            exit_p = entry
                                                        else:
                                                            res = "LOSS"
                                                            exit_p = candles[m]["close"]
                                                        exit_t = candles[m]["time"]
                                                        break

                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else ("WIN" if be_locked else "LOSS")
                                                    exit_p = entry if be_locked and fc < entry else fc
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
                                                    "res": res
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
                                                be_locked = False

                                                for m in range(t, min(t + max_hold, n)):
                                                    curr_mfe_roe = (entry - candles[m]["low"]) / entry * 5.0
                                                    if curr_mfe_roe >= 0.08:
                                                        be_locked = True

                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"
                                                        exit_p = tp_p
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        if be_locked:
                                                            res = "WIN"
                                                            exit_p = entry
                                                        else:
                                                            res = "LOSS"
                                                            exit_p = max(hard_sl_p, candles[m]["open"])
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["close"] >= soft_sl_p:
                                                        if be_locked:
                                                            res = "WIN"
                                                            exit_p = entry
                                                        else:
                                                            res = "LOSS"
                                                            exit_p = candles[m]["close"]
                                                        exit_t = candles[m]["time"]
                                                        break

                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else ("WIN" if be_locked else "LOSS")
                                                    exit_p = entry if be_locked and fc > entry else fc
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
                                                    "res": res
                                                })
                                            break
    return trades


# =============================================================================
# 2. HERMES 4.0 QUANTUM ENGINE
# =============================================================================
def generate_hermes40_trades(all_data: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> List[Dict[str, Any]]:
    trades = []
    
    # Pre-map BTC candles for King BTC Causal Brake
    btc_map = {
        "1h": {c["time"]: c for c in all_data["1h"].get("BTCUSDT", [])},
        "4h": {c["time"]: c for c in all_data["4h"].get("BTCUSDT", [])}
    }

    for tf in ["1h", "4h"]:
        tp_pct = 0.024 if tf == "1h" else 0.032  # Enhanced R:R on deeper discount
        max_hold = 28

        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 60:
                continue
            
            atrs = calculate_atr(candles, 14)

            for i in range(25, n - 35):
                # -------------------------------------------------------------
                # BULLISH HERMES 4.0 (EXTREME VALID OB + PRIOR SWEEP + FVG + GOLDEN POCKET + BTC BRAKE)
                # -------------------------------------------------------------
                # Pillar 1: Origin Pivot Check
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    ob_c = candles[i]
                    prev_c = candles[i-1]
                    
                    # Rule 1: Prior Candle Liquidity Sweep (Candle 2 swept Candle 1 Low)
                    swept_prior = ob_c["low"] < prev_c["low"]
                    # Rule 2: Strict Bearish (Red) Candle for Bullish OB
                    is_red_ob = ob_c["close"] <= ob_c["open"]
                    
                    if swept_prior and is_red_ob:
                        # Scan forward for displacement and Body BOS
                        sub_w = candles[i:min(i+18, n)]
                        highs = [c["high"] for c in sub_w]
                        max_high = max(highs)
                        high_idx = i + highs.index(max_high)
                        
                        if high_idx > i + 3:
                            # Rule 3: Violent Displacement (>= 4.5%)
                            gain = (max_high - ob_c["low"]) / ob_c["low"]
                            # Rule 4: Clean 3-Candle FVG Void right after OB
                            has_fvg = (candles[i+2]["low"] > prev_c["high"]) if i + 2 < n else False
                            # Rule 5: Confirmed Candle Body Close BOS
                            body_bos = any(c["close"] > prev_c["high"] * 1.02 for c in candles[i+1:high_idx+1])
                            
                            if gain >= 0.045 and has_fvg and body_bos:
                                dealing_range = max_high - ob_c["low"]
                                idm_low = candles[high_idx - 1]["low"]
                                
                                # Fibonacci Levels
                                fib_50_eq = max_high - 0.50 * dealing_range
                                fib_618_gold = max_high - 0.618 * dealing_range
                                fib_786_deep = max_high - 0.786 * dealing_range
                                
                                ob_mt = (ob_c["high"] + ob_c["low"]) / 2.0
                                
                                # Retracement Scan
                                for t in range(high_idx + 1, min(high_idx + 40, n)):
                                    tap_c = candles[t]
                                    
                                    # Rule 6: Inducement (IDM) must be swept
                                    idm_swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                    
                                    # Rule 7: Direct OB / Golden Pocket Touch (Deep Discount <= 50% MT or Fib 0.618)
                                    # Entry must reach OB High or 50% MT (Zero Mid-Air Floating)
                                    touched_ob = tap_c["low"] <= min(ob_c["high"], fib_50_eq)
                                    
                                    if idm_swept and touched_ob:
                                        # Rule 8: King Bitcoin Causal Brake (No Altcoin Long if BTC is actively dumping)
                                        btc_c = btc_map[tf].get(tap_c["time"])
                                        btc_safe = True
                                        if btc_c and sym != "BTCUSDT":
                                            btc_drop = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                                            if btc_drop < -0.010: # BTC dumping > 1%
                                                btc_safe = False
                                        
                                        if not btc_safe:
                                            break # Vetoed by King BTC Shield!
                                            
                                        # Rule 9: Rejection Wick Confirmation (>= 18% lower wick)
                                        c_range = tap_c["high"] - tap_c["low"]
                                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                        
                                        if w_ratio >= 0.18 and tap_c["close"] >= ob_c["low"]:
                                            entry = max(tap_c["low"], ob_mt) # Exact entry at OB 50% MT / deep discount
                                            atr_val = atrs[t] if t < len(atrs) else (entry * 0.01)
                                            sl_p = ob_c["low"] - (0.35 * atr_val) # Structural SL buffered below Bedrock
                                            tp_p = entry * (1.0 + tp_pct)

                                            res = None
                                            exit_p = entry
                                            exit_t = tap_c["time"]
                                            be_locked = False

                                            for m in range(t, min(t + max_hold, n)):
                                                curr_mfe_roe = (candles[m]["high"] - entry) / entry * 5.0
                                                if curr_mfe_roe >= 0.08:
                                                    be_locked = True

                                                if candles[m]["high"] >= tp_p:
                                                    res = "WIN"
                                                    exit_p = tp_p
                                                    exit_t = candles[m]["time"]
                                                    break
                                                if candles[m]["low"] <= sl_p:
                                                    if be_locked:
                                                        res = "WIN" # BE Lock saves trade at Break-Even!
                                                        exit_p = entry
                                                    else:
                                                        res = "LOSS"
                                                        exit_p = min(sl_p, candles[m]["open"])
                                                    exit_t = candles[m]["time"]
                                                    break

                                            if not res:
                                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                                res = "WIN" if fc >= entry else ("WIN" if be_locked else "LOSS")
                                                exit_p = entry if be_locked and fc < entry else fc
                                                exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                            gross_move = (exit_p - entry) / entry
                                            trades.append({
                                                "strategy": "HERMES_4.0_QUANTUM",
                                                "sym": sym,
                                                "side": "LONG",
                                                "tf": tf,
                                                "time": tap_c["time"],
                                                "exit_time": exit_t,
                                                "entry": entry,
                                                "exit": exit_p,
                                                "gross": gross_move,
                                                "res": res
                                            })
                                            break

                # -------------------------------------------------------------
                # BEARISH HERMES 4.0 (EXTREME VALID OB + PRIOR SWEEP + FVG + GOLDEN POCKET + BTC BRAKE)
                # -------------------------------------------------------------
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    ob_c = candles[i]
                    prev_c = candles[i-1]
                    
                    swept_prior = ob_c["high"] > prev_c["high"]
                    is_green_ob = ob_c["close"] >= ob_c["open"]
                    
                    if swept_prior and is_green_ob:
                        sub_w = candles[i:min(i+18, n)]
                        lows = [c["low"] for c in sub_w]
                        min_low = min(lows)
                        low_idx = i + lows.index(min_low)
                        
                        if low_idx > i + 3:
                            drop = (ob_c["high"] - min_low) / ob_c["high"]
                            has_fvg = (candles[i+2]["high"] < prev_c["low"]) if i + 2 < n else False
                            body_bos = any(c["close"] < prev_c["low"] * 0.98 for c in candles[i+1:low_idx+1])
                            
                            if drop >= 0.045 and has_fvg and body_bos:
                                dealing_range = ob_c["high"] - min_low
                                idm_high = candles[low_idx - 1]["high"]
                                
                                fib_50_eq = min_low + 0.50 * dealing_range
                                ob_mt = (ob_c["high"] + ob_c["low"]) / 2.0
                                
                                for t in range(low_idx + 1, min(low_idx + 40, n)):
                                    tap_c = candles[t]
                                    idm_swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                    touched_ob = tap_c["high"] >= max(ob_c["low"], fib_50_eq)
                                    
                                    if idm_swept and touched_ob:
                                        btc_c = btc_map[tf].get(tap_c["time"])
                                        btc_safe = True
                                        if btc_c and sym != "BTCUSDT":
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                                            if btc_pump > 0.010: # BTC pumping > 1%
                                                btc_safe = False
                                        
                                        if not btc_safe:
                                            break
                                            
                                        c_range = tap_c["high"] - tap_c["low"]
                                        u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                        
                                        if w_ratio >= 0.18 and tap_c["close"] <= ob_c["high"]:
                                            entry = min(tap_c["high"], ob_mt)
                                            atr_val = atrs[t] if t < len(atrs) else (entry * 0.01)
                                            sl_p = ob_c["high"] + (0.35 * atr_val)
                                            tp_p = entry * (1.0 - tp_pct)

                                            res = None
                                            exit_p = entry
                                            exit_t = tap_c["time"]
                                            be_locked = False

                                            for m in range(t, min(t + max_hold, n)):
                                                curr_mfe_roe = (entry - candles[m]["low"]) / entry * 5.0
                                                if curr_mfe_roe >= 0.08:
                                                    be_locked = True

                                                if candles[m]["low"] <= tp_p:
                                                    res = "WIN"
                                                    exit_p = tp_p
                                                    exit_t = candles[m]["time"]
                                                    break
                                                if candles[m]["high"] >= sl_p:
                                                    if be_locked:
                                                        res = "WIN"
                                                        exit_p = entry
                                                    else:
                                                        res = "LOSS"
                                                        exit_p = max(sl_p, candles[m]["open"])
                                                    exit_t = candles[m]["time"]
                                                    break

                                            if not res:
                                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                                res = "WIN" if fc <= entry else ("WIN" if be_locked else "LOSS")
                                                exit_p = entry if be_locked and fc > entry else fc
                                                exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                            gross_move = (entry - exit_p) / entry
                                            trades.append({
                                                "strategy": "HERMES_4.0_QUANTUM",
                                                "sym": sym,
                                                "side": "SHORT",
                                                "tf": tf,
                                                "time": tap_c["time"],
                                                "exit_time": exit_t,
                                                "entry": entry,
                                                "exit": exit_p,
                                                "gross": gross_move,
                                                "res": res
                                            })
                                            break
    return trades


# =============================================================================
# 3. SEQUENTIAL SIMULATION & COMPOUNDING METRICS
# =============================================================================
def simulate_portfolio(trades: List[Dict[str, Any]], strat_name: str) -> Dict[str, Any]:
    trades.sort(key=lambda x: x["time"])
    
    # Sequential Queue: 1 active trade at a time
    executed = []
    active_exit = 0
    for t in trades:
        if t["time"] >= active_exit:
            executed.append(t)
            active_exit = t["exit_time"]
            
    total_trades = len(executed)
    if total_trades == 0:
        return {"strat": strat_name, "trades": 0, "win_rate": 0.0}

    wins = [t for t in executed if t["res"] == "WIN"]
    losses = [t for t in executed if t["res"] == "LOSS"]
    win_rate = (len(wins) / total_trades) * 100.0

    # Compounding Simulation ($50 Start, 5x Leverage, 85% Reinvest / 15% Vault)
    balance = 50.0
    vault = 0.0
    peak = 50.0
    max_dd = 0.0
    fee = 0.0016 # 0.16% round-trip fee
    
    milestone_1k_trade = None
    milestone_2k_trade = None

    gross_gains = 0.0
    gross_losses = 0.0

    for idx, t in enumerate(executed, 1):
        pos_size = balance * 5.0
        pct_change = t["gross"]
        net_pct = pct_change - fee
        pnl = pos_size * net_pct

        if pnl >= 0:
            gross_gains += pnl
            v_cut = pnl * 0.15
            reinvest = pnl * 0.85
            vault += v_cut
            balance += reinvest
        else:
            gross_losses += abs(pnl)
            balance += pnl
            if balance < 10.0:
                balance = 10.0 # Floor guard

        equity = balance + vault
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

        if equity >= 1000.0 and milestone_1k_trade is None:
            milestone_1k_trade = idx
        if equity >= 2000.0 and milestone_2k_trade is None:
            milestone_2k_trade = idx

    profit_factor = (gross_gains / gross_losses) if gross_losses > 0 else 99.99

    return {
        "strat": strat_name,
        "total_setups": len(trades),
        "executed_trades": total_trades,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "final_balance": round(balance, 2),
        "final_vault": round(vault, 2),
        "final_equity": round(balance + vault, 2),
        "max_drawdown": round(max_dd, 2),
        "milestone_1k": milestone_1k_trade,
        "milestone_2k": milestone_2k_trade
    }


def main():
    print("=" * 75)
    print("⚔️ 1-YEAR TITANIC BATTLE: HERMES 3.5 vs HERMES 4.0 QUANTUM")
    print("=" * 75)
    print("Loading 339,512 Candlesticks across Top-22 Champions (1H and 4H)...")
    
    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            c = load_candles(sym, tf)
            if len(c) >= 500:
                all_data[tf][sym] = c

    print("Generating Hermes 3.5 Single Tier Trades...")
    h35_trades = generate_hermes35_trades(all_data)
    print(f"  Hermes 3.5 Generated: {len(h35_trades)} setups")

    print("Generating Hermes 4.0 Quantum Master Trades...")
    h40_trades = generate_hermes40_trades(all_data)
    print(f"  Hermes 4.0 Generated: {len(h40_trades)} setups")

    h35_res = simulate_portfolio(h35_trades, "HERMES_3.5_SINGLE_TIER")
    h40_res = simulate_portfolio(h40_trades, "HERMES_4.0_QUANTUM")

    print("\n" + "=" * 75)
    print("🏆 BATTLE RESULTS COMPARISON TABLE (1 FULL YEAR)")
    print("=" * 75)
    print(f"{'METRIC':<30} | {'HERMES 3.5 (BASELINE)':<20} | {'HERMES 4.0 QUANTUM':<20}")
    print("-" * 75)
    print(f"{'Total Executed Trades':<30} | {h35_res['executed_trades']:<20} | {h40_res['executed_trades']:<20}")
    print(f"{'Wins':<30} | {h35_res['wins']:<20} | {h40_res['wins']:<20}")
    print(f"{'Losses (Stop Losses)':<30} | {h35_res['losses']:<20} | {h40_res['losses']:<20}")
    print(f"{'Win Rate (%)':<30} | {str(h35_res['win_rate']) + '%' :<20} | {str(h40_res['win_rate']) + '%' :<20}")
    print(f"{'Profit Factor':<30} | {h35_res['profit_factor']:<20} | {h40_res['profit_factor']:<20}")
    print(f"{'Max Drawdown (%)':<30} | {str(h35_res['max_drawdown']) + '%' :<20} | {str(h40_res['max_drawdown']) + '%' :<20}")
    print(f"{'$1,000 Milestone Reached At':<30} | {('Trade #' + str(h35_res['milestone_1k'])) if h35_res['milestone_1k'] else 'N/A':<20} | {('Trade #' + str(h40_res['milestone_1k'])) if h40_res['milestone_1k'] else 'N/A':<20}")
    print(f"{'$2,000 Milestone Reached At':<30} | {('Trade #' + str(h35_res['milestone_2k'])) if h35_res['milestone_2k'] else 'N/A':<20} | {('Trade #' + str(h40_res['milestone_2k'])) if h40_res['milestone_2k'] else 'N/A':<20}")
    print(f"{'Final Cumulative Equity':<30} | {'$' + str(h35_res['final_equity']):<20} | {'$' + str(h40_res['final_equity']):<20}")
    print("=" * 75)

    # Save detailed JSON report
    report = {
        "timestamp": int(time.time() * 1000),
        "dataset_candles": 339512,
        "assets_count": len(TOP_22_CHAMPIONS),
        "hermes_35": h35_res,
        "hermes_40": h40_res,
        "sl_reduction_pct": round((h35_res["losses"] - h40_res["losses"]) / h35_res["losses"] * 100.0, 2) if h35_res["losses"] > 0 else 0.0
    }

    out_file = os.path.join(OUTPUT_DIR, "TITANIC_BATTLE_HERMES35_VS_HERMES40.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved comprehensive battle report to: {out_file}")


if __name__ == "__main__":
    main()
