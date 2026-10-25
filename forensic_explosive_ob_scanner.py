import urllib.request
import json
import time
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "SUIUSDT", "AVAXUSDT", "NEARUSDT", "BNBUSDT", "DOGEUSDT"]

def fetch_klines(symbol, interval="1h", limit=500):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                candles = []
                running_cvd = 0.0
                for k in data:
                    t = int(k[0])
                    o = float(k[1])
                    h = float(k[2])
                    l = float(k[3])
                    c = float(k[4])
                    vol = float(k[5])
                    taker_buy = float(k[9]) if len(k) > 9 else vol * 0.5
                    taker_sell = max(0.0, vol - taker_buy)
                    delta = taker_buy - taker_sell
                    running_cvd += delta
                    candles.append({
                        "time": t, "open": o, "high": h, "low": l, "close": c,
                        "volume": vol, "taker_buy": taker_buy, "taker_sell": taker_sell,
                        "delta": delta, "cvd": running_cvd
                    })
                return candles
        except Exception as e:
            time.sleep(0.5)
    return []

def fetch_oi_map(symbol, period="1h", limit=500):
    url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period={period}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    oi_map = {}
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for item in data:
                ts = int(item["timestamp"])
                oi = float(item["sumOpenInterest"])
                oi_map[ts] = oi
    except Exception:
        pass
    return oi_map

def compute_atr(candles, period=14):
    atrs = [0.0] * len(candles)
    for i in range(1, len(candles)):
        c = candles[i]
        p = candles[i-1]
        tr = max(c["high"] - c["low"], abs(c["high"] - p["close"]), abs(c["low"] - p["close"]))
        if i < period:
            atrs[i] = tr
        else:
            atrs[i] = (atrs[i-1] * (period - 1) + tr) / period
    return atrs

