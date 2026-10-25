import requests
import datetime

# Check BTC candles
btc_res = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=6", timeout=5).json()
print("=== BTC 1H CANDLES (Last 6 Hours) ===")
for k in btc_res:
    t = datetime.datetime.fromtimestamp(k[0]/1000).strftime('%Y-%m-%d %H:%M')
    print(f"BTC 1H {t}: O={k[1]}, H={k[2]}, L={k[3]}, C={k[4]}")

# Run SMC OB detector on ENAUSDT 1H candles
from engine.smc_core import smc_core
klines_ena = requests.get("https://api.binance.com/api/v3/klines?symbol=ENAUSDT&interval=1h&limit=100", timeout=5).json()
candles = []
for k in klines_ena:
    candles.append({
        'timestamp': k[0],
        'open': float(k[1]),
        'high': float(k[2]),
        'low': float(k[3]),
        'close': float(k[4]),
        'volume': float(k[5])
    })

obs = smc_core.find_order_blocks(candles, timeframe='1h')
print(f"\nTotal Order Blocks found on ENA 1H: {len(obs)}")
for o in obs[-5:]:
    print("OB:", o)
