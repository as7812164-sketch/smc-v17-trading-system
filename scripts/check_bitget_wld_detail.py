import sys
import os

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

print("=== CHECKING BITGET LIVE POSITIONS ===")
res = bitget_trader.exchange.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES'})
pos = [p for p in res.get('data', []) if float(p.get('total', 0) or 0) > 0]
print(f"Total Active Positions on Bitget: {len(pos)}")
for p in pos:
    print(f"* Symbol: {p.get('symbol')} | Side: {p.get('holdSide')} | Contracts: {p.get('total')} | Entry: {p.get('openPriceAvg')} | Mark: {p.get('markPrice')} | PnL: {p.get('unrealizedPL')}")

print("\n=== CHECKING BITGET OPEN LIMIT ORDERS ===")
# Fetch open orders using ccxt fetch_open_orders
try:
    open_orders = bitget_trader.exchange.fetch_open_orders()
    print(f"Total Open Orders on Bitget: {len(open_orders)}")
    for o in open_orders:
        print(f"* ID: {o['id']} | Symbol: {o['symbol']} | Side: {o['side']} | Type: {o['type']} | Price: {o['price']} | Amount: {o['amount']} | Status: {o['status']}")
except Exception as e:
    print("Error fetch_open_orders:", e)

# Also check raw orders history detail for WLD
try:
    res = bitget_trader.exchange.privateMixGetV2MixOrderOrdersHistory({'productType': 'USDT-FUTURES', 'symbol': 'WLDUSDT', 'limit': '5'})
    print("\nWLD Orders Detail in Bitget:")
    wld_orders = res.get('data', {}).get('entrustedList', [])
    for wo in wld_orders:
        print(f"* OrderId: {wo.get('orderId')} | Symbol: {wo.get('symbol')} | State: {wo.get('state')} | Price: {wo.get('price')} | Size: {wo.get('size')} | Filled: {wo.get('baseVolume')} | CancelReason: {wo.get('cancelReason')}")
except Exception as e:
    print("Error:", e)
