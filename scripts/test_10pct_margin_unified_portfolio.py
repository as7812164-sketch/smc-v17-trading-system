import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
import json
from datetime import datetime, timezone

def run_10pct_portfolio_audit():
    with open("september_deca_trailing_oos_results.json", "r", encoding="utf-8") as f:
        data_sep = json.load(f)
    trades_sep = data_sep["trades"]
    
    print(f"Loaded {len(trades_sep)} executed trades for September 2026 OOS.\n")
    
    # -------------------------------------------------------------------------
    # SIMULATION 1: DYNAMIC 10% OF TOTAL PORTFOLIO EQUITY (COMPOUNDING)
    # Starting Capital = $500.00
    # Every trade uses Margin = 10% of current equity at entry time.
    # -------------------------------------------------------------------------
    def sim_dynamic_10pct(trades_list, start_cap=500.0, max_concurrent=10):
        # Sort trades by entry time
        trades = sorted(trades_list, key=lambda x: x["entry_time"])
        
        equity = start_cap
        peak_equity = start_cap
        max_dd_pct = 0.0
        
        # Track events: (time, event_type, trade_info)
        # We need a proper chronological event queue to handle concurrent trades and accurate balance
        events = []
        for i, t in enumerate(trades):
            events.append((t["entry_time"], "ENTRY", i, t))
            events.append((t["exit_time"], "EXIT", i, t))
        events.sort(key=lambda x: (x[0], 0 if x[1] == "EXIT" else 1)) # Exits processed first if same ms
        
        open_positions = {}
        trade_results = []
        
        for ts, ev_type, idx, t in events:
            if ev_type == "ENTRY":
                if len(open_positions) >= max_concurrent:
                    # Skip if maximum concurrent capacity reached
                    continue
                # Calculate margin = 10% of current equity
                margin = round(equity * 0.10, 2)
                open_positions[idx] = {
                    "trade": t,
                    "margin": margin,
                    "entry_time": ts
                }
            elif ev_type == "EXIT":
                if idx in open_positions:
                    pos = open_positions.pop(idx)
                    margin = pos["margin"]
                    roi = t["realized_roi"]
                    pnl = round(margin * (roi / 100.0), 2)
                    equity = round(equity + pnl, 2)
                    
                    if equity > peak_equity:
                        peak_equity = equity
                    dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
                    if dd > max_dd_pct:
                        max_dd_pct = dd
                        
                    trade_results.append({
                        "symbol": t["symbol"],
                        "side": t["side"],
                        "roi": roi,
                        "margin": margin,
                        "pnl": pnl,
                        "equity_after": equity
                    })
                    
        return {
            "mode": "DYNAMIC_10PCT_EQUITY",
            "start_capital": start_cap,
            "final_equity": equity,
            "net_pnl": equity - start_cap,
            "growth_pct": ((equity - start_cap) / start_cap) * 100.0,
            "max_dd_pct": max_dd_pct,
            "total_trades_taken": len(trade_results),
            "trade_results": trade_results
        }

    # -------------------------------------------------------------------------
    # SIMULATION 2: FIXED $50 MARGIN (FLAT 10% OF $500 STARTING CAPITAL)
    # Non-compounding position size ($50 constant margin) from unified $500 pool
    # -------------------------------------------------------------------------
    def sim_fixed_50_margin(trades_list, start_cap=500.0, max_concurrent=10):
        trades = sorted(trades_list, key=lambda x: x["entry_time"])
        equity = start_cap
        peak_equity = start_cap
        max_dd_pct = 0.0
        
        events = []
        for i, t in enumerate(trades):
            events.append((t["entry_time"], "ENTRY", i, t))
            events.append((t["exit_time"], "EXIT", i, t))
        events.sort(key=lambda x: (x[0], 0 if x[1] == "EXIT" else 1))
        
        open_positions = {}
        trade_results = []
        fixed_margin = 50.0
        
        for ts, ev_type, idx, t in events:
            if ev_type == "ENTRY":
                if len(open_positions) >= max_concurrent:
                    continue
                open_positions[idx] = {
                    "trade": t,
                    "margin": fixed_margin,
                    "entry_time": ts
                }
            elif ev_type == "EXIT":
                if idx in open_positions:
                    pos = open_positions.pop(idx)
                    margin = pos["margin"]
                    roi = t["realized_roi"]
                    pnl = round(margin * (roi / 100.0), 2)
                    equity = round(equity + pnl, 2)
                    
                    if equity > peak_equity:
                        peak_equity = equity
                    dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
                    if dd > max_dd_pct:
                        max_dd_pct = dd
                        
                    trade_results.append({
                        "symbol": t["symbol"],
                        "side": t["side"],
                        "roi": roi,
                        "margin": margin,
                        "pnl": pnl,
                        "equity_after": equity
                    })
                    
        return {
            "mode": "FIXED_50_MARGIN",
            "start_capital": start_cap,
            "final_equity": equity,
            "net_pnl": equity - start_cap,
            "growth_pct": ((equity - start_cap) / start_cap) * 100.0,
            "max_dd_pct": max_dd_pct,
            "total_trades_taken": len(trade_results),
            "trade_results": trade_results
        }

    res_dyn_sep = sim_dynamic_10pct(trades_sep, 500.0)
    res_fix_sep = sim_fixed_50_margin(trades_sep, 500.0)
    
    print("========================================================================================")
    print("SEPTEMBER 2026 (LAST MONTH OOS): 10% MARGIN PORTFOLIO AUDIT ($500 START)")
    print("========================================================================================")
    print(f"Model A: Dynamic 10% Compounding (Margin = 10% of Current Total Equity at Entry)")
    print(f"  - Trades Taken:     {res_dyn_sep['total_trades_taken']} / {len(trades_sep)}")
    print(f"  - Starting Balance: ${res_dyn_sep['start_capital']:.2f}")
    print(f"  - Final Balance:    ${res_dyn_sep['final_equity']:.2f} (+${res_dyn_sep['net_pnl']:.2f} USDT)")
    print(f"  - Net Growth %:     +{res_dyn_sep['growth_pct']:.2f}%")
    print(f"  - Max Drawdown:     {res_dyn_sep['max_dd_pct']:.2f}%\n")
    
    print(f"Model B: Fixed $50 Margin (Flat 10% of Starting $500, Non-Compounding Sizing)")
    print(f"  - Trades Taken:     {res_fix_sep['total_trades_taken']} / {len(trades_sep)}")
    print(f"  - Starting Balance: ${res_fix_sep['start_capital']:.2f}")
    print(f"  - Final Balance:    ${res_fix_sep['final_equity']:.2f} (+${res_fix_sep['net_pnl']:.2f} USDT)")
    print(f"  - Net Growth %:     +{res_fix_sep['growth_pct']:.2f}%")
    print(f"  - Max Drawdown:     {res_fix_sep['max_dd_pct']:.2f}%\n")
    
    print(f"Model C: Deca Compounding Matrix (10 Isolated $50 Slots - Benchmark from Previous Audit)")
    print(f"  - Final Balance:    $643.08 USDT (+28.62% Net Growth) | Max DD: 2.25% avg")
    print("========================================================================================\n")
    
    # Also test on August 2026 data if file exists
    if os.path.exists("august_deca_trailing_oos_results.json"):
        with open("august_deca_trailing_oos_results.json", "r", encoding="utf-8") as f:
            data_aug = json.load(f)
        trades_aug = data_aug["trades"]
        res_dyn_aug = sim_dynamic_10pct(trades_aug, 500.0)
        res_fix_aug = sim_fixed_50_margin(trades_aug, 500.0)
        print("========================================================================================")
        print("AUGUST 2026 OOS: 10% MARGIN PORTFOLIO AUDIT ($500 START)")
        print("========================================================================================")
        print(f"Model A: Dynamic 10% Compounding (Margin = 10% of Current Total Equity at Entry)")
        print(f"  - Trades Taken:     {res_dyn_aug['total_trades_taken']} / {len(trades_aug)}")
        print(f"  - Starting Balance: ${res_dyn_aug['start_capital']:.2f}")
        print(f"  - Final Balance:    ${res_dyn_aug['final_equity']:.2f} (+${res_dyn_aug['net_pnl']:.2f} USDT)")
        print(f"  - Net Growth %:     +{res_dyn_aug['growth_pct']:.2f}%")
        print(f"  - Max Drawdown:     {res_dyn_aug['max_dd_pct']:.2f}%\n")
        
        print(f"Model B: Fixed $50 Margin (Flat 10% of Starting $500, Non-Compounding Sizing)")
        print(f"  - Trades Taken:     {res_fix_aug['total_trades_taken']} / {len(trades_aug)}")
        print(f"  - Starting Balance: ${res_fix_aug['start_capital']:.2f}")
        print(f"  - Final Balance:    ${res_fix_aug['final_equity']:.2f} (+${res_fix_aug['net_pnl']:.2f} USDT)")
        print(f"  - Net Growth %:     +{res_fix_aug['growth_pct']:.2f}%")
        print(f"  - Max Drawdown:     {res_fix_aug['max_dd_pct']:.2f}%\n")
        
        print(f"Model C: Deca Compounding Matrix (10 Isolated $50 Slots - Benchmark from Previous Audit)")
        print(f"  - Final Balance:    $655.95 USDT (+31.19% Net Growth) | Max DD: 3.57% avg")
        print("========================================================================================\n")
    else:
        res_dyn_aug = None
        res_fix_aug = None

    # Save results
    with open("audit_10pct_portfolio_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "september": {"dynamic_10pct": res_dyn_sep, "fixed_50": res_fix_sep},
            "august": {"dynamic_10pct": res_dyn_aug, "fixed_50": res_fix_aug} if res_dyn_aug else None
        }, f, indent=2)

if __name__ == "__main__":
    run_10pct_portfolio_audit()
