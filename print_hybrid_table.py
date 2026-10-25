import json

with open('hermes_35_zen_hybrid_audit_result.json', encoding='utf-8') as f:
    d = json.load(f)

champs = d['champions_15_pairs']['stats']
sorted_c = sorted(champs.items(), key=lambda x: x[1]['net_roe'], reverse=True)

print(f"{'Symbol':<12} | {'Trades':<6} | {'Wins':<5} | {'Loss':<5} | {'WinRate':<8} | {'Net ROE':<10}")
print("-" * 60)
for s, st in sorted_c:
    print(f"{s:<12} | {st['total']:<6} | {st['wins']:<5} | {st['losses']:<5} | {st['win_rate']:>6.1f}% | {st['net_roe']:>+8.1f}%")

print("-" * 60)
tot = d['champions_15_pairs']
print(f"{'CHAMPIONS':<12} | {tot['total_trades']:<6} | {tot['wins']:<5} | {tot['losses']:<5} | {tot['win_rate']:>6.1f}% | {tot['net_roe']:>+8.1f}%")
print(f"Profit Factor: {tot['profit_factor']:.2f}")
