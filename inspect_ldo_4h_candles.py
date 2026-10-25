import urllib.request
import json
from datetime import datetime

url = 'https://fapi.binance.com/fapi/v1/klines?symbol=LDOUSDT&interval=4h&limit=200'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req)
raw = json.loads(resp.read().decode())
candles = [{"time": int(d[0]), "open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4]), "vol": float(d[5])} for d in raw]
n = len(candles)

print(f"Total 4H candles: {n}")
print(f"Current candle: {datetime.fromtimestamp(candles[-1]['time']/1000)} | Close: {candles[-1]['close']}")

# Check all OBs with basic rules: red candle c3, c1['low'] > c3['high'] (bull FVG), displacement >= 5.0%
print("\n--- ALL QUALIFYING BULLISH OBs ON LDO 4H ---")
for i in range(5, n - 3):
    c3, c2, c1 = candles[i], candles[i+1], candles[i+2]
    impulse_h = max(c1["high"], c2["high"])
    impulse_l = min(c1["low"], c2["low"])

    is_strict_red = (c3["close"] < c3["open"])
    has_bull_fvg = (c1["low"] > c3["high"])
    bull_gain = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0

    if is_strict_red and has_bull_fvg and bull_gain >= 0.05:
        ob_high, ob_low = c3["high"], c3["low"]
        ob_range = ob_high - ob_low
        eff_entry = round(ob_high - (ob_range * 0.05), 6)
        mt = (ob_high + ob_low) / 2.0
        
        # Origin check with 25 bars lookback
        prior_low_25 = min(candles[k]["low"] for k in range(max(0, i - 25), i + 1))
        is_origin_25 = (c3["low"] <= prior_low_25)

        # Origin check with 20 bars lookback (Pine Script: ta.lowest(low, 20)[3])
        prior_low_20 = min(candles[k]["low"] for k in range(max(0, i - 20), i + 1))
        is_origin_20 = (c3["low"] <= prior_low_20)

        # Runway
        peak_runway = max(candles[k]["high"] for k in range(i + 1, min(i + 25, n)))
        runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0

        t_ob = datetime.fromtimestamp(c3["time"]/1000).strftime('%Y-%m-%d %H:%M')
        age_ob = (n - 1) - (i + 2)

        # Check touches
        taps = []
        broken = False
        for t in range(i + 3, n):
            if candles[t]["close"] < ob_low:
                broken = True
                break
            if candles[t]["low"] <= eff_entry * 1.0005:
                taps.append(t)

        print(f"OB at {t_ob} (bar #{i}, age {age_ob}b)")
        print(f"  Range: [{ob_low:.4f} - {ob_high:.4f}] | 5% Entry: {eff_entry:.4f} | Disp: +{bull_gain*100:.1f}% | Airspace: +{runway_pct:.1f}%")
        print(f"  is_origin_25: {is_origin_25} (prior 25 min: {prior_low_25:.4f}) | is_origin_20: {is_origin_20} (prior 20 min: {prior_low_20:.4f})")
        print(f"  Broken: {broken} | Total Taps: {len(taps)}")
        if taps:
            first_t = taps[0]
            t_tap = datetime.fromtimestamp(candles[first_t]["time"]/1000).strftime('%Y-%m-%d %H:%M')
            alive_at_tap = first_t - (i + 2)
            age_from_now = (n - 1) - first_t
            print(f"  First Tap at {t_tap} (bar #{first_t}, alive {alive_at_tap}b, age from now {age_from_now}b)")
        print()
