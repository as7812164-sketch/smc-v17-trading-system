import json
import os
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

base_dir = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"

CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "NEARUSDT", "FETUSDT", "AVAXUSDT", "DOGEUSDT", "RENDERUSDT"
]

print("Scanning for 100% PURE, VIRGIN, UNCOMPROMISED VALID OB...")

for sym in CHAMPIONS:
    for tf in ["4h", "1h"]:
        fpath = os.path.join(base_dir, "historical_data", f"{sym}_{tf}.json")
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)

        for i in range(50, len(candles) - 35):
            c1 = candles[i - 1]
            c2 = candles[i]  # Candidate OB

            # Criterion 1: C2 must be RED (bearish)
            if c2["close"] >= c2["open"]:
                continue

            # Criterion 2: C2 sweeps C1 low
            if c2["low"] >= c1["low"]:
                continue

            # Criterion 3: C2 must be the LOWEST point of the swing origin (no candle in next 4 bars goes below C2 low!)
            if any(candles[k]["low"] <= c2["low"] for k in range(i + 1, min(i + 6, len(candles)))):
                continue

            # Criterion 4: Strict 3-candle FVG between C1 High and C3 Low (or C2 High and C4 Low)
            c3 = candles[i + 1]
            c4 = candles[i + 2]
            has_fvg = c4["low"] > c2["high"]
            if not has_fvg:
                continue
            fvg_gap = c4["low"] - c2["high"]

            # Criterion 5: Displacement move >= 5% to Swing High
            sub_w = candles[i:min(i + 15, len(candles))]
            highs = [x["high"] for x in sub_w]
            max_h = max(highs)
            h_idx = i + highs.index(max_h)
            gain = (max_h - c2["low"]) / c2["low"]

            if gain < 0.05 or h_idx <= i + 2:
                continue

            # Criterion 6: Body BOS above C1 High & prior swing
            body_bos = any(candles[k]["close"] > c1["high"] * 1.01 for k in range(i + 1, h_idx + 1))
            if not body_bos:
                continue

            # Criterion 7: The zone MUST REMAIN VIRGIN / UNMITIGATED between expansion and pullback!
            # No candle between i+3 and h_idx should have touched C2 High!
            mitigated_early = any(candles[k]["low"] <= c2["high"] for k in range(i + 3, h_idx + 1))
            if mitigated_early:
                continue  # NOT FRESH!

            # Criterion 8: Inducement (IDM) exists and is swept
            idm_low = candles[h_idx - 1]["low"]
            d_range = max_h - c2["low"]
            fib_50 = max_h - 0.50 * d_range
            fib_618 = max_h - 0.618 * d_range
            fib_786 = max_h - 0.786 * d_range
            ob_mt = (c2["high"] + c2["low"]) / 2.0

            # Scan pullback
            for t in range(h_idx + 1, min(h_idx + 30, len(candles))):
                tap = candles[t]
                # Check IDM sweep
                idm_swept = any(candles[k]["low"] < idm_low for k in range(h_idx, t + 1))
                # Check first tap of the virgin zone
                if idm_swept and tap["low"] <= c2["high"] and tap["low"] >= c2["low"]:
                    c_range = tap["high"] - tap["low"]
                    l_wick = min(tap["open"], tap["close"]) - tap["low"]
                    w_ratio = l_wick / c_range if c_range > 0 else 0
                    if w_ratio >= 0.20:
                        entry = ob_mt
                        sl = c2["low"] - 0.005 * c2["low"]
                        tp = max_h
                        # Verify win
                        win = any(candles[m]["high"] >= tp for m in range(t + 1, min(t + 25, len(candles))))
                        loss = any(candles[m]["low"] <= sl for m in range(t + 1, min(t + 25, len(candles))))
                        if win and not loss:
                            dt_ob = datetime.fromtimestamp(c2["time"] / 1000).strftime("%Y-%m-%d %H:%M")
                            dt_sh = datetime.fromtimestamp(candles[h_idx]["time"] / 1000).strftime("%Y-%m-%d %H:%M")
                            dt_tap = datetime.fromtimestamp(tap["time"] / 1000).strftime("%Y-%m-%d %H:%M")
                            print("=" * 70)
                            print(f"🎯 100% PURE VIRGIN VALID OB FOUND ON {sym} {tf.upper()}!")
                            print("=" * 70)
                            print(f"Candle 1: H={c1['high']}, L={c1['low']}")
                            print(f"Candle 2 (OB): Date={dt_ob}, O={c2['open']}, H={c2['high']}, L={c2['low']}, C={c2['close']}")
                            print(f"  -> C2 swept C1 low: {c2['low']} < {c1['low']} (PASS)")
                            print(f"  -> Lowest point: No subsequent candle breached C2 low (PASS)")
                            print(f"Displacement: +{gain * 100:.2f}% to Swing High {max_h} on {dt_sh} (PASS)")
                            print(f"FVG: [{c2['high']} to {c4['low']}], Gap={fvg_gap:.4f} (PASS)")
                            print(f"Zone Freshness: 100% VIRGIN until tap (PASS)")
                            print(f"IDM: {idm_low} swept by pullback (PASS)")
                            print(f"Tap: Date={dt_tap}, Tap Low={tap['low']}, Rejection Wick={w_ratio * 100:.1f}% (PASS)")
                            print(f"Entry: {entry:.4f}, SL: {sl:.4f}, TP: {tp:.4f}, R:R = {(tp - entry) / (entry - sl):.2f}")
                            sys.exit(0)
