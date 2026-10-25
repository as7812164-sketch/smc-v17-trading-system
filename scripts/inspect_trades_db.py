import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import get_connection

with get_connection() as conn:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_trades)").fetchall()]
    print("Columns:", cols)
    
    total = conn.execute("SELECT COUNT(*) FROM paper_trades").fetchone()[0]
    print(f"Total trades: {total}")
    
    status_counts = conn.execute("SELECT status, COUNT(*) FROM paper_trades GROUP BY status").fetchall()
    print("Status counts:", [dict(status=r[0], count=r[1]) for r in status_counts])
    
    rows = conn.execute("SELECT id, symbol, side, timeframe, entry_price, exit_price, status, pnl_usdt, net_pnl_usdt, mode, account_id, entry_time FROM paper_trades ORDER BY id DESC LIMIT 10").fetchall()
    print("\nRecent 10 trades:")
    for r in rows:
        print(dict(r))
