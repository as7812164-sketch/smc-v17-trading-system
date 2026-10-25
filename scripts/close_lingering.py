import sqlite3

conn = sqlite3.connect("C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/database/smc_v17.db")
cur = conn.cursor()

# Mark the 4 already-exited trades with their proper outcome
cur.execute("UPDATE paper_trades SET status = CASE WHEN pnl_usdt > 0 THEN 'TP_HIT' ELSE 'SL_HIT' END WHERE id IN (584, 616, 621, 623);")

# Check if any remaining OPEN trades exist
open_rows = cur.execute("SELECT id, symbol, side, status, account_id FROM paper_trades WHERE status = 'OPEN'").fetchall()
print(f"Remaining OPEN trades in database: {len(open_rows)}")
for r in open_rows:
    print(r)

conn.commit()
conn.close()
print("Lingering trades settled cleanly.")
