import sqlite3
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
start_ms = int(datetime(2026, 9, 29, 0, 0, 0, tzinfo=IST).timestamp() * 1000)
end_ms = int(datetime(2026, 9, 29, 23, 59, 59, tzinfo=IST).timestamp() * 1000)

conn = sqlite3.connect("database/smc_v17.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM paper_trades WHERE entry_time >= ? AND entry_time <= ? ORDER BY entry_time ASC", (start_ms, end_ms)).fetchall()

print(f"Total trades entered on 29-Sep: {len(rows)}")
for r in rows:
    t_in = datetime.fromtimestamp(r["entry_time"]/1000, tz=IST).strftime("%d-%b %I:%M %p")
    t_out = datetime.fromtimestamp(r["exit_time"]/1000, tz=IST).strftime("%d-%b %I:%M %p") if r["exit_time"] else "STILL OPEN"
    pnl = f"+${r['pnl_usdt']:.2f}" if r['pnl_usdt'] and r['pnl_usdt'] > 0 else (f"-${abs(r['pnl_usdt']):.2f}" if r['pnl_usdt'] else "$0.00")
    print(f"• #{r['id']} | {r['symbol']:10s} | {r['side']:5s} ({r['timeframe']}) | In: {t_in} | Out: {t_out} | PnL: {pnl:8s} | Status: {r['status']}")
