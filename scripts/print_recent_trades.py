import json

data = json.load(open('last_7days_audit_results.json', encoding='utf-8'))
trades = data['trades']

print("RECENT EXECUTIONS (LAST 18 TRADES):")
for t in trades[-18:]:
    sym = t['symbol']
    side = t['side']
    tf = t['timeframe']
    in_p = t['entry_price']
    out_p = t['exit_price']
    out = t['outcome']
    pnl = t['pnl_usdt']
    pnl_pct = t['pnl_pct']
    dur = t['duration_str']
    t_in = t['entry_time_str']
    wick = t['wick_pct']
    print(f"{t_in} | {sym:<10} | {side:<5} | {tf} | In: {in_p} -> Out: {out_p} | Wick: {wick:4.1f}% | {out:<18} | ${pnl:+5.2f} ({pnl_pct:+5.1f}%) | {dur}")
