import json

with open("locked_100pct_compounding_100trades.json", "r", encoding="utf-8") as f:
    d = json.load(f)

trades = d["scenario1_single_wallet"]["trades"]
indices = [0, 4, 9, 19, 29, 39, 49, 59, 69, 79, 83, 89, 97, 99]

print("-" * 75)
print(f"{'Trade #':<8} | {'Side':<6} | {'Symbol':<10} | {'Result':<6} | {'P&L ($)':<12} | {'New Balance ($)':<15}")
print("-" * 75)
for i in indices:
    t = trades[i]
    print(f"#{t['trade_num']:<7} | {t['side']:<6} | {t['sym']:<10} | {t['res']:<6} | ${t['pnl']:>10.2f} | ${t['balance']:>13.2f}")
print("-" * 75)
