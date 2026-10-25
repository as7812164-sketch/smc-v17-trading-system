import urllib.request
import json
import datetime
from engine.smc_v17 import analyze_candles_smc_v17

url = 'https://fapi.binance.com/fapi/v1/klines?symbol=AXSUSDT&interval=4h&limit=300'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())

candles = []
for c in data:
    candles.append({
        'time': int(c[0]),
        'dt': datetime.datetime.fromtimestamp(int(c[0])/1000).strftime('%Y-%m-%d %H:%M'),
        'open': float(c[1]),
        'high': float(c[2]),
        'low': float(c[3]),
        'close': float(c[4]),
        'volume': float(c[5])
    })

zones = analyze_candles_smc_v17("AXSUSDT", candles)
print(f"Total zones detected for AXS: {len(zones)}")
for z in zones:
    print(f"Side:{z['side']:<4} | Origin DT:{z.get('origin_dt', z.get('origin_time'))} | H:{z['origin_high']:.4f} L:{z['origin_low']:.4f} | Status:{z['status']} | Active:{z.get('is_active')}")
