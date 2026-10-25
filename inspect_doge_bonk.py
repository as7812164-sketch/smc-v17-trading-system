import sqlite3
import json

conn = sqlite3.connect('database/smc_v17.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT * FROM paper_trades WHERE symbol IN ('DOGEUSDT', '1000BONKUSDT', 'BONKUSDT') ORDER BY id DESC LIMIT 5")
rows = c.fetchall()
for r in rows:
    print(dict(r))
