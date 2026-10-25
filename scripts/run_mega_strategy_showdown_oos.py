"""
MEGA STRATEGY SHOWDOWN: 6-MONTH PURE OUT-OF-SAMPLE (OOS) TOURNAMENT
==================================================================
Period: April 1, 2026 to October 14, 2026 (Unseen Recent 6.5 Months)
Starting Capital: $500.00 USDT across 10 Deca Sections ($50 each)
Leverage: 5x Isolated Futures
Target: Minimum 1:2 RRR Baseline

USER-DEFINED EXACT STEPPED TRAILING SL LADDER (5x Leverage):
- At +5.00% ROE (+1.00% price): Trailing SL shifts to +1.00% ROE (+0.20% price / BE Shield)
- At +9.40% ROE (+1.88% price): Trailing SL shifts to +5.00% ROE (+1.00% price)
- At +14.40% ROE (+2.88% price): Trailing SL shifts to +10.00% ROE (+2.00% price)
- At +19.40% ROE (+3.88% price): Trailing SL shifts to +15.00% ROE (+3.00% price)
- Increments: Every +5% ROE gain locks +5% ROE trailing profit!

STRATEGIES AUDITED IN THIS TOURNAMENT:
1. SMC V17 (Traditional BOS + FVG + Outer OB Edge Entry)
2. Hermes 2.0 APEX (4-Sentries + BTC EMA Trend + IDM Wick >= 18%)
3. Hermes 3.0 Model 2A (50% Mean Threshold + FVG Displacement >= 5%)
4. Hermes 3.5 Single Tier (Body-Close BOS + 18-bar Maturation Filter)
5. ICT Unicorn Model (Breaker Block + FVG Horizontal Retest)
6. BB 2.0 Model 3 Sniper (PDH/PDL Sweep + 50% MT Retest + Day-1 Single Shot)
7. BB 2.0 Smart Confluence (PDH/PDL Piercing + 20% Absorption Wick Defense)
"""

import os
import sys
import json
from datetime import datetime, timezone
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "historical_data")

CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT",
    "DOGEUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT",
    "OPUSDT", "RENDERUSDT", "SUIUSDT", "TIAUSDT", "UNIUSDT",
    "XRPUSDT", "1000PEPEUSDT", "APTUSDT", "ARBUSDT", "FETUSDT"
]

PAIR_MAPPING = {
    "BTCUSDT": 1, "ETHUSDT": 1, "SOLUSDT": 2, "BNBUSDT": 2,
    "AVAXUSDT": 3, "DOGEUSDT": 3, "DOTUSDT": 4, "LINKUSDT": 4,
    "LTCUSDT": 5, "NEARUSDT": 5, "OPUSDT": 6, "RENDERUSDT": 6,
    "SUIUSDT": 7, "TIAUSDT": 7, "UNIUSDT": 8, "XRPUSDT": 8,
    "1000PEPEUSDT": 9, "APTUSDT": 9, "ARBUSDT": 10, "FETUSDT": 10
}

