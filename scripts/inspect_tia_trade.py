import sqlite3
import json
from datetime import datetime

def inspect_tia():
    conn = sqlite3.connect("database/smc_v17.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM paper_trades WHERE symbol = 'TIAUSDT' ORDER BY id DESC LIMIT 5").fetchall()
    print(f"Total TIA trades: {len(rows)}")
    for r in rows:
        print("="*60)
        for k in r.keys():
            val = r[k]
            if "time" in k and val:
                val = f"{val} ({datetime.fromtimestamp(val/1000.0).strftime('%Y-%m-%d %H:%M:%S')})"
            print(f"  {k}: {val}")
    conn.close()

if __name__ == "__main__":
    inspect_tia()
