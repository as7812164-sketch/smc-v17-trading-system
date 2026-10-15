import sqlite3
import json
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


db_path = r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\database\smc_v17.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Ensure trade 538 is cleanly OPEN with no ghost exit artifacts
cursor.execute("""
    UPDATE paper_trades
    SET exit_price = NULL, exit_time = NULL, pnl_usdt = NULL, pnl_pct = NULL, status = 'OPEN'
    WHERE id = 538
""")
conn.commit()

# 2. Verify 536, 537, 538 are OPEN
cursor.execute("SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, status, account_id FROM paper_trades WHERE id IN (536, 537, 538) ORDER BY id ASC")
target_open = [dict(r) for r in cursor.fetchall()]
print("TARGET OPEN TRADES:")
for t in target_open:
    print(t)

# 3. Verify total closed trades
cursor.execute("SELECT count(*) as cnt FROM paper_trades WHERE status != 'OPEN'")
closed_count = cursor.fetchone()['cnt']
print(f"\nTOTAL CLOSED TRADES: {closed_count}")

# 4. Verify accounts 1 to 10
cursor.execute("SELECT id, name, current_balance, total_pnl, win_count, loss_count FROM paper_account WHERE id <= 10 ORDER BY id ASC")
accs = [dict(r) for r in cursor.fetchall()]
tot_bal = sum(a['current_balance'] for a in accs)
print(f"\nACCOUNTS 1-10 TOTAL EQUITY: ${tot_bal:.2f}")

conn.close()

# 5. Push clean state to local vault backup and cloud vault
from database.cloud_vault import push_vault_state
push_res = push_vault_state()
print(f"Vault sync pushed: {push_res}")
