import ccxt
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BITGET_API_KEY, BITGET_SECRET, BITGET_PASSPHRASE

print("=== BITGET LIVE BALANCE ===")
try:
    bitget = ccxt.bitget({
        'apiKey': BITGET_API_KEY,
        'secret': BITGET_SECRET,
        'password': BITGET_PASSPHRASE,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    bg_bal = bitget.fetch_balance()
    usdt = bg_bal.get('USDT', {})
    print(f"Bitget USDT Free: {usdt.get('free')}, Total: {usdt.get('total')}")
except Exception as e:
    print("Bitget error:", e)

print("\n=== BINANCE LIVE BALANCE ===")
try:
    binance = ccxt.binance({
        'apiKey': BINANCE_API_KEY,
        'secret': BINANCE_API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    acc = binance.fapiPrivateV2GetAccount()
    print(f"Binance Wallet: {acc.get('totalWalletBalance')}, Margin: {acc.get('totalMarginBalance')}, Avail: {acc.get('availableBalance')}")
    pos = binance.fapiPrivateV2GetPositionRisk()
    active = [p for p in pos if abs(float(p.get('positionAmt', 0))) > 0]
    print(f"Active Binance positions: {len(active)}")
    for p in active:
        print(f"  {p.get('symbol')}: Amt {p.get('positionAmt')}, Entry {p.get('entryPrice')}, UPNL {p.get('unrealizedProfit')}")
except Exception as e:
    print("Binance error:", e)
