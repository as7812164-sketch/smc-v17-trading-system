import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

APPROVED_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "APTUSDT",
    "ARBUSDT", "OPUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", "RUNEUSDT", "RENDERUSDT",
    "INJUSDT", "FETUSDT", "THETAUSDT", "ALGOUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT", "ICPUSDT",
    "PYTHUSDT", "PEPEUSDT", "SHIBUSDT", "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOGEUSDT"
]

def fetch_klines(sym, interval, limit=1200):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                candles = []
                for k in data:
                    candles.append({
                        "time": int(k[0]), "open": float(k[1]), "high": float(k[2]),
                        "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])
                    })
                return sym, interval, candles
        except Exception:
            time.sleep(0.2)
    return sym, interval, []

def analyze_multiple_obs():
    print("=" * 90)
    print(" 🔬 EXPERIMENT: MULTIPLE OBs ON CHART (EXTREME vs DECISIONAL vs INDUCEMENT)")
    print(" Testing 3-Month Binance 1H & 4H Data Across 31 Approved Coins...")
    print(" Target: Quick +2.0% to +2.5% Take Profit | Dynamic Stop Loss Optimization")
    print("=" * 90)

    tasks = []
    for s in APPROVED_COINS:
        tasks.append((s, "4h", 600))
        tasks.append((s, "1h", 1500))

    all_data = {"4h": {}, "1h": {}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_klines, t[0], t[1], t[2]) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            sym, tf, klines = f.result()
            if len(klines) >= 100:
                all_data[tf][sym] = klines

    print(f"Loaded {len(all_data['1h'])} pairs for 1H and {len(all_data['4h'])} pairs for 4H.\n")

    # We evaluate 3 distinct OB Types when an impulse wave occurs:
    # 1. EXTREME OB: The Origin of the move (Lowest Low of 20 bars before explosive rally)
    # 2. DECISIONAL OB: Mid-leg consolidation base where BOS occurred (Equilibrium 40-60% zone)
    # 3. INDUCEMENT / SHALLOW OB: The upper minor base created right before the final push high

    ob_types = ["EXTREME", "DECISIONAL", "SHALLOW_INDUCEMENT"]
    
    # Store trades per type
    results_by_type = {t: {"1h": [], "4h": []} for t in ob_types}

    for tf in ["1h", "4h"]:
        tp_target_pct = 0.022 if tf == "1h" else 0.025 # 2.2% on 1H (11% ROE), 2.5% on 4H (12.5% ROE)
        sl_pct = 0.025 # 2.5% move (12.5% ROE at 5x)
        
        for sym, candles in all_data[tf].items():
            n = len(candles)
            
            # Scan for impulse moves of >= 5.0% over 8 to 15 bars
            for i in range(25, n - 35):
                # Origin swing low
                swing_low_idx = i
                swing_low = candles[i]["low"]
                
                # Check if it's a local minimum of at least 15 bars
                if swing_low != min(c["low"] for c in candles[i-15:i+1]):
                    continue
                    
                # Find swing high in the next 6-15 bars
                window = candles[i:min(i+16, n)]
                highs = [c["high"] for c in window]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                
                if high_idx <= i + 3: continue
                
                total_expansion = (max_high - swing_low) / swing_low
                if total_expansion < 0.045: # Must be a genuine expansion wave (>= 4.5%)
                    continue
                    
                # Now classify the 3 candidate OBs in this swing leg:
                # 1. Extreme OB: The candle at swing_low_idx
                ext_c = candles[swing_low_idx]
                ext_top = max(ext_c["open"], ext_c["close"])
                ext_bot = ext_c["low"]
                
                # 2. Decisional OB: Look between swing_low_idx and high_idx for the candle before the biggest breakout
                # Measure largest single candle displacement in the leg
                best_dec_idx = -1
                max_bar_gain = 0.0
                for mid in range(swing_low_idx + 1, high_idx):
                    bar_gain = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                    # Must be in the middle 30% to 70% of the swing range
                    mid_p = candles[mid]["low"]
                    fib_pos = (mid_p - swing_low) / (max_high - swing_low)
                    if 0.25 <= fib_pos <= 0.65 and bar_gain > max_bar_gain:
                        max_bar_gain = bar_gain
                        best_dec_idx = mid
                        
                dec_top, dec_bot = None, None
                if best_dec_idx != -1:
                    dec_c = candles[best_dec_idx - 1] # The base candle before the explosion
                    dec_top = max(dec_c["open"], dec_c["close"])
                    dec_bot = dec_c["low"]
                    
                # 3. Shallow / Inducement OB: The last minor base just before high_idx
                shallow_idx = high_idx - 1
                sha_top, sha_bot = None, None
                if shallow_idx > swing_low_idx + 2:
                    sha_c = candles[shallow_idx]
                    sha_top = max(sha_c["open"], sha_c["close"])
                    sha_bot = sha_c["low"]
                    
                # Check retracements for each of the 3 OBs after high_idx
                tested_obs = []
                if ext_top and ext_bot:
                    tested_obs.append(("EXTREME", ext_top, ext_bot, swing_low_idx))
                if dec_top and dec_bot and dec_top > ext_top * 1.01:
                    tested_obs.append(("DECISIONAL", dec_top, dec_bot, best_dec_idx))
                if sha_top and sha_bot and sha_top > (dec_top if dec_top else ext_top) * 1.015:
                    tested_obs.append(("SHALLOW_INDUCEMENT", sha_top, sha_bot, shallow_idx))
                    
                # Trace forward from high_idx to see how each OB reacts when tapped
                for ob_name, top, bot, origin_k in tested_obs:
                    # Look for first tap after high_idx
                    tap_idx = -1
                    for t_idx in range(high_idx + 1, min(high_idx + 45, n)):
                        if candles[t_idx]["low"] <= top:
                            tap_idx = t_idx
                            break
                            
                    if tap_idx == -1 or tap_idx >= n - 10:
                        continue
                        
                    tap_c = candles[tap_idx]
                    
                    # Smart Money confirmation filter: Wick absorption check
                    c_range = tap_c["high"] - tap_c["low"]
                    lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                    wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                    
                    # OB 50% Mean Threshold
                    mt = (top + bot) / 2.0
                    holds_mt = tap_c["close"] >= mt
                    
                    entry_p = top
                    tp_price = entry_p * (1.0 + tp_target_pct)
                    sl_price = entry_p * (1.0 - sl_pct)
                    
                    # Also record structural SL (below OB bot)
                    struct_sl_price = bot * 0.997
                    
                    trade_res = None
                    exit_p = entry_p
                    exit_time = tap_c["time"]
                    bars_held = 0
                    
                    # Track forward up to 30 bars
                    for m in range(tap_idx, min(tap_idx + 30, n)):
                        bar = candles[m]
                        bars_held += 1
                        
                        # TP check
                        if bar["high"] >= tp_price:
                            trade_res = "WIN"
                            exit_p = tp_price
                            exit_time = bar["time"]
                            break
                            
                        # SL check (candle close below SL)
                        if bar["close"] <= sl_price:
                            trade_res = "LOSS"
                            exit_p = sl_price
                            exit_time = bar["time"]
                            break
                            
                    if not trade_res:
                        fc = candles[min(tap_idx + 30, n - 1)]["close"]
                        exit_p = fc
                        exit_time = candles[min(tap_idx + 30, n - 1)]["time"]
                        trade_res = "WIN" if fc >= entry_p else "LOSS"
                        
                    gross_pct = (exit_p - entry_p) / entry_p
                    
                    results_by_type[ob_name][tf].append({
                        "sym": sym, "entry_time": tap_c["time"], "exit_time": exit_time,
                        "entry_p": entry_p, "exit_p": exit_p, "gross_pct": gross_pct,
                        "result": trade_res, "wick_ratio": wick_ratio, "holds_mt": holds_mt,
                        "bars": bars_held
                    })

    # Summary Analysis & Comparison
    print("\n" + "=" * 90)
    print(" 📊 DETAILED BREAKDOWN BY ORDER BLOCK TYPE (1H & 4H COMBINED)")
    print("=" * 90)

    for ob_name in ob_types:
        combined_trades = results_by_type[ob_name]["1h"] + results_by_type[ob_name]["4h"]
        # Deduplicate overlapping trades on same bar
        combined_trades.sort(key=lambda x: x["entry_time"])
        
        tot = len(combined_trades)
        if tot == 0:
            print(f"[{ob_name}]: No trades recorded.")
            continue
            
        wins = sum(1 for t in combined_trades if t["result"] == "WIN")
        losses = tot - wins
        wr = (wins / tot) * 100.0
        
        # Test with and without Lower Wick Absorption (>= 18%)
        wick_trades = [t for t in combined_trades if t["wick_ratio"] >= 0.18 and t["holds_mt"]]
        tot_w = len(wick_trades)
        wins_w = sum(1 for t in wick_trades if t["result"] == "WIN")
        wr_w = (wins_w / tot_w * 100.0) if tot_w > 0 else 0.0
        
        # Compounding simulation from $50 USDT (at 5x leverage)
        cap = 50.0
        vault = 0.0
        max_c = 50.0
        max_dd = 0.0
        for t in wick_trades:
            pos = cap * 5.0
            net_ret = t["gross_pct"] - 0.0014
            pnl = pos * net_ret
            if pnl > 0:
                cap += pnl * 0.85
                vault += pnl * 0.15
            else:
                cap = max(5.0, cap + pnl)
            tw = cap + vault
            if tw > max_c: max_c = tw
            dd = (max_c - tw) / max_c * 100.0
            if dd > max_dd: max_dd = dd
            
        print(f"\n🔹 ORDER BLOCK TYPE: [{ob_name}]")
        print(f"    Raw Setups Found:           {tot} trades | Raw Win Rate: {wr:.2f}%")
        print(f"    ⭐ With Wick Absorption Filter: {tot_w} trades | High-Quality Win Rate: {wr_w:.2f}%")
        print(f"    Avg Trade Hold Duration:    {np.mean([t['bars'] for t in wick_trades]) if wick_trades else 0:.1f} bars")
        print(f"    Compounded $50 Wealth:      ${cap + vault:,.2f} USDT (ROI: +{(((cap + vault) - 50)/50*100):,.1f}%)")
        print(f"    Max Compounding Drawdown:   {max_dd:.2f}%")

if __name__ == "__main__":
    analyze_multiple_obs()
