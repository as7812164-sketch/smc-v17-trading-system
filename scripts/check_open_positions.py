import sqlite3
import datetime

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("""
    SELECT id, symbol, side, timeframe, entry_price, tp_price, sl_price, entry_time, account_id, mode, status, position_size_usdt
    FROM paper_trades 
    WHERE status = 'OPEN'
    ORDER BY id ASC
""")
rows = c.fetchall()
print(f"Total OPEN positions in database: {len(rows)}")
for r in rows:
    entry_dt = datetime.datetime.fromtimestamp(r[7]/1000.0) if r[7] else "N/A"
    print(f"ID #{r[0]} | {r[1]} {r[2]} ({r[3]}) | Entry: {r[4]} | TP: {r[5]} | SL: {r[6]} | Time: {entry_dt} | Section: {r[8]} | Mode: {r[9]} | Margin: ${r[11]} USDT")

# Also check compounding sections status
c.execute("""
    SELECT id, current_balance, mode, milestone_target, active_trade_id 
    FROM paper_account 
    WHERE id <= 10
    ORDER BY id ASC
""")
sections = c.fetchall()
print("\n--- 10 DECA COMPOUNDING SECTIONS ---")
for s in sections:
    print(f"Section {s[0]}: Balance: ${s[1]:.2f} | Trade ID: {s[4]} | Mode: {s[2]}")
