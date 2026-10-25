"""
OCTOBER 2026 FORENSIC AUDIT (OCT 1 - OCT 15, 2026)
==================================================
Audits exact trading performance, market regime, win rate, 
and coin behavior for the first two weeks of October 2026.
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

from scripts.test_1year_bb20_model3_full import evaluate_trade, get_day_key

def audit_october():
    oct_trades = []

    for sym in CHAMPIONS:
        fpath = os.path.join(DATA_DIR, f"{sym}_1h.json")
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
            curr_day = sorted_days[d_i]
            prev_day = sorted_days[d_i - 1]

            if not curr_day.startswith("2026-10"):
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
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # Long at PDL
                if not long_taken:
                    dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                    if dist_to_pdl <= 0.015 or c_l <= pdl:
                        if (c_c < c_o or (c_h - c_l) > 0) and ((next_c["high"] - c_l) / c_l >= 0.012 or (next_c2["high"] - c_l) / c_l >= 0.018) and next_c2["low"] > c_h:
                            mt = (c_h + c_l) / 2.0
                            sl = c_l * 0.9985
                            risk = mt - sl
                            if risk > 0:
                                for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                    if candles[w_idx]["low"] <= sl:
                                        break
                                    if candles[w_idx]["low"] <= mt:
                                        long_taken = True
                                        oct_trades.append(evaluate_trade(candles, w_idx, "LONG", mt, sl, risk, sym, curr_day))
                                        break

                # Short at PDH
                if not short_taken:
                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    if dist_to_pdh <= 0.015 or c_h >= pdh:
                        if (c_c > c_o or (c_h - c_l) > 0) and ((c_h - next_c["low"]) / c_h >= 0.012 or (c_h - next_c2["low"]) / c_h >= 0.018) and next_c2["high"] < c_l:
                            mt = (c_h + c_l) / 2.0
                            sl = c_h * 1.0015
                            risk = sl - mt
                            if risk > 0:
                                for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                    if candles[w_idx]["high"] >= sl:
                                        break
                                    if candles[w_idx]["high"] >= mt:
                                        short_taken = True
                                        oct_trades.append(evaluate_trade(candles, w_idx, "SHORT", mt, sl, risk, sym, curr_day))
                                        break

                if long_taken and short_taken:
                    break

    oct_trades.sort(key=lambda t: t["fill_time"])
    return oct_trades

def main():
    trades = audit_october()
    print("=" * 85)
    print("🍁 OCTOBER 2026 FORENSIC TRADING AUDIT (OCT 1 - OCT 15, 2026)")
    print("=" * 85)
    print(f"Total October Trades Found: {len(trades)}")

    # Daily breakdown
    by_day = defaultdict(lambda: {"trades": 0, "wins": 0, "saves": 0, "losses": 0, "pnl_r": 0.0})
    for t in trades:
        d = t["day"]
        by_day[d]["trades"] += 1
        by_day[d]["pnl_r"] += t["pnl_r"]
        if "WIN" in t["outcome"]:
            by_day[d]["wins"] += 1
        elif "SAVE" in t["outcome"]:
            by_day[d]["saves"] += 1
        else:
            by_day[d]["losses"] += 1

    print("\n📅 DAY-BY-DAY OCTOBER PERFORMANCE:")
    print("-" * 85)
    print(f"{'Date':<12} | {'Trades':<8} | {'Wins':<6} | {'BE Saves':<10} | {'Losses':<8} | {'Net R PnL':<10}")
    print("-" * 85)

    tot_trades = len(trades)
    tot_wins = sum(1 for t in trades if "WIN" in t["outcome"])
    tot_saves = sum(1 for t in trades if "SAVE" in t["outcome"])
    tot_losses = sum(1 for t in trades if "LOSS" in t["outcome"] or "SL" in t["outcome"])
    tot_r = sum(t["pnl_r"] for t in trades)

    for d in sorted(by_day.keys()):
        stat = by_day[d]
        print(f"{d:<12} | {stat['trades']:<8} | {stat['wins']:<6} | {stat['saves']:<10} | {stat['losses']:<8} | {stat['pnl_r']:+6.2f}R")

    print("-" * 85)
    print(f"{'TOTAL (OCT)':<12} | {tot_trades:<8} | {tot_wins:<6} | {tot_saves:<10} | {tot_losses:<8} | {tot_r:+6.2f}R")
    print("=" * 85)

    win_rate = (tot_wins / tot_trades * 100) if tot_trades else 0
    green_rate = ((tot_wins + tot_saves) / tot_trades * 100) if tot_trades else 0
    print(f"• Pure Win Rate: {win_rate:.2f}%")
    print(f"• Total Green / Safe Rate (Wins + BE Saves): {green_rate:.2f}%")
    print(f"• Total Losses: {tot_losses} ({(tot_losses/tot_trades*100):.2f}%)")

if __name__ == "__main__":
    main()
