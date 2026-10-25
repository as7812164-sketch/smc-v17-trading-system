import urllib.request
import json

def analyze_symbol(symbol, tf="1h"):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=200"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return

    candles = []
    for r in data:
        candles.append({
            "time": int(r[0]),
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4])
        })

    qual_pct = 0.025 if tf == "4h" else 0.018
    airspace_min = 3.5 if tf == "4h" else 2.5
    disp_mult = 1.4
    avg_period = 10
    origin_lb = 12

    zones = []
    for idx in range(avg_period, len(candles)):
        c = candles[idx]
        bodies = [abs(candles[k]["close"] - candles[k]["open"]) for k in range(idx - avg_period, idx)]
        avg_b = sum(bodies) / len(bodies)
        c_body = abs(c["close"] - c["open"])
        
        is_bull_disp = (avg_b > 0) and (c_body >= disp_mult * avg_b) and (c["close"] > c["open"]) and (c["close"] > candles[idx-1]["high"])
        
        if is_bull_disp:
            origin_offset = -1
            for i in range(1, origin_lb + 1):
                if idx - i >= 0 and candles[idx - i]["close"] < candles[idx - i]["open"]:
                    origin_offset = i
                    break
            if origin_offset != -1:
                o_bar = idx - origin_offset
                if not any(z["origin_bar"] == o_bar for z in zones):
                    o_c = candles[o_bar]
                    target = o_c["high"] * (1.0 + qual_pct)
                    zones.append({
                        "origin_bar": o_bar,
                        "disp_bar": idx,
                        "origin_high": o_c["high"],
                        "origin_low": o_c["low"],
                        "target": target,
                        "status": "PENDING"
                    })

    # Lifecycle simulation
    for bar_idx in range(len(candles)):
        c = candles[bar_idx]
        for z in zones:
            if bar_idx > z["disp_bar"]:
                if z["status"] == "PENDING":
                    if c["low"] <= z["origin_low"]:
                        z["status"] = "INVALIDATED"
                    elif c["high"] >= z["target"]:
                        z["status"] = "QUALIFIED"
                elif z["status"] == "ACTIVE":
                    if c["low"] <= z["origin_low"] * 0.98:
                        z["status"] = "MITIGATED"
                    elif c["high"] >= z["origin_high"] * 1.016:
                        z["status"] = "MITIGATED"
                elif z["status"] == "QUALIFIED":
                    if c["low"] <= z["origin_high"]:
                        z["status"] = "ACTIVE"

    # Last bar extraction
    active_buy = []
    for z in reversed(zones):
        if z["status"] in ["QUALIFIED", "ACTIVE"]:
            active_buy.append(z)
            if len(active_buy) >= 3:
                break

    n_buy = len(active_buy)
    active_buy.sort(key=lambda x: x["origin_high"], reverse=True)
    
    current_p = candles[-1]["close"]
    print(f"=== {symbol} ({tf}) | Current Price: {current_p} ===")
    print(f"Total Zones Created: {len(zones)}, Active/Qualified: {n_buy}")
    for idx, z in enumerate(active_buy):
        print(f"  [{idx}] High={z['origin_high']}, Low={z['origin_low']}, Status={z['status']}")

    if n_buy >= 2:
        top_b = active_buy[0]
        mid_b = active_buy[1]
        airspace = (top_b["origin_low"] - mid_b["origin_high"]) / mid_b["origin_high"] * 100.0
        print(f"  Calculated Airspace: {airspace:.2f}% (Required: {airspace_min}%)")
        print(f"  Mid OB Entry: {mid_b['origin_high']}, Dist from Current: {((current_p - mid_b['origin_high']) / current_p * 100):.2f}%")
    else:
        print("  ❌ NOT ENOUGH ACTIVE ZONES (< 2) -> NO SETUP DISPLAYED ON CHART!")
    print()

for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]:
    analyze_symbol(s, "1h")
    analyze_symbol(s, "4h")
