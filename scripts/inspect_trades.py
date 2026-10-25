import sqlite3
import datetime

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("SELECT DISTINCT mode FROM paper_trades")
print("Distinct modes:", c.fetchall())

c.execute("""
    SELECT id, symbol, side, timeframe, entry_price, exit_price, tp_price, sl_price, pnl_usdt, roi_pct, entry_time, exit_time, mode
    FROM paper_trades 
    WHERE id >= 600
    ORDER BY id ASC
""")
rows = c.fetchall()
print(f"Total trades with id >= 600: {len(rows)}")
for r in rows:
    entry_dt = datetime.datetime.fromtimestamp(r[10]/1000.0) if r[10] else "N/A"
    exit_dt = datetime.datetime.fromtimestamp(r[11]/1000.0) if r[11] else "N/A"
    print(f"ID: {r[0]} | {r[1]} {r[2]} ({r[3]}) | Entry: {r[4]} | Exit: {r[5]} | TP: {r[6]} | SL: {r[7]} | PnL: {r[8]} USDT ({r[9]}% ROI) | Entry Time: {entry_dt} | Exit Time: {exit_dt} | Mode: {r[12]}")
