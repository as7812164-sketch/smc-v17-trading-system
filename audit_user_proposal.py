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

def run_user_rules_audit():
    print("=" * 85)
    print(" 🎯 TESTING USER'S EXACT PROPOSED PARAMETERS ON 28 COINS (1H & 4H)")
    print(" 1H: TP = 12% ROE (2.4% move), Soft SL = 8% ROE (1.6% move), Hard SL = 18% ROE (3.6% move)")
    print(" 4H: TP = 15% ROE (3.0% move), Soft SL = 8% ROE (1.6% move), Hard SL = 18% ROE (3.6% move)")
    print(" OB Height filter: REMOVED (No setup starvation!)")
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

    btc_candles = all_data["4h"].get("BTCUSDT", [])
    btc_map = {c["time"]: c["close"] for c in btc_candles}
    btc_closes = [c["close"] for c in btc_candles]
    btc_ema20 = [0.0] * len(btc_closes)
    if btc_closes:
        k_mult = 2.0 / (20 + 1)
        btc_ema20[0] = btc_closes[0]
        for i in range(1, len(btc_closes)):
            btc_ema20[i] = btc_closes[i] * k_mult + btc_ema20[i-1] * (1.0 - k_mult)
    btc_ema_map = {btc_candles[i]["time"]: btc_ema20[i] for i in range(len(btc_candles))}

    # We will test two variations of the user's idea:
    # Option A: With BE lock at +10% profit (+2.0% move) -> move SL to +0.5% profit (+0.1% move)
    # Option B: Direct TP / SL without early BE shift (clean run to TP)
    # Option C: Dynamic Soft SL at 50% Mean Threshold or 1.6% move (whichever is tighter)
    
    for opt_name, use_be in [("DIRECT TP/SL (Clean Target)", False), ("WITH BREAKEVEN LOCK AT +10% ROE", True)]:
        all_trades = []
        for tf, tp_pct, soft_sl_pct, disp_min in [("1h", 0.024, 0.016, 0.018), ("4h", 0.030, 0.016, 0.030)]:
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
                    
                    entry_p = ob_top
                    tp_target = entry_p * (1.0 + tp_pct)
                    soft_sl_target = entry_p * (1.0 - soft_sl_pct)
                    hard_sl_target = entry_p * (1.0 - 0.036) # 18% ROE at 5x = 3.6% move
                    
                    be_trigger_p = entry_p * (1.0 + 0.020) # +10% ROE = +2.0% move
                    be_lock_p = entry_p * (1.0 + 0.001)    # +0.5% ROE = +0.1% move
                    
                    trade_res = None
                    exit_p = entry_p
                    exit_time = tap_c["time"]
                    be_active = False
                    
                    for m in range(tap_idx, min(tap_idx + 40, n)):
                        bar = candles[m]
                        
                        # 1. Hard SL check (Flash dump)
                        if bar["low"] <= hard_sl_target:
                            trade_res = "HARD_SL"
                            exit_p = hard_sl_target
                            exit_time = bar["time"]
                            break
                            
                        # 2. Check BE Trigger if enabled
                        if use_be and not be_active and bar["high"] >= be_trigger_p:
                            be_active = True
                            
                        # 3. Check TP
                        if bar["high"] >= tp_target:
                            trade_res = "WIN"
                            exit_p = tp_target
                            exit_time = bar["time"]
                            break
                            
                        # 4. If BE is active, check if price fell back to BE lock
                        if be_active and bar["low"] <= be_lock_p:
                            trade_res = "BE_EXIT"
                            exit_p = be_lock_p
                            exit_time = bar["time"]
                            break
                            
                        # 5. Soft SL on candle close
                        if not be_active and bar["close"] <= soft_sl_target:
                            trade_res = "SOFT_SL"
                            exit_p = bar["close"]
                            exit_time = bar["time"]
                            break
                            
                    if not trade_res:
                        final_c = candles[min(tap_idx + 40, n - 1)]["close"]
                        exit_p = final_c
                        exit_time = candles[min(tap_idx + 40, n - 1)]["time"]
                        trade_res = "WIN" if final_c >= entry_p else "LOSS"
                        
                    gross_pct = (exit_p - entry_p) / entry_p
                    all_trades.append({
                        "symbol": sym, "tf": tf, "entry_time": tap_c["time"],
                        "exit_time": exit_time, "entry_p": entry_p, "exit_p": exit_p,
                        "gross_pct": gross_pct, "result": trade_res
                    })
                    
        all_trades.sort(key=lambda x: x["entry_time"])
        
        # Compounding from $50 with 100% reinvest vs 80/20 reinvest
        for reinvest_mode in ["100% Full Compounding", "80% Trade / 20% Secure Vault"]:
            cap = 50.0
            vault = 0.0
            wins = sum(1 for t in all_trades if t["result"] in ["WIN", "BE_EXIT"] and t["gross_pct"] > 0)
            losses = len(all_trades) - wins
            wr = (wins / len(all_trades) * 100) if all_trades else 0
            
            hit_1000 = None
            max_cap = 50.0
            max_dd = 0.0
            
            for idx, t in enumerate(all_trades, 1):
                pos = cap * 5.0
                net_ret = t["gross_pct"] - 0.0014 # fees + slippage
                net_pnl = pos * net_ret
                
                if reinvest_mode == "100% Full Compounding":
                    cap = max(5.0, cap + net_pnl)
                else:
                    if net_pnl > 0:
                        cap += net_pnl * 0.80
                        vault += net_pnl * 0.20
                    else:
                        cap = max(5.0, cap + net_pnl)
                        
                total_w = cap + vault
                if total_w > max_cap: max_cap = total_w
                dd = (max_cap - total_w) / max_cap * 100.0
                if dd > max_dd: max_dd = dd
                
                if total_w >= 1000.0 and hit_1000 is None:
                    hit_1000 = idx
                    
            print(f"\n>>> CONFIG: [{opt_name}] | ALLOCATION: [{reinvest_mode}] <<<")
            print(f"Total Trades:       {len(all_trades)}")
            print(f"Wins / Green:       {wins} ({wr:.1f}%)")
            print(f"Losses:             {losses} ({100-wr:.1f}%)")
            print(f"Final Trading Cap:  ${cap:,.2f} USDT")
            print(f"Secured Vault:      ${vault:,.2f} USDT")
            print(f"Total Wealth:       ${cap+vault:,.2f} USDT")
            print(f"Compounded ROI:     +{(((cap+vault)-50)/50*100):,.1f}%")
            print(f"Max Drawdown:       {max_dd:.2f}%")
            print(f"Hit $1,000 Target:  {'🎉 YES! Reached at Trade #' + str(hit_1000) if hit_1000 else 'NO (Did not reach 1000)'}")

if __name__ == "__main__":
    run_user_rules_audit()
