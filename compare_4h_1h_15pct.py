import urllib.request
import json
import time
import sys
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SYMBOLS = [
    "ETHUSDT", "SOLUSDT", "BTCUSDT", "BNBUSDT", "DOGEUSDT", "ARBUSDT",
    "SUIUSDT", "AVAXUSDT", "LINKUSDT", "NEARUSDT", "APTUSDT", "LTCUSDT",
    "DOTUSDT", "UNIUSDT", "INJUSDT", "OPUSDT", "RENDERUSDT", "WIFUSDT",
    "STXUSDT", "SEIUSDT", "AAVEUSDT", "JUPUSDT", "PYTHUSDT", "RUNEUSDT",
    "SANDUSDT", "THETAUSDT", "PENDLEUSDT", "ZECUSDT", "ONEUSDT", "CRVUSDT",
    "ETHFIUSDT", "ONGUSDT", "LDOUSDT", "PEOPLEUSDT", "AEROUSDT", "SUSDT",
    "VETUSDT", "TIAUSDT", "AXSUSDT", "MANAUSDT"
]

def fetch_klines(symbol, interval, limit=1000):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                candles = []
                for c in data:
                    candles.append({
                        "time": int(c[0]),
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": float(c[5])
                    })
                return symbol, interval, candles
        except Exception:
            time.sleep(0.5)
    return symbol, interval, None

def analyze_strategy(symbol, interval, candles):
    if not candles or len(candles) < 150:
        return None
        
    trades = []
    # Target: Real Market Move = +1.5% (+7.5% ROE @ 5x)
    # SL: Real Market Move = -2.5% (-12.5% ROE @ 5x) or OB low
    
    exp_threshold = 0.05 if interval == "4h" else 0.025
    look_candles = 6 if interval == "4h" else 8
    
    for i in range(12, len(candles) - 15):
        ob_candle = candles[i]
        ob_high = ob_candle["high"]
        ob_low = ob_candle["low"]
        
        if ob_high <= ob_low or ob_high == 0:
            continue
            
        max_exp = 0
        for f in range(1, look_candles):
            if i + f < len(candles):
                exp = (candles[i+f]["high"] - ob_high) / ob_high
                if exp > max_exp:
                    max_exp = exp
                    
        if max_exp < exp_threshold:
            continue
            
        entry_price = ob_high
        sl_price = min(ob_low * 0.995, entry_price * 0.975) # -2.5% SL
        tp_price = entry_price * 1.015 # EXACTLY +1.5% REAL MARKET MOVE (+7.5% ROE @ 5x)
        
        entered = False
        entry_bar = -1
        
        max_forward = 35 if interval == "4h" else 50
        for j in range(i + 3, min(i + max_forward, len(candles))):
            curr = candles[j]
            if not entered:
                if curr["low"] <= entry_price and curr["high"] >= entry_price:
                    entered = True
                    entry_bar = j
                    if curr["low"] <= sl_price:
                        trades.append({"result": "LOSS", "bars": 1})
                        break
            else:
                bars_held = j - entry_bar
                if curr["low"] <= sl_price:
                    trades.append({"result": "LOSS", "bars": bars_held})
                    break
                elif curr["high"] >= tp_price:
                    trades.append({"result": "WIN", "bars": bars_held})
                    break
                    
    if len(trades) < 6:
        return None
        
    wins = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    total = wins + losses
    win_rate = (wins / total) * 100
    
    win_trades = [t for t in trades if t["result"] == "WIN"]
    avg_bars = sum(t["bars"] for t in win_trades) / len(win_trades) if win_trades else 99
    hours_multiplier = 4.0 if interval == "4h" else 1.0
    avg_hours = avg_bars * hours_multiplier
    
    return {
        "symbol": symbol,
        "interval": interval,
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "avg_hours": round(avg_hours, 1)
    }

def main():
    print("[*] Running Dual Timeframe Test: +1.5% Real Market Move (+7.5% ROE @ 5x)")
    print("Testing 4H Timeframe vs 1H Timeframe on 40 liquid pairs...")
    
    res_4h = []
    res_1h = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for sym in SYMBOLS:
            futures.append(executor.submit(fetch_klines, sym, "4h"))
            futures.append(executor.submit(fetch_klines, sym, "1h"))
            
        for future in concurrent.futures.as_completed(futures):
            sym, interval, candles = future.result()
            if candles:
                res = analyze_strategy(sym, interval, candles)
                if res:
                    if interval == "4h":
                        res_4h.append(res)
                    else:
                        res_1h.append(res)
                        
    # 4H Aggregate
    total_4h_trades = sum(r["total_trades"] for r in res_4h)
    total_4h_wins = sum(r["wins"] for r in res_4h)
    wr_4h = (total_4h_wins / total_4h_trades * 100) if total_4h_trades else 0
    avg_time_4h = sum(r["avg_hours"] for r in res_4h) / len(res_4h) if res_4h else 0
    
    # 1H Aggregate
    total_1h_trades = sum(r["total_trades"] for r in res_1h)
    total_1h_wins = sum(r["wins"] for r in res_1h)
    wr_1h = (total_1h_wins / total_1h_trades * 100) if total_1h_trades else 0
    avg_time_1h = sum(r["avg_hours"] for r in res_1h) / len(res_1h) if res_1h else 0
    
    print("\n" + "="*65)
    print("   COMPARATIVE ACCURACY: +1.5% REAL MARKET MOVE (+7.5% ROE @ 5x)")
    print("="*65)
    print(f"{'Timeframe':<16} | {'Accuracy (Win Rate)':<20} | {'Total Trades':<14} | {'Avg Time to TP':<15}")
    print("-"*65)
    print(f"{'4-Hour (4H)':<16} | {wr_4h:>18.1f}% | {total_4h_trades:>12} | {avg_time_4h:>10.1f} Hours")
    print(f"{'1-Hour (1H)':<16} | {wr_1h:>18.1f}% | {total_1h_trades:>12} | {avg_time_1h:>10.1f} Hours")
    print("="*65)
    
    print("\nTop 5 Coins on 4H (+1.5% Move):")
    for c in sorted(res_4h, key=lambda x: x["win_rate"], reverse=True)[:5]:
        print(f"  • {c['symbol']:<12}: {c['win_rate']}% Win Rate ({c['wins']}/{c['losses']}) | TP in ~{c['avg_hours']}h")
        
    print("\nTop 5 Coins on 1H (+1.5% Move):")
    for c in sorted(res_1h, key=lambda x: x["win_rate"], reverse=True)[:5]:
        print(f"  • {c['symbol']:<12}: {c['win_rate']}% Win Rate ({c['wins']}/{c['losses']}) | TP in ~{c['avg_hours']}h")

if __name__ == "__main__":
    main()
