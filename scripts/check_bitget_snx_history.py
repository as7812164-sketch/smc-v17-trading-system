import sys
import os
import datetime

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

print("Checking Bitget order history without symbol filter...")
res = bitget_trader.exchange.privateMixGetV2MixOrderOrdersHistory({'productType': 'USDT-FUTURES', 'limit': '20'})
hist = res.get('data', {}).get('entrustedList', [])
print(f"Total orders returned: {len(hist)}")
for h in hist:
    c_time = datetime.datetime.fromtimestamp(int(h.get('cTime', 0))/1000.0) if h.get('cTime') else 'N/A'
    print(f"- {h.get('symbol')} {h.get('side')} {h.get('orderType')} | Price: {h.get('price')} | Size: {h.get('size')} | State: {h.get('state')} | Time: {c_time} | Reason: {h.get('cancelReason', h.get('errCode', ''))}")

# Also check open orders on Bitget right now!
open_orders = bitget_trader.exchange.fetch_open_orders()
print(f"\nTotal Open Orders on Bitget right now: {len(open_orders)}")
for o in open_orders:
    print(f"* {o['symbol']} {o['side']} {o['type']} | Price: {o['price']} | Amount: {o['amount']} | Status: {o['status']}")

# Check live positions on Bitget right now
res = bitget_trader.exchange.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES'})
pos = [p for p in res.get('data', []) if float(p.get('total', 0) or 0) > 0]
print(f"\nTotal Live Positions on Bitget: {len(pos)}")
for p in pos:
    print(f"* Symbol: {p.get('symbol')} | Side: {p.get('holdSide')} | Contracts: {p.get('total')} | Entry: {p.get('openPriceAvg')} | Mark: {p.get('markPrice')} | PnL: {p.get('unrealizedPL')}")
