import sqlite3
import time

# 1. Update database/db.py
db_py_path = "C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/database/db.py"
with open(db_py_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace section init 50.0 with 5.0
text = text.replace(
    "VALUES (?, ?, ?, ?, ?, 50.0, 50.0, 0.0, 0.0, 0, 0, 0, 2000.0, 'HERMES_3.0_MODEL_2A');",
    "VALUES (?, ?, ?, ?, ?, 5.0, 5.0, 0.0, 0.0, 0, 0, 0, 2000.0, 'HERMES_3.0_MODEL_2A');"
)
text = text.replace(
    "initial_balance = 50.0,\n                    current_balance = 50.0,",
    "initial_balance = 5.0,\n                    current_balance = 5.0,"
)
text = text.replace(
    "conn.execute(\"INSERT OR REPLACE INTO settings (key, value) VALUES ('total_compounding_capital', '500.0')\")",
    "conn.execute(\"INSERT OR REPLACE INTO settings (key, value) VALUES ('total_compounding_capital', '50.0')\")\n"
    "        conn.execute(\"INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_auto_trade', 'true')\")\n"
    "        conn.execute(\"INSERT OR REPLACE INTO settings (key, value) VALUES ('allow_local_live_trading', 'true')\")\n"
    "        conn.execute(\"INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_starting_margin', '5.0')\")\n"
    "        conn.execute(\"INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_compounding_balance', '5.0')\")\n"
    "        conn.execute(\"INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_1h_compounding_balance', '5.0')\")"
)

with open(db_py_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated database/db.py successfully")

# 2. Update smc_v17.db directly
db_file = "C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/database/smc_v17.db"
conn = sqlite3.connect(db_file)
cur = conn.cursor()

# Set all 10 sections to $5.00 initial and current balance
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
WHERE id BETWEEN 1 AND 10;
""")

# Delete any old legacy phantom open trades to ensure all 10 sections are completely idle and free
cur.execute("UPDATE paper_trades SET status = 'CLOSED' WHERE status = 'OPEN';")

# Settings
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
print("Updated SQLite database smc_v17.db successfully")
