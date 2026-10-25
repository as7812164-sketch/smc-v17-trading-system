import sqlite3
import os

db_path = os.path.join("database", "smc_v17.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Update settings
c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('strategy_version', 'HERMES_3.0_MODEL_2A')")
c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('hermes_entry_mode', '50% Mean Threshold (MT)')")
c.execute("DELETE FROM settings WHERE key = 'hermes35_entry_mode'")

# Update system metrics
c.execute("INSERT OR REPLACE INTO system_metrics (key, value) VALUES ('hermes_mode', 'HERMES_3.0_MODEL_2A')")
c.execute("INSERT OR REPLACE INTO system_metrics (key, value) VALUES ('last_alert', 'Hermes 3.0 Model 2A Armed 24/7')")

# Update all paper accounts
c.execute("UPDATE paper_account SET mode = 'HERMES_3.0_MODEL_2A' WHERE id <= 10")
c.execute("UPDATE paper_trades SET mode = 'HERMES_3.0_MODEL_2A' WHERE account_id <= 10 OR account_id IS NULL")

conn.commit()
print("DB settings successfully refreshed!")

print("CURRENT SETTINGS:")
for r in c.execute("SELECT key, value FROM settings WHERE key LIKE '%hermes%' OR key LIKE '%strategy%';").fetchall():
    print(" ", r)

print("CURRENT PAPER ACCOUNTS:")
for r in c.execute("SELECT id, name, mode FROM paper_account LIMIT 5;").fetchall():
    print(" ", r)

conn.close()