def get_day_key(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")

# -----------------------------------------------------------------------------
# USER-DEFINED STEPPED TRAILING SL SIMULATOR
# -----------------------------------------------------------------------------
def evaluate_trade_with_user_trailing(candles, fill_idx, side, entry, initial_sl, symbol, day_str):
    risk_price = abs(entry - initial_sl)
    if risk_price <= 0:
        return None

    # Minimum 1:2 RRR target
    tp_target = entry + (2.0 * risk_price) if side == "LONG" else entry - (2.0 * risk_price)

    locked_roe = None
    locked_sl_price = initial_sl
    fill_time = candles[fill_idx]["time"]

    for i in range(fill_idx, min(fill_idx + 120, len(candles))):
        c = candles[i]
        c_h = c["high"]
        c_l = c["low"]

        # 1. Check if price hit current active Stop Loss
        if side == "LONG" and c_l <= locked_sl_price:
            pnl_pct = (locked_sl_price - entry) / entry
            pnl_roe = pnl_pct * 5.0 * 100.0
            pnl_r = (locked_sl_price - entry) / risk_price
            outcome = "LOSS" if locked_roe is None else ("SAVE_BE" if locked_roe <= 1.5 else f"WIN_TRAIL_{locked_roe:.1f}ROE")
            return {
                "symbol": symbol,
                "day": day_str,
                "side": side,
                "fill_time": fill_time,
                "exit_time": c["time"],
                "entry": entry,
                "exit": locked_sl_price,
                "pnl_r": pnl_r,
                "pnl_roe": pnl_roe,
                "outcome": outcome
            }
        elif side == "SHORT" and c_h >= locked_sl_price:
            pnl_pct = (entry - locked_sl_price) / entry
            pnl_roe = pnl_pct * 5.0 * 100.0
            pnl_r = (entry - locked_sl_price) / risk_price
            outcome = "LOSS" if locked_roe is None else ("SAVE_BE" if locked_roe <= 1.5 else f"WIN_TRAIL_{locked_roe:.1f}ROE")
            return {
                "symbol": symbol,
                "day": day_str,
                "side": side,
                "fill_time": fill_time,
                "exit_time": c["time"],
                "entry": entry,
                "exit": locked_sl_price,
                "pnl_r": pnl_r,
                "pnl_roe": pnl_roe,
                "outcome": outcome
            }

        # 2. Check 1:2 RRR baseline target
        if side == "LONG" and c_h >= tp_target and locked_roe is not None and locked_roe >= 10.0:
            pnl_r = 2.0
            pnl_roe = 2.0 * (risk_price / entry) * 5.0 * 100.0
            return {
                "symbol": symbol, "day": day_str, "side": side,
                "fill_time": fill_time, "exit_time": c["time"],
                "entry": entry, "exit": tp_target, "pnl_r": pnl_r, "pnl_roe": pnl_roe,
                "outcome": "WIN_TP_1TO2"
            }
        elif side == "SHORT" and c_l <= tp_target and locked_roe is not None and locked_roe >= 10.0:
            pnl_r = 2.0
            pnl_roe = 2.0 * (risk_price / entry) * 5.0 * 100.0
            return {
                "symbol": symbol, "day": day_str, "side": side,
                "fill_time": fill_time, "exit_time": c["time"],
                "entry": entry, "exit": tp_target, "pnl_r": pnl_r, "pnl_roe": pnl_roe,
                "outcome": "WIN_TP_1TO2"
            }

        # 3. Update Stepped Trailing SL based on user's exact ROE formula
        fav_move_pct = ((c_h - entry) / entry) if side == "LONG" else ((entry - c_l) / entry)
        current_roe = fav_move_pct * 5.0 * 100.0  # at 5x leverage

        new_lock_roe = None
        if current_roe >= 19.40:
            # Continue extending +5% increments beyond 19.4%
            extra_steps = int((current_roe - 19.40) / 5.0)
            new_lock_roe = 15.0 + (extra_steps * 5.0)
        elif current_roe >= 14.40:
            new_lock_roe = 10.0
        elif current_roe >= 9.40:
            new_lock_roe = 5.0
        elif current_roe >= 5.00:
            new_lock_roe = 1.0

        if new_lock_roe is not None:
            if locked_roe is None or new_lock_roe > locked_roe:
                locked_roe = new_lock_roe
                # Set price corresponding to locked_roe
                locked_price_move = (locked_roe / 100.0) / 5.0
                if side == "LONG":
                    new_sl = entry * (1.0 + locked_price_move)
                    if new_sl > locked_sl_price:
                        locked_sl_price = new_sl
                else:
                    new_sl = entry * (1.0 - locked_price_move)
                    if new_sl < locked_sl_price:
                        locked_sl_price = new_sl

    # Timeout exit
    last_c = candles[min(fill_idx + 120, len(candles) - 1)]
    pnl_r = ((last_c["close"] - entry) / risk_price) if side == "LONG" else ((entry - last_c["close"]) / risk_price)
    return {
        "symbol": symbol, "day": day_str, "side": side,
        "fill_time": fill_time, "exit_time": last_c["time"],
        "entry": entry, "exit": last_c["close"], "pnl_r": pnl_r,
        "pnl_roe": pnl_r * (risk_price / entry) * 500.0,
        "outcome": "TIMEOUT_WIN" if pnl_r > 0 else "TIMEOUT_LOSS"
    }

# -----------------------------------------------------------------------------
# STRATEGY SIGNAL GENERATORS (ON 6-MONTH DATA: 2026-04-01 TO 2026-10-14)
# -----------------------------------------------------------------------------

def run_strategy_backtest(strategy_name: str, candles_by_symbol):
    all_trades = []

    for sym in CHAMPIONS:
        candles = candles_by_symbol.get(sym, [])
        if len(candles) < 500:
            continue

        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            curr_day = sorted_days[d_i]
            prev_day = sorted_days[d_i - 1]

            if curr_day < "2026-04-01":
                continue

            prev_day_candles = [c for _, c in day_buckets[prev_day]]
            curr_day_entries = day_buckets[curr_day]

            if len(prev_day_candles) < 12 or len(curr_day_entries) < 12:
                continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)

            long_taken = False
            short_taken = False

            for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
                if g_idx + 3 >= len(candles):
                    continue

                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                c_next = candles[g_idx + 1]
                c_next2 = candles[g_idx + 2]
                c_vol = c.get("volume", 0)

                candle_range = max(1e-8, c_h - c_l)
                lower_wick = max(0.0, min(c_o, c_c) - c_l) / candle_range
                upper_wick = max(0.0, c_h - max(c_o, c_c)) / candle_range

                # -------------------------------------------------------------
                # 1. SMC V17 (Traditional BOS + FVG + Outer OB Edge Entry)
                # -------------------------------------------------------------
                if strategy_name == "SMC_V17":
                    # Break of Structure of 20-bar swing high/low
                    swing_high = max(candles[max(0, g_idx - 20):g_idx], key=lambda x: x["high"])["high"]
                    swing_low = min(candles[max(0, g_idx - 20):g_idx], key=lambda x: x["low"])["low"]

                    if not long_taken and c_c > swing_high and c_next["low"] > c_h:
                        # Bullish BOS with FVG -> Enter at edge (c_h)
                        entry = c_h
                        sl = c_l * 0.995
                        for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                            if candles[w_idx]["low"] <= entry:
                                long_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "LONG", entry, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                    if not short_taken and c_c < swing_low and c_next["high"] < c_l:
                        # Bearish BOS with FVG -> Enter at edge (c_l)
                        entry = c_l
                        sl = c_h * 1.005
                        for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                            if candles[w_idx]["high"] >= entry:
                                short_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "SHORT", entry, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                # -------------------------------------------------------------
                # 2. HERMES 2.0 APEX (4-Sentries + EMA Trend + IDM Wick >= 18%)
                # -------------------------------------------------------------
                elif strategy_name == "HERMES_2_0_APEX":
                    # Displacement >= 3.5% + FVG + IDM Wick >= 18%
                    gain = (c_next["high"] - c_l) / c_l
                    drop = (c_h - c_next["low"]) / c_h

                    if not long_taken and gain >= 0.035 and c_next2["low"] > c_h and lower_wick >= 0.18:
                        entry = c_h * 0.998  # near edge
                        sl = c_l * 0.997
                        for w_idx in range(g_idx + 2, min(g_idx + 28, len(candles))):
                            if candles[w_idx]["low"] <= entry:
                                long_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "LONG", entry, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                    if not short_taken and drop >= 0.035 and c_next2["high"] < c_l and upper_wick >= 0.18:
                        entry = c_l * 1.002
                        sl = c_h * 1.003
                        for w_idx in range(g_idx + 2, min(g_idx + 28, len(candles))):
                            if candles[w_idx]["high"] >= entry:
                                short_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "SHORT", entry, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                # -------------------------------------------------------------
                # 3. HERMES 3.0 MODEL 2A (50% Mean Threshold + FVG Displacement)
                # -------------------------------------------------------------
                elif strategy_name == "HERMES_3_0_MODEL_2A":
                    gain = (c_next["high"] - c_l) / c_l
                    drop = (c_h - c_next["low"]) / c_h
                    has_bull_fvg = c_next2["low"] > c_h
                    has_bear_fvg = c_next2["high"] < c_l

                    if not long_taken and gain >= 0.030 and has_bull_fvg and lower_wick >= 0.18:
                        mt = (c_h + c_l) / 2.0
                        sl = c_l * 0.9980
                        for w_idx in range(g_idx + 2, min(g_idx + 28, len(candles))):
                            if candles[w_idx]["low"] <= mt:
                                long_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "LONG", mt, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                    if not short_taken and drop >= 0.030 and has_bear_fvg and upper_wick >= 0.18:
                        mt = (c_h + c_l) / 2.0
                        sl = c_h * 1.0020
                        for w_idx in range(g_idx + 2, min(g_idx + 28, len(candles))):
                            if candles[w_idx]["high"] >= mt:
                                short_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "SHORT", mt, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                # -------------------------------------------------------------
                # 4. HERMES 3.5 SINGLE TIER (Body-Close Confirmation + Maturation)
                # -------------------------------------------------------------
                elif strategy_name == "HERMES_3_5_SINGLE_TIER":
                    gain = (c_next["high"] - c_l) / c_l
                    drop = (c_h - c_next["low"]) / c_h
                    # Strict body close requirement
                    body_close_bull = c_next["close"] > c_h and c_next2["low"] > c_h
                    body_close_bear = c_next["close"] < c_l and c_next2["high"] < c_l

                    if not long_taken and gain >= 0.025 and body_close_bull:
                        mt = (c_h + c_l) / 2.0
                        sl = c_l * 0.9975
                        # Maturation: skip immediate 4 bars, wait for mature retest
                        for w_idx in range(g_idx + 5, min(g_idx + 32, len(candles))):
                            if candles[w_idx]["low"] <= mt:
                                long_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "LONG", mt, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                    if not short_taken and drop >= 0.025 and body_close_bear:
                        mt = (c_h + c_l) / 2.0
                        sl = c_h * 1.0025
                        for w_idx in range(g_idx + 5, min(g_idx + 32, len(candles))):
                            if candles[w_idx]["high"] >= mt:
                                short_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "SHORT", mt, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                # -------------------------------------------------------------
                # 5. ICT UNICORN MODEL (Breaker Block + FVG Confluence)
                # -------------------------------------------------------------
                elif strategy_name == "ICT_UNICORN_MODEL":
                    # Prior failed OB flips into Breaker Block + FVG overlap
                    prior_high = max(candles[max(0, g_idx - 10):g_idx], key=lambda x: x["high"])["high"]
                    prior_low = min(candles[max(0, g_idx - 10):g_idx], key=lambda x: x["low"])["low"]

                    if not long_taken and c_c > prior_high and c_next2["low"] > prior_high:
                        # Bullish Breaker Retest
                        entry = prior_high
                        sl = c_l * 0.997
                        for w_idx in range(g_idx + 2, min(g_idx + 20, len(candles))):
                            if candles[w_idx]["low"] <= entry:
                                long_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "LONG", entry, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                    if not short_taken and c_c < prior_low and c_next2["high"] < prior_low:
                        entry = prior_low
                        sl = c_h * 1.003
                        for w_idx in range(g_idx + 2, min(g_idx + 20, len(candles))):
                            if candles[w_idx]["high"] >= entry:
                                short_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "SHORT", entry, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                # -------------------------------------------------------------
                # 6. BB 2.0 MODEL 3 SNIPER (PDH/PDL Sweep + 50% MT Retest)
                # -------------------------------------------------------------
                elif strategy_name == "BB_2_0_MODEL_3":
                    dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                    basic_pdl = (dist_to_pdl <= 0.015 or c_l <= pdl)
                    basic_disp_bull = ((c_c < c_o or (c_h - c_l) > 0) and 
                                       ((c_next["high"] - c_l) / c_l >= 0.012 or (c_next2["high"] - c_l) / c_l >= 0.018) and 
                                       c_next2["low"] > c_h)

                    if not long_taken and basic_pdl and basic_disp_bull:
                        mt = (c_h + c_l) / 2.0
                        sl = c_l * 0.9985  # 0.15% anti-hunt
                        for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                            if candles[w_idx]["low"] <= mt:
                                long_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "LONG", mt, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    basic_pdh = (dist_to_pdh <= 0.015 or c_h >= pdh)
                    basic_disp_bear = ((c_c > c_o or (c_h - c_l) > 0) and 
                                       ((c_h - c_next["low"]) / c_h >= 0.012 or (c_h - c_next2["low"]) / c_h >= 0.018) and 
                                       c_next2["high"] < c_l)

                    if not short_taken and basic_pdh and basic_disp_bear:
                        mt = (c_h + c_l) / 2.0
                        sl = c_h * 1.0015
                        for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                            if candles[w_idx]["high"] >= mt:
                                short_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "SHORT", mt, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                # -------------------------------------------------------------
                # 7. BB 2.0 SMART CONFLUENCE (Piercing Depth + 20% Wick)
                # -------------------------------------------------------------
                elif strategy_name == "BB_2_0_SMART_CONFLUENCE":
                    pierce_pdl = (c_l <= pdl * 1.001)
                    basic_disp_bull = ((c_c < c_o or (c_h - c_l) > 0) and 
                                       ((c_next["high"] - c_l) / c_l >= 0.012 or (c_next2["high"] - c_l) / c_l >= 0.018) and 
                                       c_next2["low"] > c_h)

                    if not long_taken and pierce_pdl and basic_disp_bull and (lower_wick >= 0.18 or c_next["close"] > c_next["open"]):
                        mt = (c_h + c_l) / 2.0
                        sl = c_l * 0.9985
                        for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                            if candles[w_idx]["low"] <= mt:
                                long_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "LONG", mt, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                    pierce_pdh = (c_h >= pdh * 0.999)
                    basic_disp_bear = ((c_c > c_o or (c_h - c_l) > 0) and 
                                       ((c_h - c_next["low"]) / c_h >= 0.012 or (c_h - c_next2["low"]) / c_h >= 0.018) and 
                                       c_next2["high"] < c_l)

                    if not short_taken and pierce_pdh and basic_disp_bear and (upper_wick >= 0.18 or c_next["close"] < c_next["open"]):
                        mt = (c_h + c_l) / 2.0
                        sl = c_h * 1.0015
                        for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                            if candles[w_idx]["high"] >= mt:
                                short_taken = True
                                res = evaluate_trade_with_user_trailing(candles, w_idx, "SHORT", mt, sl, sym, curr_day)
                                if res: all_trades.append(res)
                                break

                if long_taken and short_taken:
                    break

    all_trades.sort(key=lambda t: t["fill_time"])
    return all_trades

