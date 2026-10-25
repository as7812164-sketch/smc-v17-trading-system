import urllib.request
import json
from datetime import datetime

coins = [("SANDUSDT", "1h"), ("ETCUSDT", "4h"), ("ORDIUSDT", "4h"), ("DOGEUSDT", "4h")]

for sym, interval in coins:
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={interval}&limit=120'
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
        if (c3["close"] < c3["open"]) and (c1["low"] > c3["high"]) and ((impulse_h - c3["low"])/c3["low"] >= min_disp):
            ob_h, ob_l = c3["high"], c3["low"]
            eff_entry = round(ob_h - (ob_h - ob_l)*0.05, 6)
            is_origin = (c3["low"] <= min(candles[k]["low"] for k in range(max(0, i - 25), i + 1)))
            
            # Count how many times it was already tapped before the "fresh" tap
            taps = []
            broken = False
            for t in range(i + 3, n):
                if candles[t]["close"] < ob_l:
                    broken = True
                    break
                if candles[t]["low"] <= eff_entry * 1.0005:
                    taps.append(t)
            
            t_str = datetime.fromtimestamp(c3["time"]/1000).strftime('%Y-%m-%d %H:%M')
            if not broken and taps:
                last_tap_age = (n - 1) - taps[-1]
                print(f"OB at {t_str} (bar #{i}) | Entry: {eff_entry} | Total Taps: {len(taps)} | Last Tap Age: {last_tap_age} bars | is_origin: {is_origin}")
