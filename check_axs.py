import urllib.request
import json
import datetime

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
        'vol': float(c[5])
    })

print(f"Total AXS candles: {len(candles)}")
for i, c in enumerate(candles):
    if '2026-08-18' <= c['dt'][:10] <= '2026-08-22':
        body = abs(c['close'] - c['open'])
        prev_bodies = [abs(candles[k]['close'] - candles[k]['open']) for k in range(max(0, i-10), i)]
        avg_b = sum(prev_bodies)/len(prev_bodies) if prev_bodies else 0.01
        is_disp = body >= (1.5 * avg_b)
        print(f"{c['dt']} | O:{c['open']:.4f} H:{c['high']:.4f} L:{c['low']:.4f} C:{c['close']:.4f} | Body:{body:.4f} Avg:{avg_b:.4f} Disp:{is_disp}")
