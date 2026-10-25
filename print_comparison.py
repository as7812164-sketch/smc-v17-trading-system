import json

with open('hermes_zen_sniper_1month_audit_result.json', encoding='utf-8') as f:
    d_be = json.load(f)

with open('hermes_zen_sniper_no_be_audit_result.json', encoding='utf-8') as f:
    d_no_be = json.load(f)

stats_be = d_be['symbol_stats']
stats_no_be = d_no_be['symbol_stats']

sorted_symbols = sorted(stats_no_be.items(), key=lambda x: x[1]['net_roe'], reverse=True)

print(f"{'Symbol':<10} | {'With BE Win%':<12} | {'With BE Net':<12} | {'No BE Win%':<11} | {'No BE Net':<11} | {'Diff ROE':<9}")
print("-" * 75)
for s, st_no in sorted_symbols:
    st_b = stats_be.get(s, {})
    win_b = f"{st_b.get('win_rate', 0):.1f}%"
    net_b = f"{st_b.get('net_roe', 0):+.1f}%"
    win_no = f"{st_no.get('win_rate', 0):.1f}%"
    net_no = f"{st_no.get('net_roe', 0):+.1f}%"
    diff = st_no.get('net_roe', 0) - st_b.get('net_roe', 0)
    diff_str = f"{diff:+.1f}%"
    print(f"{s:<10} | {win_b:<12} | {net_b:<12} | {win_no:<11} | {net_no:<11} | {diff_str:<9}")

print("-" * 75)
tot_win_b = f"{d_be['pure_win_rate']:.1f}%"
tot_net_b = f"{d_be['total_net_roe']:+.1f}%"
tot_win_no = f"{d_no_be['pure_win_rate']:.1f}%"
tot_net_no = f"{d_no_be['total_net_roe']:+.1f}%"
diff_tot = d_no_be['total_net_roe'] - d_be['total_net_roe']
print(f"{'TOTAL':<10} | {tot_win_b:<12} | {tot_net_b:<12} | {tot_win_no:<11} | {tot_net_no:<11} | {diff_tot:+.1f}%")
