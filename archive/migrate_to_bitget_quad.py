import sqlite3
from pathlib import Path

db_path = Path("database/smc_v17.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 1. Update open Binance trades to account 99 and channel 'binance_legacy'
conn.execute("UPDATE paper_trades SET account_id = 99, channel = 'binance_legacy' WHERE exchange = 'BINANCE' AND status = 'OPEN'")

# 2. Update the 4 Bitget accounts cleanly to $50.00 each
accounts_data = [
    (1, "4h", "Bitget 4H Macro (Section A)", "BITGET", "bitget_4h_1", 50.0, 50.0),
    (2, "4h", "Bitget 4H Macro (Section B)", "BITGET", "bitget_4h_2", 50.0, 50.0),
    (3, "1h", "Bitget 1H Intraday (Section A)", "BITGET", "bitget_1h_1", 50.0, 50.0),
    (4, "1h", "Bitget 1H Intraday (Section B)", "BITGET", "bitget_1h_2", 50.0, 50.0),
]

for acc_id, tf, name, exch, ch, init_b, curr_b in accounts_data:
    conn.execute("""
    UPDATE paper_account SET
        timeframe = ?,
        name = ?,
        exchange = ?,
        channel = ?,
        initial_balance = ?,
        current_balance = ?,
        total_pnl = 0.0,
        win_count = 0,
        loss_count = 0,
        win_streak = 0,
        vault_balance = 0.0,
        milestone_target = 2000.0,
        mode = 'HERMES_3.0_QUANTUM'
    WHERE id = ?
    """, (tf, name, exch, ch, init_b, curr_b, acc_id))

# 3. Settings update
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('binance_auto_trade', 'false')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_auto_trade', 'true')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_4h_1_compounding_balance', '50.0')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_4h_2_compounding_balance', '50.0')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_1h_1_compounding_balance', '50.0')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_1h_2_compounding_balance', '50.0')")

conn.commit()

print("MIGRATION COMPLETED SUCCESSFULLY!")
print("Accounts:")
for r in conn.execute("SELECT id, name, timeframe, exchange, channel, initial_balance, current_balance FROM paper_account").fetchall():
    print(dict(r))

print("\nOpen Trades:")
for r in conn.execute("SELECT id, symbol, side, timeframe, exchange, channel, account_id, status FROM paper_trades WHERE status = 'OPEN'").fetchall():
    print(dict(r))

conn.close()
