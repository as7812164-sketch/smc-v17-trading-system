import sqlite3
import json
from pathlib import Path
from engine.trade_journal import sync_quad_accounts_to_ledger
from database.cloud_vault import push_vault_state

db_path = Path("database/smc_v17.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- BEFORE RESET ---")
c.execute("SELECT id, symbol, side, timeframe, channel, account_id, status, pnl_usdt FROM paper_trades")
print("Paper trades count:", len(c.fetchall()))

c.execute("SELECT id, name, channel, initial_balance, current_balance, total_pnl, win_count, loss_count FROM paper_account")
for row in c.fetchall():
    print("Account:", row)

# 1. Clean paper_trades:
# Delete all OPEN trades
c.execute("DELETE FROM paper_trades WHERE status = 'OPEN'")

# Delete old simulated trades for Acc 1, Acc 2, Acc 3
c.execute("DELETE FROM paper_trades WHERE account_id IN (1, 2, 3)")

# In Acc 4 (Bitget 1H), keep only FET trade (id=293)
c.execute("DELETE FROM paper_trades WHERE account_id = 4 AND id != 293")

# 2. Reset paper_account table
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

# 3. Settings table updates
settings_updates = [
    ("binance_compounding_balance", "50.0"),
    ("binance_1h_compounding_balance", "50.0"),
    ("bitget_compounding_balance", "50.0"),
    ("bitget_1h_compounding_balance", "40.60"),
    ("binance_auto_trade", "true"),
    ("bitget_auto_trade", "true"),
    ("binance_4h_only_short", "false")
]

for k, v in settings_updates:
    c.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (k, v))

conn.commit()
conn.close()

print("--- AFTER RESET ---")
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, symbol, side, timeframe, channel, account_id, status, pnl_usdt FROM paper_trades")
print("Remaining paper trades:", c.fetchall())

c.execute("SELECT id, name, channel, initial_balance, current_balance, total_pnl, win_count, loss_count FROM paper_account")
for row in c.fetchall():
    print("Updated Account:", row)
conn.close()

# 4. Sync Quad Accounts to Ledger
print("Syncing Quad Accounts to Ledger...")
sync_quad_accounts_to_ledger()

# 5. Push to Cloud Vault
print("Pushing state to Cloud Vault...")
res = push_vault_state()
print("Cloud Vault Push Result:", res)
