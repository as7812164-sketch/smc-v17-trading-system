"""
AUDIT: BB 3.0 vs BB 3.5 — JUNE & JULY 2026 OUT-OF-SAMPLE (OOS) DUEL
===================================================================
- Period 1: June 1, 2026 to June 30, 2026 (30 Days)
- Period 2: July 1, 2026 to July 31, 2026 (31 Days)
- Dataset: Top-20 Champions (15m Real Candlesticks)
- Starting Capital: $500.00 USDT starting for each month (10 Sections @ $50 each)
- Compounding Model: 5% Compounding Section Risk (Deca Compounding Architecture)
"""

import os
import sys
import json
from datetime import datetime, timezone
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
CACHE_DIR = os.path.join(ROOT_DIR, "market_data_cache_15m")
RESEARCH_DIR = os.path.join(ROOT_DIR, "scratch", "bb35_research")
if RESEARCH_DIR not in sys.path:
    sys.path.insert(0, RESEARCH_DIR)

from bb35_backtest import run_bb35_backtest
from bb35_engine import CHAMPIONS, PAIR_MAPPING, get_day_key

def exec_bb30_trade(candles, fill_idx, side, entry_price, sl_price, risk, sym, day_str, max_hold_bars=96, friction_r=0.06):
    active_sl = sl_price
    current_tier = 0
    n = len(candles)
    fill_time = candles[fill_idx]["time"]
    highest_fav_r = 0.0

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold_bars, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]
        exit_time = b["time"]

        if side == "LONG":
            cur_r = (b_h - entry_price) / risk
            if cur_r > highest_fav_r:
                highest_fav_r = cur_r

            if b_l <= active_sl:
                if current_tier == 0:
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "LOSS", "pnl_r": -1.0 - friction_r,
                        "highest_r": highest_fav_r
                    }
                elif current_tier == 1:
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r,
                        "highest_r": highest_fav_r
                    }
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "WIN", "pnl_r": locked_r - friction_r,
                        "highest_r": highest_fav_r
                    }

            if cur_r >= 1.0:
                if cur_r >= 1.5:
                    tier_candidate = int((cur_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = (current_tier - 1) * 0.5
                        active_sl = entry_price + (locked_r * risk)
                elif current_tier < 1:
                    current_tier = 1
                    active_sl = entry_price + (0.2 * risk)

        else: # SHORT
            cur_r = (entry_price - b_l) / risk
            if cur_r > highest_fav_r:
                highest_fav_r = cur_r

            if b_h >= active_sl:
                if current_tier == 0:
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "LOSS", "pnl_r": -1.0 - friction_r,
                        "highest_r": highest_fav_r
                    }
                elif current_tier == 1:
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r,
                        "highest_r": highest_fav_r
                    }
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "WIN", "pnl_r": locked_r - friction_r,
                        "highest_r": highest_fav_r
                    }

            if cur_r >= 1.0:
                if cur_r >= 1.5:
                    tier_candidate = int((cur_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = (current_tier - 1) * 0.5
                        active_sl = entry_price - (locked_r * risk)
                elif current_tier < 1:
                    current_tier = 1
                    active_sl = entry_price - (0.2 * risk)

    # Max Hold timeout
    last_b = candles[min(fill_idx + max_hold_bars, n - 1)]
    cur_p = last_b["close"]
    cur_r = ((cur_p - entry_price) if side == "LONG" else (entry_price - cur_p)) / risk
    outcome = "WIN" if cur_r > 0 else "LOSS"
    return {
        "symbol": sym, "day": day_str, "side": side,
        "entry": entry_price, "exit": cur_p,
        "fill_time": fill_time, "exit_time": last_b["time"],
        "outcome": outcome, "pnl_r": cur_r - friction_r,
        "highest_r": highest_fav_r
    }

def run_bb30_month(month_str):
    all_trades = []
    for sym in CHAMPIONS:
        fpath = os.path.join(CACHE_DIR, f"{sym}_15m.json")
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)

        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            prev_day_key = sorted_days[d_i - 1]
            curr_day_key = sorted_days[d_i]

            if not curr_day_key.startswith(month_str):
                continue

            prev_day_candles = [c for _, c in day_buckets[prev_day_key]]
            curr_day_entries = day_buckets[curr_day_key]

            if len(prev_day_candles) < 20 or len(curr_day_entries) < 20:
                continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)

            long_taken = False
            short_taken = False

            for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
                if g_idx + 2 >= len(candles):
                    continue

                c_sweep = candles[g_idx + 1]

                # Long: Sweep PDL
                if not long_taken and c_sweep["low"] < pdl and c_sweep["close"] > pdl:
                    wick = min(c_sweep["open"], c_sweep["close"]) - c_sweep["low"]
                    c_range = c_sweep["high"] - c_sweep["low"]
                    if c_range > 0 and (wick / c_range) >= 0.18:
                        ob_low = c_sweep["low"]
                        ob_high = c_sweep["high"]
                        mt = (ob_low + ob_high) / 2.0
                        sl = ob_low * 0.9985
                        risk = mt - sl
                        if risk > 0 and (risk / mt) <= 0.045:
                            fill_idx = -1
                            for w in range(g_idx + 2, min(g_idx + 34, len(candles))):
                                if candles[w]["low"] <= sl:
                                    break
                                if candles[w]["low"] <= mt:
                                    fill_idx = w
                                    break
                            if fill_idx != -1:
                                long_taken = True
                                t = exec_bb30_trade(candles, fill_idx, "LONG", mt, sl, risk, sym, curr_day_key)
                                all_trades.append(t)

                # Short: Sweep PDH
                if not short_taken and c_sweep["high"] > pdh and c_sweep["close"] < pdh:
                    wick = c_sweep["high"] - max(c_sweep["open"], c_sweep["close"])
                    c_range = c_sweep["high"] - c_sweep["low"]
                    if c_range > 0 and (wick / c_range) >= 0.18:
                        ob_low = c_sweep["low"]
                        ob_high = c_sweep["high"]
                        mt = (ob_low + ob_high) / 2.0
                        sl = ob_high * 1.0015
                        risk = sl - mt
                        if risk > 0 and (risk / mt) <= 0.045:
                            fill_idx = -1
                            for w in range(g_idx + 2, min(g_idx + 34, len(candles))):
                                if candles[w]["high"] >= sl:
                                    break
                                if candles[w]["high"] >= mt:
                                    fill_idx = w
                                    break
                            if fill_idx != -1:
                                short_taken = True
                                t = exec_bb30_trade(candles, fill_idx, "SHORT", mt, sl, risk, sym, curr_day_key)
                                all_trades.append(t)

                if long_taken and short_taken:
                    break

    all_trades.sort(key=lambda t: t["fill_time"])
    return all_trades

