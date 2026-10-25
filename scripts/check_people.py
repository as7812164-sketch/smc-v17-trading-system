import sqlite3

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("SELECT id, symbol, side, entry_price, position_size_usdt, status, pnl_usdt, pnl_pct FROM paper_trades WHERE symbol LIKE '%PEOPLE%' ORDER BY id DESC")
rows = c.fetchall()
print(f"PEOPLE trades count: {len(rows)}")
for r in rows:
    print(r)
