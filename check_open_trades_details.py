import sqlite3
conn = sqlite3.connect('database/smc_v17.db')
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, symbol, side, timeframe, mode, tier, sentry_reasons, entry_price, tp_price, sl_price FROM paper_trades WHERE status = 'OPEN'").fetchall()
for r in rows:
    print(dict(r))
conn.close()
