import ccxt, json
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BITGET_API_KEY, BITGET_SECRET, BITGET_PASSPHRASE

print("=== BINANCE POSITIONS ===")
try:
    binance = ccxt.binance({
        'apiKey': BINANCE_API_KEY,
        'secret': BINANCE_API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    positions = binance.fapiPrivateV2GetPositionRisk()
    active_b = [p for p in positions if abs(float(p.get('positionAmt', 0))) > 0]
    for p in active_b:
        print(f"Symbol: {p.get('symbol')}, Amt: {p.get('positionAmt')}, Entry: {p.get('entryPrice')}, Mark: {p.get('markPrice')}, UPNL: {p.get('unrealizedProfit')}")
    if not active_b:
        print("No active Binance positions.")
except Exception as e:
    print("Binance error:", e)

print("\n=== BITGET POSITIONS ===")
try:
    bitget = ccxt.bitget({
        'apiKey': BITGET_API_KEY,
        'secret': BITGET_SECRET,
        'password': BITGET_PASSPHRASE,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    res = bitget.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES'})
    active_bg = []
    if res and 'data' in res:
        for p in res['data']:
            total = float(p.get('total', 0) or 0)
            if total > 0:
                print(f"Symbol: {p.get('symbol')}, Side: {p.get('holdSide')}, Total: {total}, Entry: {p.get('openPriceAvg')}, Mark: {p.get('markPrice')}, Margin: {p.get('marginSize')}, UPNL: {p.get('unrealizedPL')}")
                active_bg.append(p)
    if not active_bg:
        print("No active Bitget positions.")
except Exception as e:
    print("Bitget error:", e)
