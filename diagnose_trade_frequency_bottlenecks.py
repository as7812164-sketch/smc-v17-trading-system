"""
DIAGNOSE TRADE FREQUENCY BOTTLENECKS
Measures how many trades are filtered by each condition across 1-year data.
"""
import os
import json

DATA_DIR = "historical_data"
files = [f for f in os.listdir(DATA_DIR) if f.endswith("_1h.json") and not "1y_audit" in f]
coins = [f.replace("_1h.json", "") for f in files]

print(f"Analyzing {len(coins)} Coins on 1H and 4H to identify why frequency is choking...")

# Load BTC 4H EMA50
with open(os.path.join(DATA_DIR, "BTCUSDT_4h.json")) as f:
    btc_4h = json.load(f)
btc_closes = [float(c["close"]) for c in btc_4h]
k = 2.0 / 51.0
ema = [btc_closes[0]]
for p in btc_closes[1:]:
    ema.append(p * k + ema[-1] * (1.0 - k))
btc_map = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= ema[i]) for i in range(len(btc_4h))}
btc_times = sorted(btc_map.keys())

def get_btc_bull(t_ms):
    ans = True
    for t in btc_times:
        if t <= t_ms: ans = btc_map[t]
        else: break
    return ans

# Counters
counts = {
    "1. Raw OB + FVG": 0,
    "2. Displacement >= 5%": 0,
    "3. Runway Void >= 5%": 0,
    "4. Maturation >= 48b (1H) / 12b (4H)": 0,
    "5. 18% Rejection Wick Gate": 0,
    "6. King BTC Filter Passed": 0,
    "7. Final Qualified (Surviving All)": 0
}

# Test on a representative basket of 15 coins across 1H
sample_coins = coins[:15]
for sym in sample_coins:
    p_1h = os.path.join(DATA_DIR, f"{sym}_1h.json")
    if not os.path.exists(p_1h): continue
    with open(p_1h) as f:
        candles = json.load(f)
    n = len(candles)
    if n < 100: continue

    for i in range(25, n - 10):
        c3 = candles[i]
        c2 = candles[i+1]
        c1 = candles[i+2]

        if c3["close"] < c3["open"] and c1["low"] > c3["high"]:
            counts["1. Raw OB + FVG"] += 1
            gain = (max(c2["high"], c1["high"]) - c3["low"]) / c3["low"]
            if gain >= 0.050:
                counts["2. Displacement >= 5%"] += 1
                ob_high = c3["high"]
                ob_low = c3["low"]
                ob_range = ob_high - ob_low
                mt = (ob_high + ob_low) / 2.0
                peak_runway = max(candles[k]["high"] for k in range(i+1, min(i+25, n)))
                runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0
                if runway_pct >= 5.0:
                    counts["3. Runway Void >= 5%"] += 1
                    
                    eff_entry = ob_high - 0.05 * ob_range
                    # check tap
                    tap_found = False
                    tap_wick_ok = False
                    tap_time = None
                    for t in range(i+3, min(i+720, n)):
                        curr_c = candles[t]
                        if curr_c["close"] < ob_low: break
                        bars_alive = t - (i+2)
                        if bars_alive >= 48:
                            if curr_c["low"] <= eff_entry * 1.0005 and curr_c["close"] >= ob_low:
                                tap_found = True
                                c_range = curr_c["high"] - curr_c["low"]
                                l_wick = min(curr_c["open"], curr_c["close"]) - curr_c["low"]
                                w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                if w_ratio >= 0.18 and curr_c["close"] >= mt:
                                    tap_wick_ok = True
                                    tap_time = curr_c["time"]
                                    break
                    if tap_found:
                        counts["4. Maturation >= 48b (1H) / 12b (4H)"] += 1
                        if tap_wick_ok:
                            counts["5. 18% Rejection Wick Gate"] += 1
                            if get_btc_bull(tap_time):
                                counts["6. King BTC Filter Passed"] += 1
                                counts["7. Final Qualified (Surviving All)"] += 1

print("\n--- BOTTLENECK ANALYSIS ON 1H (Sample 15 Coins) ---")
for k, v in counts.items():
    print(f"  {k:<40}: {v:>6} setups")
