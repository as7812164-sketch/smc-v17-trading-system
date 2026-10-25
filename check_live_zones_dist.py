import urllib.request
import json

res = urllib.request.urlopen('https://smc-ai-agent.onrender.com/api/zones/active')
data = json.loads(res.read().decode())['zones']

t_res = urllib.request.urlopen('https://api.binance.com/api/v3/ticker/price')
tickers = {x['symbol']: float(x['price']) for x in json.loads(t_res.read().decode())}

print("=" * 80)
print(f"{'SYMBOL':<10} {'SIDE':<5} {'TF':<4} {'ENTRY (50% MT)':<15} {'LIVE PRICE':<15} {'DISTANCE':<12} {'IN OB ZONE'}")
print("=" * 80)

for z in data:
    sym = z['symbol']
    cur_p = tickers.get(sym, 0.0)
    entry_p = float(z['entry_price'])
    side = z['side']
    tf = z.get('timeframe', '4H')
    ob_h = float(z.get('ob_high', entry_p))
    ob_l = float(z.get('ob_low', entry_p))
    dist = (cur_p - entry_p) / entry_p * 100.0 if entry_p else 0
    in_zone = ob_l <= cur_p <= ob_h
    print(f"{sym:<10} {side:<5} {tf:<4} {entry_p:<15.5f} {cur_p:<15.5f} {dist:>+8.2f}%    {str(in_zone):<10}")

print("=" * 80)
