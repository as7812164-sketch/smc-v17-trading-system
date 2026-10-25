import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

APPROVED_28_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "APTUSDT",
    "ARBUSDT", "OPUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", "RUNEUSDT", "RENDERUSDT",
    "INJUSDT", "FETUSDT", "THETAUSDT", "ALGOUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT", "ICPUSDT",
    "PYTHUSDT", "PEPEUSDT", "SHIBUSDT", "XRPUSDT"
]

def fetch_klines(sym, interval, limit=550):
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

def run_grid_sweep():
    print("=" * 85)
    print(" 🔬 MULTI-PARAMETER GRID SWEEP OPTIMIZATION (1H & 4H DUAL-TIMEFRAME)")
    print(" 28 Approved Coins | Last 90 Days Binance Data | 5x Isolated Margin")
    print("=" * 85)
    
    tasks = []
    for s in APPROVED_28_COINS:
        tasks.append((s, "4h", 550))
        tasks.append((s, "1h", 1200))
        
    all_data = {"4h": {}, "1h": {}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_klines, t[0], t[1], t[2]) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            sym, tf, klines = f.result()
            if len(klines) >= 100:
                all_data[tf][sym] = klines

    print(f"Loaded {len(all_data['4h'])} pairs for 4H and {len(all_data['1h'])} pairs for 1H.\n")
    
    # Pre-calculate BTC 4H EMA20
    btc_candles = all_data["4h"].get("BTCUSDT", [])
    btc_map = {c["time"]: c["close"] for c in btc_candles}
    btc_closes = [c["close"] for c in btc_candles]
    btc_ema20 = [0.0] * len(btc_closes)
    if btc_closes:
        k_mult = 2.0 / 21.0
        btc_ema20[0] = btc_closes[0]
        for i in range(1, len(btc_closes)):
            btc_ema20[i] = btc_closes[i] * k_mult + btc_ema20[i-1] * (1.0 - k_mult)
    btc_ema_map = {btc_candles[i]["time"]: btc_ema20[i] for i in range(len(btc_candles))}
    
    # First, detect all qualified setups across 1H and 4H
    base_setups = []
    
    for tf, disp_min in [("1h", 0.018), ("4h", 0.030)]:
        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 20):
                is_extreme = (candles[i]["low"] == min(c["low"] for c in candles[i-20:i+1]))
                if not is_extreme: continue
                
                c = candles[i]
                ob_top = max(c["open"], c["close"])
                ob_bot = c["low"]
                ob_mt = (ob_top + ob_bot) / 2.0
                
                disp_high = max(candles[i+1]["high"], candles[i+2]["high"], candles[i+3]["high"])
                disp_gain = (disp_high - ob_top) / ob_top
                has_fvg = (candles[i+2]["low"] > candles[i]["high"]) if i+2 < n else False
                if disp_gain < disp_min or not has_fvg: continue
                
                tap_idx = -1
                for k in range(i+3, min(i+60, n)):
                    if candles[k]["low"] <= ob_top:
                        tap_idx = k
                        break
                if tap_idx == -1 or tap_idx >= n - 10: continue
                
                tap_c = candles[tap_idx]
                
                # BTC Shield Gate
                if sym != "BTCUSDT":
                    b_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                    b_c = btc_map.get(b_ts)
                    b_e = btc_ema_map.get(b_ts)
                    if b_c and b_e and b_c < b_e:
                        continue
                        
                c_range = tap_c["high"] - tap_c["low"]
                lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                if wick_ratio < 0.18 or tap_c["close"] < ob_mt: continue
                
                base_setups.append({
                    "symbol": sym, "tf": tf, "entry_p": ob_top, "ob_bot": ob_bot,
                    "tap_idx": tap_idx, "candles": candles, "time": tap_c["time"]
                })
                
    base_setups.sort(key=lambda x: x["time"])
    print(f"Total Base Setups Detected: {len(base_setups)}\n")
    
    # Define Parameter Grid to Test:
    # Soft SL models:
    #   1. "Fixed -8% ROE (-1.6%)"
    #   2. "Fixed -11% ROE (-2.2%)"
    #   3. "OB Base Low (-0.2% buffer)"
    # BE models:
    #   A. "BE at +10% ROE -> Shift to Entry"
    #   B. "BE at +10% ROE -> Shift to Entry - 0.3% Buffer"
    #   C. "No BE Shift (Pure Direct Target or Base SL)"
    
    sl_options = [
        {"name": "Fixed -8% ROE (-1.6%)", "type": "fixed", "val": 0.016},
        {"name": "Fixed -11% ROE (-2.2%)", "type": "fixed", "val": 0.022},
        {"name": "Dynamic OB Base Low", "type": "ob_base", "val": 0.002}
    ]
    
    be_options = [
        {"name": "Instant BE @ +10% ROE", "trigger": 0.020, "be_offset": 0.000},
        {"name": "Buffered BE @ +10% ROE (-0.3% cushion)", "trigger": 0.020, "be_offset": -0.003},
        {"name": "No BE (Pure Direct TP / Base SL)", "trigger": 99.0, "be_offset": 0.000}
    ]
    
    results_grid = []
    
    for sl_opt in sl_options:
        for be_opt in be_options:
            trades = []
            tp_1h = 0.024 # +12% ROE
            tp_4h = 0.030 # +15% ROE
            hard_sl_pct = 0.036 # -18% ROE
            
            for s in base_setups:
                tf = s["tf"]
                candles = s["candles"]
                tap_idx = s["tap_idx"]
                entry_p = s["entry_p"]
                ob_bot = s["ob_bot"]
                n = len(candles)
                
                tp_target = entry_p * (1.0 + (tp_1h if tf == "1h" else tp_4h))
                be_trigger = entry_p * (1.0 + be_opt["trigger"])
                be_price = entry_p * (1.0 + be_opt["be_offset"])
                
                if sl_opt["type"] == "fixed":
                    soft_sl = entry_p * (1.0 - sl_opt["val"])
                else:
                    soft_sl = ob_bot * (1.0 - sl_opt["val"])
                    
                hard_sl = entry_p * (1.0 - hard_sl_pct)
                
                be_active = False
                trade_res = None
                exit_p = entry_p
                
                for m in range(tap_idx, min(tap_idx + 45, n)):
                    bar = candles[m]
                    if not be_active and bar["high"] >= be_trigger:
                        be_active = True
                    if bar["high"] >= tp_target:
                        trade_res = "WIN"
                        exit_p = tp_target
                        break
                    if be_active and bar["low"] <= be_price:
                        trade_res = "BREAKEVEN"
                        exit_p = be_price
                        break
                    if bar["low"] <= hard_sl:
                        trade_res = "HARD_LOSS"
                        exit_p = hard_sl
                        break
                    if not be_active and bar["close"] <= soft_sl:
                        trade_res = "SOFT_LOSS"
                        exit_p = bar["close"]
                        break
                        
                if not trade_res:
                    final_close = candles[min(tap_idx + 45, n - 1)]["close"]
                    exit_p = final_close
                    trade_res = "WIN" if final_close > entry_p else ("BREAKEVEN" if be_active else "SOFT_LOSS")
                    
                gross_pct = (exit_p - entry_p) / entry_p
                trades.append({"result": trade_res, "gross_pct": gross_pct})
                
            # Compounding simulation
            cap = 50.0
            max_cap = 50.0
            max_dd = 0.0
            wins = sum(1 for t in trades if t["result"] == "WIN")
            bes = sum(1 for t in trades if t["result"] == "BREAKEVEN")
            losses = sum(1 for t in trades if "LOSS" in t["result"])
            
            for t in trades:
                pos = cap * 5.0
                net_ret = t["gross_pct"] - 0.0014
                pnl = pos * net_ret
                cap = max(1.0, cap + pnl)
                if cap > max_cap: max_cap = cap
                dd = (max_cap - cap) / max_cap * 100.0
                if dd > max_dd: max_dd = dd
                
            tot = len(trades)
            wr = (wins / tot * 100) if tot > 0 else 0
            safety = ((wins + bes) / tot * 100) if tot > 0 else 0
            
            results_grid.append({
                "sl_name": sl_opt["name"],
                "be_name": be_opt["name"],
                "total": tot, "wins": wins, "bes": bes, "losses": losses,
                "win_rate": wr, "safety": safety,
                "final_cap": cap, "max_dd": max_dd
            })

    # Sort results by Final Capital
    results_grid.sort(key=lambda x: x["final_cap"], reverse=True)
    
    print("=" * 85)
    print(" 🏆 GRID SWEEP OPTIMIZATION RANKING (BEST TO WORST)")
    print("=" * 85)
    print(f"{'Rank':<4} | {'Soft SL Model':<22} | {'Breakeven Rule':<33} | {'Wins':<5} | {'Loss':<5} | {'Win %':<6} | {'Final $50':<11} | {'Max DD':<7}")
    print("-" * 115)
    
    for idx, r in enumerate(results_grid, 1):
        print(f"#{idx:<3} | {r['sl_name']:<22} | {r['be_name']:<33} | {r['wins']:<5} | {r['losses']:<5} | {r['win_rate']:5.1f}% | ${r['final_cap']:8.2f}  | {r['max_dd']:5.1f}%")
        
    print("=" * 85)

if __name__ == "__main__":
    run_grid_sweep()
