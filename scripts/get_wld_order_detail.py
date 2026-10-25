import sys
import os
import json

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

order_id = "1497082746252185601"
print(f"Fetching full order detail for WLD order {order_id}...")

try:
    res = bitget_trader.exchange.privateMixGetV2MixOrderDetail({
        'productType': 'USDT-FUTURES',
        'symbol': 'WLDUSDT',
        'orderId': order_id
    })
    print("Bitget API Detail Response:")
    print(json.dumps(res, indent=2))
except Exception as e:
    print("Error:", e)
