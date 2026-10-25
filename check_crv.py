import sqlite3
from config import DB_PATH
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, symbol, side, status, entry_price, exit_price, pnl_usdt FROM paper_trades WHERE symbol='CRVUSDT' ORDER BY id DESC LIMIT 5").fetchall()
for r in rows:
    print(dict(r))
