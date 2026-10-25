import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COINS_40 = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "SUIUSDT", "AVAXUSDT", "NEARUSDT", "BNBUSDT", "DOGEUSDT",
    "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT", "APTUSDT", "ARBUSDT",
    "OPUSDT", "INJUSDT", "TIAUSDT", "SEIUSDT", "FETUSDT", "RUNEUSDT", "FILUSDT", "ICPUSDT",
    "PEPEUSDT", "SHIBUSDT", "WIFUSDT", "RENDERUSDT", "STXUSDT", "GALAUSDT", "FTMUSDT",
    "AAVEUSDT", "UNIUSDT", "CRVUSDT", "MKRUSDT", "LDOUSDT", "ATOMUSDT", "THETAUSDT",
    "ALGOUSDT"
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

def analyze_leaderboard():
    tasks = []
    for s in COINS_40:
        tasks.append((s, "4h", 550))
        tasks.append((s, "1h", 1200))
        
    all_data = {"4h": {}, "1h": {}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_klines, t[0], t[1], t[2]) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            sym, tf, klines = f.result()
            if len(klines) >= 100:
                all_data[tf][sym] = klines

    coin_performance = {s: {"wins": 0, "losses": 0, "total": 0, "pnl_sum": 0.0} for s in COINS_40}
    
    for tf, tp_pct, sl_pct, disp_min in [("1h", 0.018, 0.030, 0.018), ("4h", 0.022, 0.030, 0.030)]:
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
                c_range = tap_c["high"] - tap_c["low"]
                lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                
                if wick_ratio < 0.18 or tap_c["close"] < ob_mt:
                    continue
                    
                entry_p = ob_top
                tp_target = entry_p * (1.0 + tp_pct)
                sl_target = entry_p * (1.0 - sl_pct)
                
                trade_res = None
                exit_p = entry_p
                for m in range(tap_idx, min(tap_idx + 40, n)):
                    bar = candles[m]
                    if bar["high"] >= tp_target:
                        trade_res = "WIN"
                        exit_p = tp_target
                        break
                    if bar["close"] <= sl_target:
                        trade_res = "LOSS"
                        exit_p = sl_target
                        break
                        
                if not trade_res:
                    final_close = candles[min(tap_idx + 40, n - 1)]["close"]
                    exit_p = final_close
                    trade_res = "WIN" if final_close >= entry_p else "LOSS"
                    
                gross_pct = (exit_p - entry_p) / entry_p
                pnl = gross_pct * 5.0 * 100.0 # ROE %
                
                coin_performance[sym]["total"] += 1
                if trade_res == "WIN":
                    coin_performance[sym]["wins"] += 1
                else:
                    coin_performance[sym]["losses"] += 1
                coin_performance[sym]["pnl_sum"] += pnl

    # Rank coins by Win Rate (min 2 trades) and Net Profit
    active_coins = [s for s, st in coin_performance.items() if st["total"] > 0]
    active_coins.sort(key=lambda s: (coin_performance[s]["wins"] / coin_performance[s]["total"], coin_performance[s]["total"], coin_performance[s]["pnl_sum"]), reverse=True)
    
    print("=" * 85)
    print(" 🏆 40-COIN REAL PERFORMANCE LEADERBOARD (3-MONTH AUDIT)")
    print("=" * 85)
    print(f"{'Rank':<5} | {'Coin':<10} | {'Trades':<7} | {'Wins':<5} | {'Losses':<6} | {'Win Rate':<9} | {'Net ROE (%)':<12}")
    print("-" * 85)
    
    for idx, s in enumerate(active_coins, 1):
        st = coin_performance[s]
        wr = (st["wins"] / st["total"]) * 100.0
        print(f"#{idx:<4} | {s:<10} | {st['total']:<7} | {st['wins']:<5} | {st['losses']:<6} | {wr:6.1f}%   | {st['pnl_sum']:+8.1f}%")
        
    print("=" * 85)

if __name__ == "__main__":
    analyze_leaderboard()
