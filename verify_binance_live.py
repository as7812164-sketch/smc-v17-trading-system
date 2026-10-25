import os
import ccxt
from dotenv import load_dotenv

load_dotenv('C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/.env')

key = os.getenv('BINANCE_API_KEY')
secret = os.getenv('BINANCE_API_SECRET')

print("Testing Binance API connection...")
print(f"API Key prefix: {key[:8]}... length: {len(key)}")
print(f"Secret prefix: {secret[:8]}... length: {len(secret)}")

exchange = ccxt.binance({
    'apiKey': key,
    'secret': secret,
    'options': {
        'defaultType': 'future',
        'adjustForTimeDifference': True,
        'recvWindow': 60000
    },
    'enableRateLimit': True,
})

try:
    bal = exchange.fetch_balance()
    usdt = bal.get('USDT', {})
    print("\n>>> [SUCCESS] BINANCE FUTURES CONNECTED! <<<")
    print(f"Total USDT Balance: ${float(usdt.get('total', 0)):.2f}")
    print(f"Free USDT Balance:  ${float(usdt.get('free', 0)):.2f}")
    print(f"Used USDT Balance:  ${float(usdt.get('used', 0)):.2f}")
    
    positions = exchange.fetch_positions()
    active_pos = [p for p in positions if float(p.get('contracts', 0) or 0) > 0]
    print(f"Active Futures Positions: {len(active_pos)}")
    for p in active_pos:
        print(f" - {p.get('symbol')}: {p.get('side')} {p.get('contracts')} contracts @ entry {p.get('entryPrice')}, PnL: ${float(p.get('unrealizedPnl', 0)):.2f}")
except Exception as e:
    print(f"\n[ERROR]: {e}")
