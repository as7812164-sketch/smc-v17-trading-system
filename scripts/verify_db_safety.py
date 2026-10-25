import sqlite3

conn = sqlite3.connect("database/smc_v17.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print("Tables in smc_v17.db:", tables)

if "paper_trades" in tables:
    c.execute("SELECT COUNT(*) FROM paper_trades")
    print("Total Trades in paper_trades:", c.fetchone()[0])
    c.execute("SELECT COUNT(*) FROM paper_trades WHERE status='OPEN'")
    print("Open Trades:", c.fetchone()[0])

if "compounding_slots" in tables:
    c.execute("SELECT COUNT(*) FROM compounding_slots")
    print("Total slots in compounding_slots:", c.fetchone()[0])

if "paper_account" in tables:
    c.execute("SELECT * FROM paper_account")
    for r in c.fetchall():
        print("Paper account row:", r)
