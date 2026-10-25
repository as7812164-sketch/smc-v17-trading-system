import json

with open("hermes30_1to2_oos_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)
trades = d["trades"]
sls = [t for t in trades if t["outcome"] == "SL_HIT"]
print("--- HERMES 3.0 STOP LOSS TRADES (TOTAL 6) ---")
for idx, t in enumerate(sls, 1):
    print(f"{idx}. {t['symbol']} {t['side']} ({t['timeframe']}) on {t['entry_time_str']} | Dur: {t['duration']} | Net P&L: ${t['net_pnl_usdt']} | Bal: ${t['balance_after']}")
