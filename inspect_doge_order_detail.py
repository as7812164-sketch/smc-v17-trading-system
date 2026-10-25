import json
from engine.bitget_trader import bitget_trader

if not bitget_trader.exchange:
    bitget_trader._init_exchange()

try:
    order = bitget_trader.exchange.privateMixGetV2MixOrderDetail({
        'productType': 'USDT-FUTURES',
        'symbol': 'DOGEUSDT',
        'orderId': '1497481199893499905'
    })
    print(json.dumps(order, indent=2))
except Exception as e:
    print("Err order detail:", e)

try:
    plan_orders = bitget_trader.exchange.privateMixGetV2MixOrderOrdersPlanPending({
        'productType': 'USDT-FUTURES'
    })
    print("Pending Plan orders:", json.dumps(plan_orders, indent=2))
except Exception as e:
    print("Err plan:", e)
