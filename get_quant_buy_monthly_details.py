import json
import os
import sys
from datetime import datetime
from collections import defaultdict

# Load the backtest logic and run detailed month-by-month audit
from run_full_quant_buy_1year_backtest import run_backtest, simulate_compounding

b_4h, b_all, q_4h, q_all = run_backtest()

def analyze_monthly_and_assets(trades, name):
    trades.sort(key=lambda x: x["time"])
    
    # Sequential compounding run
    executed = []
    active_exit = 0
    for t in trades:
        if t["time"] >= active_exit:
            executed.append(t)
            active_exit = t["exit_time"]
            
    months_data = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0, "gross_pnl": 0.0, "trades": []})
    coin_data = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0})
    
    cap = 50.0
    vault = 0.0
    ladder = []
    
    for idx, trade in enumerate(executed):
        dt = datetime.fromtimestamp(trade["time"] / 1000)
        m_key = dt.strftime("%Y-%m")
        
        net_move = trade["gross"] - 0.0016
        pos_size = cap * 5.0
        pnl = pos_size * net_move
        
        is_win = (trade["res"] == "WIN")
        if is_win:
            cap += (pnl * 0.85)
            vault += (pnl * 0.15)
        else:
            cap += pnl
            if cap < 2.0:
                cap = 0.0
                
        tot = cap + vault
        
        months_data[m_key]["total"] += 1
        coin_data[trade["sym"]]["total"] += 1
        if is_win:
            months_data[m_key]["wins"] += 1
            coin_data[trade["sym"]]["wins"] += 1
        else:
            months_data[m_key]["losses"] += 1
            coin_data[trade["sym"]]["losses"] += 1
            
        months_data[m_key]["gross_pnl"] += pnl
        months_data[m_key]["end_balance"] = round(tot, 2)
        months_data[m_key]["trades"].append({
            "idx": idx + 1,
            "sym": trade["sym"],
            "tf": trade["tf"],
            "time": dt.strftime("%Y-%m-%d %H:%M"),
            "entry": trade["entry"],
            "exit": trade["exit"],
            "res": trade["res"],
            "equity": round(tot, 2)
        })
        
    print(f"\n=======================================================")
    print(f"   MONTHLY AUDIT: {name}")
    print(f"=======================================================")
    print(f"{'Month':<10} | {'Trades':<7} | {'Wins':<5} | {'Loss':<5} | {'Win Rate':<10} | {'End Equity':<12}")
    print("-" * 62)
    
    monthly_summary = {}
    for m in sorted(months_data.keys()):
        d = months_data[m]
        wr = (d["wins"] / d["total"] * 100.0) if d["total"] > 0 else 0.0
        print(f"{m:<10} | {d['total']:<7} | {d['wins']:<5} | {d['losses']:<5} | {wr:6.2f}%    | ${d.get('end_balance', 0):>10,.2f}")
        monthly_summary[m] = {
            "month": m,
            "trades": d["total"],
            "wins": d["wins"],
            "losses": d["losses"],
            "win_rate": round(wr, 2),
            "end_balance": d.get("end_balance", 0)
        }
        
    print(f"\n--- TOP PERFORMING COINS ({name}) ---")
    sorted_coins = sorted(coin_data.items(), key=lambda x: (x[1]["wins"], x[1]["total"]), reverse=True)
    for sym, cd in sorted_coins[:10]:
        c_wr = (cd["wins"] / cd["total"] * 100.0) if cd["total"] > 0 else 0.0
        print(f"{sym:<10}: {cd['wins']}/{cd['total']} Wins ({c_wr:5.1f}%)")
        
    return monthly_summary, executed

m_q4h, ex_q4h = analyze_monthly_and_assets(q_4h, "FULL QUANT 4H BUY")
m_qall, ex_qall = analyze_monthly_and_assets(q_all, "FULL QUANT 1H+4H BUY")

audit_full = {
    "q4h_monthly": m_q4h,
    "qall_monthly": m_qall,
    "qall_executed_sample": ex_qall[:30]
}

with open("full_quant_buy_monthly_audit.json", "w", encoding="utf-8") as f:
    json.dump(audit_full, f, indent=2)

print("\nAudit complete and saved to full_quant_buy_monthly_audit.json")
