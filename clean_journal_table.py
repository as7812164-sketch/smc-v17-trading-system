import sqlite3
from pathlib import Path
from engine.trade_journal import sync_quad_accounts_to_ledger, _sync_db_to_csv
from database.cloud_vault import push_vault_state

db_path = Path("database/smc_v17.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Clear trade_journal completely except the FET trade (paper_trade_id = 293)
c.execute("DELETE FROM trade_journal WHERE paper_trade_id != 293")
# If trade_journal had trades with paper_trade_id=0 or None, clean them too
c.execute("DELETE FROM trade_journal WHERE symbol != 'FETUSDT'")

# Reset trade_num for FETUSDT to 1
c.execute("""
UPDATE trade_journal SET
    trade_num = 1,
    account_id = 4,
    channel = 'bitget_1h',
    account_name = 'Bitget 1H Intraday',
    exchange = 'Bitget',
    account_balance = 40.60
WHERE symbol = 'FETUSDT'
""")

conn.commit()
conn.close()

# 2. Sync to CSV
_sync_db_to_csv()

# 3. Verify
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, trade_num, symbol, side, channel, account_balance, pnl_usdt FROM trade_journal")
print("Verified trade_journal rows:", c.fetchall())

c.execute("SELECT id, symbol, side, timeframe, channel, account_id, status, pnl_usdt FROM paper_trades")
print("Verified paper_trades rows:", c.fetchall())

c.execute("SELECT id, name, channel, initial_balance, current_balance, total_pnl, win_count, loss_count FROM paper_account")
for row in c.fetchall():
    print("Verified account:", row)
conn.close()

# 4. Push to Cloud Vault
push_vault_state()
print("Cloud vault updated!")
