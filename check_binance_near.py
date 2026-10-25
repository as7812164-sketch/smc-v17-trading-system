import ccxt
from config import BINANCE_API_KEY, BINANCE_API_SECRET

binance = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

print("Fetching all open orders for NEARUSDT:")
try:
    orders = binance.fetch_open_orders('NEAR/USDT:USDT')
    for o in orders:
        print("Order:", o.get('id'), o.get('type'), o.get('side'), o.get('price'), o.get('stopPrice'), o.get('status'))
except Exception as e:
    print("Fetch open orders error:", e)

print("\nFetching position risk for NEARUSDT:")
try:
    pos = binance.fapiPrivateV2GetPositionRisk({'symbol': 'NEARUSDT'})
    print(pos)
except Exception as e:
    print("Pos risk error:", e)
