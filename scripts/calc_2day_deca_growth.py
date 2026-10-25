import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
RESEARCH_DIR = os.path.join(ROOT_DIR, "scratch", "bb35_research")
if RESEARCH_DIR not in sys.path:
    sys.path.insert(0, RESEARCH_DIR)

from bb35_backtest import run_bb35_backtest
from bb35_engine import PAIR_MAPPING

def run_sim(start_total, label):
    oct_trades = run_bb35_backtest("2026-10")
    two_days = [t for t in oct_trades if t.get("day") in ("2026-10-15", "2026-10-16")]
    two_days.sort(key=lambda x: x["fill_time"])

    sec_names = {
        1: "Section 1 (BTC/ETH)",
        2: "Section 2 (SOL/BNB)",
        3: "Section 3 (AVAX/DOGE)",
        4: "Section 4 (DOT/LINK)",
        5: "Section 5 (LTC/NEAR)",
        6: "Section 6 (OP/RENDER)",
        7: "Section 7 (SUI/TIA)",
        8: "Section 8 (UNI/XRP)",
        9: "Section 9 (PEPE/APT)",
        10: "Section 10 (ARB/FET)",
    }

    base_sec_bal = start_total / 10.0
    sections = {
        i: {
            "name": sec_names[i],
            "start": base_sec_bal,
            "balance": base_sec_bal,
            "busy_until": 0,
            "trades": 0,
            "wins": 0,
            "saves": 0,
            "losses": 0,
            "history": []
        }
        for i in range(1, 11)
    }

    for t in two_days:
        s_id = PAIR_MAPPING[t["symbol"]]
        sec = sections[s_id]

        if sec["busy_until"] > t["fill_time"]:
            continue

        sec["busy_until"] = t["exit_time"]
        sec["trades"] += 1

        risk_dollars = sec["balance"] * 0.05
        dollar_pnl = risk_dollars * t["pnl_r"]
        prev_bal = sec["balance"]
        sec["balance"] = round(sec["balance"] + dollar_pnl, 2)

        if t["outcome"] == "WIN":
            sec["wins"] += 1
        elif t["outcome"] == "FEE_SHIELD_SAVE":
            sec["saves"] += 1
        else:
            sec["losses"] += 1

        sec["history"].append({
            "symbol": t["symbol"],
            "side": t["side"],
            "pnl_r": t["pnl_r"],
            "dollar_pnl": dollar_pnl,
            "new_balance": sec["balance"]
        })

    final_total = sum(s["balance"] for s in sections.values())
    net_pnl = final_total - start_total
    roi_pct = (net_pnl / start_total) * 100.0

    print("=" * 95)
    print(f"📊 {label.upper()}: 2-DAY DECA COMPOUNDING BREAKDOWN")
    print(f"Starting Portfolio Equity: ${start_total:.2f} USDT across 10 Sections (${base_sec_bal:.2f} each)")
    print(f"Final Portfolio Equity   : ${final_total:.2f} USDT")
    print(f"Net Profit (2 Days)      : ${net_pnl:+.2f} USDT ({roi_pct:+.2f}% 2-Day Return)")
    print("=" * 95)

    print(f"{'Section':<24} | {'Start Bal':<11} | {'Final Bal':<11} | {'Net PnL':<11} | {'Trades':<8} | {'Record (W-S-L)':<14}")
    print("-" * 95)
    for i in range(1, 11):
        s = sections[i]
        sec_net = s["balance"] - s["start"]
        record = f"{s['wins']}W {s['saves']}S {s['losses']}L"
        print(f"{s['name']:<24} | ${s['start']:<10.2f} | ${s['balance']:<10.2f} | ${sec_net:>+9.2f} | {s['trades']:<8} | {record:<14}")
    print("=" * 95)

if __name__ == "__main__":
    run_sim(500.00, "Scenario 1: Standard $500.00 Baseline")
    print("\n")
    run_sim(575.06, "Scenario 2: Current Live Portfolio Equity ($575.06)")
