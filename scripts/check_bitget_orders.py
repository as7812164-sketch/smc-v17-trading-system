import sys
import os

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

print("Checking Bitget orders and history...")
if bitget_trader.exchange:
    try:
        # Fetch open orders via ccxt
        orders = bitget_trader.exchange.fetch_open_orders()
        print(f"\nfetch_open_orders() returned {len(orders)} orders:")
        for o in orders:
            print(f"- {o['symbol']} {o['side']} {o['type']} | Price: {o['price']} | Amount: {o['amount']} | Status: {o['status']}")
    except Exception as e:
        print("fetch_open_orders error:", e)

    try:
        # Check plan orders (trigger/TP/SL)
        res = bitget_trader.exchange.privateMixGetV2MixOrderCurrentPlanOrder({'productType': 'USDT-FUTURES'})
        print(f"\nprivateMixGetV2MixOrderCurrentPlanOrder: {res}")
    except Exception as e:
        print("plan order error:", e)

    try:
        # Check order history (last 5 orders) to see if UNIUSDT order was placed, rejected, or canceled
        res = bitget_trader.exchange.privateMixGetV2MixOrderOrdersHistory({'productType': 'USDT-FUTURES', 'limit': '10'})
        hist = res.get('data', {}).get('entrustedList', [])
        print(f"\nRecent Order History ({len(hist)}):")
        for h in hist:
            print(f"- {h.get('symbol')} {h.get('side')} {h.get('orderType')} | Price: {h.get('price')} | Size: {h.get('size')} | State: {h.get('state')} | Reason: {h.get('cancelReason', h.get('errCode', ''))}")
    except Exception as e:
        print("orders history error:", e)
