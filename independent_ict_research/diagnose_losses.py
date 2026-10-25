import os, sys, json
sys.path.append(r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\independent_ict_research')
from battle_hermes35_vs_apex_ict import load_candles, generate_hermes35_trades, TOP_22_CHAMPIONS

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

trades = generate_hermes35_trades(all_data)
trades.sort(key=lambda x: x['time'])
executed = []
active_exit = 0
for t in trades:
    if t['time'] >= active_exit:
        executed.append(t)
        active_exit = t['exit_time']

losses = [t for t in executed if t['res'] == 'LOSS']

# 1. Test BTC Alignment on Losses
btc_against_losses = 0
btc_matched = 0
for t in losses:
    tf = t['tf']
    t_time = t['time']
    btc_c = btc_data[tf].get(t_time)
    if btc_c:
        btc_matched += 1
        btc_dir = 'BULLISH' if btc_c['close'] > btc_c['open'] else 'BEARISH'
        if t['side'] == 'LONG' and btc_dir == 'BEARISH':
            btc_against_losses += 1
        elif t['side'] == 'SHORT' and btc_dir == 'BULLISH':
            btc_against_losses += 1

print(f"Losses taken AGAINST current BTC candle direction: {btc_against_losses} / {btc_matched} ({btc_against_losses/btc_matched*100:.1f}%)")

# 2. Check 1H vs 4H Win Rate
trades_1h = [t for t in executed if t['tf'] == '1h']
trades_4h = [t for t in executed if t['tf'] == '4h']
w_1h = sum(1 for t in trades_1h if t['res'] == 'WIN')
w_4h = sum(1 for t in trades_4h if t['res'] == 'WIN')
l_1h = len(trades_1h) - w_1h
l_4h = len(trades_4h) - w_4h

print(f"1H Trades: {len(trades_1h)} | Win Rate: {w_1h/len(trades_1h)*100:.2f}% | Wins: {w_1h} | Losses: {l_1h}")
print(f"4H Trades: {len(trades_4h)} | Win Rate: {w_4h/len(trades_4h)*100:.2f}% | Wins: {w_4h} | Losses: {l_4h}")

# 3. Fast loss vs Slow loss (Duration in bars before hitting SL)
durations = []
for t in losses:
    # calculate rough bars
    bar_sec = 3600 if t['tf'] == '1h' else 14400
    bars = (t['exit_time'] - t['time']) / 1000 / bar_sec
    durations.append(bars)

import numpy as np
print(f"Mean loss duration: {np.mean(durations):.1f} bars | Median: {np.median(durations):.1f} bars")
instant_losses = sum(1 for d in durations if d <= 3)
print(f"Instant stop-outs within 1-3 bars: {instant_losses} / {len(losses)} ({instant_losses/len(losses)*100:.1f}%)")
