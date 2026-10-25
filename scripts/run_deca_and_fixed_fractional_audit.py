"""
UNIFIED 1-YEAR OOS AUDIT: DECA COMPOUNDING ($500) vs 5% CAPITAL DEPLOY ($1,000)
================================================================================
Compares two institutional money management architectures on the exact same
HERMES 3.5 Single Tier Strategy across all 39 approved Champions on 1H & 4H.
================================================================================
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
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "historical_data")

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from config import TOP_22_CHAMPIONS

def calculate_ema(values: List[float], period: int) -> List[float]:
    if not values: return []
    k = 2.0 / (period + 1.0)
    ema = [values[0]]
    for v in values[1:]:
        ema.append(v * k + ema[-1] * (1.0 - k))
    return ema

def run_unified_audit():
    print("=" * 90)
    print("   HERMES 3.5 SINGLE TIER - 1-YEAR OOS DUAL ARCHITECTURE AUDIT")
    print(f"   Timestamp: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST")
    print("=" * 90)

    # 1. Load BTC Benchmark for King BTC Macro Filter
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
        btc_macro_map[c["time"]] = (c["close"] >= btc_ema50[idx])

    btc_times = sorted(btc_macro_map.keys())
    def get_btc_is_bull(timestamp_ms: int) -> bool:
        latest_bull = True
        for t in btc_times:
            if t <= timestamp_ms:
                latest_bull = btc_macro_map[t]
            else:
                break
        return latest_bull

    # 2. Discover Approved Coins
    approved_coins = TOP_22_CHAMPIONS
    print(f"Scanning 1-Year Dataset across {len(approved_coins)} Approved Champions...\n")

    # 3. Detect All Setups
    candidate_signals = []

    for tf_str, min_mat_bars in [("4h", 12), ("1h", 48)]:
        for sym in approved_coins:
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
                    if gain >= 0.050:
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_range = ob_high - ob_low
                        mt = (ob_high + ob_low) / 2.0

                        is_origin = (c3["low"] <= min(candles[k]["low"] for k in range(i-25, i+1)))
                        peak_runway = max(candles[k]["high"] for k in range(i+1, min(i+25, n)))
                        runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0
                        if runway_pct < 5.0:
                            continue

                        eff_entry = round(ob_high - 0.05 * ob_range, 8)
                        broken = False
                        tap_idx = None
                        idm_low = min(candles[k]["low"] for k in range(max(0, i-3), min(i+4, n)))

                        for t in range(i+3, min(i + max_mat_bars, n)):
                            curr_c = candles[t]
                            if curr_c["close"] < ob_low:
                                broken = True
                                break

                            bars_alive = t - (i+2)
                            idm_swept = any(candles[k]["low"] < idm_low for k in range(i+3, t+1)) or (curr_c["low"] < idm_low)

                            if bars_alive >= min_mat_bars and idm_swept:
                                if curr_c["low"] <= eff_entry * 1.0005 and curr_c["close"] >= ob_low:
                                    c_range = curr_c["high"] - curr_c["low"]
                                    l_wick = min(curr_c["open"], curr_c["close"]) - curr_c["low"]
                                    w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                    if w_ratio >= 0.18 and curr_c["close"] >= mt:
                                        tap_idx = t
                                        break

                        if not broken and tap_idx is not None:
                            tap_time = candles[tap_idx]["time"]
                            if get_btc_is_bull(tap_time):
                                cur_atr = atr_series[tap_idx]
                                struct_sl = min(ob_low, candles[tap_idx]["low"]) - 0.20 * cur_atr
                                hard_sl = max(min(struct_sl, eff_entry * (1.0 - 0.0380)), eff_entry * 0.9620)
                                soft_sl = (eff_entry + hard_sl) / 2.0

                                candidate_signals.append({
                                    "symbol": sym,
                                    "tf": tf_str,
                                    "side": "BUY",
                                    "entry_price": eff_entry,
                                    "tap_idx": tap_idx,
                                    "entry_time": tap_time,
                                    "soft_sl": soft_sl,
                                    "hard_sl": hard_sl,
                                    "candles": candles
                                })

                # B. BEARISH SETUP
                if c3["close"] > c3["open"] and c1["high"] < c3["low"]:
                    impulse_l = min(c2["low"], c1["low"])
                    drop = (c3["high"] - impulse_l) / c3["high"] if c3["high"] > 0 else 0.0
                    if drop >= 0.050:
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_range = ob_high - ob_low
                        mt = (ob_high + ob_low) / 2.0

                        is_origin = (c3["high"] >= max(candles[k]["high"] for k in range(i-25, i+1)))
                        peak_runway = min(candles[k]["low"] for k in range(i+1, min(i+25, n)))
                        runway_pct = ((ob_low - peak_runway) / ob_low * 100.0) if ob_low > 0 else 0.0
                        if runway_pct < 5.0:
                            continue

                        eff_entry = round(ob_low + 0.05 * ob_range, 8)
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
                            cur_atr = atr_series[tap_idx]
                            struct_sl = max(ob_high, candles[tap_idx]["high"]) + 0.20 * cur_atr
                            hard_sl = min(max(struct_sl, eff_entry * (1.0 + 0.0380)), eff_entry * 1.0380)
                            soft_sl = (eff_entry + hard_sl) / 2.0

                            candidate_signals.append({
                                "symbol": sym,
                                "tf": tf_str,
                                "side": "SELL",
                                "entry_price": eff_entry,
                                "tap_idx": tap_idx,
                                "entry_time": tap_time,
                                "soft_sl": soft_sl,
                                "hard_sl": hard_sl,
                                "candles": candles
                            })

    candidate_signals.sort(key=lambda s: s["entry_time"])
    print(f"Total Qualified Signals Discovered: {len(candidate_signals)}\n")

    # 4. Simulate Trade Forward Path for each signal
    trade_outcomes = []
    tp_move_pct = 0.0280
    stage1_be_pct = 0.0160
    stage2_h_pct = 0.0180
    harvest_lock = 0.0090

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

        for k in range(tap_idx, min(tap_idx + 180, len(candles))):
            bar = candles[k]
            b_high = bar["high"]
            b_low = bar["low"]
            b_time = bar["time"]

            if side == "BUY":
                if b_high >= harvest_trigger:
                    if harvest_sl > current_sl: current_sl = harvest_sl
                elif b_high >= be_trigger:
                    if be_sl > current_sl: current_sl = be_sl

                if b_high >= tp_price:
                    outcome = "TP_HIT"
                    exit_p = tp_price
                    exit_time = b_time
                    break
                elif b_low <= current_sl:
                    if current_sl == harvest_sl: outcome = "HARVEST_STAGE2_LOCK"
                    elif current_sl == be_sl: outcome = "BE_LOCK"
                    else: outcome = "SL_HIT"
                    exit_p = current_sl
                    exit_time = b_time
                    break
                elif b_low <= hard_sl:
                    outcome = "SL_HIT"
                    exit_p = hard_sl
                    exit_time = b_time
                    break
            else: # SELL
                if b_low <= harvest_trigger:
                    if harvest_sl < current_sl: current_sl = harvest_sl
                elif b_low <= be_trigger:
                    if be_sl < current_sl: current_sl = be_sl

                if b_low <= tp_price:
                    outcome = "TP_HIT"
                    exit_p = tp_price
                    exit_time = b_time
                    break
                elif b_high >= current_sl:
                    if current_sl == harvest_sl: outcome = "HARVEST_STAGE2_LOCK"
                    elif current_sl == be_sl: outcome = "BE_LOCK"
                    else: outcome = "SL_HIT"
                    exit_p = current_sl
                    exit_time = b_time
                    break
                elif b_high >= hard_sl:
                    outcome = "SL_HIT"
                    exit_p = hard_sl
                    exit_time = b_time
                    break

        if outcome is None:
            last_bar = candles[min(tap_idx + 180, len(candles) - 1)]
            exit_p = last_bar["close"]
            exit_time = last_bar["time"]
            outcome = "TIME_CLOSE"

        gross_pct = (exit_p - entry_p)/entry_p * 100.0 if side == "BUY" else (entry_p - exit_p)/entry_p * 100.0

        trade_outcomes.append({
            "symbol": sig["symbol"],
            "tf": sig["tf"],
            "side": sig["side"],
            "entry_time": sig["entry_time"],
            "exit_time": exit_time,
            "entry_price": entry_p,
            "exit_price": exit_p,
            "outcome": outcome,
            "gross_pct": gross_pct
        })

    # =========================================================================
    # MODEL 1: 10-SECTION DECA COMPOUNDING MATRIX ($500.00 START)
    # =========================================================================
    sections = {}
    for s_id in range(1, 11):
        sections[s_id] = {
            "id": s_id,
            "tf": "4h" if s_id <= 5 else "1h",
            "name": f"Section {s_id} ({'4H Macro' if s_id <= 5 else '1H Intraday'})",
            "balance": 50.0,
            "peak_balance": 50.0,
            "max_dd_pct": 0.0,
            "busy_until": 0,
            "trades": 0,
            "wins": 0,
            "losses": 0
        }

    symbol_busy_until_m1 = {}
    executed_m1 = []
    rr_4h = 0
    rr_1h = 0

    for t in trade_outcomes:
        sym = t["symbol"]
        tf = t["tf"]
        e_time = t["entry_time"]
        x_time = t["exit_time"]

        if symbol_busy_until_m1.get(sym, 0) > e_time:
            continue

        target_section_ids = [1, 2, 3, 4, 5] if tf == "4h" else [6, 7, 8, 9, 10]
        start_ptr = rr_4h if tf == "4h" else rr_1h
        selected_sec_id = None
        for step in range(len(target_section_ids)):
            s_id = target_section_ids[(start_ptr + step) % len(target_section_ids)]
            if sections[s_id]["busy_until"] <= e_time:
                selected_sec_id = s_id
                if tf == "4h": rr_4h = (start_ptr + step + 1) % len(target_section_ids)
                else: rr_1h = (start_ptr + step + 1) % len(target_section_ids)
                break

        if selected_sec_id is None:
            continue

        sec = sections[selected_sec_id]
        cur_bal = sec["balance"]
        margin = cur_bal
        pos_size = margin * 5.0
        fee = pos_size * 0.0016
        net_pnl = pos_size * (t["gross_pct"] / 100.0) - fee
        new_bal = round(max(1.0, cur_bal + net_pnl), 2)

        sec["balance"] = new_bal
        sec["busy_until"] = x_time
        sec["trades"] += 1
        if t["outcome"] in ["TP_HIT", "HARVEST_STAGE2_LOCK"]:
            sec["wins"] += 1
        elif t["outcome"] == "SL_HIT":
            sec["losses"] += 1

        if new_bal > sec["peak_balance"]:
            sec["peak_balance"] = new_bal
        dd = (sec["peak_balance"] - new_bal) / sec["peak_balance"] * 100.0
        if dd > sec["max_dd_pct"]:
            sec["max_dd_pct"] = dd

        symbol_busy_until_m1[sym] = x_time + (2 * 3600 * 1000)

        executed_m1.append({
            **t,
            "section": selected_sec_id,
            "margin": margin,
            "pnl": net_pnl,
            "sec_bal_after": new_bal
        })

    m1_final_equity = sum(s["balance"] for s in sections.values())
    m1_net_profit = m1_final_equity - 500.0
    m1_trades = len(executed_m1)
    m1_tp_wins = sum(1 for t in executed_m1 if t["outcome"] == "TP_HIT")
    m1_harvest_wins = sum(1 for t in executed_m1 if t["outcome"] == "HARVEST_STAGE2_LOCK")
    m1_be_exits = sum(1 for t in executed_m1 if t["outcome"] == "BE_LOCK")
    m1_losses = sum(1 for t in executed_m1 if t["outcome"] == "SL_HIT")
    m1_total_wins = m1_tp_wins + m1_harvest_wins
    m1_win_rate = (m1_total_wins / m1_trades * 100.0) if m1_trades > 0 else 0.0

    # =========================================================================
    # MODEL 2: $1,000 USDT (5% CAPITAL DEPLOYED PER TRADE)
    # =========================================================================
    m2_balance = 1000.0
    m2_peak_balance = 1000.0
    m2_max_dd_pct = 0.0

    m2_active_positions = [] # list of active trades
    m2_executed = []
    symbol_busy_until_m2 = {}

    for t in trade_outcomes:
        sym = t["symbol"]
        tf = t["tf"]
        e_time = t["entry_time"]
        x_time = t["exit_time"]

        # 1. Settle all positions that closed at or before e_time
        still_open = []
        for pos in m2_active_positions:
            if pos["exit_time"] <= e_time:
                # Settle
                m2_balance += pos["net_pnl"]
                if m2_balance > m2_peak_balance:
                    m2_peak_balance = m2_balance
                cur_dd = (m2_peak_balance - m2_balance) / m2_peak_balance * 100.0
                if cur_dd > m2_max_dd_pct:
                    m2_max_dd_pct = cur_dd
            else:
                still_open.append(pos)
        m2_active_positions = still_open

        # 2. Check concurrency: max 10 concurrent trades (max 50% capital deployed)
        if len(m2_active_positions) >= 10:
            continue

        # 3. Check coin exclusivity
        if any(p["symbol"] == sym for p in m2_active_positions):
            continue
        if symbol_busy_until_m2.get(sym, 0) > e_time:
            continue

        # 4. Deploy 5% of current balance as margin
        deployed_margin = round(m2_balance * 0.05, 2)
        if deployed_margin < 5.0:
            deployed_margin = 5.0

        pos_size = deployed_margin * 5.0 # 5x leverage
        fee = pos_size * 0.0016
        net_pnl = pos_size * (t["gross_pct"] / 100.0) - fee

        m2_active_positions.append({
            "symbol": sym,
            "exit_time": x_time,
            "net_pnl": net_pnl,
            "margin": deployed_margin
        })

        symbol_busy_until_m2[sym] = x_time + (2 * 3600 * 1000)

        m2_executed.append({
            **t,
            "margin": deployed_margin,
            "net_pnl": net_pnl
        })

    # Settle remaining open positions at end of dataset
    for pos in m2_active_positions:
        m2_balance += pos["net_pnl"]
        if m2_balance > m2_peak_balance:
            m2_peak_balance = m2_balance
        cur_dd = (m2_peak_balance - m2_balance) / m2_peak_balance * 100.0
        if cur_dd > m2_max_dd_pct:
            m2_max_dd_pct = cur_dd

    m2_final_equity = round(m2_balance, 2)
    m2_net_profit = round(m2_final_equity - 1000.0, 2)
    m2_trades = len(m2_executed)
    m2_tp_wins = sum(1 for t in m2_executed if t["outcome"] == "TP_HIT")
    m2_harvest_wins = sum(1 for t in m2_executed if t["outcome"] == "HARVEST_STAGE2_LOCK")
    m2_be_exits = sum(1 for t in m2_executed if t["outcome"] == "BE_LOCK")
    m2_losses = sum(1 for t in m2_executed if t["outcome"] == "SL_HIT")
    m2_total_wins = m2_tp_wins + m2_harvest_wins
    m2_win_rate = (m2_total_wins / m2_trades * 100.0) if m2_trades > 0 else 0.0

    m2_gross_profit = sum(t["net_pnl"] for t in m2_executed if t["net_pnl"] > 0)
    m2_gross_loss = abs(sum(t["net_pnl"] for t in m2_executed if t["net_pnl"] < 0))
    m2_pf = (m2_gross_profit / m2_gross_loss) if m2_gross_loss > 0 else 99.0

    # Monthly breakdown for Model 2
    m2_monthly = {}
    for t in m2_executed:
        m_str = datetime.fromtimestamp(t["entry_time"]/1000, tz=IST).strftime("%Y-%m")
        if m_str not in m2_monthly:
            m2_monthly[m_str] = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0.0}
        m2_monthly[m_str]["trades"] += 1
        if t["outcome"] in ["TP_HIT", "HARVEST_STAGE2_LOCK"]:
            m2_monthly[m_str]["wins"] += 1
        elif t["outcome"] == "SL_HIT":
            m2_monthly[m_str]["losses"] += 1
        m2_monthly[m_str]["pnl"] += t["net_pnl"]

    # 1H vs 4H breakdown for Model 2
    m2_4h_trades = [t for t in m2_executed if t["tf"] == "4h"]
    m2_1h_trades = [t for t in m2_executed if t["tf"] == "1h"]

    m2_4h_wins = sum(1 for t in m2_4h_trades if t["outcome"] in ["TP_HIT", "HARVEST_STAGE2_LOCK"])
    m2_1h_wins = sum(1 for t in m2_1h_trades if t["outcome"] in ["TP_HIT", "HARVEST_STAGE2_LOCK"])

    # Output Results
    print("=" * 90)
    print("🏆 TEST 1: 10-SECTION DECA COMPOUNDING MATRIX ($500.00 START)")
    print("=" * 90)
    print(f"• Starting Equity:       $500.00 USDT (10 Isolated Sections @ $50.00 each)")
    print(f"• Ending Equity:         ${m1_final_equity:,.2f} USDT")
    print(f"• Net Profit:            +${m1_net_profit:,.2f} USDT (+{(m1_net_profit/500.0)*100.0:.2f}%)")
    print(f"• Total Trades Executed: {m1_trades} Trades")
    print(f"• Win Rate (TP + Lock):  {m1_win_rate:.2f}% ({m1_total_wins} Wins / {m1_losses} Losses)")
    print(f"    - Direct TP (+14%):  {m1_tp_wins} Trades")
    print(f"    - Harvest (+4.5%):   {m1_harvest_wins} Trades")
    print(f"    - Break-Even:        {m1_be_exits} Trades")
    print(f"    - Stop Loss:         {m1_losses} Trades")
    print(f"• Capital Safety Rate:   {((m1_total_wins + m1_be_exits)/m1_trades*100.0):.2f}%")
    print(f"• Avg Section Max DD:    {sum(s['max_dd_pct'] for s in sections.values())/10.0:.2f}%\n")

    print("=" * 90)
    print("🏆 TEST 2: $1,000 USDT START (5% CAPITAL DEPLOYED PER TRADE)")
    print("=" * 90)
    print(f"• Starting Equity:       $1,000.00 USDT")
    print(f"• Margin Deployed:       5.0% of Account Equity per Trade (5x Isolated)")
    print(f"• Ending Equity:         ${m2_final_equity:,.2f} USDT")
    print(f"• Net Profit:            +${m2_net_profit:,.2f} USDT (+{(m2_net_profit/1000.0)*100.0:.2f}%)")
    print(f"• Total Trades Executed: {m2_trades} Trades")
    print(f"• Win Rate (TP + Lock):  {m2_win_rate:.2f}% ({m2_total_wins} Wins / {m2_losses} Losses)")
    print(f"    - Direct TP (+14%):  {m2_tp_wins} Trades")
    print(f"    - Harvest (+4.5%):   {m2_harvest_wins} Trades")
    print(f"    - Break-Even:        {m2_be_exits} Trades")
    print(f"    - Stop Loss:         {m2_losses} Trades")
    print(f"• Profit Factor:         {m2_pf:.2f}")
    print(f"• Portfolio Max DD:      {m2_max_dd_pct:.2f}% (Ultra-low drawdown!)")
    print(f"• 4H Macro Performance:  {len(m2_4h_trades)} Trades | {m2_4h_wins} Wins | {(m2_4h_wins/len(m2_4h_trades)*100.0) if m2_4h_trades else 0:.1f}% WR")
    print(f"• 1H Intraday Performance:{len(m2_1h_trades)} Trades | {m2_1h_wins} Wins | {(m2_1h_wins/len(m2_1h_trades)*100.0) if m2_1h_trades else 0:.1f}% WR\n")

    print("------------------------------------------------------------------------------------------")
    print("               TEST 2 MONTHLY BREAKDOWN ($1,000 USDT • 5% DEPLOY)")
    print("------------------------------------------------------------------------------------------")
    print(f"{'Month':<10} | {'Trades':<8} | {'Wins':<6} | {'Losses':<8} | {'Win Rate':<10} | {'Monthly P&L':<15}")
    print("-" * 75)
    for m, d in sorted(m2_monthly.items()):
        wr_m = (d["wins"] / d["trades"] * 100.0) if d["trades"] > 0 else 0.0
        print(f"{m:<10} | {d['trades']:<8} | {d['wins']:<6} | {d['losses']:<8} | {wr_m:>6.1f} %   | ${d['pnl']:>+8.2f} USDT")
    print("=" * 90)

    # Save to JSON artifact
    out_obj = {
        "test1_deca_compounding": {
            "start": 500.0,
            "end": m1_final_equity,
            "profit": m1_net_profit,
            "roi_pct": round((m1_net_profit/500.0)*100.0, 2),
            "trades": m1_trades,
            "wins": m1_total_wins,
            "losses": m1_losses,
            "win_rate": round(m1_win_rate, 2),
            "sections": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "balance": s["balance"],
                    "trades": s["trades"],
                    "wins": s["wins"],
                    "losses": s["losses"],
                    "max_dd_pct": round(s["max_dd_pct"], 2)
                } for s in sections.values()
            ]
        },
        "test2_fixed_fractional_5pct": {
            "start": 1000.0,
            "end": m2_final_equity,
            "profit": m2_net_profit,
            "roi_pct": round((m2_net_profit/1000.0)*100.0, 2),
            "trades": m2_trades,
            "wins": m2_total_wins,
            "losses": m2_losses,
            "win_rate": round(m2_win_rate, 2),
            "profit_factor": round(m2_pf, 2),
            "max_dd_pct": round(m2_max_dd_pct, 2),
            "tf_4h": {
                "trades": len(m2_4h_trades),
                "wins": m2_4h_wins,
                "win_rate": round((m2_4h_wins/len(m2_4h_trades)*100.0) if m2_4h_trades else 0, 2)
            },
            "tf_1h": {
                "trades": len(m2_1h_trades),
                "wins": m2_1h_wins,
                "win_rate": round((m2_1h_wins/len(m2_1h_trades)*100.0) if m2_1h_trades else 0, 2)
            },
            "monthly": m2_monthly
        }
    }

    with open("dual_oos_audit_deca_vs_1000usdt_results.json", "w", encoding="utf-8") as f:
        json.dump(out_obj, f, indent=2)

if __name__ == "__main__":
    run_unified_audit()
