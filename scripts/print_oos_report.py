import json

with open("last_month_oos_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print(f"Summary:")
print(f"Period: {d['period']}")
print(f"Start: ${d['starting_balance_usdt']} -> End: ${d['ending_balance_usdt']} (+{d['net_growth_pct']}%)")
print(f"Trades: {d['total_trades']} | Wins: {d['wins']} | BE Saves: {d['be_saves']} | Losses: {d['losses']}")
print(f"Pure WR: {d['pure_win_rate_pct']}% | Effective WR: {d['effective_win_rate_pct']}% | PF: {d['profit_factor']} | Max DD: {d['max_drawdown_pct']}%")

print("\n--- ALL 58 TRADES LOG ---")
for t in d['trades']:
    tid = t['trade_id']
    sym = t['symbol']
    side = t['side']
    tf = t['timeframe']
    et = t['entry_time_str']
    ep = t['entry_price']
    tp = t['tp_price']
    sl = t['sl_price']
    xt = t['exit_time_str']
    xp = t['exit_price']
    dur = t['duration']
    out = t['outcome']
    pnl = t['net_pnl_usdt']
    bal = t['balance_after']
    print(f"#{tid:02d} | {sym:<9} | {side:<5} {tf} | Entry: {et} @ {ep} | Exit: {xt} @ {xp} | Dur: {dur} | {out:<7} | Net: {pnl:+.2f} USDT | Bal: ${bal:.2f}")
