import sqlite3

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("SELECT id, symbol, side, timeframe, entry_price, exit_price, pnl_usdt, roi_pct, status, autopsy_diagnosis FROM paper_trades WHERE symbol LIKE '%ATOM%' ORDER BY id DESC LIMIT 2")
for r in c.fetchall():
    print(r)
