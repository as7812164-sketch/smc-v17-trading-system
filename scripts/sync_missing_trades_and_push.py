import sys
sys.path.append("C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system")

import urllib.request, json, base64, sqlite3
from database.cloud_vault import get_vault_headers, GITHUB_REPO, VAULT_BRANCH, VAULT_FILE, push_vault_state
from database.db import get_connection

# 1. Fetch remote vault trades
url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{VAULT_FILE}?ref={VAULT_BRANCH}"
headers = get_vault_headers()
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    vault = json.loads(base64.b64decode(data["content"]).decode("utf-8"))
    remote_trades = vault.get("paper_trades", [])

# 2. Insert any missing remote trades into local SQLite as CLOSED so counts match perfectly
with get_connection() as conn:
    cols = [col[1] for col in conn.execute("PRAGMA table_info(paper_trades)").fetchall()]
    local_ids = {r[0] for r in conn.execute("SELECT id FROM paper_trades").fetchall()}
    
    for pt in remote_trades:
        pt_id = pt.get("id")
        if pt_id not in local_ids:
            pt_copy = dict(pt)
            # Ensure status is closed so it doesn't block live sections
            pt_copy["status"] = "CLOSED"
            insert_cols = [c for c in cols if c in pt_copy and pt_copy[c] is not None]
            placeholders = ", ".join(["?"] * len(insert_cols))
            col_names = ", ".join(insert_cols)
            vals = [pt_copy[c] for c in insert_cols]
            conn.execute(f"INSERT INTO paper_trades ({col_names}) VALUES ({placeholders})", vals)
            print(f"Inserted missing trade #{pt_id} ({pt_copy.get('symbol')}) as CLOSED")
            
    # Mark all trades on sections 1-10 as CLOSED
    conn.execute("UPDATE paper_trades SET status = 'CLOSED' WHERE status = 'OPEN' AND (account_id <= 10 OR account_id IS NULL);")
    conn.commit()

# 3. Re-check count
with get_connection() as conn:
    cnt = conn.execute("SELECT COUNT(*) FROM paper_trades").fetchone()[0]
    print(f"Total local trades count now: {cnt}")

# 4. Push cleanly to GitHub Vault
success = push_vault_state()
print(f"Push to GitHub Cloud Vault success: {success}")
