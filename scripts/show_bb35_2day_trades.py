import sys
import os
import json
import sqlite3
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
RESEARCH_DIR = os.path.join(ROOT_DIR, "scratch", "bb35_research")
if RESEARCH_DIR not in sys.path:
    sys.path.insert(0, RESEARCH_DIR)

from bb35_backtest import run_bb35_backtest

def main():
    print("=" * 110)
    print("🎯 BB 3.5 RECENT 2-DAY FORENSIC TRADE AUDIT")
    print("=" * 110)

    # 1. 15m Real Candlestick Trades for Oct 15 & Oct 16
    oct_trades = run_bb35_backtest("2026-10")
    two_days_trades = [t for t in oct_trades if t.get("day") in ("2026-10-15", "2026-10-16")]

    print(f"\n[PART 1] BB 3.5 15M CANDLE TRADES (October 15 & 16, 2026): {len(two_days_trades)} Trades")
    print("-" * 110)
    print(f"{'Date':<11} | {'Symbol':<14} | {'Side':<6} | {'Entry':<12} | {'Exit':<12} | {'Outcome':<18} | {'PnL (R)':<10} | {'Max R'}")
    print("-" * 110)

    total_r = 0.0
    wins = 0
    saves = 0
    losses = 0

    for t in sorted(two_days_trades, key=lambda x: x["fill_time"]):
        fill_dt = datetime.fromtimestamp(t["fill_time"] / 1000.0, tz=timezone.utc).strftime("%m-%d %H:%M")
        sym = t["symbol"]
        side = t["side"]
        entry = t["entry"]
        exit_p = t["exit"]
        outcome = t["outcome"]
        pnl_r = t["pnl_r"]
        max_r = t.get("highest_r", 0.0)

        total_r += pnl_r
        if outcome == "WIN":
            wins += 1
            badge = "🟢 WIN"
        elif outcome == "FEE_SHIELD_SAVE":
            saves += 1
            badge = "🛡️ FEE SHIELD (BE)"
        else:
            losses += 1
            badge = "🔴 LOSS"

        print(f"{fill_dt:<11} | {sym:<14} | {side:<6} | {entry:<12.5f} | {exit_p:<12.5f} | {badge:<18} | {pnl_r:>+8.2f}R | {max_r:>5.2f}R")

    print("-" * 110)
    tot = wins + saves + losses
    win_rate = (wins / tot * 100.0) if tot else 0.0
    green_rate = ((wins + saves) / tot * 100.0) if tot else 0.0
    print(f"Summary: Total: {tot} | Wins: {wins} | Saves: {saves} | Losses: {losses} | Pure WinRate: {win_rate:.1f}% | GreenRate: {green_rate:.1f}% | Net R: {total_r:+.2f}R")

    # 2. Check Shadow Database
    shadow_db = os.path.join(RESEARCH_DIR, "bb35_shadow.db")
    if os.path.exists(shadow_db):
        conn = sqlite3.connect(shadow_db)
        c = conn.cursor()
        print("\n" + "=" * 110)
        print("[PART 2] BB 3.5 SHADOW DAEMON LIVE MONITORING LOGS (Real-Time Background Sentinel)")
        print("=" * 110)
        try:
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in c.fetchall()]
            for tbl in tables:
                c.execute(f"SELECT count(*) FROM {tbl}")
                cnt = c.fetchone()[0]
                print(f"Shadow Table `{tbl}`: {cnt} records")
                c.execute(f"SELECT * FROM {tbl} ORDER BY rowid DESC LIMIT 5")
                rows = c.fetchall()
                for r in rows:
                    print("  ->", r)
        except Exception as e:
            print(f"Shadow DB read error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    main()
