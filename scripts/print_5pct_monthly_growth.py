"""
Print exact month-by-month compounding growth for BB 2.0 Model 3 (5% Section Risk).
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

def main():
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
            day_buckets[get_day_key(c["time"])].append((idx, c))

        sorted_days = sorted(day_buckets.keys())
        for d_i in range(1, len(sorted_days)):
            prev_day_candles = [c for _, c in day_buckets[sorted_days[d_i - 1]]]
            curr_day_entries = day_buckets[sorted_days[d_i]]
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
                                        all_trades.append(evaluate_trade(candles, w_idx, "LONG", mt, sl, risk, sym, sorted_days[d_i]))
                                        break

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
                                        all_trades.append(evaluate_trade(candles, w_idx, "SHORT", mt, sl, risk, sym, sorted_days[d_i]))
                                        break

                if long_taken and short_taken:
                    break

    all_trades.sort(key=lambda t: t["fill_time"])

    sections = {i: {"id": i, "balance": 50.0, "busy_until": 0} for i in range(1, 11)}

    # We want to group by month and track:
    # Start balance, End balance, Net profit, Monthly ROI %, Trades, Wins/Saves/Losses
    monthly_data = {}
    current_total_eq = 500.0

    for t in all_trades:
        sec_id = PAIR_MAPPING.get(t["symbol"], 1)
        sec = sections[sec_id]

        if sec["busy_until"] > t["fill_time"]:
            continue
        sec["busy_until"] = t["exit_time"]

        m_key = t["day"][:7] # YYYY-MM
        if m_key not in monthly_data:
            monthly_data[m_key] = {
                "start_eq": current_total_eq,
                "trades": 0,
                "wins": 0,
                "saves": 0,
                "losses": 0,
                "dollar_pnl": 0.0,
                "end_eq": current_total_eq
            }

        risk_usd = sec["balance"] * 0.05
        dollar_pnl = risk_usd * t["pnl_r"]
        sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))
        current_total_eq = sum(s["balance"] for s in sections.values())

        m = monthly_data[m_key]
        m["trades"] += 1
        m["dollar_pnl"] += dollar_pnl
        m["end_eq"] = current_total_eq
        if "WIN" in t["outcome"]:
            m["wins"] += 1
        elif "SAVE" in t["outcome"]:
            m["saves"] += 1
        else:
            m["losses"] += 1

    print("=" * 105)
    print("🚀 BB 2.0 (MODEL 3) — 5% AGGRESSIVE COMPOUNDING MONTH-BY-MONTH GROWTH ($500 START)")
    print("=" * 105)
    print(f"{'MONTH':<10} | {'STARTING BALANCE':<18} | {'ENDING BALANCE':<18} | {'NET MONTH PROFIT':<18} | {'MONTHLY GAIN':<14} | {'TRADES':<7} | {'ACCURACY (W/S/L)'}")
    print("-" * 105)

    cumulative_gain = 0.0
    for m_key in sorted(monthly_data.keys()):
        m = monthly_data[m_key]
        start_b = m["start_eq"]
        end_b = m["end_eq"]
        pnl = m["dollar_pnl"]
        gain_pct = ((end_b - start_b) / start_b * 100.0) if start_b else 0.0
        tot_t = m["trades"]
        acc = ((m["wins"] + m["saves"]) / tot_t * 100.0) if tot_t else 0.0
        wsl = f"{m['wins']}W / {m['saves']}S / {m['losses']}L"
        
        print(f"{m_key:<10} | ${start_b:<17,.2f} | ${end_b:<17,.2f} | ${pnl:<+17,.2f} | {gain_pct:+12.1f}% | {tot_t:<7} | {acc:.1f}% ({wsl})")

    print("=" * 105)
    print(f"🏁 FINAL 1-YEAR BALANCE: ${current_total_eq:,.2f} USDT (Initial: $500.00 USDT | Total Gain: +{(current_total_eq - 500)/500*100:,.1f}%)")
    print("=" * 105)

if __name__ == "__main__":
    main()
