import os
import sqlite3
import json
from datetime import datetime, timezone, timedelta

db_path = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\database\smc_v17.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]
print("Tables in smc_v17.db:", tables)

for t in tables:
    cur.execute(f"SELECT count(*) FROM {t};")
    cnt = cur.fetchone()[0]
    print(f"Table: {t} -> {cnt} rows")

# Look at schema of paper_trades or trades
if "paper_trades" in tables:
    cur.execute("PRAGMA table_info(paper_trades);")
    cols = [r[1] for r in cur.fetchall()]
    print("\npaper_trades columns:", cols)

    cur.execute("SELECT * FROM paper_trades ORDER BY id DESC LIMIT 20;")
    rows = cur.fetchall()
    print(f"\nLast {len(rows)} paper_trades:")
    for r in rows:
        print(dict(zip(cols, r)))

if "trades" in tables:
    cur.execute("PRAGMA table_info(trades);")
    cols = [r[1] for r in cur.fetchall()]
    print("\ntrades columns:", cols)

    cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 20;")
    rows = cur.fetchall()
    print(f"\nLast {len(rows)} trades:")
    for r in rows:
        print(dict(zip(cols, r)))
