import sys, os
sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

res = bitget_trader.exchange.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES'})
active_symbols = set()
for p in res.get('data', []):
    if float(p.get('total', 0) or 0) > 0:
        clean = p.get('symbol', '').replace('/', '').replace(':USDT', '').upper()
        active_symbols.add(clean)

print("Real Filled Positions on Bitget:", active_symbols)
print("Is ALGOUSDT filled on Bitget?", 'ALGOUSDT' in active_symbols)
print("Is SNXUSDT filled on Bitget?", 'SNXUSDT' in active_symbols)
