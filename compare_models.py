import json
from run_1year_master_backtest import load_candles_1y, CHAMPIONS, calculate_ema, backtest_engine

candles_dict = {}
for sym in CHAMPIONS:
    c = load_candles_1y(sym)
    if c: candles_dict[sym] = c

btc_candles = candles_dict.get('BTCUSDT', [])
btc_trend = {}
if btc_candles:
    btc_closes = [c[4] for c in btc_candles]
    ema50 = calculate_ema(btc_closes, 50)
    for i in range(len(btc_candles)):
        btc_trend[btc_candles[i][0]] = (btc_candles[i][4] >= ema50[i])

print("Running ZEN_NO_BE backtest...")
res_no_be, trades_no_be = backtest_engine(candles_dict, btc_trend, CHAMPIONS, mode='ZEN_NO_BE')
print("=== ZEN NO BE RESULTS ===")
print(f"Total trades : {len(trades_no_be)}")
print(f"Wins         : {res_no_be['wins']} | Losses: {res_no_be['losses']} | Win Rate: {res_no_be['win_rate']:.2f}%")
print(f"Net ROE      : +{res_no_be['net_roe']:.1f}%")
print(f"Profit Factor: {res_no_be['profit_factor']:.2f}")
print(f"Ending Balance ($50 start): ${res_no_be['ending_balance']:.2f}")
print(f"Max Drawdown : {res_no_be['max_drawdown']:.2f}%")
