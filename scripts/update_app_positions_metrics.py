import re

path_app = "C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/app.py"
with open(path_app, "r", encoding="utf-8") as f:
    text = f.read()

# Update liq_price formula in get_futures_positions
old_liq = """        if is_buy:
            pnl_pct = ((mark_price - entry) / entry * 100.0) if entry > 0 else 0.0
            liq_price = round(entry * 0.805, 4)
        else:
            pnl_pct = ((entry - mark_price) / entry * 100.0) if entry > 0 else 0.0
            liq_price = round(entry * 1.195, 4)"""

new_liq = """        if is_buy:
            pnl_pct = ((mark_price - entry) / entry * 100.0) if entry > 0 else 0.0
            liq_price = round(entry * (1.0 - (1.0 / leverage) + 0.0125), 4)
        else:
            pnl_pct = ((entry - mark_price) / entry * 100.0) if entry > 0 else 0.0
            liq_price = round(entry * (1.0 + (1.0 / leverage) - 0.0125), 4)"""

text = text.replace(old_liq, new_liq)

# Update size_coin in get_futures_positions
old_size_coin = 'size_coin = round(size_usdt / entry, 2) if entry > 0 else 0.0'
new_size_coin = '''raw_coin = (size_usdt / entry) if entry > 0 else 0.0
        size_coin = int(round(raw_coin)) if raw_coin >= 10 else round(raw_coin, 2)'''

text = text.replace(old_size_coin, new_size_coin)

# Update margin_mode & mmr
text = text.replace('"margin_mode": "Cross",', '"margin_mode": "Isolated",')
text = text.replace('"mmr": "0.39%",', '"mmr": "5.30%",')
text = text.replace('"realized_pnl": -0.0115,', '"realized_pnl": -0.005,')
text = text.replace('"realized_pnl_str": "-0.0115",', '"realized_pnl_str": "-0.005",')

with open(path_app, "w", encoding="utf-8") as f:
    f.write(text)

print("Updated app.py with Bitget exact metrics successfully")
