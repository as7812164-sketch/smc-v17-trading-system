import sqlite3

conn = sqlite3.connect('database/smc_v17.db')
cursor = conn.cursor()

print("--- PAPER TRADES ---")
cursor.execute("SELECT id, symbol, side, entry_price, status, pnl_usdt, entry_time, exit_time FROM paper_trades")
for r in cursor.fetchall():
    print(r)

print("\n--- TRADE JOURNAL ---")
cursor.execute("SELECT id, symbol, direction, entry_price, status, pnl_usdt, entry_time, exit_time FROM trade_journal")
for r in cursor.fetchall():
    print(r)

print("\n--- PAPER ACCOUNT ---")
cursor.execute("SELECT * FROM paper_account")
for r in cursor.fetchall():
    print(r)

conn.close()
