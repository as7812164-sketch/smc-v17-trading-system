import re

# 1. Update engine/hermes30_apex_live.py
path_live = "C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/engine/hermes30_apex_live.py"
with open(path_live, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('curr_balance = float(acc.get("current_balance", 50.0) or 50.0)', 'curr_balance = float(acc.get("current_balance", 5.0) or 5.0)')
text = text.replace('if curr_balance < 5.0:', 'if curr_balance < 4.50:')
text = text.replace('new_b = close_res.get("new_balance", 50.0)', 'new_b = close_res.get("new_balance", 5.0)')

with open(path_live, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated hermes30_apex_live.py successfully")

# 2. Update config.py
path_cfg = "C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/config.py"
with open(path_cfg, "r", encoding="utf-8") as f:
    cfg = f.read()

cfg = cfg.replace('BITGET_AUTO_TRADE = False', 'BITGET_AUTO_TRADE = True')
cfg = cfg.replace('BITGET_STARTING_MARGIN = 50.0', 'BITGET_STARTING_MARGIN = 5.0')

with open(path_cfg, "w", encoding="utf-8") as f:
    f.write(cfg)
print("Updated config.py successfully")
