import sqlite3

conn = sqlite3.connect("database/smc_v17.db")
c = conn.cursor()
c.execute("PRAGMA table_info(paper_trades)")
cols = [r[1] for r in c.fetchall()]
print("Columns in paper_trades:", cols)

c.execute("SELECT * FROM paper_trades ORDER BY id DESC LIMIT 5")
rows = c.fetchall()
for r in rows:
    print("--- Trade ---")
    for col, val in zip(cols, r):
        if col in ['id', 'symbol', 'side', 'entry_price', 'exit_price', 'realized_pnl', 'pnl_pct', 'roi_pct', 'status', 'exit_reason', 'entry_time', 'exit_time', 'section_id']:
            print(f"  {col}: {val}")

c.execute("SELECT * FROM paper_account WHERE id=1")
print("Section 1:", c.fetchone())
