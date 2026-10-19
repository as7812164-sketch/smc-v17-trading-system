import urllib.request
import json
import sqlite3

def sync_trades():
    url = "https://smc-ai-agent.onrender.com/api/paper/trades"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    res = urllib.request.urlopen(req, timeout=15)
    data = json.loads(res.read().decode())
    remote_trades = data.get("trades", [])
    print(f"Total remote trades fetched from Render: {len(remote_trades)}")

    conn = sqlite3.connect("database/smc_v17.db")
    conn.row_factory = sqlite3.Row
    cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_trades)").fetchall()]

    added = 0
    updated = 0
    for t in remote_trades:
        tid = t.get("id")
        existing = conn.execute("SELECT id, status FROM paper_trades WHERE id = ?", (tid,)).fetchone()
        if not existing:
            col_names = [c for c in cols if c in t and t[c] is not None]
            placeholders = ", ".join(["?"] * len(col_names))
            vals = [t[c] for c in col_names]
            conn.execute(f"INSERT INTO paper_trades ({', '.join(col_names)}) VALUES ({placeholders})", vals)
            added += 1
        elif existing["status"] != t.get("status") or t.get("pnl_usdt") is not None:
            conn.execute("""
            UPDATE paper_trades SET
                status = ?, exit_time = ?, exit_price = ?, pnl_usdt = ?, pnl_pct = ?
            WHERE id = ?
            """, (t.get("status"), t.get("exit_time"), t.get("exit_price"), t.get("pnl_usdt"), t.get("pnl_pct"), tid))
            updated += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(1) FROM paper_trades").fetchone()[0]
    print(f"Local sync complete: {added} added, {updated} updated. Total now in local db: {total}")
    conn.close()

if __name__ == "__main__":
    sync_trades()
