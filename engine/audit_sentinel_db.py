import sqlite3
import json
import os
import sys

db_path = r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\database\smc_v17.db'

print(f"--- DATABASE INTEGRITY AUDIT ---")
print(f"Path: {db_path}")
print(f"Exists: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Integrity check
cursor.execute("PRAGMA integrity_check;")
res = cursor.fetchall()
print("PRAGMA integrity_check:", [dict(r) for r in res])

# 2. Tables list
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r['name'] for r in cursor.fetchall()]
print("Tables:", tables)

# 3. Check paper_trades
if 'paper_trades' in tables:
    cursor.execute("SELECT count(*) as total FROM paper_trades")
    total_trades = cursor.fetchone()['total']
    
    cursor.execute("SELECT count(*) as open_cnt FROM paper_trades WHERE status='OPEN'")
    open_cnt = cursor.fetchone()['open_cnt']

    cursor.execute("SELECT count(*) as closed_cnt FROM paper_trades WHERE status!='OPEN'")
    closed_cnt = cursor.fetchone()['closed_cnt']

    print(f"\n[PAPER_TRADES] Total: {total_trades}, OPEN: {open_cnt}, CLOSED: {closed_cnt}")
    
    print("\n--- OPEN TRADES ---")
    cursor.execute("SELECT * FROM paper_trades WHERE status='OPEN'")
    open_trades = [dict(r) for r in cursor.fetchall()]
    for t in open_trades:
        print(f"ID: {t.get('id')}, Symbol: {t.get('symbol')}, Side: {t.get('side') or t.get('direction')}, "
              f"Entry: {t.get('entry_price')}, Current/Exit: {t.get('exit_price')}, PnL: {t.get('pnl') or t.get('realized_pnl')}, "
              f"Status: {t.get('status')}, Time: {t.get('entry_time')}")

    print("\n--- CLOSED TRADES SAMPLE & STATS ---")
    cursor.execute("SELECT * FROM paper_trades WHERE status!='OPEN' ORDER BY id DESC LIMIT 25")
    closed_sample = [dict(r) for r in cursor.fetchall()]
    for t in closed_sample:
        print(f"ID: {t.get('id')}, Symbol: {t.get('symbol')}, Side: {t.get('side') or t.get('direction')}, "
              f"Entry: {t.get('entry_price')}, Exit: {t.get('exit_price')}, PnL: {t.get('pnl') or t.get('realized_pnl')}, "
              f"Status: {t.get('status')}, Exit Time: {t.get('exit_time')}")

# 4. Check paper_account
if 'paper_account' in tables:
    print("\n--- PAPER_ACCOUNT ---")
    cursor.execute("SELECT * FROM paper_account")
    accounts = [dict(r) for r in cursor.fetchall()]
    total_balance = 0.0
    for a in accounts:
        print(a)
        # sum balance or equity if numeric
        bal = a.get('balance', a.get('equity', 0))
        try:
            total_balance += float(bal)
        except:
            pass
    print(f"Calculated Total Balance/Equity: {total_balance}")

# 5. Check other tables
for tbl in tables:
    if tbl not in ['paper_trades', 'paper_account']:
        cursor.execute(f"SELECT count(*) as cnt FROM {tbl}")
        cnt = cursor.fetchone()['cnt']
        print(f"Table '{tbl}' row count: {cnt}")

conn.close()
