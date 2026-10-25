import sqlite3
import time

# 1. Update database/db.py
db_py_path = "C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/database/db.py"
with open(db_py_path, "r", encoding="utf-8") as f:
    text = f.read()

# Update reconcile_portfolio_from_trades to respect live_trading_start_time
old_reconcile_block = """            trades = conn.execute(\"\"\"
                SELECT pnl_usdt, status FROM paper_trades
                WHERE (account_id = ? OR channel IN (?, ?, ?, ?))
                  AND status != 'OPEN'
                ORDER BY exit_time ASC
            \"\"\", (sec_id, ch_patterns[0], ch_patterns[1], ch_patterns[2], ch_patterns[3])).fetchall()"""

new_reconcile_block = """            live_start_ms = int(float(get_setting("live_trading_start_time", "0")) * 1000)
            if live_start_ms > 0:
                trades = conn.execute(\"\"\"
                    SELECT pnl_usdt, status FROM paper_trades
                    WHERE (account_id = ? OR channel IN (?, ?, ?, ?))
                      AND status != 'OPEN'
                      AND entry_time >= ?
                    ORDER BY exit_time ASC
                \"\"\", (sec_id, ch_patterns[0], ch_patterns[1], ch_patterns[2], ch_patterns[3], live_start_ms)).fetchall()
            else:
                trades = conn.execute(\"\"\"
                    SELECT pnl_usdt, status FROM paper_trades
                    WHERE (account_id = ? OR channel IN (?, ?, ?, ?))
                      AND status != 'OPEN'
                    ORDER BY exit_time ASC
                \"\"\", (sec_id, ch_patterns[0], ch_patterns[1], ch_patterns[2], ch_patterns[3])).fetchall()"""

text = text.replace(old_reconcile_block, new_reconcile_block)

# Update expected_bal in get_compounding_sections
old_expected_bal = """            trade_pnl_sum = conn.execute("SELECT SUM(pnl_usdt) FROM paper_trades WHERE status != 'OPEN' AND (account_id <= 10 OR account_id IS NULL)").fetchone()[0] or 0.0
            expected_bal = round(500.0 + max(0.0, trade_pnl_sum), 2)
            if curr_acc_sum < (expected_bal - 5.0) and trade_pnl_sum > 0:
                reconcile_portfolio_from_trades()"""

new_expected_bal = """            live_start_ms = int(float(get_setting("live_trading_start_time", "0")) * 1000)
            if live_start_ms > 0:
                trade_pnl_sum = conn.execute("SELECT SUM(pnl_usdt) FROM paper_trades WHERE status != 'OPEN' AND (account_id <= 10 OR account_id IS NULL) AND entry_time >= ?", (live_start_ms,)).fetchone()[0] or 0.0
            else:
                trade_pnl_sum = conn.execute("SELECT SUM(pnl_usdt) FROM paper_trades WHERE status != 'OPEN' AND (account_id <= 10 OR account_id IS NULL)").fetchone()[0] or 0.0
            expected_bal = round(50.0 + max(0.0, trade_pnl_sum), 2)
            if curr_acc_sum < (expected_bal - 5.0) and trade_pnl_sum > 0:
                reconcile_portfolio_from_trades()"""

text = text.replace(old_expected_bal, new_expected_bal)

# Update init_b fallback to 5.0 in reconcile
text = text.replace(
    'init_b = float(acc_row["initial_balance"] if acc_row else 50.0)',
    'init_b = float(acc_row["initial_balance"] if acc_row else 5.0)'
)

# In reconcile, always update paper_account even if trades list is empty (so it sets to init_b = $5.00)
old_update = """            if trades:
                conn.execute(\"\"\"
                UPDATE paper_account SET
                    current_balance = ?,
                    total_pnl = ?,
                    win_count = ?,
                    loss_count = ?,
                    win_streak = ?
                WHERE id = ?
                \"\"\", (true_bal, tot_pnl, wins, losses, streak, sec_id))"""

new_update = """            conn.execute(\"\"\"
            UPDATE paper_account SET
                current_balance = ?,
                total_pnl = ?,
                win_count = ?,
                loss_count = ?,
                win_streak = ?
            WHERE id = ?
            \"\"\", (true_bal, tot_pnl, wins, losses, streak, sec_id))"""

text = text.replace(old_update, new_update)

with open(db_py_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated database/db.py with live_trading_start_time support")

# 2. Update smc_v17.db directly
now_ts = time.time()
db_file = "C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/database/smc_v17.db"
conn = sqlite3.connect(db_file)
cur = conn.cursor()

# Set live trading start time to right now
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('live_trading_start_time', ?);", (str(now_ts),))

# Clean legacy paper simulated open positions so all 10 live sections start 100% IDLE
cur.execute("UPDATE paper_trades SET status = 'CLOSED' WHERE status = 'OPEN';")

# Re-initialize all 10 sections to $5.00 each
for i in range(1, 11):
    cur.execute("""
        UPDATE paper_account
        SET initial_balance = 5.0,
            current_balance = 5.0,
            vault_balance = 0.0,
            total_pnl = 0.0,
            win_count = 0,
            loss_count = 0,
            win_streak = 0,
            milestone_target = 2000.0,
            mode = 'HERMES_3.0_MODEL_2A'
        WHERE id = ?;
    """, (i,))

cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_auto_trade', 'true');")
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('allow_local_live_trading', 'true');")
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('binance_auto_trade', 'false');")
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('total_compounding_capital', '50.0');")
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('total_compounding_sections', '10');")
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_starting_margin', '5.0');")
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_compounding_balance', '5.0');")
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_1h_compounding_balance', '5.0');")

conn.commit()
conn.close()
print("Initialized smc_v17.db for Live Trading launch successfully")
