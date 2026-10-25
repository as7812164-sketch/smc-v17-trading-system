import urllib.request
import json
import sys
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22 = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT",
    "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "NEARUSDT",
    "SUIUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
    "TIAUSDT", "SEIUSDT", "FETUSDT", "RENDERUSDT", "GALAUSDT",
    "SANDUSDT", "ORDIUSDT"
]

all_candidates = []

for tf in ["1h", "4h"]:
    min_mat = 18 if tf == "1h" else 8
    for sym in TOP_22:
        try:
            url = f'https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={tf}&limit=200'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=4)
            raw = json.loads(resp.read().decode())
            candles = [{"time": int(d[0]), "open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4])} for d in raw]
            n = len(candles)
            if n < 40: continue

            cur_p = candles[-1]["close"]

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
                    
                    is_origin = (c3["low"] <= min(candles[k]["low"] for k in range(max(0, i - 25), i + 1)))
                    if not is_origin: continue

                    peak_runway = max(candles[k]["high"] for k in range(i + 1, min(i + 25, n)))
                    runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0
                    if runway_pct < 5.0: continue

                    idm_low = min(candles[k]["low"] for k in range(max(0, i - 3), min(i + 4, n)))
                    broken = False
                    first_tap = False

                    for t in range(i + 3, n):
                        curr_c = candles[t]
                        if curr_c["close"] < ob_low:
                            broken = True; break
                        if curr_c["low"] <= eff_entry * 1.0005:
                            bars_alive = t - (i + 2)
                            if bars_alive < min_mat:
                                broken = True; break
                            first_tap = True
                            break

                    if not broken and not first_tap:
                        dist = (cur_p - eff_entry) / eff_entry * 100.0
                        all_candidates.append({
                            "symbol": sym, "tf": tf, "side": "LONG",
                            "cur_p": cur_p, "entry": eff_entry, "dist": dist,
                            "ob_h": ob_high, "ob_l": ob_low, "mt": mt,
                            "tp": round(eff_entry * 1.028, 6),
                            "sl": round(eff_entry * 0.972, 6),
                            "disp": round((impulse_h - c3["low"])/c3["low"] * 100, 1),
                            "airspace": round(runway_pct, 1),
                            "age": (n - 1) - (i + 2)
                        })

                # Bearish
                if (c3["close"] > c3["open"]) and (c1["high"] < c3["low"]) and ((c3["high"] - impulse_l)/c3["high"] >= 0.05):
                    ob_high, ob_low = c3["high"], c3["low"]
                    ob_range = ob_high - ob_low
                    eff_entry = round(ob_low + (ob_range * 0.05), 8)
                    mt = (ob_high + ob_low) / 2.0
                    
                    is_origin = (c3["high"] >= max(candles[k]["high"] for k in range(max(0, i - 25), i + 1)))
                    if not is_origin: continue

                    peak_runway = min(candles[k]["low"] for k in range(i + 1, min(i + 25, n)))
                    runway_pct = ((ob_low - peak_runway) / ob_low * 100.0) if ob_low > 0 else 0.0
                    if runway_pct < 5.0: continue

                    broken = False
                    first_tap = False

                    for t in range(i + 3, n):
                        curr_c = candles[t]
                        if curr_c["close"] > ob_high:
                            broken = True; break
                        if curr_c["high"] >= eff_entry * 0.9995:
                            bars_alive = t - (i + 2)
                            if bars_alive < min_mat:
                                broken = True; break
                            first_tap = True
                            break

                    if not broken and not first_tap:
                        dist = (eff_entry - cur_p) / cur_p * 100.0
                        all_candidates.append({
                            "symbol": sym, "tf": tf, "side": "SHORT",
                            "cur_p": cur_p, "entry": eff_entry, "dist": dist,
                            "ob_h": ob_high, "ob_l": ob_low, "mt": mt,
                            "tp": round(eff_entry * 0.972, 6),
                            "sl": round(eff_entry * 1.028, 6),
                            "disp": round((c3["high"] - impulse_l)/c3["high"] * 100, 1),
                            "airspace": round(runway_pct, 1),
                            "age": (n - 1) - (i + 2)
                        })

        except Exception as e:
            pass

# Sort by distance
all_candidates.sort(key=lambda x: abs(x['dist']))
print(f"Total Untouched Origin Bedrock Setups Found: {len(all_candidates)}")
for c in all_candidates[:8]:
    print(f"[{c['tf'].upper()}] {c['symbol']} {c['side']} | Cur: {c['cur_p']} | Entry: {c['entry']} | Dist: {c['dist']:+.2f}% | OB: [{c['ob_l']} - {c['ob_h']}] | TP: {c['tp']} | SL: {c['sl']} | Disp: +{c['disp']}% | Airspace: +{c['airspace']}% | Age: {c['age']}b")
