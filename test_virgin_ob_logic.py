import urllib.request
import json
from datetime import datetime

coins = [("GALAUSDT", "1h"), ("SANDUSDT", "1h"), ("ETCUSDT", "4h"), ("ORDIUSDT", "4h"), ("DOGEUSDT", "4h")]

for sym, interval in coins:
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={interval}&limit=200'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req)
    raw = json.loads(resp.read().decode())
    candles = [{"time": int(d[0]), "open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4])} for d in raw]
    n = len(candles)

    min_disp = 0.05
    min_mat = 18 if interval == "1h" else 8

    print(f"\n=================== {sym} ({interval}) ===================")
    for i in range(5, n - 3):
        c3, c2, c1 = candles[i], candles[i+1], candles[i+2]
        impulse_h = max(c1["high"], c2["high"])
        
        is_strict_red = (c3["close"] < c3["open"])
        has_bull_fvg = (c1["low"] > c3["high"])
        bull_gain = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0

        if is_strict_red and has_bull_fvg and bull_gain >= min_disp:
            ob_high, ob_low = c3["high"], c3["low"]
            ob_range = ob_high - ob_low
            eff_entry = round(ob_high - (ob_range * 0.05), 8)
            is_origin = (c3["low"] <= min(candles[k]["low"] for k in range(max(0, i - 25), i + 1)))

            # Track first touch
            first_touch_bar = None
            for t in range(i + 3, n):
                if candles[t]["low"] <= eff_entry * 1.0005:
                    first_touch_bar = t
                    break
            
            t_str = datetime.fromtimestamp(c3["time"]/1000).strftime('%Y-%m-%d %H:%M')
            if first_touch_bar is not None:
                bars_to_first_touch = first_touch_bar - (i + 2)
                age_of_first_touch = (n - 1) - first_touch_bar
                touch_str = datetime.fromtimestamp(candles[first_touch_bar]["time"]/1000).strftime('%Y-%m-%d %H:%M')
                print(f"OB formed at {t_str} (bar #{i}) | is_origin: {is_origin}")
                print(f"  -> FIRST TOUCH at {touch_str} (bar #{first_touch_bar}) | Bars alive: {bars_to_first_touch} (min required: {min_mat}) | Age of tap from now: {age_of_first_touch} bars")
                if bars_to_first_touch < min_mat:
                    print(f"  -> INVALIDATED: Premature mitigation (touched after only {bars_to_first_touch} bars, before maturing {min_mat} bars)!")
                elif age_of_first_touch > 1:
                    print(f"  -> EXPIRED/HISTORICAL: First tap was {age_of_first_touch} bars ago (not a fresh live trigger)!")
                else:
                    print(f"  -> *** VALID FRESH TRIGGER RIGHT NOW ***")
            else:
                print(f"OB formed at {t_str} | is_origin: {is_origin} | UNTOUCHED (ARMED WAITING TAP)")
