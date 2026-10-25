import sqlite3
import json

conn = sqlite3.connect("database/smc_v17.db")
c = conn.cursor()

tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables in smc_v17.db:", tables)

for t in ["paper_account", "account", "settings", "paper_positions", "paper_trades", "trades"]:
    if t in tables:
        print(f"\n=======================================================")
        print(f"TABLE: {t}")
        print(f"=======================================================")
        col_names = [d[0] for d in c.execute(f"SELECT * FROM {t} LIMIT 1").description]
        print("Columns:", col_names)
        rows = c.execute(f"SELECT * FROM {t}").fetchall()
        print(f"Total rows: {len(rows)}")
        for r in rows[:10]:
            print(dict(zip(col_names, r)))
