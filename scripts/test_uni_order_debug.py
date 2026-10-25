import sys
import os

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

setup = {
    'symbol': 'UNIUSDT',
    'side': 'BUY',
    'entry_price': 7.3115,
    'tp_price': 7.5308,
    'sl_price': 7.2018,
    'margin_usdt': 5.72,
    'timeframe': '1h',
    'managed_by_hermes': True
}

# Test precision and order parameters without submitting live order
ccxt_sym = bitget_trader.format_symbol_for_bitget("UNIUSDT")
margin = 5.72
leverage = 5
notional = margin * leverage
raw_amount = notional / setup['entry_price']
amount = float(bitget_trader.exchange.amount_to_precision(ccxt_sym, raw_amount))
print("Raw amount:", raw_amount)
print("Precision amount:", amount)
print("Amount * Price (Notional):", amount * setup['entry_price'])

# Check what error could have happened
print("Testing set_leverage:")
try:
    bitget_trader.enforce_isolated_margin("UNIUSDT")
    bitget_trader.set_leverage_isolated(5, "UNIUSDT", "long")
    print("Leverage and margin mode OK!")
except Exception as e:
    print("Error:", e)
