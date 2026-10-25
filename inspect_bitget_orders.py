import json
from engine.bitget_trader import bitget_trader

if not bitget_trader.exchange:
    bitget_trader._init_exchange()

print("--- BITGET POSITION HISTORY ---")
try:
    res = bitget_trader.exchange.privateMixGetV2MixPositionHistoryPosition({'productType': 'USDT-FUTURES', 'pageSize': '10'})
    for p in res.get('data', {}).get('list', []):
        if p.get('symbol') in ('DOGEUSDT', '1000BONKUSDT'):
            print(json.dumps(p, indent=2))
except Exception as e:
    print("Error pos hist:", e)

print("--- BITGET ORDER HISTORY ---")
try:
    orders = bitget_trader.exchange.privateMixGetV2MixOrderHistoryOrders({'productType': 'USDT-FUTURES', 'symbol': 'DOGEUSDT', 'pageSize': '5'})
    for o in orders.get('data', {}).get('entrustedList', []):
        print(f"DOGE Order: id={o.get('orderId')} type={o.get('orderType')} side={o.get('side')} status={o.get('status')} price={o.get('price')} avg={o.get('priceAvg')} size={o.get('size')} uTime={o.get('uTime')}")
except Exception as e:
    print("Error order hist DOGE:", e)

try:
    orders = bitget_trader.exchange.privateMixGetV2MixOrderHistoryOrders({'productType': 'USDT-FUTURES', 'symbol': '1000BONKUSDT', 'pageSize': '5'})
    for o in orders.get('data', {}).get('entrustedList', []):
        print(f"BONK Order: id={o.get('orderId')} type={o.get('orderType')} side={o.get('side')} status={o.get('status')} price={o.get('price')} avg={o.get('priceAvg')} size={o.get('size')} uTime={o.get('uTime')}")
except Exception as e:
    print("Error order hist BONK:", e)
