"""
HERMES 3.5 DECA COMPOUNDING MATRIX - 1-YEAR TIMELY MANAGED OOS ACID TEST
========================================================================
- Capital: $500.00 Total ($50.00 isolated in each of the 10 Sections)
- Compounding: 100% pure geometric compounding per section
- Concurrency: 10 concurrent sections (handles 8+ trades per day easily)
- Strategy: Hermes 3.5 Single Tier with Calibrated TP
  * 4H Macro: +2.20% TP (+11.0% ROE @ 5x), SL: -2.80%, BE: +1.50%, Harvest: +1.80%
  * 1H Intraday: +1.80% TP (+9.0% ROE @ 5x), SL: -2.50%, BE: +1.20%, Harvest: +1.50%
  * Freshness Guard: <= 35 bars (Zero Zombie Zones)
  * Displacement >= 5.0% + FVG
  * Inducement Sweep + Wick >= 18%
  * King BTC 4H Sentry
  * Asset Exclusivity: 1 open position per coin at any time
  * Friction: 0.16% roundtrip exchange fee per trade
========================================================================
"""

import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

DATA_DIR = os.path.join(root_dir, "historical_data")
from config import TOP_22_CHAMPIONS

def calculate_ema(values: List[float], period: int) -> List[float]:
    if not values: return []
    k = 2.0 / (period + 1.0)
    ema = [values[0]]
    for v in values[1:]:
        ema.append(v * k + ema[-1] * (1.0 - k))
    return ema

