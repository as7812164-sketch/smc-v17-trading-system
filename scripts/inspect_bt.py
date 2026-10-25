import sys
sys.path.append('.')
from engine.bitget_trader import BitgetTrader

trader = BitgetTrader()
bal = trader.fetch_futures_balance()
print("Live Futures Balance on Bitget:", bal)

active_aero = trader.is_symbol_active_on_exchange("AEROUSDT")
print("Is AEROUSDT active on Bitget?", active_aero)
