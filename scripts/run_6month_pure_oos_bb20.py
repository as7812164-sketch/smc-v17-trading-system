"""
PURE 6-MONTH OUT-OF-SAMPLE (OOS) AUDIT: BB 2.0 MODEL 3 (APRIL 1, 2026 - OCTOBER 14, 2026)
==========================================================================================
- Starting Capital: $500.00 USDT fresh on April 1, 2026 (Zero carryover from prior period)
- Scope: Exactly the most recent 6.5 months (April 1 to October 14, 2026)
- Dataset: Top-20 Champions (Hourly & 15m real candles)
- Strategy: Extreme OB at PDH/PDL Sweep + 50% MT Limit Retest + Stepped Trailing SL
- Architecture: 10 Isolated Deca Sections ($50.00 each)
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
    print("=" * 90)
    print("🛡️ PURE 6-MONTH OUT-OF-SAMPLE (OOS) AUDIT: BB 2.0 MODEL 3")
    print("• Period: April 1, 2026 to October 14, 2026 (Unseen Recent 6 Months)")
    print("• Starting Capital: $500.00 USDT across 10 Deca Sections ($50 each)")
    print("=" * 90)

    all_oos_trades = []

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

            # Filter for pure OOS period: April 1, 2026 onwards
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
                                        all_oos_trades.append(evaluate_trade(candles, w_idx, "LONG", mt, sl, risk, sym, curr_day))
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
                                        all_oos_trades.append(evaluate_trade(candles, w_idx, "SHORT", mt, sl, risk, sym, curr_day))
                                        break

                if long_taken and short_taken:
                    break

    all_oos_trades.sort(key=lambda t: t["fill_time"])
    print(f"Total OOS Trades in 6-Month Period (Apr - Oct 2026): {len(all_oos_trades)}")

    def run_simulation(risk_pct: float, label: str, is_flat: bool = False):
        sections = {i: {"id": i, "balance": 50.0, "peak": 50.0, "busy_until": 0, "trades": 0, "wins": 0, "saves": 0, "losses": 0, "pnl": 0.0} for i in range(1, 11)}
        monthly_pnl = defaultdict(float)
        executed = []

        for t in all_oos_trades:
            sec_id = PAIR_MAPPING.get(t["symbol"], 1)
            sec = sections[sec_id]
            if sec["busy_until"] > t["fill_time"]:
                continue
            sec["busy_until"] = t["exit_time"]
            sec["trades"] += 1

            r_pnl = t["pnl_r"]
            if is_flat:
                risk_usd = 10.0
            else:
                risk_usd = sec["balance"] * risk_pct

            dollar_pnl = risk_usd * r_pnl
            sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))
            sec["pnl"] = round(sec["pnl"] + dollar_pnl, 2)
            if sec["balance"] > sec["peak"]:
                sec["peak"] = sec["balance"]

            m_key = t["day"][:7]
            monthly_pnl[m_key] += dollar_pnl

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
            "label": label,
            "total_trades": tot_exec,
            "wins": tot_wins,
            "saves": tot_saves,
            "losses": tot_losses,
            "win_rate": win_rate,
            "green_rate": green_rate,
            "loss_rate": loss_rate,
            "initial": 500.0,
            "final": tot_eq,
            "profit": net_profit,
            "roi_pct": roi_pct,
            "max_dd": max_dd,
            "sections": sections,
            "monthly_pnl": dict(monthly_pnl)
        }

    res_flat = run_simulation(0.0, "A. Flat Risk ($10/trade Fixed)", is_flat=True)
    res_2pct = run_simulation(0.02, "B. Deca Conservative (2% Section Risk)")
    res_5pct = run_simulation(0.05, "C. Deca Aggressive (5% Section Risk)")

    print("\n" + "=" * 90)
    print("🏆 6-MONTH PURE OUT-OF-SAMPLE (OOS) OFFICIAL RESULTS ($500 START)")
    print("=" * 90)

    for res in [res_flat, res_2pct, res_5pct]:
        print(f"\n--- {res['label']} ---")
        print(f"• Total Executed OOS Trades: {res['total_trades']}")
        print(f"• Pure Wins: {res['wins']} | Fee Shield Saves (BE): {res['saves']} | Losses (SL): {res['losses']}")
        print(f"• Pure Win Rate: {res['win_rate']:.2f}%")
        print(f"• Total Green / Protected Rate: {res['green_rate']:.2f}%")
        print(f"• Loss Rate: {res['loss_rate']:.2f}%")
        print(f"• Starting Balance: ${res['initial']:.2f} USDT")
        print(f"• Final Balance: ${res['final']:,.2f} USDT")
        print(f"• Net Profit: ${res['profit']:+,.2f} USDT ({res['roi_pct']:+,.1f}%)")
        print(f"• Max Account Drawdown: {res['max_dd']:.2f}%")

    print("\n" + "-" * 90)
    print("📅 MONTH-BY-MONTH OOS BREAKDOWN (5% Aggressive Compounding Mode):")
    print("-" * 90)
    for m, pnl in sorted(res_5pct["monthly_pnl"].items()):
        print(f"  {m}: ${pnl:+12,.2f} USDT")

    print("\n" + "-" * 90)
    print("🧩 SECTION-BY-SECTION OOS BALANCES (2% Conservative Mode):")
    print("-" * 90)
    for s_id in range(1, 11):
        s = res_2pct["sections"][s_id]
        assigned = [c.replace("USDT","") for c, sid in PAIR_MAPPING.items() if sid == s_id]
        gain = (s['balance'] - 50.0) / 50.0 * 100
        print(f"Sec #{s['id']:<2} ({', '.join(assigned):<14}) | Final: ${s['balance']:<8.2f} | PnL: ${s['pnl']:+8.2f} ({gain:+6.1f}%) | Trades: {s['trades']}")

if __name__ == "__main__":
    main()
