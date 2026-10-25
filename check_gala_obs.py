import urllib.request
import json
from datetime import datetime

url = 'https://fapi.binance.com/fapi/v1/klines?symbol=GALAUSDT&interval=1h&limit=200'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req)
raw = json.loads(resp.read().decode())

candles = []
for d in raw:
    candles.append({
        "time": int(d[0]),
        "open": float(d[1]),
        "high": float(d[2]),
        "low": float(d[3]),
        "close": float(d[4]),
        "volume": float(d[5]),
    })

n = len(candles)
print(f"Total 1H candles: {n}")
print(f"First candle: {datetime.fromtimestamp(candles[0]['time']/1000)} | Last candle: {datetime.fromtimestamp(candles[-1]['time']/1000)}")

# Run detection exactly as hermes35_live.py does
min_displacement = 0.050
min_runway_pct = 5.0
min_maturation_bars = 18

for i in range(5, n - 3):
    c3 = candles[i]
    c2 = candles[i+1]
    c1 = candles[i+2]

    impulse_h = max(c1["high"], c2["high"])
    impulse_l = min(c1["low"], c2["low"])

    is_strict_red = (c3["close"] < c3["open"])
    has_bull_fvg = (c1["low"] > c3["high"])
    bull_gain = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0

    if is_strict_red and has_bull_fvg and bull_gain >= min_displacement:
        ob_high = c3["high"]
        ob_low = c3["low"]
        ob_range = ob_high - ob_low
        eff_entry = round(ob_high - (ob_range * 0.05), 8)
        
        is_origin = (c3["low"] <= min(candles[k]["low"] for k in range(max(0, i - 25), i + 1)))
        peak_runway = max(candles[k]["high"] for k in range(i + 1, min(i + 25, n)))
        runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0

        t_str = datetime.fromtimestamp(c3["time"]/1000).strftime('%Y-%m-%d %H:%M')
        print(f"\n[FOUND OB] Time: {t_str} (bar #{i}) | High: {ob_high:.6f} | Low: {ob_low:.6f} | 5% Entry: {eff_entry:.6f} | Disp: {bull_gain*100:.2f}% | Runway: {runway_pct:.2f}% | is_origin: {is_origin}")

        # Check tap
        for t in range(i + 3, n):
            curr_c = candles[t]
            bars_alive = t - (i + 2)
            if curr_c["close"] < ob_low:
                print(f"  -> BROKEN at bar {t} ({datetime.fromtimestamp(curr_c['time']/1000)})")
                break
            if curr_c["low"] <= eff_entry * 1.0005:
                t_tap_str = datetime.fromtimestamp(curr_c["time"]/1000).strftime('%Y-%m-%d %H:%M')
                age = (n - 1) - t
                print(f"  -> TAPPED at bar {t} ({t_tap_str}) | Low: {curr_c['low']:.6f} | Age from now: {age} bars | Alive: {bars_alive}b")
