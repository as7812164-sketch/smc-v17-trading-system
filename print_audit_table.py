import json

with open('hermes_zen_sniper_1month_audit_result.json', encoding='utf-8') as f:
    d = json.load(f)

stats = d['symbol_stats']
sorted_symbols = sorted(stats.items(), key=lambda x: x[1]['net_roe'], reverse=True)
print(f"{'Symbol':<12} | {'Trades':<6} | {'Wins':<4} | {'BE':<4} | {'Loss':<4} | {'WinRate':<8} | {'CapPreserved':<12} | {'Net ROE':<10}")
print("-" * 75)
for s, st in sorted_symbols:
    print(f"{s:<12} | {st['total']:<6} | {st['wins']:<4} | {st['bes']:<4} | {st['losses']:<4} | {st['win_rate']:>6.1f}% | {st['capital_preserved']:>10.1f}% | {st['net_roe']:>+8.1f}%")

print("-" * 75)
print(f"{'TOTAL':<12} | {d['total_trades']:<6} | {d['wins']:<4} | {d['bes']:<4} | {d['losses']:<4} | {d['pure_win_rate']:>6.1f}% | {d['capital_preserved_rate']:>10.1f}% | {d['total_net_roe']:>+8.1f}%")
