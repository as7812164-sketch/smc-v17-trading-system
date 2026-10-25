import sqlite3
import os
import glob

for db in glob.glob("**/*.db", recursive=True) + glob.glob("*.db"):
    print("=" * 60)
    print(f"DATABASE: {db}")
    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"Tables: {tables}")
        for t in tables:
            cnt = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"  {t}: {cnt} rows")
            if "trade" in t.lower():
                sample = conn.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 5").fetchall()
                for s in sample:
                    print("    SAMPLE:", dict(s))
    except Exception as e:
        print(f"Error {db}: {e}")
