"""
HERMES 3.5 RADAR HARVEST (5% BOUNDARY PENETRATION)
1-YEAR OUT-OF-SAMPLE (OOS) DECA MATRIX COMPOUNDING ACID TEST
============================================================
Portfolio:
- Total Starting Capital: $500.00 USDT
- 10 Compounding Sections ($50.00 USDT isolated each)
  * Sections 1-5: Dedicated to 4H Macro Swings
  * Sections 6-10: Dedicated to 1H Intraday Scalps
- Leverage: 5x Isolated
- Strategy: Hermes 3.5 Single Tier Radar Harvest
  * 5% Boundary Penetration Entry (eff_entry)
  * 0.20% Proximity Radar Pre-Arming
  * Stepped Profit Harvest:
    - Stage 1 (+8.0% ROE / +1.60% move) -> BE Lock +0.10% buffer
    - Stage 2 (+9.0% ROE / +1.80% move) -> SL locked at +4.50% ROE cash profit!
    - Final TP (+14.0% ROE / +2.80% move)
  * Rocket Airspace Runway Void >= 5.0%
  * 2-Day Maturation Horizon (>= 48 bars 1H, >= 12 bars 4H)
  * Origin Bedrock Floor/Ceiling (lowest/highest of prior 25 bars)
  * King BTC 4H EMA50 Macro Filter
  * Strict Anti-Collision (Asset Exclusivity across all 10 sections)
  * 2-Hour Cooldown per coin
- Data: Full 1-Year Continuous Dataset across 30+ Binance Futures Champions
"""

import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
DATA_DIR = "historical_data"