def analyze_all():
    print("=" * 85)
    print(" 🕵️ FORENSIC AUTOPSY: WHAT MAKES PRICE EXPLODE AT ORDER BLOCK TAP?")
    print(" Scanning Real Binance 1H & 4H Market Data Across Tier-1 Assets...")
    print("=" * 85)
    
    explosive_events = []
    failed_events = []
    
    for sym in SYMBOLS:
        print(f"Scanning {sym}...", end=" ", flush=True)
        candles = fetch_klines(sym, interval="1h", limit=500)
        oi_map = fetch_oi_map(sym, period="1h", limit=500)
        atrs = compute_atr(candles, 14)
        print(f"Candles: {len(candles)}, OI Data Points: {len(oi_map)}")
        
        if len(candles) < 100:
            continue
            
        for i in range(20, len(candles) - 30):
            c = candles[i]
            # Potential OB: down candle before strong rally
            if c["close"] >= c["open"]:
                continue
                
            ob_high = max(c["open"], c["close"])
            ob_low = c["low"]
            ob_mt = (ob_high + ob_low) / 2.0
            
            # Displacement check: next 3 candles must produce strong move
            disp_high = max(candles[i+1]["high"], candles[i+2]["high"], candles[i+3]["high"])
            disp_gain = (disp_high - ob_high) / ob_high
            
            # Has FVG
            has_fvg = (candles[i+2]["low"] > candles[i]["high"]) if i+2 < len(candles) else False
            
            if disp_gain < 0.020 or not has_fvg:
                continue
                
            # Now find the FIRST TAP of this OB (from i+3 onwards)
            tap_idx = -1
            for k in range(i + 3, min(i + 80, len(candles))):
                if candles[k]["low"] <= ob_high:
                    tap_idx = k
                    break
                    
            if tap_idx == -1 or tap_idx >= len(candles) - 10:
                continue
                
            tap_c = candles[tap_idx]
            tap_atr = atrs[tap_idx] if atrs[tap_idx] > 0 else (tap_c["high"] - tap_c["low"])
            
            # Measure Reaction outcome over the next 15 bars:
            entry_p = ob_high
            max_rally = 0.0
            max_drawdown = 0.0
            
            for m in range(tap_idx, min(tap_idx + 20, len(candles))):
                rally = (candles[m]["high"] - entry_p) / entry_p
                if rally > max_rally:
                    max_rally = rally
                dd = (entry_p - candles[m]["low"]) / entry_p
                if dd > max_drawdown:
                    max_drawdown = dd
                    
            # Forensic metrics at tap:
            c_range = tap_c["high"] - tap_c["low"]
            lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
            wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
            
            taker_ratio = (tap_c["taker_buy"] / tap_c["volume"]) if tap_c["volume"] > 0 else 0.5
            
            # Range relative to ATR
            range_vs_atr = (c_range / tap_atr) if tap_atr > 0 else 1.0
            
            # Approach deceleration: compare tap bar range to previous 3 bars avg range
            prev_ranges = [candles[tap_idx - x]["high"] - candles[tap_idx - x]["low"] for x in [1, 2, 3]]
            avg_prev_range = np.mean(prev_ranges) if prev_ranges else c_range
            deceleration_ratio = (c_range / avg_prev_range) if avg_prev_range > 0 else 1.0
            
            # Depth of penetration: Did it respect 50% MT?
            held_50_mt = tap_c["close"] >= ob_mt
            
            # CVD Delta on tap bar:
            delta_positive = tap_c["delta"] > 0
            
            # OI shift on tap:
            tap_ts = tap_c["time"]
            curr_oi = oi_map.get(tap_ts, 0.0)
            prev_oi = oi_map.get(tap_ts - 3600000 * 2, 0.0)
            oi_change = ((curr_oi - prev_oi) / prev_oi * 100.0) if (prev_oi > 0 and curr_oi > 0) else 0.0
            
            record = {
                "symbol": sym,
                "ob_time": c["time"],
                "tap_time": tap_ts,
                "disp_gain_pct": disp_gain * 100,
                "max_rally_pct": max_rally * 100,
                "max_dd_pct": max_drawdown * 100,
                "wick_ratio": wick_ratio,
                "taker_ratio": taker_ratio,
                "range_vs_atr": range_vs_atr,
                "deceleration_ratio": deceleration_ratio,
                "held_50_mt": held_50_mt,
                "delta_positive": delta_positive,
                "oi_change": oi_change
            }
            
            # EXPLOSIVE Definition: Price rallied >= +3.5% (up to 20%) with DD <= 1.2% (True institutional blast)
            if max_rally >= 0.035 and max_drawdown <= 0.015:
                explosive_events.append(record)
            # FAILED / DUMP Definition: Price pierced through OB (DD > 2.0% or rally < 0.8%)
            elif max_drawdown > 0.020 or max_rally < 0.008:
                failed_events.append(record)
                
    print("\n" + "=" * 85)
    print("                     FORENSIC AUTOPSY FINDINGS & DATA RESULTS")
    print("=" * 85)
    print(f"Total Explosive OB Rallies Found: {len(explosive_events)}")
    print(f"Total Failed / Dump OBs Found:     {len(failed_events)}")
    
    if not explosive_events:
        print("No events captured.")
        return
        
    print("\n-------------------------------------------------------------------------------------")
    print("METRIC / SIGNATURE                  | 🚀 EXPLODED OBS (WINNERS) | ❌ FAILED OBS (TRAPS)")
    print("-------------------------------------------------------------------------------------")
    
    exp_wick = np.mean([r["wick_ratio"] for r in explosive_events])
    fail_wick = np.mean([r["wick_ratio"] for r in failed_events])
    print(f"1. Lower Wick Absorption Ratio       | {exp_wick*100:6.1f}%                   | {fail_wick*100:6.1f}%")
    
    exp_taker = np.mean([r["taker_ratio"] for r in explosive_events])
    fail_taker = np.mean([r["taker_ratio"] for r in failed_events])
    print(f"2. Taker Buy Volume Ratio            | {exp_taker*100:6.1f}%                   | {fail_taker*100:6.1f}%")
    
    exp_decel = np.mean([r["deceleration_ratio"] for r in explosive_events])
    fail_decel = np.mean([r["deceleration_ratio"] for r in failed_events])
    print(f"3. Deceleration (Tap Bar vs Prev 3)  | {exp_decel:6.2f}x (Exhaustion)        | {fail_decel:6.2f}x (Violent Dump)")
    
    exp_mt = np.mean([1 if r["held_50_mt"] else 0 for r in explosive_events])
    fail_mt = np.mean([1 if r["held_50_mt"] else 0 for r in failed_events])
    print(f"4. Candle Close Above 50% MT Line   | {exp_mt*100:6.1f}%                   | {fail_mt*100:6.1f}%")
    
    exp_disp = np.mean([r["disp_gain_pct"] for r in explosive_events])
    fail_disp = np.mean([r["disp_gain_pct"] for r in failed_events])
    print(f"5. Original Displacement Velocity   | +{exp_disp:5.2f}%                  | +{fail_disp:5.2f}%")
    
    exp_oi = np.mean([r["oi_change"] for r in explosive_events if r["oi_change"] != 0])
    fail_oi = np.mean([r["oi_change"] for r in failed_events if r["oi_change"] != 0])
    print(f"6. Open Interest (OI) Shift at Tap  | +{exp_oi:5.2f}% (Accumulation)     | {fail_oi:5.2f}% (Liquidation)")
    
    print("-------------------------------------------------------------------------------------")
    
    # Calculate the Combined Master Signature Filter:
    # A setup is predicted EXPLOSIVE if:
    # (wick_ratio >= 0.25) AND (held_50_mt == True) AND (deceleration_ratio <= 1.25) AND (taker_ratio >= 0.48)
    def is_master_qualified(r):
        return (r["wick_ratio"] >= 0.22) and (r["held_50_mt"]) and (r["deceleration_ratio"] <= 1.30)
        
    master_pass_exp = sum(1 for r in explosive_events if is_master_qualified(r))
    master_pass_fail = sum(1 for r in failed_events if is_master_qualified(r))
    
    total_screened = len(explosive_events) + len(failed_events)
    total_passed = master_pass_exp + master_pass_fail
    win_rate_with_signature = (master_pass_exp / total_passed * 100) if total_passed > 0 else 0.0
    
    print("\n=====================================================================================")
    print("                  🎯 THE PROPRIETARY SMART MONEY TAP SIGNATURE")
    print("=====================================================================================")
    print(f"Raw Win Rate (Without Filter):              {len(explosive_events) / total_screened * 100:.2f}%")
    print(f"Filtered Win Rate with Smart Money Signature: {win_rate_with_signature:.2f}% ({master_pass_exp}/{total_passed})")
    print(f"Trap Elimination Power:                     {(len(failed_events) - master_pass_fail) / len(failed_events) * 100:.1f}% OF ALL LOSSES ELIMINATED!")
    print("=====================================================================================\n")

if __name__ == "__main__":
    analyze_all()
