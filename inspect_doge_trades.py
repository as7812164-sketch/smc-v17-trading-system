import json
from engine.bitget_trader import bitget_trader

if not bitget_trader.exchange:
    bitget_trader._init_exchange()

# Try fetch_my_trades or fetch_orders
try:
    trades = bitget_trader.exchange.fetch_my_trades('DOGE/USDT:USDT', limit=5)
    print("DOGE Trades:")
    for t in trades:
        print(t.get('datetime'), t.get('side'), t.get('price'), t.get('amount'), t.get('info', {}).get('orderId'), t.get('info', {}).get('tradeScope'))
except Exception as e:
    print("Trades err:", e)

try:
    orders = bitget_trader.exchange.fetch_orders('DOGE/USDT:USDT', limit=5)
    print("DOGE Orders:")
    for o in orders:
        print(o.get('datetime'), o.get('status'), o.get('type'), o.get('side'), o.get('price'), o.get('average'), o.get('amount'), o.get('info', {}).get('orderType'), o.get('info', {}).get('tradeSide'))
except Exception as e:
    print("Orders err:", e)
