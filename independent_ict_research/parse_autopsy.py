import os, sqlite3
from datetime import datetime, timezone

db_path = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\database\smc_v17.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT id, trade_id, symbol, side, timeframe, entry_price, exit_price, pnl_usdt, roe_pct, loss_category, autopsy_diagnosis, created_at FROM trade_autopsy ORDER BY created_at DESC;")
rows = cur.fetchall()

print(f"Total Trade Autopsy records: {len(rows)}")
for r in rows:
    ts = r[11]
    dt = datetime.fromtimestamp(ts / 1000.0 if ts > 1e11 else ts, tz=timezone.utc)
    d_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"ID {r[0]} | Trade #{r[1]} | {r[2]} {r[3]} ({r[4]}) | Entry: {r[5]} -> Exit: {r[6]} | ROE: {r[8]}% | Category: {r[9]} | Date: {d_str}")
    print(f"   Diagnosis: {r[10]}\n")