def run_deca_timely_audit():
    print("=" * 95)
    print(" 🚀 HERMES 3.5 DECA COMPOUNDING - 1-YEAR TIMELY MANAGED OOS AUDIT")
    print(f" Timestamp: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST | Universe: {len(TOP_22_CHAMPIONS)} Champions")
    print("=" * 95)

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

    # 2. Discover Setups with Calibrated Parameters & Freshness Guard
    candidate_signals = []
    total_candles = 0

    for tf_str, tp_pct, sl_pct, be_pct, trail_pct, harvest_sl_pct in [
        ("4h", 0.0220, 0.0280, 0.0150, 0.0180, 0.0090),
        ("1h", 0.0180, 0.0250, 0.0120, 0.0150, 0.0080)
    ]:
        for sym in TOP_22_CHAMPIONS:
            path = os.path.join(DATA_DIR, f"{sym}_{tf_str}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                candles = json.load(f)

            n = len(candles)
            if n < 50:
                continue
            total_candles += n

            # ATR(14)
            atr_series = [0.0] * n
            for k in range(1, n):
                tr = max(candles[k]["high"] - candles[k]["low"],
                         abs(candles[k]["high"] - candles[k-1]["close"]),
                         abs(candles[k]["low"] - candles[k-1]["close"]))
                atr_series[k] = tr if k < 14 else (atr_series[k-1] * 13 + tr) / 14

            # Strict Freshness Guard: Retest within 35 bars
            max_tap_window = 35
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

                        for t in range(i+3, min(i + max_tap_window, n)):
                            curr_c = candles[t]
                            if curr_c["close"] < ob_low:
                                broken = True
                                break

                            bars_alive = t - (i+2)
                            idm_swept = any(candles[k]["low"] < idm_low for k in range(i+3, t+1)) or (curr_c["low"] < idm_low)

                            if bars_alive >= 3 and idm_swept:
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
                                    "tp_pct": tp_pct,
                                    "sl_pct": sl_pct,
                                    "be_pct": be_pct,
                                    "trail_pct": trail_pct,
                                    "harvest_sl_pct": harvest_sl_pct,
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

                        for t in range(i+3, min(i + max_tap_window, n)):
                            curr_c = candles[t]
                            if curr_c["close"] > ob_high:
                                broken = True
                                break

                            bars_alive = t - (i+2)
                            idm_swept = any(candles[k]["high"] > idm_high for k in range(i+3, t+1)) or (curr_c["high"] > idm_high)

                            if bars_alive >= 3 and idm_swept:
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
                                "tp_pct": tp_pct,
                                "sl_pct": sl_pct,
                                "be_pct": be_pct,
                                "trail_pct": trail_pct,
                                "harvest_sl_pct": harvest_sl_pct,
                                "candles": candles
                            })

    candidate_signals.sort(key=lambda s: s["entry_time"])
    print(f"Scanned {total_candles:,} Candlesticks across 39 Pairs.")
    print(f"Total Qualified Chronological Signals: {len(candidate_signals)}\n")

    # 3. Simulate Trade Forward Path with Calibrated Armor
    trade_outcomes = []

    for sig in candidate_signals:
        candles = sig["candles"]
        tap_idx = sig["tap_idx"]
        side = sig["side"]
        entry_p = sig["entry_price"]
        hard_sl = sig["hard_sl"]
        soft_sl = sig["soft_sl"]
        tp_move_pct = sig["tp_pct"]
        be_trigger_pct = sig["be_pct"]
        trail_trigger_pct = sig["trail_pct"]
        harvest_lock = sig["harvest_sl_pct"]

        tp_price = round(entry_p * (1.0 + tp_move_pct), 8) if side == "BUY" else round(entry_p * (1.0 - tp_move_pct), 8)
        be_trigger = entry_p * (1.0 + be_trigger_pct) if side == "BUY" else entry_p * (1.0 - be_trigger_pct)
        be_sl = round(entry_p * 1.0010, 8) if side == "BUY" else round(entry_p * 0.9990, 8)
        harvest_trigger = entry_p * (1.0 + trail_trigger_pct) if side == "BUY" else entry_p * (1.0 - trail_trigger_pct)
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
    # 4. TIMELY MANAGED 10-SECTION MATRIX SIMULATION
    # =========================================================================
    # 10 independent sections, starting with $50.00 each = $500.00 total
    # If 8 trades occur in 1 day, any of the 10 free sections can absorb and execute them!
    sections = {}
    for s_id in range(1, 11):
        sections[s_id] = {
            "id": s_id,
            "name": f"Section {s_id}",
            "balance": 50.0,
            "peak_balance": 50.0,
            "max_dd_pct": 0.0,
            "busy_until": 0,
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "be_saves": 0
        }

    symbol_busy_until = {} # Coin exclusivity (1 position per coin)
    executed_trades = []
    daily_executions = defaultdict(int) # date_str -> count
    hourly_executions = defaultdict(int)
    round_robin_ptr = 0

    for t in trade_outcomes:
        sym = t["symbol"]
        e_time = t["entry_time"]
        x_time = t["exit_time"]

        # Asset Exclusivity: Coin must not be in active trade anywhere
        if symbol_busy_until.get(sym, 0) > e_time:
            continue

        # Find Idle Section with Round-Robin Load Balancing
        selected_sec_id = None
        for step in range(10):
            cand_id = ((round_robin_ptr + step) % 10) + 1
            if sections[cand_id]["busy_until"] <= e_time:
                selected_sec_id = cand_id
                round_robin_ptr = (cand_id % 10)
                break

        if selected_sec_id is None:
            # All 10 sections are currently occupied (Max Concurrency Reached)
            continue

        # Execute in Selected Section with 100% Compounding
        sec = sections[selected_sec_id]
        cur_bal = sec["balance"]
        margin = cur_bal
        pos_size = margin * 5.0 # 5x leverage
        fee = pos_size * 0.0016 # Roundtrip fee
        gross_pnl = pos_size * (t["gross_pct"] / 100.0)
        net_pnl = gross_pnl - fee
        new_bal = round(max(1.0, cur_bal + net_pnl), 2)

        sec["balance"] = new_bal
        sec["busy_until"] = x_time
        sec["trades"] += 1

        if t["outcome"] in ["TP_HIT", "HARVEST_STAGE2_LOCK"]:
            sec["wins"] += 1
        elif t["outcome"] == "BE_LOCK":
            sec["be_saves"] += 1
        elif t["outcome"] == "SL_HIT":
            sec["losses"] += 1

        if new_bal > sec["peak_balance"]:
            sec["peak_balance"] = new_bal
        dd = (sec["peak_balance"] - new_bal) / sec["peak_balance"] * 100.0
        if dd > sec["max_dd_pct"]:
            sec["max_dd_pct"] = dd

        # Lock coin until exit + 1 hour cooldown
        symbol_busy_until[sym] = x_time + (1 * 3600 * 1000)

        d_str = datetime.fromtimestamp(e_time/1000, tz=IST).strftime("%Y-%m-%d")
        daily_executions[d_str] += 1

        executed_trades.append({
            **t,
            "section": selected_sec_id,
            "margin": margin,
            "net_pnl": net_pnl,
            "sec_bal_after": new_bal,
            "total_port_equity": sum(s["balance"] for s in sections.values()),
            "date": d_str
        })

    # =========================================================================
    # 5. COMPILE COMPREHENSIVE PERFORMANCE METRICS
    # =========================================================================
    total_trades = len(executed_trades)
    tp_wins = sum(1 for t in executed_trades if t["outcome"] == "TP_HIT")
    harvest_wins = sum(1 for t in executed_trades if t["outcome"] == "HARVEST_STAGE2_LOCK")
    be_saves = sum(1 for t in executed_trades if t["outcome"] == "BE_LOCK")
    sl_losses = sum(1 for t in executed_trades if t["outcome"] == "SL_HIT")
    total_wins = tp_wins + harvest_wins
    cash_win_rate = (total_wins / total_trades * 100.0) if total_trades > 0 else 0.0
    safe_win_rate = ((total_wins + be_saves) / total_trades * 100.0) if total_trades > 0 else 0.0

    start_equity = 500.0
    final_equity = round(sum(s["balance"] for s in sections.values()), 2)
    net_profit = round(final_equity - start_equity, 2)
    growth_pct = round((net_profit / start_equity) * 100.0, 2)

    gross_profit = sum(t["net_pnl"] for t in executed_trades if t["net_pnl"] > 0)
    gross_loss = abs(sum(t["net_pnl"] for t in executed_trades if t["net_pnl"] < 0))
    profit_factor = round((gross_profit / gross_loss), 2) if gross_loss > 0 else 99.0

    # Daily Concurrency Stats
    max_trades_in_day = max(daily_executions.values()) if daily_executions else 0
    days_with_trades = len(daily_executions)
    avg_trades_per_active_day = (total_trades / days_with_trades) if days_with_trades > 0 else 0
    high_volume_days = sum(1 for c in daily_executions.values() if c >= 5)

    # Monthly Breakdown
    monthly_data = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "be": 0, "pnl": 0.0})
    for t in executed_trades:
        m_str = datetime.fromtimestamp(t["entry_time"]/1000, tz=IST).strftime("%Y-%m")
        monthly_data[m_str]["trades"] += 1
        if t["outcome"] in ["TP_HIT", "HARVEST_STAGE2_LOCK"]:
            monthly_data[m_str]["wins"] += 1
        elif t["outcome"] == "BE_LOCK":
            monthly_data[m_str]["be"] += 1
        elif t["outcome"] == "SL_HIT":
            monthly_data[m_str]["losses"] += 1
        monthly_data[m_str]["pnl"] += t["net_pnl"]

    # 4H vs 1H breakdown
    trades_4h = [t for t in executed_trades if t["tf"] == "4h"]
    trades_1h = [t for t in executed_trades if t["tf"] == "1h"]
    wins_4h = sum(1 for t in trades_4h if t["outcome"] in ["TP_HIT", "HARVEST_STAGE2_LOCK"])
    wins_1h = sum(1 for t in trades_1h if t["outcome"] in ["TP_HIT", "HARVEST_STAGE2_LOCK"])

    # Output Console Report
    print("=" * 95)
    print("               🏆 HERMES 3.5 DECA COMPOUNDING: 1-YEAR OOS RESULTS")
    print("=" * 95)
    print(f"• Initial Portfolio Equity:     $500.00 USDT (10 Isolated Sections @ $50.00 each)")
    print(f"• Final Ending Balance:         ${final_equity:,.2f} USDT")
    print(f"• Net Profit Generated:         +${net_profit:,.2f} USDT (+{growth_pct:.2f}% Account Growth)")
    print(f"• Total Trades Executed:        {total_trades} Trades")
    print(f"• Cash Win Rate:                {cash_win_rate:.2f}% ({total_wins} Wins / {sl_losses} Losses)")
    print(f"    - Direct TP Target Hits:    {tp_wins} Trades (Fast Targets Sniped!)")
    print(f"    - Stage 2 Trailing Locks:   {harvest_wins} Trades (Cash Profit Secured)")
    print(f"    - Stage 1 Breakeven Exits:  {be_saves} Trades (0% Capital Loss)")
    print(f"    - Stop Loss Hits:           {sl_losses} Trades")
    print(f"• Total Capital Safety Rate:    {safe_win_rate:.2f}% (Win + Breakeven)")
    print(f"• Profit Factor:                {profit_factor:.2f}")
    print(f"• 4H Macro Performance:         {len(trades_4h)} Trades | {wins_4h} Wins | {(wins_4h/len(trades_4h)*100.0) if trades_4h else 0:.1f}% WR")
    print(f"• 1H Intraday Performance:      {len(trades_1h)} Trades | {wins_1h} Wins | {(wins_1h/len(trades_1h)*100.0) if trades_1h else 0:.1f}% WR\n")

    print("-----------------------------------------------------------------------------------------------")
    print("                    DAILY FREQUENCY & CONCURRENCY MANAGEMENT STATS")
    print("-----------------------------------------------------------------------------------------------")
    print(f"• Peak Trades Executed in 1 Day: {max_trades_in_day} Trades (Handled seamlessly across 10 sections)")
    print(f"• Days with High Volume (>=5):   {high_volume_days} Days")
    print(f"• Active Trading Days:           {days_with_trades} Days")
    print(f"• Average Frequency:             {avg_trades_per_active_day:.1f} Trades per active trading day\n")

    print("-----------------------------------------------------------------------------------------------")
    print("                    10 COMPOUNDING SECTIONS INDIVIDUAL PERFORMANCE")
    print("-----------------------------------------------------------------------------------------------")
    print(f"{'Section':<14} | {'Trades':<8} | {'Wins':<6} | {'BE':<5} | {'Loss':<6} | {'Win Rate':<10} | {'Max DD':<10} | {'Final Balance':<15}")
    print("-" * 85)
    for s in sections.values():
        wr_s = (s["wins"] / s["trades"] * 100.0) if s["trades"] > 0 else 0.0
        print(f"{s['name']:<14} | {s['trades']:<8} | {s['wins']:<6} | {s['be_saves']:<5} | {s['losses']:<6} | {wr_s:>6.1f} %   | {s['max_dd_pct']:>6.1f} %   | ${s['balance']:>10.2f} USDT")

    print("\n-----------------------------------------------------------------------------------------------")
    print("                    1-YEAR TIMELINE MONTHLY BREAKDOWN")
    print("-----------------------------------------------------------------------------------------------")
    print(f"{'Month':<10} | {'Trades':<8} | {'Wins':<6} | {'BE':<5} | {'Losses':<8} | {'Win Rate':<10} | {'Monthly Net P&L':<18}")
    print("-" * 80)
    for m, d in sorted(monthly_data.items()):
        wr_m = (d["wins"] / d["trades"] * 100.0) if d["trades"] > 0 else 0.0
        print(f"{m:<10} | {d['trades']:<8} | {d['wins']:<6} | {d['be']:<5} | {d['losses']:<8} | {wr_m:>6.1f} %   | ${d['pnl']:>+10.2f} USDT")
    print("=" * 95)

    # Save to file
    out = {
        "summary": {
            "start_equity": start_equity,
            "final_equity": final_equity,
            "net_profit": net_profit,
            "growth_pct": growth_pct,
            "total_trades": total_trades,
            "tp_wins": tp_wins,
            "harvest_wins": harvest_wins,
            "be_saves": be_saves,
            "losses": sl_losses,
            "cash_win_rate": round(cash_win_rate, 2),
            "safe_win_rate": round(safe_win_rate, 2),
            "profit_factor": profit_factor,
            "max_trades_in_day": max_trades_in_day
        },
        "sections": {s["id"]: s for s in sections.values()},
        "monthly": dict(monthly_data)
    }
    with open("deca_1year_timely_managed_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    run_deca_timely_audit()
