import ccxt
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BITGET_API_KEY, BITGET_SECRET, BITGET_PASSPHRASE

print("=== BINANCE OPEN ORDERS (NEARUSDT) ===")
try:
    binance = ccxt.binance({
        'apiKey': BINANCE_API_KEY,
        'secret': BINANCE_API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    orders = binance.fapiPrivateGetOpenOrders({'symbol': 'NEARUSDT'})
    print(f"Total open orders: {len(orders)}")
    for o in orders:
        print(f"ID: {o.get('orderId')}, Type: {o.get('type')}, Side: {o.get('side')}, OrigQty: {o.get('origQty')}, Price: {o.get('price')}, StopPrice: {o.get('stopPrice')}")
except Exception as e:
    print("Binance error:", e)

print("\n=== BITGET OPEN ORDERS (FETUSDT) ===")
try:
    bitget = ccxt.bitget({
        'apiKey': BITGET_API_KEY,
        'secret': BITGET_SECRET,
        'password': BITGET_PASSPHRASE,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    orders = bitget.privateMixGetV2MixOrderOrdersPlanPending({'symbol': 'FETUSDT', 'productType': 'USDT-FUTURES'})
    print("Bitget Plan orders response:", orders)
    regular = bitget.privateMixGetV2MixOrderOrdersPending({'symbol': 'FETUSDT', 'productType': 'USDT-FUTURES'})
    print("Bitget Regular orders response:", regular)
except Exception as e:
    print("Bitget error:", e)
