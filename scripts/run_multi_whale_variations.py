"""
MULTI-VARIATION EXPERIMENT: TESTING INSTITUTIONAL WHALE FILTERS
==============================================================
Tests 4 variations across the 6-Month Period (Apr - Oct 2026):
- Var 1: Baseline BB 2.0 (PDH/PDL Sweep + 50% MT Retest)
- Var 2: Institutional Wick Defense (Wick >= 18% absorption)
- Var 3: Volume Climax (Stopping Volume >= 1.25x)
- Var 4: Combined Smart Confluence (Piercing Depth + Wick Defense)
"""

import os
import sys
import json
from datetime import datetime, timezone
from collections import defaultdict

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

from scripts.test_1year_bb20_model3_full import evaluate_trade, get_day_key

def run_variation(mode: str):
    all_trades = []

    for sym in CHAMPIONS:
        fpath = os.path.join(DATA_DIR, f"{sym}_1h.json")
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)
        if len(candles) < 1000:
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
                if g_idx + 2 >= len(candles):
                    continue
                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                c_vol = c.get("volume", 0.0)
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                candle_range = max(1e-8, c_h - c_l)
                lower_wick = max(0.0, min(c_o, c_c) - c_l)
                upper_wick = max(0.0, c_h - max(c_o, c_c))
                lower_wick_ratio = lower_wick / candle_range
                upper_wick_ratio = upper_wick / candle_range

                past_10_vol = [candles[max(0, g_idx - k)]["volume"] for k in range(1, 11)]
                avg_vol = sum(past_10_vol) / len(past_10_vol) if past_10_vol else 1.0

                # Long at PDL
                if not long_taken:
                    dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                    basic_pdl = (dist_to_pdl <= 0.015 or c_l <= pdl)
                    basic_disp = ((c_c < c_o or (c_h - c_l) > 0) and 
                                  ((next_c["high"] - c_l) / c_l >= 0.012 or (next_c2["high"] - c_l) / c_l >= 0.018) and 
                                  next_c2["low"] > c_h)

                    if basic_pdl and basic_disp:
                        passed = True
                        if mode == "wick_defense":
                            if lower_wick_ratio < 0.18 and next_c["close"] <= next_c["open"]:
                                passed = False
                        elif mode == "volume_climax":
                            if c_vol < 1.25 * avg_vol:
                                passed = False
                        elif mode == "smart_confluence":
                            # Piercing depth + wick defense
                            if not (c_l <= pdl * 1.001 and (lower_wick_ratio >= 0.18 or next_c["close"] > next_c["open"])):
                                passed = False

                        if passed:
                            mt = (c_h + c_l) / 2.0
                            sl = c_l * 0.9985
                            risk = mt - sl
                            if risk > 0:
                                for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                    if candles[w_idx]["low"] <= sl:
                                        break
                                    if candles[w_idx]["low"] <= mt:
                                        long_taken = True
                                        all_trades.append(evaluate_trade(candles, w_idx, "LONG", mt, sl, risk, sym, curr_day))
                                        break

                # Short at PDH
                if not short_taken:
                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    basic_pdh = (dist_to_pdh <= 0.015 or c_h >= pdh)
                    basic_disp = ((c_c > c_o or (c_h - c_l) > 0) and 
                                  ((c_h - next_c["low"]) / c_h >= 0.012 or (c_h - next_c2["low"]) / c_h >= 0.018) and 
                                  next_c2["high"] < c_l)

                    if basic_pdh and basic_disp:
                        passed = True
                        if mode == "wick_defense":
                            if upper_wick_ratio < 0.18 and next_c["close"] >= next_c["open"]:
                                passed = False
                        elif mode == "volume_climax":
                            if c_vol < 1.25 * avg_vol:
                                passed = False
                        elif mode == "smart_confluence":
                            if not (c_h >= pdh * 0.999 and (upper_wick_ratio >= 0.18 or next_c["close"] < next_c["open"])):
                                passed = False

                        if passed:
                            mt = (c_h + c_l) / 2.0
                            sl = c_h * 1.0015
                            risk = sl - mt
                            if risk > 0:
                                for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                    if candles[w_idx]["high"] >= sl:
                                        break
                                    if candles[w_idx]["high"] >= mt:
                                        short_taken = True
                                        all_trades.append(evaluate_trade(candles, w_idx, "SHORT", mt, sl, risk, sym, curr_day))
                                        break

                if long_taken and short_taken:
                    break

    all_trades.sort(key=lambda t: t["fill_time"])
    return all_trades

def simulate(trades, risk_pct):
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
        "win_rate": win_rate,
        "green_rate": green_rate,
        "final_balance": tot_eq,
        "roi_pct": roi_pct,
        "max_dd": max_dd
    }

def main():
    variations = [
        ("Baseline (No Extra Filter)", "baseline"),
        ("Wick Defense (Absorption >= 18%)", "wick_defense"),
        ("Volume Climax (Vol >= 1.25x)", "volume_climax"),
        ("Smart Confluence (Pierce + Wick)", "smart_confluence")
    ]

    print("=" * 95)
    print("🔬 6-MONTH INSTITUTIONAL WHALE FILTER COMPARISON EXPERIMENT ($500 START)")
    print("=" * 95)
    print(f"{'Variation':<35} | {'Trades':<7} | {'Win Rate':<9} | {'Green Rate':<11} | {'Cons 2% Final':<13} | {'Aggr 5% Final':<14} | {'Max DD':<7}")
    print("-" * 95)

    for label, mode in variations:
        trades = run_variation(mode)
        res_2 = simulate(trades, 0.02)
        res_5 = simulate(trades, 0.05)
        print(f"{label:<35} | {res_2['trades']:<7} | {res_2['win_rate']:.1f}%{'':<3} | {res_2['green_rate']:.1f}%{'':<4} | ${res_2['final_balance']:<12.2f} | ${res_5['final_balance']:<13.2f} | {res_2['max_dd']:.2f}%")
    print("=" * 95)

if __name__ == "__main__":
    main()
