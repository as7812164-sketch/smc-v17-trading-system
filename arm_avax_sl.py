import ccxt
from config import BINANCE_API_KEY, BINANCE_API_SECRET

binance = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# AVAX is SHORT 23 contracts. Entry 10.949.
# Hard Disaster SL is 11.262 (+2.86% or +3.8%). Close side is 'buy'.
try:
    res = binance.create_order(
        symbol='AVAX/USDT:USDT',
        type='STOP_MARKET',
        side='buy',
        amount=23,
        params={
            'stopPrice': 11.262,
            'positionSide': 'SHORT'
        }
    )
    print("SUCCESS ARMING AVAX SL:", res.get('id'), res.get('type'), res.get('triggerPrice'))
except Exception as e:
    print("Error arming AVAX SL:", e)
