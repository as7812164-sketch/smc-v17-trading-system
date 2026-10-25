import urllib.request
import json
import sys
from datetime import datetime

# Set utf-8 stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22 = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT",
    "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "NEARUSDT",
    "SUIUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
    "TIAUSDT", "SEIUSDT", "FETUSDT", "RENDERUSDT", "GALAUSDT",
    "SANDUSDT", "ORDIUSDT"
]

print("=== AUDITING TOP 22 COINS WITH VIRGIN OB + ORIGIN BEDROCK ===")

for tf in ["1h", "4h"]:
    min_mat = 18 if tf == "1h" else 8
    print(f"\n---------------- TIMEFRAME: {tf.upper()} (Min Maturation: {min_mat} bars) ----------------")
    
    fresh_triggers = []
    armed_waiting = []
    
    for sym in TOP_22:
        try:
            url = f'https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={tf}&limit=200'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=5)
            raw = json.loads(resp.read().decode())
            candles = [{"time": int(d[0]), "open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4])} for d in raw]
            n = len(candles)
            if n < 40:
                continue

            for i in range(max(5, n - 200), n - 3):
                c3, c2, c1 = candles[i], candles[i+1], candles[i+2]
                impulse_h = max(c1["high"], c2["high"])
                impulse_l = min(c1["low"], c2["low"])

                # Bullish
                if (c3["close"] < c3["open"]) and (c1["low"] > c3["high"]) and ((impulse_h - c3["low"])/c3["low"] >= 0.05):
                    ob_high, ob_low = c3["high"], c3["low"]
                    ob_range = ob_high - ob_low
                    eff_entry = round(ob_high - (ob_range * 0.05), 8)
                    mt = (ob_high + ob_low) / 2.0
                    
                    # Origin Bedrock
                    is_origin = (c3["low"] <= min(candles[k]["low"] for k in range(max(0, i - 25), i + 1)))
                    if not is_origin:
                        continue # MUST BE ORIGIN BEDROCK!

                    peak_runway = max(candles[k]["high"] for k in range(i + 1, min(i + 25, n)))
                    runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0
                    if runway_pct < 5.0:
                        continue

                    idm_low = min(candles[k]["low"] for k in range(max(0, i - 3), min(i + 4, n)))
                    broken = False
                    first_tap_bar = None
                    first_tap_wick = 0.0

                    for t in range(i + 3, n):
                        curr_c = candles[t]
                        if curr_c["close"] < ob_low:
                            broken = True
                            break
                        
                        if curr_c["low"] <= eff_entry * 1.0005:
                            bars_alive = t - (i + 2)
                            if bars_alive < min_mat:
                                broken = True # Premature touch!
                                break
                            
                            idm_swept = any(candles[k]["low"] < idm_low for k in range(i + 3, t + 1)) or (curr_c["low"] < idm_low)
                            c_range = curr_c["high"] - curr_c["low"]
                            l_wick = min(curr_c["open"], curr_c["close"]) - curr_c["low"]
                            w_ratio = (l_wick / c_range) if c_range > 0 else 0.0

                            if w_ratio >= 0.18 and curr_c["close"] >= mt and idm_swept and curr_c["low"] >= ob_low * 0.972:
                                first_tap_bar = t
                                first_tap_wick = w_ratio
                            else:
                                broken = True
                            break # ONLY FIRST TOUCH!

                    if not broken:
                        t_ob_str = datetime.fromtimestamp(c3["time"]/1000).strftime('%Y-%m-%d %H:%M')
                        if first_tap_bar is not None:
                            age = (n - 1) - first_tap_bar
                            t_tap_str = datetime.fromtimestamp(candles[first_tap_bar]["time"]/1000).strftime('%Y-%m-%d %H:%M')
                            if age <= 1:
                                fresh_triggers.append(f"{sym} [LONG] Entry: {eff_entry} | OB: {t_ob_str} | Tap: {t_tap_str} (age {age}b) | Wick: {first_tap_wick*100:.1f}%")
                        else:
                            cur_p = candles[-1]["close"]
                            dist_pct = (cur_p - eff_entry) / eff_entry * 100.0
                            armed_waiting.append(f"{sym} [LONG] Entry: {eff_entry} | OB: {t_ob_str} | Current: {cur_p} (dist: +{dist_pct:.2f}%)")

                # Bearish
                if (c3["close"] > c3["open"]) and (c1["high"] < c3["low"]) and ((c3["high"] - impulse_l)/c3["high"] >= 0.05):
                    ob_high, ob_low = c3["high"], c3["low"]
                    ob_range = ob_high - ob_low
                    eff_entry = round(ob_low + (ob_range * 0.05), 8)
                    mt = (ob_high + ob_low) / 2.0
                    
                    # Origin Bedrock
                    is_origin = (c3["high"] >= max(candles[k]["high"] for k in range(max(0, i - 25), i + 1)))
                    if not is_origin:
                        continue # MUST BE ORIGIN BEDROCK!

                    peak_runway = min(candles[k]["low"] for k in range(i + 1, min(i + 25, n)))
                    runway_pct = ((ob_low - peak_runway) / ob_low * 100.0) if ob_low > 0 else 0.0
                    if runway_pct < 5.0:
                        continue

                    idm_high = max(candles[k]["high"] for k in range(max(0, i - 3), min(i + 4, n)))
                    broken = False
                    first_tap_bar = None
                    first_tap_wick = 0.0

                    for t in range(i + 3, n):
                        curr_c = candles[t]
                        if curr_c["close"] > ob_high:
                            broken = True
                            break
                        
                        if curr_c["high"] >= eff_entry * 0.9995:
                            bars_alive = t - (i + 2)
                            if bars_alive < min_mat:
                                broken = True # Premature touch!
                                break
                            
                            idm_swept = any(candles[k]["high"] > idm_high for k in range(i + 3, t + 1)) or (curr_c["high"] > idm_high)
                            c_range = curr_c["high"] - curr_c["low"]
                            u_wick = curr_c["high"] - max(curr_c["open"], curr_c["close"])
                            w_ratio = (u_wick / c_range) if c_range > 0 else 0.0

                            if w_ratio >= 0.18 and curr_c["close"] <= mt and idm_swept and curr_c["high"] <= ob_high * 1.028:
                                first_tap_bar = t
                                first_tap_wick = w_ratio
                            else:
                                broken = True
                            break # ONLY FIRST TOUCH!

                    if not broken:
                        t_ob_str = datetime.fromtimestamp(c3["time"]/1000).strftime('%Y-%m-%d %H:%M')
                        if first_tap_bar is not None:
                            age = (n - 1) - first_tap_bar
                            t_tap_str = datetime.fromtimestamp(candles[first_tap_bar]["time"]/1000).strftime('%Y-%m-%d %H:%M')
                            if age <= 1:
                                fresh_triggers.append(f"{sym} [SHORT] Entry: {eff_entry} | OB: {t_ob_str} | Tap: {t_tap_str} (age {age}b) | Wick: {first_tap_wick*100:.1f}%")
                        else:
                            cur_p = candles[-1]["close"]
                            dist_pct = (eff_entry - cur_p) / cur_p * 100.0
                            armed_waiting.append(f"{sym} [SHORT] Entry: {eff_entry} | OB: {t_ob_str} | Current: {cur_p} (dist: +{dist_pct:.2f}%)")

        except Exception as e:
            print(f"Error {sym}: {e}")

    print(f"FRESH TRIGGERS ({len(fresh_triggers)}):")
    for ft in fresh_triggers:
        print(f"  [TRIGGER] {ft}")
    print(f"ARMED WAITING ZONES ({len(armed_waiting)}):")
    for aw in armed_waiting[:10]:
        print(f"  [ARMED] {aw}")