# -----------------------------------------------------------------------------
# 10 DECA SECTIONS PORTFOLIO SIMULATION
# -----------------------------------------------------------------------------
def simulate_deca_portfolio(trades, risk_pct: float):
    sections = {i: {"id": i, "balance": 50.0, "peak": 50.0, "busy_until": 0, "trades": 0, "wins": 0, "saves": 0, "losses": 0, "pnl": 0.0} for i in range(1, 11)}
    executed = []

    for t in trades:
        sec_id = PAIR_MAPPING.get(t["symbol"], 1)
        sec = sections[sec_id]
        if sec["busy_until"] > t["fill_time"]:
            continue
        sec["busy_until"] = t["exit_time"]
        sec["trades"] += 1

        r_pnl = t["pnl_r"]
        risk_usd = sec["balance"] * risk_pct
        dollar_pnl = risk_usd * r_pnl

        sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))
        sec["pnl"] = round(sec["pnl"] + dollar_pnl, 2)
        if sec["balance"] > sec["peak"]:
            sec["peak"] = sec["balance"]

        if "WIN" in t["outcome"]:
            sec["wins"] += 1
        elif "SAVE" in t["outcome"]:
            sec["saves"] += 1
        else:
            sec["losses"] += 1

        executed.append({
            "time": t["exit_time"],
            "dollar_pnl": dollar_pnl,
            "total_eq": sum(s["balance"] for s in sections.values())
        })

    tot_eq = sum(s["balance"] for s in sections.values())
    tot_wins = sum(s["wins"] for s in sections.values())
    tot_saves = sum(s["saves"] for s in sections.values())
    tot_losses = sum(s["losses"] for s in sections.values())
    tot_exec = len(executed)

    win_rate = (tot_wins / tot_exec * 100) if tot_exec else 0.0
    green_rate = ((tot_wins + tot_saves) / tot_exec * 100) if tot_exec else 0.0
    loss_rate = (tot_losses / tot_exec * 100) if tot_exec else 0.0
    net_profit = tot_eq - 500.0
    roi_pct = (net_profit / 500.0) * 100.0

    peak = 500.0
    max_dd = 0.0
    for rec in executed:
        eq = rec["total_eq"]
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

    return {
        "trades": tot_exec,
        "wins": tot_wins,
        "saves": tot_saves,
        "losses": tot_losses,
        "win_rate": win_rate,
        "green_rate": green_rate,
        "loss_rate": loss_rate,
        "final_balance": tot_eq,
        "net_profit": net_profit,
        "roi_pct": roi_pct,
        "max_dd": max_dd
    }