def simulate_deca_compounding(trades, start_balance=500.0, risk_pct=0.05):
    sections = {i: {"balance": start_balance / 10.0, "busy_until": 0, "wins": 0, "saves": 0, "losses": 0, "trades": 0} for i in range(1, 11)}
    equity_curve = [start_balance]

    for t in trades:
        sec_id = PAIR_MAPPING.get(t["symbol"], 1)
        sec = sections[sec_id]
        if sec["busy_until"] > t["fill_time"]:
            continue
        sec["busy_until"] = t["exit_time"]
        sec["trades"] += 1

        dollar_pnl = (sec["balance"] * risk_pct) * t["pnl_r"]
        sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))

        if t["outcome"] == "WIN":
            sec["wins"] += 1
        elif t["outcome"] == "FEE_SHIELD_SAVE":
            sec["saves"] += 1
        else:
            sec["losses"] += 1

        curr_tot = sum(s["balance"] for s in sections.values())
        equity_curve.append(curr_tot)

    final_eq = sum(s["balance"] for s in sections.values())
    net_pnl = final_eq - start_balance
    roi = (net_pnl / start_balance) * 100.0

    # Max Drawdown
    peak = start_balance
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

    wins = sum(s["wins"] for s in sections.values())
    saves = sum(s["saves"] for s in sections.values())
    losses = sum(s["losses"] for s in sections.values())
    tot = wins + saves + losses

    return {
        "final_equity": final_eq,
        "net_pnl": net_pnl,
        "roi_pct": roi,
        "max_dd": max_dd,
        "total_trades": tot,
        "wins": wins,
        "saves": saves,
        "losses": losses,
        "win_rate": (wins / tot * 100.0) if tot else 0.0,
        "green_rate": ((wins + saves) / tot * 100.0) if tot else 0.0,
        "loss_rate": (losses / tot * 100.0) if tot else 0.0,
        "sections": sections
    }

