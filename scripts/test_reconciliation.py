import sqlite3
import json

def test_reconciliation():
    # Let's inspect local database smc_v17.db
    conn = sqlite3.connect("database/smc_v17.db")
    conn.row_factory = sqlite3.Row
    
    # Check trades count in local db
    local_trades = conn.execute("SELECT * FROM paper_trades").fetchall()
    print(f"Local db paper_trades count: {len(local_trades)}")
    
    # We know Render has 62 trades (and 4 open). Let's see if local has them all or needs sync
    # Let's query Render trades and compare with local
    import urllib.request
    req = urllib.request.Request("https://smc-ai-agent.onrender.com/api/paper/trades", headers={"User-Agent": "Mozilla/5.0"})
    res = urllib.request.urlopen(req, timeout=10)
    data = json.loads(res.read().decode())
    remote_trades = data.get("trades", [])
    print(f"Remote Render trades count: {len(remote_trades)}")
    
    local_ids = {r["id"] for r in local_trades}
    missing_in_local = [t for t in remote_trades if t.get("id") not in local_ids]
    print(f"Trades on Render missing locally: {len(missing_in_local)}")
    for mt in missing_in_local:
        print(f"  Missing: ID {mt.get('id')} {mt.get('symbol')} {mt.get('status')} pnl={mt.get('pnl_usdt')}")

if __name__ == "__main__":
    test_reconciliation()
