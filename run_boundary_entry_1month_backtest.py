import os
import sys
import glob
import json
import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TOP_22_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT", "NEARUSDT", "OPUSDT",
    "ARBUSDT", "APTUSDT", "TIAUSDT", "INJUSDT", "FETUSDT", "AAVEUSDT",
    "ALGOUSDT", "DOTUSDT", "MATICUSDT", "LDOUSDT"
]

def run_backtest(min_pump_pct=0.08, entry_mode="BOUNDARY", use_be_armor=True):
    results = {
        "1h": {"trades": [], "wins": 0, "losses": 0, "breakeven": 0},
        "4h": {"trades": [], "wins": 0, "losses": 0, "breakeven": 0}
    }
    
    tp_spot_pct = 0.1220 / 5.0  # +2.44%
    sl_spot_pct = 0.1200 / 5.0  # -2.40%
    be_trigger_spot = 0.015     # +1.5% spot move triggers BE

    for tf in ["1h", "4h"]:
        bars_per_month = 720 if tf == "1h" else 180
        
        for sym in TOP_22_SYMBOLS:
            fn = f"historical_data/{sym}_{tf}.json"
            if not os.path.exists(fn):
                continue
            with open(fn, "r") as fp:
                raw = json.load(fp)
            
            candles = [
                {
                    "time": c.get("time") or c.get("open_time"),
                    "open": float(c["open"]),
                    "high": float(c["high"]),
                    "low": float(c["low"]),
                    "close": float(c["close"]),
                    "volume": float(c.get("volume", 0))
                } for c in raw
            ]
            
            n = len(candles)
            if n < bars_per_month:
                continue
            
            # Restrict strictly to last 30 days (1 month)
            c_month = candles[-bars_per_month:]
            nm = len(c_month)
            seen_ob = set()
            
            for i in range(10, nm - 20):
                # ---------------------------------------------------------
                # 1. BULLISH EXTREME OB (LONG SETUP)
                # ---------------------------------------------------------
                w_lows = [x["low"] for x in c_month[i-8:i+1]]
                if c_month[i]["low"] == min(w_lows) and c_month[i]["close"] < c_month[i]["open"]:
                    if i in seen_ob:
                        continue
                    
                    # Judas sweep
                    p_low = min(x["low"] for x in c_month[max(0, i-5):i]) if i >= 5 else c_month[i]["low"]
                    is_judas = c_month[i]["low"] <= p_low
                    
                    # FVG in candle 2 or 3
                    has_fvg = False
                    if i + 2 < nm and c_month[i+2]["low"] > c_month[i]["high"]:
                        has_fvg = True
                    elif i + 3 < nm and c_month[i+3]["low"] > c_month[i+1]["high"]:
                        has_fvg = True
                    
                    # Check 8-10% pump displacement
                    sub = c_month[i:min(i+16, nm)]
                    highs = [x["high"] for x in sub]
                    max_h = max(highs)
                    h_idx = i + highs.index(max_h)
                    gain = (max_h - c_month[i]["low"]) / c_month[i]["low"]
                    
                    if gain >= min_pump_pct and has_fvg and is_judas and h_idx > i + 2:
                        seen_ob.add(i)
                        ob_high = c_month[i]["high"]
                        ob_low = c_month[i]["low"]
                        
                        entry_p = ob_high if entry_mode == "BOUNDARY" else ((ob_high + ob_low) / 2.0)
                        tp_p = round(entry_p * (1.0 + tp_spot_pct), 6)
                        sl_p = round(entry_p * (1.0 - sl_spot_pct), 6)
                        
                        # Look for 1st Tap on Boundary
                        for t in range(h_idx + 1, min(h_idx + 35, nm)):
                            tap_bar = c_month[t]
                            
                            is_tap = tap_bar["low"] <= entry_p if entry_mode == "BOUNDARY" else (tap_bar["low"] <= entry_p and tap_bar["close"] >= entry_p)
                            
                            if is_tap and tap_bar["low"] > sl_p:
                                # Position opened!
                                entry_time_str = datetime.datetime.fromtimestamp(tap_bar["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                
                                outcome = "PENDING"
                                exit_time_str = ""
                                max_favorable = 0.0
                                
                                for k in range(t + 1, min(t + 35, nm)):
                                    bar_k = c_month[k]
                                    fav_move = (bar_k["high"] - entry_p) / entry_p
                                    if fav_move > max_favorable:
                                        max_favorable = fav_move
                                    
                                    # Target Hit
                                    if bar_k["high"] >= tp_p:
                                        outcome = "WIN"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                    
                                    # Breakeven Protection
                                    elif use_be_armor and max_favorable >= be_trigger_spot and bar_k["low"] <= entry_p:
                                        outcome = "BREAKEVEN"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                    
                                    # Stop Loss Hit
                                    elif bar_k["low"] <= sl_p:
                                        outcome = "LOSS"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                
                                if outcome == "WIN":
                                    results[tf]["wins"] += 1
                                elif outcome == "LOSS":
                                    results[tf]["losses"] += 1
                                elif outcome == "BREAKEVEN":
                                    results[tf]["breakeven"] += 1
                                
                                results[tf]["trades"].append({
                                    "symbol": sym,
                                    "side": "LONG",
                                    "entry_price": entry_p,
                                    "tp_price": tp_p,
                                    "sl_price": sl_p,
                                    "entry_time": entry_time_str,
                                    "exit_time": exit_time_str,
                                    "outcome": outcome,
                                    "pump_pct": round(gain * 100, 2)
                                })
                                break

                # ---------------------------------------------------------
                # 2. BEARISH EXTREME OB (SHORT SETUP)
                # ---------------------------------------------------------
                w_highs = [x["high"] for x in c_month[i-8:i+1]]
                if c_month[i]["high"] == max(w_highs) and c_month[i]["close"] > c_month[i]["open"]:
                    if i in seen_ob:
                        continue
                    
                    p_high = max(x["high"] for x in c_month[max(0, i-5):i]) if i >= 5 else c_month[i]["high"]
                    is_judas = c_month[i]["high"] >= p_high
                    
                    has_fvg = False
                    if i + 2 < nm and c_month[i+2]["high"] < c_month[i]["low"]:
                        has_fvg = True
                    elif i + 3 < nm and c_month[i+3]["high"] < c_month[i+1]["low"]:
                        has_fvg = True
                    
                    sub = c_month[i:min(i+16, nm)]
                    lows = [x["low"] for x in sub]
                    min_l = min(lows)
                    l_idx = i + lows.index(min_l)
                    drop = (c_month[i]["high"] - min_l) / c_month[i]["high"]
                    
                    if drop >= min_pump_pct and has_fvg and is_judas and l_idx > i + 2:
                        seen_ob.add(i)
                        ob_high = c_month[i]["high"]
                        ob_low = c_month[i]["low"]
                        
                        entry_p = ob_low if entry_mode == "BOUNDARY" else ((ob_high + ob_low) / 2.0)
                        tp_p = round(entry_p * (1.0 - tp_spot_pct), 6)
                        sl_p = round(entry_p * (1.0 + sl_spot_pct), 6)
                        
                        for t in range(l_idx + 1, min(l_idx + 35, nm)):
                            tap_bar = c_month[t]
                            
                            is_tap = tap_bar["high"] >= entry_p if entry_mode == "BOUNDARY" else (tap_bar["high"] >= entry_p and tap_bar["close"] <= entry_p)
                            
                            if is_tap and tap_bar["high"] < sl_p:
                                entry_time_str = datetime.datetime.fromtimestamp(tap_bar["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                
                                outcome = "PENDING"
                                exit_time_str = ""
                                max_favorable = 0.0
                                
                                for k in range(t + 1, min(t + 35, nm)):
                                    bar_k = c_month[k]
                                    fav_move = (entry_p - bar_k["low"]) / entry_p
                                    if fav_move > max_favorable:
                                        max_favorable = fav_move
                                    
                                    if bar_k["low"] <= tp_p:
                                        outcome = "WIN"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                    elif use_be_armor and max_favorable >= be_trigger_spot and bar_k["high"] >= entry_p:
                                        outcome = "BREAKEVEN"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                    elif bar_k["high"] >= sl_p:
                                        outcome = "LOSS"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                
                                if outcome == "WIN":
                                    results[tf]["wins"] += 1
                                elif outcome == "LOSS":
                                    results[tf]["losses"] += 1
                                elif outcome == "BREAKEVEN":
                                    results[tf]["breakeven"] += 1
                                
                                results[tf]["trades"].append({
                                    "symbol": sym,
                                    "side": "SHORT",
                                    "entry_price": entry_p,
                                    "tp_price": tp_p,
                                    "sl_price": sl_p,
                                    "entry_time": entry_time_str,
                                    "exit_time": exit_time_str,
                                    "outcome": outcome,
                                    "pump_pct": round(drop * 100, 2)
                                })
                                break
                                
    return results

if __name__ == "__main__":
    print("================================================================================")
    print("🔬 1-MONTH (30-DAY) AUDIT: BOUNDARY ENTRY + 8-10% PUMP + CANDLE 2/3 FVG")
    print("================================================================================")
    
    # 1. User Strategy: Boundary Entry + 8% Pump
    res_bound = run_backtest(min_pump_pct=0.08, entry_mode="BOUNDARY", use_be_armor=True)
    
    # 2. Baseline Comparison: 50% Mean Threshold + 8% Pump
    res_mt = run_backtest(min_pump_pct=0.08, entry_mode="MEAN_THRESHOLD", use_be_armor=True)

    with open("audit_1month_comparison.json", "w") as fp:
        json.dump({"boundary": res_bound, "mean_threshold": res_mt}, fp, indent=2)

    for mode_name, r in [("BOUNDARY ENTRY (Aapki Strategy)", res_bound), ("50% MEAN THRESHOLD (Baseline)", res_mt)]:
        print(f"\n📊 --- {mode_name} ---")
        for tf in ["4h", "1h"]:
            tot = len(r[tf]["trades"])
            w = r[tf]["wins"]
            l = r[tf]["losses"]
            be = r[tf]["breakeven"]
            decided = w + l
            wr = (w / decided * 100) if decided > 0 else 0
            cap_pres = ((w + be) / tot * 100) if tot > 0 else 0
            
            print(f"[{tf.upper()} Timeframe]:")
            print(f"  Total Trades: {tot} | Wins: {w} | Losses: {l} | Breakeven Protected: {be}")
            print(f"  Real Win Rate (Decided): {wr:.2f}%")
            print(f"  Capital Preservation Rate: {cap_pres:.2f}%")
            
            # Print sample trades
            for t in r[tf]["trades"][:3]:
                print(f"    -> {t['symbol']} {t['side']} Entry:{t['entry_price']} | Pump:{t['pump_pct']}% | Result: {t['outcome']} ({t['entry_time']} -> {t['exit_time']})")
