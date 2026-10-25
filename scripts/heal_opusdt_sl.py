import sqlite3
import json

db_path = 'database/smc_v17.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# For OPUSDT (id 537): entry 0.1409 SHORT, lowest 0.1353 -> peak ROI 19.87%
# Step 4: locked_roi_pct = 15.0%, spot_gain_pct = 0.03 -> sl_price = 0.1409 * (1 - 0.03) = 0.136673
c.execute("""
UPDATE paper_trades
SET trailing_sl_price = 0.136673,
    sl_price = 0.136673,
    locked_roi_pct = 15.0,
    trailing_step = 4,
    be_locked = 1
WHERE id = 537
""")
conn.commit()
conn.close()
print("OPUSDT trailing SL healed in SQLite!")

backup_path = 'database/local_vault_backup.json'
with open(backup_path, 'r', encoding='utf-8') as f:
    v = json.load(f)

for t in v.get('paper_trades', []):
    if t.get('id') == 537:
        t['trailing_sl_price'] = 0.136673
        t['sl_price'] = 0.136673
        t['locked_roi_pct'] = 15.0
        t['trailing_step'] = 4
        t['be_locked'] = 1

with open(backup_path, 'w', encoding='utf-8') as f:
    json.dump(v, f, indent=2)

print("OPUSDT trailing SL healed in local vault backup!")