def print_month_table(month_name, bb30_res, bb35_res):
    print("\n" + "=" * 85)
    print(f"📊 {month_name.upper()} 2026: BB 3.0 vs BB 3.5 DUEL RESULTS")
    print("=" * 85)
    print(f"{'Metric':<32} | {'BB 3.0 (Classic)':<22} | {'BB 3.5 (Dual-Confluence)':<24}")
    print("-" * 85)
    print(f"{'Total Trades Executed':<32} | {bb30_res['total_trades']:<22} | {bb35_res['total_trades']:<24}")
    print(f"{'Pure Wins':<32} | {bb30_res['wins']:<22} | {bb35_res['wins']:<24}")
    print(f"{'Fee Shield Saves (BE +0.2R)':<32} | {bb30_res['saves']:<22} | {bb35_res['saves']:<24}")
    print(f"{'Stop Losses Hit (-1.0R)':<32} | {bb30_res['losses']:<22} | {bb35_res['losses']:<24}")
    print(f"{'Pure Win Rate':<32} | {bb30_res['win_rate']:.2f}%{'':<16} | {bb35_res['win_rate']:.2f}%{'':<18}")
    print(f"{'Total Green / Protected Rate':<32} | {bb30_res['green_rate']:.2f}%{'':<16} | {bb35_res['green_rate']:.2f}%{'':<18}")
    print(f"{'Starting Balance':<32} | $500.00 USDT{'':<10} | $500.00 USDT{'':<12}")
    print(f"{'Final Balance':<32} | ${bb30_res['final_equity']:.2f} USDT{'':<9} | ${bb35_res['final_equity']:.2f} USDT{'':<10}")
    print(f"{'Net Profit':<32} | ${bb30_res['net_pnl']:+.2f} USDT{'':<8} | ${bb35_res['net_pnl']:+.2f} USDT{'':<10}")
    print(f"{'Monthly ROI %':<32} | {bb30_res['roi_pct']:+.2f}%{'':<16} | {bb35_res['roi_pct']:+.2f}%{'':<17}")
    print(f"{'Max Account Drawdown':<32} | {bb30_res['max_dd']:.2f}%{'':<16} | {bb35_res['max_dd']:.2f}%{'':<18}")
    print("=" * 85)

def main():
    months = [("June 2026", "2026-06"), ("July 2026", "2026-07")]
    results = {}

    for name, m_key in months:
        print(f"\n[RUNNING] Simulating {name} for BB 3.0...")
        bb30_t = run_bb30_month(m_key)
        bb30_res = simulate_deca_compounding(bb30_t)

        print(f"[RUNNING] Simulating {name} for BB 3.5...")
        bb35_t = run_bb35_backtest(m_key)
        bb35_res = simulate_deca_compounding(bb35_t)

        results[m_key] = {"bb30": bb30_res, "bb35": bb35_res}
        print_month_table(name, bb30_res, bb35_res)

    # Save results as JSON
    out_file = os.path.join(ROOT_DIR, "scripts", "audit_june_july_bb30_vs_bb35_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[SUCCESS] Results saved to {out_file}")

if __name__ == "__main__":
    main()
