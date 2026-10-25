import ccxt
from config import BINANCE_API_KEY, BINANCE_API_SECRET

binance = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

print("=== AVAXUSDT OPEN ORDERS ===")
orders = binance.fetch_open_orders('AVAX/USDT:USDT')
for o in orders:
    print(o.get('id'), o.get('type'), o.get('side'), o.get('price'), o.get('stopPrice'))
if not orders:
    print("NO OPEN ORDERS FOR AVAX!")
