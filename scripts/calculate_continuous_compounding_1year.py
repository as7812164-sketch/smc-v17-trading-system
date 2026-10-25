import os
import sys
import json
from collections import defaultdict
from datetime import datetime, timezone

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the exact engines from audit_1year_bb30_vs_bb35
from scripts.audit_1year_bb30_vs_bb35 import (
    CHAMPIONS,
    PAIR_MAPPING,
    CACHE_DIR,
    run_bb30_all,
    run_bb35_backtest
)

def simulate_continuous_compounding_by_month(all_trades, start_balance=500.0, risk_pct=0.05):
    """
    Runs CONTINUOUS COMPOUNDING across the entire 1 year dataset,
    tracking the exact state at the boundary of each month!
    """
    # 10 isolated sections
    sections = {}
    init_per_sec = start_balance / 10.0
    for sid in range(1, 11):
        sections[str(sid)] = {
            "balance": init_per_sec,
            "busy_until": 0,
            "wins": 0,
            "saves": 0,
            "losses": 0,
            "trades": 0
        }

    # Sort trades chronologically
    sorted_trades = sorted(all_trades, key=lambda x: x["fill_time"])
    
    # Identify unique months in order
    months_order = sorted(list(set(t["day"][:7] for t in sorted_trades)))

    monthly_records = []
    trade_idx = 0
    total_trades_count = len(sorted_trades)

    prev_month_end_equity = start_balance

    for m in months_order:
        month_start_equity = sum(s["balance"] for s in sections.values())
        month_trades = 0
        month_wins = 0
        month_saves = 0
        month_losses = 0

        # Process trades belonging to this month
        while trade_idx < total_trades_count and sorted_trades[trade_idx]["day"].startswith(m):
            t = sorted_trades[trade_idx]
            trade_idx += 1

            sym = t["symbol"]
            sec_id = str(PAIR_MAPPING.get(sym, 1))
            sec = sections[sec_id]

            # Collision check: Section cannot take overlapping trade
            if t["fill_time"] < sec["busy_until"]:
                continue

            sec["busy_until"] = t["exit_time"]
            sec["trades"] += 1
            month_trades += 1

            dollar_pnl = (sec["balance"] * risk_pct) * t["pnl_r"]
            sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))

            if t["outcome"] == "WIN":
                sec["wins"] += 1
                month_wins += 1
            elif t["outcome"] == "FEE_SHIELD_SAVE":
                sec["saves"] += 1
                month_saves += 1
            else:
                sec["losses"] += 1
                month_losses += 1

        month_end_equity = sum(s["balance"] for s in sections.values())
        month_pnl = month_end_equity - month_start_equity
        month_roi = (month_pnl / month_start_equity) * 100.0 if month_start_equity > 0 else 0.0
        
        cumulative_pnl = month_end_equity - start_balance
        cumulative_roi = (cumulative_pnl / start_balance) * 100.0

        pure_wr = (month_wins / month_trades * 100.0) if month_trades > 0 else 0.0
        green_rate = ((month_wins + month_saves) / month_trades * 100.0) if month_trades > 0 else 0.0

        monthly_records.append({
            "month": m,
            "start_equity": round(month_start_equity, 2),
            "end_equity": round(month_end_equity, 2),
            "month_pnl": round(month_pnl, 2),
            "month_roi_pct": round(month_roi, 2),
            "cumulative_roi_pct": round(cumulative_roi, 2),
            "trades": month_trades,
            "wins": month_wins,
            "saves": month_saves,
            "losses": month_losses,
            "win_rate": round(pure_wr, 2),
            "green_rate": round(green_rate, 2),
            "sections_snapshot": {sid: round(s["balance"], 2) for sid, s in sections.items()}
        })

    return monthly_records

def main():
    print("Loading 1-Year historical datasets & running Continuous Compounding simulation...")
    bb30_trades = run_bb30_all()
    bb35_trades = run_bb35_backtest(period_filter=None)

    print(f"BB 3.0 Total raw trades: {len(bb30_trades)}")
    print(f"BB 3.5 Total raw trades: {len(bb35_trades)}")

    comp_bb30 = simulate_continuous_compounding_by_month(bb30_trades, start_balance=500.0)
    comp_bb35 = simulate_continuous_compounding_by_month(bb35_trades, start_balance=500.0)

    out = {
        "bb30": comp_bb30,
        "bb35": comp_bb35
    }

    with open("scripts/continuous_compounding_1year_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print("\n" + "=" * 100)
    print("CONTINUOUS COMPOUNDING 1-YEAR FORENSIC REPORT ($500 START)")
    print("=" * 100)
    print(f"{'Month':<8} | {'BB 3.0 End Eq':<14} | {'BB 3.0 Mo.ROI':<14} | {'BB 3.5 End Eq':<14} | {'BB 3.5 Mo.ROI':<14} | {'BB 3.5 Win%':<11} | {'BB 3.5 Green%'}")
    print("-" * 100)

    for i in range(len(comp_bb35)):
        m35 = comp_bb35[i]
        m30 = comp_bb30[i]
        print(f"{m35['month']:<8} | ${m30['end_equity']:>10.2f}    | {m30['month_roi_pct']:>+10.2f}%   | ${m35['end_equity']:>10.2f}    | {m35['month_roi_pct']:>+10.2f}%   | {m35['win_rate']:>8.1f}%  | {m35['green_rate']:>8.1f}%")

if __name__ == "__main__":
    main()
