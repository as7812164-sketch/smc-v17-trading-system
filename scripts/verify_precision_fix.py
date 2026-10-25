import sys
import os

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

print("Testing load_markets and amount_to_precision:")
bitget_trader.exchange.load_markets()
ccxt_sym = bitget_trader.format_symbol_for_bitget("UNIUSDT")
raw_amount = 3.9116
amount = float(bitget_trader.exchange.amount_to_precision(ccxt_sym, raw_amount))
print(f"CCXT Symbol: {ccxt_sym} | Raw: {raw_amount} -> Precision Amount: {amount}")

ccxt_one = bitget_trader.format_symbol_for_bitget("ONEUSDT")
raw_one = 17301.038
amount_one = float(bitget_trader.exchange.amount_to_precision(ccxt_one, raw_one))
print(f"CCXT Symbol: {ccxt_one} | Raw: {raw_one} -> Precision Amount: {amount_one}")
