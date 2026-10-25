import sqlite3

conn = sqlite3.connect("C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/database/smc_v17.db")
cur = conn.cursor()

cur.execute("UPDATE paper_trades SET status = 'CLOSED' WHERE id IN (584, 616, 621, 623)")
print("Updated rows:", cur.rowcount)
conn.commit()

rows = cur.execute("SELECT id, symbol, status FROM paper_trades WHERE id IN (584, 616, 621, 623)").fetchall()
print("After commit:", rows)
conn.close()
