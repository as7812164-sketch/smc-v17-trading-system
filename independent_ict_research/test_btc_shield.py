import os, sys, json
sys.path.append(r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\independent_ict_research')
from battle_hermes35_vs_apex_ict import load_candles, generate_hermes35_trades, TOP_22_CHAMPIONS, run_compounding_arena

all_data = {'1h': {}, '4h': {}}
for sym in TOP_22_CHAMPIONS:
    for tf in ['1h', '4h']:
        c = load_candles(sym, tf)
        if len(c) >= 500:
            all_data[tf][sym] = c

btc_data = {
    '1h': {c['time']: c for c in all_data['1h'].get('BTCUSDT', [])},
    '4h': {c['time']: c for c in all_data['4h'].get('BTCUSDT', [])}
}

raw_trades = generate_hermes35_trades(all_data)

# Test with King BTC Filter:
# Rule: If Altcoin is LONG, BTC must NOT be actively dumping (> -0.5% red bar)
# Rule: If Altcoin is SHORT, BTC must NOT be actively pumping (> +0.5% green bar)
filtered_trades = []
for t in raw_trades:
    if t['sym'] == 'BTCUSDT':
        filtered_trades.append(t)
        continue
    tf = t['tf']
    btc_c = btc_data[tf].get(t['time'])
    if btc_c:
        btc_return = (btc_c['close'] - btc_c['open']) / btc_c['open']
        # Disqualify long if BTC is dumping
        if t['side'] == 'LONG' and btc_return < -0.005:
            continue
        # Disqualify short if BTC is pumping
        if t['side'] == 'SHORT' and btc_return > 0.005:
            continue
    filtered_trades.append(t)

res_raw = run_compounding_arena(raw_trades, 'HERMES_3.5_RAW')
res_btc = run_compounding_arena(filtered_trades, 'HERMES_3.5_BTC_SHIELD')

print(f"RAW HERMES 3.5: Trades: {res_raw['sequential_trades_executed']} | Win Rate: {res_raw['win_rate_pct']}% | Wins: {res_raw['wins']} | Losses: {res_raw['losses']}")
print(f"BTC SHIELDED:  Trades: {res_btc['sequential_trades_executed']} | Win Rate: {res_btc['win_rate_pct']}% | Wins: {res_btc['wins']} | Losses: {res_btc['losses']}")
print(f"Max DD: RAW={res_raw['max_drawdown_pct']}% vs BTC_SHIELD={res_btc['max_drawdown_pct']}%")
print(f"Wealth: RAW=${res_raw['total_wealth_usdt']:,.2f} vs BTC_SHIELD=${res_btc['total_wealth_usdt']:,.2f}")
