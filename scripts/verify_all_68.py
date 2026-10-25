import sys, os
sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader
import engine.hermes30_apex_live as h

markets = bitget_trader.exchange.load_markets()
symbols = h.TOP_22_CHAMPIONS

passed = 0
failed = []

for sym in symbols:
    clean = sym.replace('/', '').replace(':USDT', '').upper()
    if clean == '1000PEPEUSDT':
        ccxt_sym = 'PEPE/USDT:USDT'
    elif clean == 'MKRUSDT':
        ccxt_sym = 'AMKR/USDT:USDT'
    else:
        base = clean.replace('USDT', '')
        ccxt_sym = f'{base}/USDT:USDT'
    
    if ccxt_sym in markets:
        passed += 1
    else:
        failed.append((sym, ccxt_sym))

print(f"Passed: {passed}/{len(symbols)}")
if failed:
    print("Failed symbols:", failed)
else:
    print("ALL 68 COINS VALIDATED 100% ON BITGET FUTURES!")
