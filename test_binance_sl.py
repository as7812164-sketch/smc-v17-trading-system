import ccxt
from config import BINANCE_API_KEY, BINANCE_API_SECRET

binance = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# Let's test what order type Binance Futures accepts for Stop Loss
# NEAR entry is 4.908. Hard disaster SL is around 4.721.
# Pos side is LONG, so close side is sell.
try:
    print("Testing STOP_MARKET...")
    res = binance.create_order(
        symbol='NEAR/USDT:USDT',
        type='STOP_MARKET',
        side='sell',
        amount=50,
        params={
            'stopPrice': 4.721,
            'positionSide': 'LONG'
        }
    )
    print("SUCCESS STOP_MARKET:", res)
except Exception as e:
    print("STOP_MARKET error:", e)
