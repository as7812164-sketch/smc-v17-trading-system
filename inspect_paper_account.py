import sqlite3
import json
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- PAPER ACCOUNTS 1-10 ---")
for r in c.execute("SELECT * FROM paper_account WHERE id BETWEEN 1 AND 10;").fetchall():
    d = dict(r)
    print(f"ID={d['id']} Init=${d.get('initial_balance')} Curr=${d.get('current_balance')} Wins={d.get('win_count')} Losses={d.get('loss_count')} TotalPnL={d.get('total_pnl')}")

print("\n--- OPEN TRADES ---")
for r in c.execute("SELECT id, symbol, side, entry_price, position_size_usdt, account_id, timeframe FROM paper_trades WHERE status='OPEN';").fetchall():
    print(dict(r))

print("\n--- PAPER TRADES SCHEMA ---")
cols = [col[1] for col in c.execute("PRAGMA table_info(paper_trades);").fetchall()]
print(cols)

print("\n--- RECENT 10 PAPER TRADES ---")
for r in c.execute("SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, status FROM paper_trades ORDER BY id DESC LIMIT 10;").fetchall():
    print(dict(r))
