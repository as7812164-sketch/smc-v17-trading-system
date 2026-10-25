import os
from database.db import set_setting, get_setting, get_paper_account, get_connection
from database.cloud_vault import push_vault_state

set_setting("strategy_version", "HERMES_3.5_DUAL_TIER_SNIPER")
set_setting("bitget_auto_trade", "false")
set_setting("binance_auto_trade", "false")
set_setting("allow_local_live_trading", "false")

with get_connection() as conn:
    conn.execute("UPDATE paper_account SET mode = 'HERMES_3.5_DUAL_TIER_SNIPER'")
    conn.execute("UPDATE system_metrics SET value = 'HERMES_3.5_DUAL_TIER_SNIPER' WHERE key = 'hermes_mode'")
    conn.commit()

from engine.self_healing_sentinel import self_healing_sentinel
repairs = self_healing_sentinel.auto_heal_strategy_consistency()
print("Self-healing repairs:", repairs)
print("strategy_version:", get_setting("strategy_version"))

for i in [1, 2, 3, 4]:
    acc = get_paper_account(account_id=i)
    print(f"Account {i}: name='{acc['name']}', balance=${acc['current_balance']}, mode='{acc['mode']}'")

# Push to vault
push_res = push_vault_state()
print("Vault pushed successfully:", push_res)
