import sys
sys.path.append("C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system")

from database.db import get_connection
from database.cloud_vault import push_vault_state

# 1. Update SQLite trades
with get_connection() as conn:
    conn.execute("UPDATE paper_trades SET status = CASE WHEN pnl_usdt > 0 THEN 'TP_HIT' ELSE 'SL_HIT' END WHERE id IN (584, 616, 621, 623);")
    conn.commit()

# 2. Push to local backup and Cloud Vault GitHub
success = push_vault_state()
print("Cloud Vault push success:", success)

# 3. Verify open trades in db
with get_connection() as conn:
    rows = conn.execute("SELECT id, symbol, side, status, account_id FROM paper_trades WHERE status = 'OPEN'").fetchall()
    print("Open trades in DB now:", len(rows), [dict(r) for r in rows])
