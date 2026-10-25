import ccxt
from config import BITGET_API_KEY, BITGET_SECRET, BITGET_PASSPHRASE

bitget = ccxt.bitget({
    'apiKey': BITGET_API_KEY,
    'secret': BITGET_SECRET,
    'password': BITGET_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# FET is currently SHORT on Bitget. Entry 0.2338.
# Let's check open positions
pos = bitget.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES'})
for p in pos.get('data', []):
    if float(p.get('total', 0) or 0) > 0:
        print("Bitget active pos:", p.get('symbol'), p.get('holdSide'), p.get('total'), p.get('openPriceAvg'))

# Let's try placing Pos TP/SL
try:
    res = bitget.privateMixPostV2MixOrderPlacePosTpsl({
        'marginCoin': 'USDT',
        'symbol': 'FETUSDT',
        'productType': 'USDT-FUTURES',
        'holdSide': 'short',
        'stopSurplusTriggerPrice': '0.2272',
        'stopSurplusTriggerType': 'fill_price',
        'stopLossTriggerPrice': '0.2427',
        'stopLossTriggerType': 'fill_price'
    })
    print("Pos TP/SL result:", res)
except Exception as e:
    print("Pos TP/SL error:", e)
