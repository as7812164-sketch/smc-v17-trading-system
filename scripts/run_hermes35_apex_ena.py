import sys, os, requests
sys.path.insert(0, os.getcwd())
from engine.hermes3_5_apex import hermes35_engine

# 1H candles
k1h = requests.get('https://api.binance.com/api/v3/klines?symbol=ENAUSDT&interval=1h&limit=100', timeout=5).json()
candles_1h = []
for k in k1h:
    candles_1h.append({
        'timestamp': k[0],
        'open': float(k[1]),
        'high': float(k[2]),
        'low': float(k[3]),
        'close': float(k[4]),
        'volume': float(k[5])
    })

# 4H candles
k4h = requests.get('https://api.binance.com/api/v3/klines?symbol=ENAUSDT&interval=4h&limit=100', timeout=5).json()
candles_4h = []
for k in k4h:
    candles_4h.append({
        'timestamp': k[0],
        'open': float(k[1]),
        'high': float(k[2]),
        'low': float(k[3]),
        'close': float(k[4]),
        'volume': float(k[5])
    })

print("=== 1H ENA SCAN ===")
res1h = hermes35_engine.detect_order_blocks(candles_1h, '1h')
print("1H OBs found:", len(res1h))
for ob in res1h[-3:]:
    print("1H OB:", ob)

print("\n=== 4H ENA SCAN ===")
res4h = hermes35_engine.detect_order_blocks(candles_4h, '4h')
print("4H OBs found:", len(res4h))
for ob in res4h[-3:]:
    print("4H OB:", ob)
