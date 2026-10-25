import sqlite3
import json
import base64
import time
import urllib.request
from pathlib import Path

db_path = Path("database/smc_v17.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Set clean accounts
c.execute("""
UPDATE paper_account SET
    initial_balance = 50.0,
    current_balance = 50.0,
    total_pnl = 0.0,
    win_count = 0,
    loss_count = 0,
    vault_balance = 0.0,
    win_streak = 0
WHERE id = 1
""")

c.execute("""
UPDATE paper_account SET
    initial_balance = 50.0,
    current_balance = 50.0,
    total_pnl = 0.0,
    win_count = 0,
    loss_count = 0,
    vault_balance = 0.0,
    win_streak = 0
WHERE id = 2
""")

c.execute("""
UPDATE paper_account SET
    initial_balance = 50.0,
    current_balance = 50.0,
    total_pnl = 0.0,
    win_count = 0,
    loss_count = 0,
    vault_balance = 0.0,
    win_streak = 0
WHERE id = 3
""")

c.execute("""
UPDATE paper_account SET
    initial_balance = 50.0,
    current_balance = 40.60,
    total_pnl = -9.40,
    win_count = 0,
    loss_count = 1,
    vault_balance = 0.0,
    win_streak = 0
WHERE id = 4
""")

# Delete all open trades
c.execute("DELETE FROM paper_trades WHERE status = 'OPEN'")
# Delete all non-FET trades
c.execute("DELETE FROM paper_trades WHERE symbol != 'FETUSDT'")
# Delete all non-FET journal rows
c.execute("DELETE FROM trade_journal WHERE symbol != 'FETUSDT'")

conn.commit()

# Read accounts, trades, journal
conn.row_factory = sqlite3.Row
c = conn.cursor()
accounts = [dict(r) for r in c.execute("SELECT * FROM paper_account").fetchall()]
paper_trades = [dict(r) for r in c.execute("SELECT * FROM paper_trades").fetchall()]
journal_trades = [dict(r) for r in c.execute("SELECT * FROM trade_journal").fetchall()]
conn.close()

payload_data = {
    "version": "1.0",
    "updated_at": int(time.time() * 1000),
    "updated_at_str": time.strftime("%Y-%m-%d %H:%M:%S IST", time.localtime()),
    "accounts": accounts,
    "paper_trades": paper_trades,
    "journal_trades": journal_trades,
    "metrics": {}
}

# 1. Save local backup file
backup_path = Path("database/local_vault_backup.json")
with open(backup_path, "w", encoding="utf-8") as f:
    json.dump(payload_data, f, indent=2)
print("Saved local backup:", backup_path)

# 2. Push to GitHub branch data-vault
GITHUB_TOKEN = "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"
GITHUB_REPO = "as7812164-sketch/smc-ai-agent"
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "User-Agent": "Hermes-Cloud-Vault",
    "Accept": "application/vnd.github.v3+json"
}

url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/vault_state.json?ref=data-vault"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    info = json.loads(resp.read().decode())
    sha = info.get("sha")

content_bytes = json.dumps(payload_data, indent=2).encode("utf-8")
b64_content = base64.b64encode(content_bytes).decode("utf-8")

put_payload = {
    "message": "Vault Snapshot: Reset accounts to $50 clean forward test",
    "content": b64_content,
    "branch": "data-vault",
    "sha": sha
}

req_put = urllib.request.Request(
    f"https://api.github.com/repos/{GITHUB_REPO}/contents/vault_state.json",
    data=json.dumps(put_payload).encode("utf-8"),
    headers=headers,
    method="PUT"
)

with urllib.request.urlopen(req_put) as resp:
    print("GitHub data-vault updated successfully! Status:", resp.status)

for a in accounts:
    print(a["name"], "Balance:", a["current_balance"], "PnL:", a["total_pnl"], "Trades:", a["win_count"] + a["loss_count"])
