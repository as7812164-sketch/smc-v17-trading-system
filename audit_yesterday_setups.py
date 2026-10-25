import sqlite3
import json
from datetime import datetime, timezone, timedelta

conn = sqlite3.connect("database/smc_v17.db")
conn.row_factory = sqlite3.Row

# Start and end of yesterday (29 Sep 2026 IST)
# 29 Sep 2026 00:00 IST = 28 Sep 2026 18:30 UTC = 1790620200000 ms approx
start_29_utc = datetime(2026, 9, 28, 18, 30, tzinfo=timezone.utc).timestamp() * 1000
end_29_utc = datetime(2026, 9, 29, 18, 30, tzinfo=timezone.utc).timestamp() * 1000

print(f"Querying window: 29 Sep 2026 IST ({start_29_utc} to {end_29_utc})")

# 1. Executed Trades yesterday
trades_29 = conn.execute("""
    SELECT * FROM paper_trades 
    WHERE entry_time >= ? AND entry_time <= ?
    ORDER BY entry_time ASC
""", (start_29_utc - 3600000*6, end_29_utc + 3600000*6)).fetchall()

print(f"\n--- EXECUTED TRADES (around 29 Sep) [Total: {len(trades_29)}] ---")
for t in trades_29:
    dt = datetime.fromtimestamp(t["entry_time"]/1000, tz=timezone.utc) + timedelta(hours=5, minutes=30)
    print(f"Trade #{t['id']} | {t['symbol']} | {t['side']} ({t['timeframe']}) | In: {t['entry_price']} | Out: {t['exit_price']} | PnL: ${t['pnl_usdt']} ({t['pnl_pct']}%) | Status: {t['status']} | Entered: {dt.strftime('%d %b %I:%M %p')}")

# 2. Zones detected around 29 Sep
zones_29 = conn.execute("""
    SELECT * FROM zones 
    ORDER BY origin_time DESC LIMIT 40
""").fetchall()

print(f"\n--- ALL RECENT ZONES IN DATABASE [Total: {len(zones_29)}] ---")
for z in zones_29[:20]:
    t_ms = z["origin_time"]
    dt = datetime.fromtimestamp(t_ms/1000, tz=timezone.utc) + timedelta(hours=5, minutes=30)
    print(f"Zone #{z['id']} | {z['symbol']} | {z['side']} | OB: [{z['ob_low']} - {z['ob_high']}] | Status: {z['status']} | Origin: {dt.strftime('%d %b %I:%M %p')}")

# 3. Signals generated
signals_29 = conn.execute("""
    SELECT * FROM signals ORDER BY sent_at DESC LIMIT 20
""").fetchall()
print(f"\n--- RECENT SIGNALS IN DB [Total: {len(signals_29)}] ---")
for s in signals_29[:10]:
    t_ms = s["sent_at"]
    dt = datetime.fromtimestamp(t_ms/1000, tz=timezone.utc) + timedelta(hours=5, minutes=30)
    print(f"Sig #{s['id']} | {s['symbol']} | {s['side']} | Price: {s['entry_price']} | Sent: {dt.strftime('%d %b %I:%M %p')}")

