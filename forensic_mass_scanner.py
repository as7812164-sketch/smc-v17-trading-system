import urllib.request
import json
import time
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "SUIUSDT", "AVAXUSDT", "NEARUSDT", "DOGEUSDT", "BNBUSDT"]

def fetch_klines(sym, interval="1h", limit=1000):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                candles = []
                for k in data:
                    t, o, h, l, c, vol = int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])
                    tb = float(k[9]) if len(k) > 9 else vol * 0.5
                    ts = max(0.0, vol - tb)
                    candles.append({
                        "time": t, "open": o, "high": h, "low": l, "close": c,
                        "volume": vol, "taker_buy": tb, "taker_sell": ts, "delta": tb - ts
                    })
                return candles
        except Exception:
            time.sleep(0.5)
    return []

def run_forensic():
    print("=" * 80)
    print(" 🚀 MASS FORENSIC SCANNER: 1H & 4H EXPLOSIVE OB AUTOPSY")
    print("=" * 80)
    
    all_explosive = []
    all_normal = []
    all_failed = []
    
    for tf in ["1h", "4h"]:
        print(f"\nScanning Timeframe: {tf.upper()}...")
        for sym in SYMBOLS:
            candles = fetch_klines(sym, interval=tf, limit=1000)
            if len(candles) < 100:
                continue
            
            # Simple rolling ATR
            atrs = [0.0] * len(candles)
            for i in range(1, len(candles)):
                tr = max(candles[i]["high"] - candles[i]["low"],
                         abs(candles[i]["high"] - candles[i-1]["close"]),
                         abs(candles[i]["low"] - candles[i-1]["close"]))
                atrs[i] = (atrs[i-1] * 13 + tr) / 14 if i >= 14 else tr

            # Detect Order Blocks
            for i in range(15, len(candles) - 30):
                c = candles[i]
                if c["close"] >= c["open"]: # Must be a down candle
                    continue
                
                ob_top = max(c["open"], c["close"])
                ob_bot = c["low"]
                ob_mt = (ob_top + ob_bot) / 2.0
                
                # Check for subsequent displacement (next 1-3 bars)
                disp_high = max(candles[i+1]["high"], candles[i+2]["high"], candles[i+3]["high"])
                disp_pct = (disp_high - ob_top) / ob_top
                has_fvg = (candles[i+2]["low"] > candles[i]["high"]) if i+2 < len(candles) else False
                
                if disp_pct < 0.012 or not has_fvg:
                    continue
                
                # First tap of the OB (between i+3 and i+60)
                tap_idx = -1
                for k in range(i+3, min(i+60, len(candles))):
                    if candles[k]["low"] <= ob_top:
                        tap_idx = k
                        break
                
                if tap_idx == -1 or tap_idx >= len(candles) - 15:
                    continue
                
                tap_c = candles[tap_idx]
                atr = atrs[tap_idx] if atrs[tap_idx] > 0 else (tap_c["high"] - tap_c["low"])
                
                # Measure outcome over next 15 bars
                entry_p = ob_top
                max_gain = max((candles[m]["high"] - entry_p) / entry_p for m in range(tap_idx, min(tap_idx+15, len(candles))))
                max_drawdown = max((entry_p - candles[m]["low"]) / entry_p for m in range(tap_idx, min(tap_idx+15, len(candles))))
                
                # Tap metrics:
                c_range = tap_c["high"] - tap_c["low"]
                lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                wick_pct = (lower_wick / c_range * 100) if c_range > 0 else 0
                taker_ratio = (tap_c["taker_buy"] / tap_c["volume"] * 100) if tap_c["volume"] > 0 else 50
                
                # Approach velocity: Tap bar range vs previous 3 bars
                prev_ranges = [candles[tap_idx-x]["high"] - candles[tap_idx-x]["low"] for x in [1, 2, 3]]
                decel = (c_range / np.mean(prev_ranges)) if prev_ranges and np.mean(prev_ranges) > 0 else 1.0
                
                held_mt = tap_c["close"] >= ob_mt
                
                rec = {
                    "symbol": sym, "tf": tf, "time": tap_c["time"],
                    "disp_pct": disp_pct * 100,
                    "max_gain": max_gain * 100,
                    "max_dd": max_drawdown * 100,
                    "wick_pct": wick_pct,
                    "taker_ratio": taker_ratio,
                    "decel": decel,
                    "held_mt": held_mt
                }
                
                if max_gain >= 0.030 and max_drawdown <= 0.012: # True explosive move (>= 3% gain, <= 1.2% DD)
                    all_explosive.append(rec)
                elif max_drawdown > 0.018 or max_gain < 0.010: # Failed / Smashed OB
                    all_failed.append(rec)
                else:
                    all_normal.append(rec)

    print("\n" + "=" * 80)
    print("                    STATISTICAL AUTOPSY RESULTS")
    print("=" * 80)
    print(f"Total Explosive OBs (+3% to +15% instant blast): {len(all_explosive)}")
    print(f"Total Normal/Chop Reactions:                     {len(all_normal)}")
    print(f"Total Failed/Smashed OBs:                        {len(all_failed)}")
    
    if all_explosive:
        print("\n--- FORENSIC COMPARISON TABLE ---")
        print(f"Metric                               | Explosive OBs ({len(all_explosive)}) | Failed OBs ({len(all_failed)})")
        print(f"-------------------------------------+------------------+-----------------")
        print(f"1. Lower Wick Absorption Ratio       | {np.mean([r['wick_pct'] for r in all_explosive]):.1f}%            | {np.mean([r['wick_pct'] for r in all_failed]):.1f}%")
        print(f"2. Deceleration Ratio (Speed check)  | {np.mean([r['decel'] for r in all_explosive]):.2f}x (Exhaustion)| {np.mean([r['decel'] for r in all_failed]):.2f}x (Aggressive Dump)")
        print(f"3. Candle Close Above 50% MT Line    | {np.mean([1 if r['held_mt'] else 0 for r in all_explosive])*100:.1f}%            | {np.mean([1 if r['held_mt'] else 0 for r in all_failed])*100:.1f}%")
        print(f"4. Original Displacement Force       | +{np.mean([r['disp_pct'] for r in all_explosive]):.2f}%           | +{np.mean([r['disp_pct'] for r in all_failed]):.2f}%")
        print(f"5. Taker Buy Volume Ratio            | {np.mean([r['taker_ratio'] for r in all_explosive]):.1f}%            | {np.mean([r['taker_ratio'] for r in all_failed]):.1f}%")
        print("-------------------------------------+------------------+-----------------")
        
        # Test combined signature:
        # Lower wick >= 25% AND decel <= 1.2 AND held_mt == True
        passed_exp = sum(1 for r in all_explosive if r['wick_pct'] >= 25.0 and r['decel'] <= 1.25 and r['held_mt'])
        passed_fail = sum(1 for r in all_failed if r['wick_pct'] >= 25.0 and r['decel'] <= 1.25 and r['held_mt'])
        
        total_p = passed_exp + passed_fail
        precision = (passed_exp / total_p * 100) if total_p > 0 else 0
        
        print("\n🎯 FILTERED RESULTS WITH SMART MONEY TAP SIGNATURE:")
        print(f"  • Qualified Explosive Setups: {passed_exp}")
        print(f"  • Filtered False Traps:       {len(all_failed) - passed_fail} out of {len(all_failed)} traps ELIMINATED! ({((len(all_failed) - passed_fail)/len(all_failed)*100):.1f}%)")
        print(f"  • Filtered Direct Win Rate:   {precision:.2f}%")
        print("=" * 80)

if __name__ == "__main__":
    run_forensic()
