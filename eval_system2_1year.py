import json
import os

# Let's inspect the trades of System 2 and run compounding
from run_1year_master_backtest import ALL_AVAILABLE, load_candles_1y, backtest_engine, calculate_ema

candles_dict = {}
for s in ALL_AVAILABLE:
    c = load_candles_1y(s)
    if c:
        candles_dict[s] = c

btc_candles = candles_dict.get('BTCUSDT', [])
btc_closes = [c[4] for c in btc_candles]
btc_ema50 = calculate_ema(btc_closes, 50)
btc_trend_dict = {btc_candles[i][0]: (btc_closes[i] >= btc_ema50[i]) for i in range(len(btc_candles))}

t2, s2 = backtest_engine(candles_dict, btc_trend_dict, ALL_AVAILABLE, mode="ZEN_NO_BE")

# Sort symbols by Net ROE
sorted_s2 = sorted(s2.items(), key=lambda x: x[1]['net_roe'], reverse=True)

print(f"{'Symbol':<12} | {'Trades':<6} | {'Wins':<5} | {'Loss':<5} | {'WinRate':<8} | {'Net ROE':<10}")
print("-" * 60)
for s, st in sorted_s2:
    print(f"{s:<12} | {st['total']:<6} | {st['wins']:<5} | {st['losses']:<5} | {st['win_rate']:>6.1f}% | {st['net_roe']:>+8.1f}%")

# Sequential Compounding Simulation with realistic position risk (2.5% risk or fixed 10% margin)
# Risk model: Margin = 20% equity @ 5x leverage
sorted_trades = sorted(t2, key=lambda x: x['entry_time'])
bal = 50.0
peak = bal
mdd = 0.0
bal_history = []

for tr in sorted_trades:
    # 15% account margin per trade
    margin = bal * 0.15
    pnl = margin * (tr['roe'] / 100.0)
    bal += pnl
    if bal > peak: peak = bal
    dd = (peak - bal) / peak * 100.0
    if dd > mdd: mdd = dd
    bal_history.append(bal)

print("=" * 60)
print(f"1-Year Compounding ($50 start, 15% margin allocation):")
print(f"Ending Balance: ${bal:,.2f}")
print(f"Total Growth: {((bal-50)/50)*100:+,.1f}%")
print(f"Max Drawdown: {mdd:.1f}%")
