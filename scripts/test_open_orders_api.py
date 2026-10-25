import sys, os
sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader
import urllib.request, json

raw_orders = bitget_trader.exchange.fetch_open_orders()
print("Raw Bitget open orders count:", len(raw_orders))
for o in raw_orders:
    sym = o.get('symbol', '').replace('/', '').replace(':USDT', '').upper()
    print(f"Order: {sym} | Side: {o.get('side')} | Price: {o.get('price')} | Amount: {o.get('amount')} | Status: {o.get('status')}")
