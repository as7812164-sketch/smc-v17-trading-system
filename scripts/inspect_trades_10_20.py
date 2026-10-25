import json

with open("hermes30_1to2_oos_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)
trades = d["trades"]
print("TRADES 10 TO 20 IN JSON:")
for t in trades[9:20]:
    print(f"#{t['trade_id']} | {t['symbol']} | {t['side']} | {t['timeframe']} | Entry Time: {t['entry_time_str']} | Entry: {t['entry_price']:.4f} | TP: {t['tp_price']:.4f} | SL: {t['sl_price']:.4f} | Exit: {t['exit_price']:.4f} | Outcome: {t['outcome']} | P&L: ${t['net_pnl_usdt']:.2f} | Bal: ${t['balance_after']:.2f}")