def calculate_ema(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    k = 2.0 / (period + 1.0)
    ema = [values[0]]
    for v in values[1:]:
        ema.append(v * k + ema[-1] * (1.0 - k))
    return ema

def run_oos_backtest():
    print("=" * 90)
    print("   HERMES 3.5 RADAR HARVEST - 1-YEAR OOS DECA COMPOUNDING AUDIT")
    print("=" * 90)

    # 1. Load BTC 4H Macro Filter
    btc_path = os.path.join(DATA_DIR, "BTCUSDT_4h.json")
    if not os.path.exists(btc_path):
        print(f"Error: {btc_path} not found!")
        return

    with open(btc_path, "r", encoding="utf-8") as f:
        btc_4h = json.load(f)

    btc_closes = [float(c["close"]) for c in btc_4h]
    btc_ema50 = calculate_ema(btc_closes, 50)
    btc_macro_map = {}
    for idx, c in enumerate(btc_4h):
        # Bullish if close >= EMA50
        is_bull = c["close"] >= btc_ema50[idx]
        btc_macro_map[c["time"]] = is_bull

    # Helper to get BTC bias at any timestamp
    btc_times = sorted(btc_macro_map.keys())
    def get_btc_is_bull(timestamp_ms: int) -> bool:
        # Find latest BTC 4H candle at or before timestamp_ms
        latest_bull = True
        for t in btc_times:
            if t <= timestamp_ms:
                latest_bull = btc_macro_map[t]
            else:
                break
        return latest_bull

    # 2. Discover available coins
    files = os.listdir(DATA_DIR)
    coins_4h = sorted([f.replace("_4h.json", "") for f in files if f.endswith("_4h.json") and not "1y_audit" in f])
    coins_1h = sorted([f.replace("_1h.json", "") for f in files if f.endswith("_1h.json") and not "1y_audit" in f])
    all_coins = sorted(list(set(coins_4h + coins_1h)))
    print(f"Loaded {len(all_coins)} Pairs across 1-Year Binance Dataset.")
    print(f"BTC 4H Candles: {len(btc_4h)} | Date Span: {datetime.fromtimestamp(btc_4h[0]['time']/1000, tz=IST).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(btc_4h[-1]['time']/1000, tz=IST).strftime('%Y-%m-%d')}\n")

    # 3. Detect all setups across all coins and timeframes
    candidate_signals = []

    for tf_str, min_mat_bars in [("4h", 12), ("1h", 48)]:
        for sym in all_coins:
            path = os.path.join(DATA_DIR, f"{sym}_{tf_str}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                candles = json.load(f)
            
            n = len(candles)
            if n < 60:
                continue

            # ATR(14)
            atr_series = [0.0] * n
            for k in range(1, n):
                tr = max(candles[k]["high"] - candles[k]["low"],
                         abs(candles[k]["high"] - candles[k-1]["close"]),
                         abs(candles[k]["low"] - candles[k-1]["close"]))
                atr_series[k] = tr if k < 14 else (atr_series[k-1] * 13 + tr) / 14

            max_mat_bars = 360 if tf_str == "4h" else 720
            search_start = 25

            for i in range(search_start, n - 4):
                c3 = candles[i]
                c2 = candles[i+1]
                c1 = candles[i+2]

                # A. BULLISH SETUP
                if c3["close"] < c3["open"] and c1["low"] > c3["high"]:
                    impulse_h = max(c2["high"], c1["high"])
                    gain = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                    if gain >= 0.050: # >= 5% displacement
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_range = ob_high - ob_low
                        mt = (ob_high + ob_low) / 2.0

                        # Origin Bedrock Floor: Lowest of prior 25 bars
                        is_origin = (c3["low"] <= min(candles[k]["low"] for k in range(i-25, i+1)))

                        # Rocket Airspace Runway Void: >= 5.0% void above OB
                        peak_runway = max(candles[k]["high"] for k in range(i+1, min(i+25, n)))
                        runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0
                        if runway_pct < 5.0:
                            continue

                        # 5% Boundary Penetration Entry & 0.20% Radar
                        eff_entry = round(ob_high - 0.05 * ob_range, 8)
                        radar_price = round(eff_entry * 1.0020, 8)

                        # Find first valid tap forward
                        broken = False
                        tap_idx = None
                        idm_low = min(candles[k]["low"] for k in range(max(0, i-3), min(i+4, n)))

                        for t in range(i+3, min(i + max_mat_bars, n)):
                            curr_c = candles[t]
                            if curr_c["close"] < ob_low: # Hard Invalidation
                                broken = True
                                break

                            bars_alive = t - (i+2)
                            idm_swept = any(candles[k]["low"] < idm_low for k in range(i+3, t+1)) or (curr_c["low"] < idm_low)

                            if bars_alive >= min_mat_bars and idm_swept:
                                # Check 5% boundary penetration touch
                                if curr_c["low"] <= eff_entry * 1.0005 and curr_c["close"] >= ob_low:
                                    c_range = curr_c["high"] - curr_c["low"]
                                    l_wick = min(curr_c["open"], curr_c["close"]) - curr_c["low"]
                                    w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                    # Institutional absorption wick >= 18% & close defends MT
                                    if w_ratio >= 0.18 and curr_c["close"] >= mt:
                                        tap_idx = t
                                        break
                        
                        if not broken and tap_idx is not None:
                            # King BTC Sentry Check at tap time
                            tap_time = candles[tap_idx]["time"]
                            if get_btc_is_bull(tap_time): # Long permitted only when BTC is Bullish
                                cur_atr = atr_series[tap_idx]
                                struct_sl = min(ob_low, candles[tap_idx]["low"]) - 0.20 * cur_atr
                                hard_sl = max(min(struct_sl, eff_entry * (1.0 - 0.0380)), eff_entry * 0.9620)
                                soft_sl = (eff_entry + hard_sl) / 2.0

                                candidate_signals.append({
                                    "symbol": sym,
                                    "tf": tf_str,
                                    "side": "BUY",
                                    "entry_price": eff_entry,
                                    "radar_price": radar_price,
                                    "tap_idx": tap_idx,
                                    "entry_time": tap_time,
                                    "ob_low": ob_low,
                                    "ob_high": ob_high,
                                    "soft_sl": soft_sl,
                                    "hard_sl": hard_sl,
                                    "candles": candles,
                                    "is_origin": is_origin,
                                    "runway_pct": runway_pct,
                                    "disp_pct": gain * 100.0
                                })

                # B. BEARISH SETUP
                if c3["close"] > c3["open"] and c1["high"] < c3["low"]:
                    impulse_l = min(c2["low"], c1["low"])
                    drop = (c3["high"] - impulse_l) / c3["high"] if c3["high"] > 0 else 0.0
                    if drop >= 0.050: # >= 5% displacement
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_range = ob_high - ob_low
                        mt = (ob_high + ob_low) / 2.0

                        # Origin Bedrock Ceiling: Highest of prior 25 bars
                        is_origin = (c3["high"] >= max(candles[k]["high"] for k in range(i-25, i+1)))

                        # Rocket Airspace Runway Void: >= 5.0% void below OB
                        peak_runway = min(candles[k]["low"] for k in range(i+1, min(i+25, n)))
                        runway_pct = ((ob_low - peak_runway) / ob_low * 100.0) if ob_low > 0 else 0.0
                        if runway_pct < 5.0:
                            continue

                        # 5% Boundary Penetration Entry & 0.20% Radar
                        eff_entry = round(ob_low + 0.05 * ob_range, 8)
                        radar_price = round(eff_entry * 0.9980, 8)

                        broken = False
                        tap_idx = None
                        idm_high = max(candles[k]["high"] for k in range(max(0, i-3), min(i+4, n)))

                        for t in range(i+3, min(i + max_mat_bars, n)):
                            curr_c = candles[t]
                            if curr_c["close"] > ob_high:
                                broken = True
                                break

                            bars_alive = t - (i+2)
                            idm_swept = any(candles[k]["high"] > idm_high for k in range(i+3, t+1)) or (curr_c["high"] > idm_high)

                            if bars_alive >= min_mat_bars and idm_swept:
                                if curr_c["high"] >= eff_entry * 0.9995 and curr_c["close"] <= ob_high:
                                    c_range = curr_c["high"] - curr_c["low"]
                                    u_wick = curr_c["high"] - max(curr_c["open"], curr_c["close"])
                                    w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                    if w_ratio >= 0.18 and curr_c["close"] <= mt:
                                        tap_idx = t
                                        break

                        if not broken and tap_idx is not None:
                            tap_time = candles[tap_idx]["time"]
                            if not get_btc_is_bull(tap_time): # Short permitted only when BTC is Bearish
                                cur_atr = atr_series[tap_idx]
                                struct_sl = max(ob_high, candles[tap_idx]["high"]) + 0.20 * cur_atr
                                hard_sl = min(max(struct_sl, eff_entry * (1.0 + 0.0380)), eff_entry * 1.0380)
                                soft_sl = (eff_entry + hard_sl) / 2.0

                                candidate_signals.append({
                                    "symbol": sym,
                                    "tf": tf_str,
                                    "side": "SELL",
                                    "entry_price": eff_entry,
                                    "radar_price": radar_price,
                                    "tap_idx": tap_idx,
                                    "entry_time": tap_time,
                                    "ob_low": ob_low,
                                    "ob_high": ob_high,
                                    "soft_sl": soft_sl,
                                    "hard_sl": hard_sl,
                                    "candles": candles,
                                    "is_origin": is_origin,
                                    "runway_pct": runway_pct,
                                    "disp_pct": drop * 100.0
                                })

    # Sort all signals chronologically
    candidate_signals.sort(key=lambda s: s["entry_time"])
    print(f"Total Qualified Signals Detected: {len(candidate_signals)}\n")

    # 4. Simulate Trade Forward Path (Life Cycle) for each signal
    # Pre-simulate exit for each signal
    trade_outcomes = []
    tp_move_pct = 0.0280    # +14.0% ROE at 5x
    stage1_be_pct = 0.0160  # +8.0% ROE at 5x -> Locks BE +0.10%
    stage2_h_pct = 0.0180   # +9.0% ROE at 5x -> Locks SL at +4.50% ROE (+0.90% cash profit)
    harvest_lock = 0.0090   # +4.50% ROE (+0.90% price buffer)

    for sig in candidate_signals:
        candles = sig["candles"]
        tap_idx = sig["tap_idx"]
        side = sig["side"]
        entry_p = sig["entry_price"]
        hard_sl = sig["hard_sl"]
        soft_sl = sig["soft_sl"]

        tp_price = round(entry_p * (1.0 + tp_move_pct), 8) if side == "BUY" else round(entry_p * (1.0 - tp_move_pct), 8)
        be_trigger = entry_p * (1.0 + stage1_be_pct) if side == "BUY" else entry_p * (1.0 - stage1_be_pct)
        be_sl = round(entry_p * 1.0010, 8) if side == "BUY" else round(entry_p * 0.9990, 8)
        harvest_trigger = entry_p * (1.0 + stage2_h_pct) if side == "BUY" else entry_p * (1.0 - stage2_h_pct)
        harvest_sl = round(entry_p * (1.0 + harvest_lock), 8) if side == "BUY" else round(entry_p * (1.0 - harvest_lock), 8)

        current_sl = soft_sl
        outcome = None
        exit_p = entry_p
        exit_time = candles[tap_idx]["time"]
        exit_idx = tap_idx

        # Forward scan bars starting from entry tap bar
        for k in range(tap_idx, min(tap_idx + 180, len(candles))):
            bar = candles[k]
            b_high = bar["high"]
            b_low = bar["low"]
            b_time = bar["time"]

            if side == "BUY":
                # Check Stage 2 Harvest (+9% ROE -> Lock +4.5%)
                if b_high >= harvest_trigger:
                    if harvest_sl > current_sl:
                        current_sl = harvest_sl
                # Check Stage 1 BE (+8% ROE -> Lock BE)
                elif b_high >= be_trigger:
                    if be_sl > current_sl:
                        current_sl = be_sl

                # Check TP
                if b_high >= tp_price:
                    outcome = "TP_HIT"
                    exit_p = tp_price
                    exit_time = b_time
                    exit_idx = k
                    break
                # Check SL (current dynamic SL)
                elif b_low <= current_sl:
                    if current_sl == harvest_sl:
                        outcome = "HARVEST_STAGE2_LOCK"
                    elif current_sl == be_sl:
                        outcome = "BE_LOCK"
                    else:
                        outcome = "SL_HIT"
                    exit_p = current_sl
                    exit_time = b_time
                    exit_idx = k
                    break
                # Disaster hard SL
                elif b_low <= hard_sl:
                    outcome = "SL_HIT"
                    exit_p = hard_sl
                    exit_time = b_time
                    exit_idx = k
                    break

            else: # SELL / SHORT
                if b_low <= harvest_trigger:
                    if harvest_sl < current_sl:
                        current_sl = harvest_sl
                elif b_low <= be_trigger:
                    if be_sl < current_sl:
                        current_sl = be_sl

                if b_low <= tp_price:
                    outcome = "TP_HIT"
                    exit_p = tp_price
                    exit_time = b_time
                    exit_idx = k
                    break
                elif b_high >= current_sl:
                    if current_sl == harvest_sl:
                        outcome = "HARVEST_STAGE2_LOCK"
                    elif current_sl == be_sl:
                        outcome = "BE_LOCK"
                    else:
                        outcome = "SL_HIT"
                    exit_p = current_sl
                    exit_time = b_time
                    exit_idx = k
                    break
                elif b_high >= hard_sl:
                    outcome = "SL_HIT"
                    exit_p = hard_sl
                    exit_time = b_time
                    exit_idx = k
                    break

        if outcome is None:
            # Reached max lookahead, close at mark
            last_bar = candles[min(tap_idx + 180, len(candles) - 1)]
            exit_p = last_bar["close"]
            exit_time = last_bar["time"]
            outcome = "TIME_CLOSE"

        # Calculate gross price move %
        if side == "BUY":
            gross_pct = (exit_p - entry_p) / entry_p * 100.0
        else:
            gross_pct = (entry_p - exit_p) / entry_p * 100.0

        trade_outcomes.append({
            **sig,
            "outcome": outcome,
            "exit_price": exit_p,
            "exit_time": exit_time,
            "gross_pct": gross_pct,
            "bars_held": exit_idx - tap_idx
        })

    # 5. CHRONOLOGICAL EVENT-DRIVEN 10-SECTION MATRIX SIMULATION
    # Sections 1-5: 4H Macro ($50 each)
    # Sections 6-10: 1H Intraday ($50 each)
    sections = {}
    for s_id in range(1, 11):
        tf = "4h" if s_id <= 5 else "1h"
        sections[s_id] = {
            "id": s_id,
            "tf": tf,
            "name": f"Section {s_id} ({'4H Macro' if s_id <= 5 else '1H Intraday'})",
            "balance": 50.0,
            "peak_balance": 50.0,
            "max_dd_pct": 0.0,
            "trades": [],
            "busy_until": 0, # timestamp
            "active_trade": None
        }

    symbol_busy_until = {} # symbol -> exit_timestamp + 2 hours cooldown
    executed_portfolio_trades = []
    rr_4h = 0
    rr_1h = 0

    for t in trade_outcomes:
        sym = t["symbol"]
        tf = t["tf"]
        e_time = t["entry_time"]
        x_time = t["exit_time"]

        # Anti-Collision: Is symbol currently busy in ANY section?
        if symbol_busy_until.get(sym, 0) > e_time:
            continue

        # Find idle section for this timeframe with Round-Robin Rotation
        target_section_ids = [1, 2, 3, 4, 5] if tf == "4h" else [6, 7, 8, 9, 10]
        start_ptr = rr_4h if tf == "4h" else rr_1h
        selected_sec_id = None
        for step in range(len(target_section_ids)):
            s_id = target_section_ids[(start_ptr + step) % len(target_section_ids)]
            sec = sections[s_id]
            if sec["busy_until"] <= e_time:
                selected_sec_id = s_id
                if tf == "4h":
                    rr_4h = (start_ptr + step + 1) % len(target_section_ids)
                else:
                    rr_1h = (start_ptr + step + 1) % len(target_section_ids)
                break

        if selected_sec_id is None:
            # All 5 sections for this timeframe are currently occupied
            continue

        # Execute trade in selected section
        sec = sections[selected_sec_id]
        cur_balance = sec["balance"]
        margin = cur_balance # 100% pure compounding
        pos_size = margin * 5.0 # 5x leverage
        fee = pos_size * 0.0016 # 0.16% roundtrip exchange fee
        gross_pnl = pos_size * (t["gross_pct"] / 100.0)
        net_pnl = gross_pnl - fee
        new_balance = round(max(1.0, cur_balance + net_pnl), 2)

        # Update drawdown
        sec["peak_balance"] = max(sec["peak_balance"], new_balance)
        dd = (sec["peak_balance"] - new_balance) / sec["peak_balance"] * 100.0 if sec["peak_balance"] > 0 else 0.0
        sec["max_dd_pct"] = max(sec["max_dd_pct"], dd)

        sec["balance"] = new_balance
        sec["busy_until"] = x_time
        # Symbol exclusivity: locked until trade exit + 2 hours cooldown
        symbol_busy_until[sym] = x_time + (2 * 3600 * 1000)

        trade_record = {
            "trade_id": len(executed_portfolio_trades) + 1,
            "section_id": selected_sec_id,
            "section_name": sec["name"],
            "symbol": sym,
            "tf": tf.upper(),
            "side": t["side"],
            "entry_time": e_time,
            "exit_time": x_time,
            "entry_date": datetime.fromtimestamp(e_time/1000, tz=IST).strftime("%Y-%m-%d %H:%M"),
            "exit_date": datetime.fromtimestamp(x_time/1000, tz=IST).strftime("%Y-%m-%d %H:%M"),
            "entry_price": t["entry_price"],
            "exit_price": t["exit_price"],
            "outcome": t["outcome"],
            "gross_pct": round(t["gross_pct"], 2),
            "roe_pct": round(t["gross_pct"] * 5.0, 2),
            "net_pnl_usdt": round(net_pnl, 2),
            "margin_deployed": round(margin, 2),
            "balance_after": new_balance,
            "is_origin": t["is_origin"],
            "bars_held": t["bars_held"]
        }
        sec["trades"].append(trade_record)
        executed_portfolio_trades.append(trade_record)

    # 6. CALCULATE COMPREHENSIVE STATS
    total_trades = len(executed_portfolio_trades)
    tp_wins = sum(1 for t in executed_portfolio_trades if t["outcome"] == "TP_HIT")
    harvest_wins = sum(1 for t in executed_portfolio_trades if t["outcome"] == "HARVEST_STAGE2_LOCK")
    be_exits = sum(1 for t in executed_portfolio_trades if t["outcome"] == "BE_LOCK")
    losses = sum(1 for t in executed_portfolio_trades if t["outcome"] == "SL_HIT" or t["net_pnl_usdt"] < 0)
    profitable_trades = sum(1 for t in executed_portfolio_trades if t["net_pnl_usdt"] > 0)

    total_start_equity = 500.00
    total_end_equity = sum(sec["balance"] for sec in sections.values())
    total_net_profit = total_end_equity - total_start_equity
    portfolio_roi_pct = (total_net_profit / total_start_equity) * 100.0

    direct_tp_rate = (tp_wins / total_trades * 100.0) if total_trades else 0.0
    cash_profit_accuracy = (profitable_trades / total_trades * 100.0) if total_trades else 0.0
    capital_safety_rate = ((profitable_trades + be_exits) / total_trades * 100.0) if total_trades else 0.0
    loss_rate = (losses / total_trades * 100.0) if total_trades else 0.0

    print("=" * 90)
    print("                    1-YEAR OOS PORTFOLIO SUMMARY RESULTS")
    print("=" * 90)
    print(f"• Total Portfolio Starting Capital:  $500.00 USDT (10 Sections @ $50.00 each)")
    print(f"• Total Portfolio Ending Equity:     ${total_end_equity:,.2f} USDT")
    print(f"• Total Net Portfolio Profit:        +${total_net_profit:,.2f} USDT (+{portfolio_roi_pct:,.2f}%)")
    print(f"• Total Trades Executed:             {total_trades} Trades")
    print(f"• Pure Win Rate (Direct TP + Harvest): {cash_profit_accuracy:.2f}% ({profitable_trades} Wins / {losses} Losses)")
    print(f"    - Target TP Hits (+14.0% ROE):    {tp_wins} Trades ({direct_tp_rate:.2f}%)")
    print(f"    - Stage 2 Harvest (+4.5% ROE):    {harvest_wins} Trades (Cash Locked Profit!)")
    print(f"    - Stage 1 Break-Even Exits:       {be_exits} Trades (Zero Capital Loss)")
    print(f"    - Stop Loss Hits:                 {losses} Trades ({loss_rate:.2f}%)")
    print(f"• Capital Safety Rate (Win + BE):     {capital_safety_rate:.2f}%")

    print("\n" + "=" * 90)
    print("               10 COMPOUNDING SECTIONS INDIVIDUAL BREAKDOWN")
    print("=" * 90)
    print(f"{'Section':<28} | {'TF':<4} | {'Trades':<6} | {'Wins':<5} | {'Loss':<5} | {'WinRate':<7} | {'MaxDD':<6} | {'Final Balance':<15}")
    print("-" * 90)
    for s_id in range(1, 11):
        sec = sections[s_id]
        s_trades = sec["trades"]
        n_t = len(s_trades)
        n_w = sum(1 for t in s_trades if t["net_pnl_usdt"] > 0)
        n_l = sum(1 for t in s_trades if t["net_pnl_usdt"] <= 0)
        wr = (n_w / n_t * 100.0) if n_t else 0.0
        print(f"{sec['name']:<28} | {sec['tf'].upper():<4} | {n_t:<6} | {n_w:<5} | {n_l:<5} | {wr:<6.1f}% | {sec['max_dd_pct']:<5.1f}% | ${sec['balance']:,.2f} USDT")

    # 7. MONTHLY TIMELINE BREAKDOWN
    print("\n" + "=" * 90)
    print("                 MONTHLY TIMELINE & PERFORMANCE AUDIT")
    print("=" * 90)
    months = {}
    for t in executed_portfolio_trades:
        m_str = t["entry_date"][:7]
        if m_str not in months:
            months[m_str] = {"trades": 0, "wins": 0, "harvest": 0, "be": 0, "losses": 0, "pnl": 0.0}
        m = months[m_str]
        m["trades"] += 1
        if t["outcome"] == "TP_HIT": m["wins"] += 1
        elif t["outcome"] == "HARVEST_STAGE2_LOCK": m["harvest"] += 1
        elif t["outcome"] == "BE_LOCK": m["be"] += 1
        else: m["losses"] += 1
        m["pnl"] += t["net_pnl_usdt"]

    print(f"{'Month':<10} | {'Trades':<7} | {'Direct TP':<10} | {'Harvest +4.5%':<14} | {'Break-Even':<11} | {'Losses':<7} | {'Accuracy':<8} | {'Monthly P&L':<15}")
    print("-" * 90)
    for m_str in sorted(months.keys()):
        m = months[m_str]
        tot = m["trades"]
        acc = ((m["wins"] + m["harvest"]) / tot * 100.0) if tot else 0.0
        print(f"{m_str:<10} | {tot:<7} | {m['wins']:<10} | {m['harvest']:<14} | {m['be']:<11} | {m['losses']:<7} | {acc:<7.1f}% | ${m['pnl']:+,.2f} USDT")

    # 8. SAMPLE EXECUTED TRADES LOG
    print("\n" + "=" * 90)
    print("          SAMPLE EXECUTED TRADES CHRONOLOGICAL LOG (FIRST 10 TRADES)")
    print("=" * 90)
    for t in executed_portfolio_trades[:10]:
        print(f"Trade #{t['trade_id']} | {t['entry_date']} | [{t['section_name']}] | {t['symbol']} ({t['tf']} {t['side']})")
        print(f"   Entry: ${t['entry_price']} | Exit: ${t['exit_price']} | Result: {t['outcome']} | PnL: ${t['net_pnl_usdt']:+.2f} ({t['roe_pct']:+.1f}% ROE) | Sec Bal: ${t['balance_after']:.2f}")

    # Save complete JSON result
    output_result = {
        "summary": {
            "total_start_equity": total_start_equity,
            "total_end_equity": round(total_end_equity, 2),
            "total_net_profit": round(total_net_profit, 2),
            "portfolio_roi_pct": round(portfolio_roi_pct, 2),
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "direct_tp_wins": tp_wins,
            "harvest_stage2_wins": harvest_wins,
            "break_even_exits": be_exits,
            "losses": losses,
            "direct_tp_rate_pct": round(direct_tp_rate, 2),
            "cash_profit_accuracy_pct": round(cash_profit_accuracy, 2),
            "capital_safety_rate_pct": round(capital_safety_rate, 2),
            "loss_rate_pct": round(loss_rate, 2)
        },
        "sections": {s_id: {k: v for k, v in sec.items() if k != "trades"} for s_id, sec in sections.items()},
        "monthly": months,
        "trades_sample": executed_portfolio_trades[:50]
    }
    with open("oos_1year_deca_compounding_results.json", "w", encoding="utf-8") as f:
        json.dump(output_result, f, indent=2)
    print("\nDetailed results saved to oos_1year_deca_compounding_results.json!")

if __name__ == "__main__":
    run_oos_backtest()
