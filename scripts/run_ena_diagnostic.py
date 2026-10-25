import sys, os, requests
sys.path.insert(0, os.getcwd())
from engine.smc_core import smc_core

klines_ena = requests.get('https://api.binance.com/api/v3/klines?symbol=ENAUSDT&interval=1h&limit=100', timeout=5).json()
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
print('Total ENA 1H OBs:', len(obs))
for o in obs[-6:]:
    ot = o.get('type')
    oh = o.get('high')
    ol = o.get('low')
    omt = o.get('mt')
    omit = o.get('mitigated')
    print(f"OB: Type={ot}, High={oh}, Low={ol}, MT={omt}, Mitigated={omit}")
