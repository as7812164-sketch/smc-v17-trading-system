import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.cloud_vault import get_vault_headers, GITHUB_REPO, VAULT_BRANCH, VAULT_FILE
import urllib.request
import json
import base64
import sqlite3

def sync_all_vault_trades():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{VAULT_FILE}?ref={VAULT_BRANCH}"
    req = urllib.request.Request(url, headers=get_vault_headers())
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        vault_data = json.loads(base64.b64decode(data.get("content", "")).decode("utf-8"))

    remote_trades = vault_data.get("paper_trades", [])

    conn = sqlite3.connect("database/smc_v17.db")
    conn.row_factory = sqlite3.Row
    cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_trades)").fetchall()]

    added = 0
    for t in remote_trades:
        tid = t.get("id")
        existing = conn.execute("SELECT id FROM paper_trades WHERE id = ?", (tid,)).fetchone()
        if not existing:
            col_names = [c for c in cols if c in t and t[c] is not None]
            placeholders = ", ".join(["?"] * len(col_names))
            cols_str = ", ".join(col_names)
            vals = [t[c] for c in col_names]
            conn.execute(f"INSERT INTO paper_trades ({cols_str}) VALUES ({placeholders})", vals)
            added += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(1) FROM paper_trades").fetchone()[0]
    print(f"Added {added} missing trades. Total in local db now: {total}")
    conn.close()

if __name__ == "__main__":
    sync_all_vault_trades()
