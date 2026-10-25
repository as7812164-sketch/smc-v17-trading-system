import sys
sys.path.append('C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system')
import ccxt
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BITGET_API_KEY, BITGET_SECRET, BITGET_PASSPHRASE

print("=== CHECKING BINANCE FUTURES BALANCE ===")
try:
    binance = ccxt.binance({
        'apiKey': BINANCE_API_KEY,
        'secret': BINANCE_API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    b_bal = binance.fapiPrivateV2GetAccount()
    usdt = [a for a in b_bal.get('assets', []) if a.get('asset') == 'USDT']
    if usdt:
        u = usdt[0]
        print(f"Binance USDT: Wallet={u.get('walletBalance')}, Available={u.get('availableBalance')}, Margin={u.get('marginBalance')}")
    else:
        print("No USDT found on Binance Futures.")
except Exception as e:
    print(f"Binance error: {e}")

print("\n=== CHECKING BITGET FUTURES BALANCE ===")
try:
    bitget = ccxt.bitget({
        'apiKey': BITGET_API_KEY,
        'secret': BITGET_SECRET,
        'password': BITGET_PASSPHRASE,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    bg_bal = bitget.privateMixGetV2AccountAccounts({'productType': 'USDT-FUTURES'})
    for a in bg_bal.get('data', []):
        print(f"Bitget: Coin={a.get('marginCoin')}, Equity={a.get('equity')}, Available={a.get('available')}, Locked={a.get('locked')}")
except Exception as e:
    print(f"Bitget error: {e}")
