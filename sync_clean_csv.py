import sqlite3
from engine.trade_journal import _sync_db_to_csv
from database.cloud_vault import push_vault_state

conn = sqlite3.connect("database/smc_v17.db")
c = conn.cursor()
c.execute("DELETE FROM trade_journal WHERE symbol != 'FETUSDT'")
c.execute("UPDATE trade_journal SET trade_num=1, account_id=4, channel='bitget_1h', account_name='Bitget 1H Intraday', account_balance=40.6 WHERE symbol='FETUSDT'")
conn.commit()
count = c.execute("SELECT count(*) FROM trade_journal").fetchone()[0]
print("Rows in trade_journal table:", count)
conn.close()

_sync_db_to_csv()
print("Synced trade_journal to trade_journal_ledger.csv successfully!")

push_vault_state()
print("Pushed clean state to cloud vault!")
