import sys
import os

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

print("Checking UNIUSDT market rules on Bitget...")
ccxt_sym = bitget_trader.format_symbol_for_bitget("UNIUSDT")
print("CCXT Symbol:", ccxt_sym)

if bitget_trader.exchange:
    try:
        # Load markets to check min amount, precision, etc.
        markets = bitget_trader.exchange.load_markets()
        market = markets.get(ccxt_sym)
        if market:
            print("Market found:")
            print("Limits:", market.get("limits"))
            print("Precision:", market.get("precision"))
            print("Contract size:", market.get("contractSize"))
        else:
            print(f"Market {ccxt_sym} NOT FOUND in bitget markets!")
            # Check what UNI markets exist
            uni_matches = [m for m in markets.keys() if "UNI" in m]
            print("UNI matches in markets:", uni_matches)
    except Exception as e:
        print("Error checking market:", e)

    # Also check what the free balance was or is
    bal = bitget_trader.fetch_futures_balance()
    print("Balance:", bal)
