import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import get_connection

with get_connection() as conn:
    conn.execute("UPDATE paper_account SET mode = 'HERMES_3.0_MODEL_2A'")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('strategy_version', 'HERMES_3.0_MODEL_2A')")
    conn.execute("UPDATE system_metrics SET value = 'HERMES_3.0_MODEL_2A' WHERE key = 'hermes_mode'")
    conn.commit()

print("SQLite database successfully updated to HERMES_3.0_MODEL_2A!")
