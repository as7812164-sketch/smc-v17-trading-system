import sys
sys.path.append("C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system")
from database.db import get_connection

with get_connection() as conn:
    rows = conn.execute("SELECT id, symbol, side, status, account_id, mode FROM paper_trades WHERE status = 'OPEN'").fetchall()
    print("Rows count:", len(rows))
    for r in rows:
        print(dict(r))
