import sqlite3

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()

# Check trade 633
c.execute("SELECT id, symbol, side, timeframe, entry_price, status, account_id, position_size_usdt FROM paper_trades WHERE id = 633")
trade = c.fetchone()
print("Trade 633:", trade)

# Reconcile Trade 633 so it doesn't show as a phantom open position
c.execute("""
    UPDATE paper_trades 
    SET status = 'CLOSED',
        exit_price = entry_price,
        exit_time = 1792636800000,
        pnl_usdt = 0.0,
        pnl_pct = 0.0,
        roi_pct = 0.0,
        autopsy_diagnosis = 'RECONCILED: Bitget rejected order due to whole contract size precision (amount 3.91 vs int required). Position not filled on exchange.'
    WHERE id = 633 AND status = 'OPEN'
""")
conn.commit()

# Reconcile Section 6 balance
c.execute("UPDATE paper_account SET current_balance = 50.0 WHERE id = 6")
conn.commit()

print("Reconciled Trade #633 and restored Section 6 balance.")

# Verify open trades now
c.execute("SELECT id, symbol, side, status, account_id FROM paper_trades WHERE status = 'OPEN'")
open_trades = c.fetchall()
print("\nOpen trades in database now:")
for ot in open_trades:
    print(ot)
