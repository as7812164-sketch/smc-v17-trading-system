import json

with open(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\scripts\bb30_sep_oct_trades.json", "r", encoding="utf-8") as f:
    data = json.load(f)

oct_trades = data["october"]
sep_trades = data["september"]

print(f"Total October trades: {len(oct_trades)}")
print(f"Total September trades: {len(sep_trades)}")

print("\n--- TOP 5 OCTOBER 2026 WINNERS ---")
oct_sorted = sorted(oct_trades, key=lambda x: x["pnl_r"], reverse=True)
for t in oct_sorted[:5]:
    print(f"  {t['day']} | {t['symbol']:<12} | {t['side']:<5} | Entry: {t['entry']:<10.4f} | Exit: {t['exit']:<10.4f} | Net: {t['pnl_r']:+6.2f}R | Peak: +{t['highest_r']:.2f}R")

print("\n--- RECENT 5 OCTOBER 2026 TRADES ---")
for t in oct_trades[-5:]:
    print(f"  {t['day']} | {t['symbol']:<12} | {t['side']:<5} | Entry: {t['entry']:<10.4f} | Outcome: {t['outcome']:<16} | Net: {t['pnl_r']:+6.2f}R")

print("\n--- TOP 5 SEPTEMBER 2026 WINNERS ---")
sep_sorted = sorted(sep_trades, key=lambda x: x["pnl_r"], reverse=True)
for t in sep_sorted[:5]:
    print(f"  {t['day']} | {t['symbol']:<12} | {t['side']:<5} | Entry: {t['entry']:<10.4f} | Exit: {t['exit']:<10.4f} | Net: {t['pnl_r']:+6.2f}R | Peak: +{t['highest_r']:.2f}R")
