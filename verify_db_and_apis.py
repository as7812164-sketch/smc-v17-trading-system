import sqlite3
import json
from pathlib import Path
from config import DB_PATH

def inspect_db():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print("Tables:", tables)

    print("\n--- OPEN TRADES IN paper_trades ---")
    open_trades = [dict(r) for r in c.execute("SELECT * FROM paper_trades WHERE status='OPEN';").fetchall()]
    print(f"Count: {len(open_trades)}")
    for t in open_trades:
        print(f"ID={t.get('id')} Sym={t.get('symbol')} Side={t.get('side')} Entry={t.get('entry_price')} Account={t.get('account_id')} Timeframe={t.get('timeframe')}")

    print("\n--- RECENT CLOSED TRADES ---")
    closed = [dict(r) for r in c.execute("SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, status, exit_reason FROM paper_trades WHERE status!='OPEN' ORDER BY id DESC LIMIT 10;").fetchall()]
    for t in closed:
        print(f"ID={t.get('id')} Sym={t.get('symbol')} Side={t.get('side')} Entry={t.get('entry_price')} Exit={t.get('exit_price')} PnL={t.get('pnl_usdt')} Status={t.get('status')} Reason={t.get('exit_reason')}")

    print("\n--- COMPOUNDING SECTIONS ---")
    sections = [dict(r) for r in c.execute("SELECT * FROM compounding_sections;").fetchall()]
    print(f"Sections count: {len(sections)}")
    for s in sections:
        print(f"Section #{s.get('section_num', s.get('id'))}: Balance=${s.get('balance')} Wins={s.get('win_count')} Losses={s.get('loss_count')} Status={s.get('status')}")

if __name__ == "__main__":
    inspect_db()
