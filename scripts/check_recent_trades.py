import os
import sys
import sqlite3
import json
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')

IST = timezone(timedelta(hours=5, minutes=30))
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "smc_v17.db")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in c.fetchall()]
print(f"Database Tables: {tables}")

# Check paper_trades
if "paper_trades" in tables:
    c.execute("PRAGMA table_info(paper_trades);")
    cols = [col[1] for col in c.fetchall()]
    print(f"Columns in paper_trades: {cols}")

    # Fetch all trades
    c.execute("SELECT * FROM paper_trades ORDER BY id DESC;")
    all_trades = [dict(zip(cols, r)) for r in c.fetchall()]
    print(f"Total trades in database: {len(all_trades)}")

    # Check trades from yesterday (2026-10-06) and today (2026-10-07)
    recent_trades = []
    for t in all_trades:
        # Check created_at or timestamp
        t_time = t.get("created_at") or t.get("entry_time") or t.get("timestamp") or ""
        # Check if 2026-10-06 or 2026-10-07 or recently closed
        recent_trades.append(t)

    print(f"\nLast 15 Trades:")
    for t in all_trades[:15]:
        print(f"ID: {t.get('id')} | Section: {t.get('account_id')} | Symbol: {t.get('symbol')} | Side: {t.get('side')} | Status: {t.get('status')} | PnL: ${t.get('pnl')} ({t.get('pnl_pct')}%) | Reason: {t.get('exit_reason')} | Created: {t.get('created_at')} | Closed: {t.get('closed_at')}")

# Check sections balances
if "paper_sections" in tables or "paper_account" in tables:
    table_name = "paper_sections" if "paper_sections" in tables else "paper_account"
    c.execute(f"PRAGMA table_info({table_name});")
    cols_acc = [col[1] for col in c.fetchall()]
    c.execute(f"SELECT * FROM {table_name};")
    accs = [dict(zip(cols_acc, r)) for r in c.fetchall()]
    print(f"\nAccount / Section Balances ({table_name}):")
    for a in accs:
        print(f"Section/Account: {a.get('id') or a.get('account_id')} | Balance: ${a.get('current_balance')} | Total PnL: ${a.get('total_pnl')} | Wins: {a.get('winning_trades')} | Losses: {a.get('losing_trades')}")

# Check live engine logs or recent executed trades