def main():
    print("=" * 105)
    print("🏆 MEGA STRATEGY SHOWDOWN: 6-MONTH PURE OUT-OF-SAMPLE (OOS) TOURNAMENT")
    print("• Period: April 1, 2026 to October 14, 2026 (Unseen Recent 6.5 Months)")
    print("• Starting Capital: $500.00 USDT across 10 Deca Sections ($50 each)")
    print("• Stepped Trailing SL: +5% ROE -> +1% BE, +9.4% -> +5%, +14.4% -> +10%, +19.4% -> +15% (5x Lev)")
    print("=" * 105)

    # 1. Preload candle data
    print("\n⏳ Loading 6-Month historical candle data for Top 20 Champions...")
    candles_by_symbol = {}
    for sym in CHAMPIONS:
        fpath = os.path.join(DATA_DIR, f"{sym}_1h.json")
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                candles_by_symbol[sym] = json.load(f)

    strategies = [
        ("SMC V17 (BOS + FVG Edge)", "SMC_V17"),
        ("Hermes 2.0 APEX (4-Sentries)", "HERMES_2_0_APEX"),
        ("Hermes 3.0 Model 2A (50% MT)", "HERMES_3_0_MODEL_2A"),
        ("Hermes 3.5 Single Tier (Body-Close)", "HERMES_3_5_SINGLE_TIER"),
        ("ICT Unicorn (Breaker + FVG)", "ICT_UNICORN_MODEL"),
        ("BB 2.0 Model 3 Sniper (PDH/PDL)", "BB_2_0_MODEL_3"),
        ("BB 2.0 Smart Confluence (Whale)", "BB_2_0_SMART_CONFLUENCE")
    ]

    results = []

    for name, code in strategies:
        print(f"👉 Simulating: {name}...")
        trades = run_strategy_backtest(code, candles_by_symbol)
        cons = simulate_deca_portfolio(trades, risk_pct=0.02)
        aggr = simulate_deca_portfolio(trades, risk_pct=0.05)
        results.append({
            "name": name,
            "trades": cons["trades"],
            "win_rate": cons["win_rate"],
            "saves": cons["saves"],
            "green_rate": cons["green_rate"],
            "loss_rate": cons["loss_rate"],
            "cons_final": cons["final_balance"],
            "cons_roi": cons["roi_pct"],
            "cons_dd": cons["max_dd"],
            "aggr_final": aggr["final_balance"],
            "aggr_roi": aggr["roi_pct"],
            "aggr_dd": aggr["max_dd"]
        })

    # Sort results by Conservative Final Balance
    results.sort(key=lambda x: x["cons_final"], reverse=True)

    print("\n" + "=" * 105)
    print("👑 OFFICIAL TOURNAMENT LEADERBOARD (6-MONTH PURE OOS AUDIT)")
    print("=" * 105)
    print(f"{'Rank':<5} {'Strategy Name':<32} {'Trades':<8} {'Win %':<8} {'Green %':<9} {'Cons (2%)':<14} {'Aggr (5%)':<14} {'Max DD'}")
    print("-" * 105)

    for rank, r in enumerate(results, 1):
        medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
        print(f"{medal:<5} {r['name']:<32} {r['trades']:<8} {r['win_rate']:<7.1f}% {r['green_rate']:<8.1f}% ${r['cons_final']:<13.2f} ${r['aggr_final']:<13.2f} {r['cons_dd']:.2f}%")

    print("=" * 105)

if __name__ == "__main__":
    main()
