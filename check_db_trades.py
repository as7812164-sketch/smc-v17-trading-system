import sqlite3

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
rows = c.execute("SELECT id, symbol, side, entry_price, position_size_usdt, tp_price, sl_price, hard_sl_price, status, exchange, channel, roi_pct FROM paper_trades WHERE status = 'OPEN'").fetchall()
print(f"Total OPEN trades in DB: {len(rows)}")
for r in rows:
    print(r)
