import json
import sqlite3
import os
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"

def main():
    ledger_path = os.path.join(ROOT_DIR, "bb20_shadow_ledger.json")
    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    today_str = "2026-10-17"

    # Closed trades today
    closed_today = []
    for t in ledger.get("closed_trades", []):
        c_at = t.get("closed_at", "")
        f_at = t.get("filled_at", "")
        if c_at.startswith(today_str) or f_at.startswith(today_str):
            closed_today.append(t)

    # Active open positions right now
    active_positions = ledger.get("active_positions", {})

    # Armed pending limit setups
    active_setups = ledger.get("active_setups", {})

    # Single-shot executed coins today
    d_ss = ledger.get("daily_single_shot", {}).get(today_str, {})

    print("=" * 85)
    print(f"🎯 BB 3.0 SNIPER: TODAY'S TRADE AUDIT ({today_str})")
    print("=" * 85)

    print(f"\n1. CLOSED TRADES TODAY ({len(closed_today)}):")
    print("-" * 85)
    if closed_today:
        for t in closed_today:
            sym = t.get("symbol")
            side = t.get("side")
            entry = t.get("mt_entry")
            exit_p = t.get("exit_price")
            pnl = t.get("dollar_pnl")
            outcome = t.get("outcome")
            c_time = t.get("closed_at")
            sec_id = t.get("section_id")
            print(f"  • {sym} {side} (Section #{sec_id}): Entry ${entry} ➔ Exit ${exit_p} | PnL: ${pnl:+.2f} USDT ({outcome}) | Closed: {c_time}")
    else:
        print("  None")

    print(f"\n2. CURRENT ACTIVE OPEN POSITIONS RIGHT NOW ({len(active_positions)}):")
    print("-" * 85)
    if active_positions:
        for sym, p in active_positions.items():
            side = p.get("side")
            entry = p.get("mt_entry")
            sl = p.get("active_sl")
            highest_r = p.get("highest_r")
            sec_id = p.get("section_id")
            filled_at = p.get("filled_at")
            print(f"  • {sym} {side} (Section #{sec_id}): Entry ${entry} | Active SL: ${sl} | Peak Reach: +{highest_r}R | Filled: {filled_at}")
    else:
        print("  Zero active positions currently open (all flat).")

    print(f"\n3. PENDING LIMIT SETUPS ARMED TODAY WAITING FOR RETEST ({len(active_setups)}):")
    print("-" * 85)
    if active_setups:
        for sym, s in active_setups.items():
            side = s.get("side")
            entry = s.get("mt_entry")
            sl = s.get("sl")
            armed_at = s.get("armed_at")
            sec_id = s.get("section_id")
            print(f"  • {sym} {side} (Section #{sec_id}): 50% MT Limit @ ${entry} | SL: ${sl} | Armed: {armed_at}")
    else:
        print("  None")

    # Section Balances
    print(f"\n4. DECA SECTIONS STATUS AFTER TODAY'S ACTIVITY:")
    print("-" * 85)
    sections = ledger.get("sections", {})
    for s_id, sec in sorted(sections.items(), key=lambda x: int(x[0])):
        status = sec.get("status", "IDLE")
        bal = sec.get("balance", 50.0)
        pnl = sec.get("pnl_usd", 0.0)
        trades = sec.get("trades_count", 0)
        wins = sec.get("wins", 0)
        saves = sec.get("saves", 0)
        losses = sec.get("losses", 0)
        print(f"  Section #{s_id:<2} | Balance: ${bal:<6.2f} | PnL: ${pnl:<+6.2f} | Record: {wins}W {saves}S {losses}L (Total {trades}) | Status: {status}")

    print("-" * 85)
    tot_eq = sum(s.get("balance", 50.0) for s in sections.values())
    print(f"Total Deca Equity: ${tot_eq:.2f} USDT (Initial: $500.00)")
    print("=" * 85)

if __name__ == "__main__":
    main()
