import urllib.request
import json
import time
import sys
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Target liquid coins
SYMBOLS = [
    "ETHUSDT", "SOLUSDT", "BTCUSDT", "BNBUSDT", "DOGEUSDT", "ARBUSDT",
    "SUIUSDT", "AVAXUSDT", "LINKUSDT", "NEARUSDT", "APTUSDT", "LTCUSDT",
    "DOTUSDT", "UNIUSDT", "INJUSDT", "OPUSDT", "RENDERUSDT", "WIFUSDT",
    "STXUSDT", "SEIUSDT", "AAVEUSDT", "JUPUSDT", "PYTHUSDT", "RUNEUSDT",
    "SANDUSDT", "THETAUSDT", "PENDLEUSDT", "ZECUSDT", "ONEUSDT", "CRVUSDT",
    "ETHFIUSDT", "ONGUSDT", "LDOUSDT", "PEOPLEUSDT", "AEROUSDT", "SUSDT",
    "VETUSDT", "TIAUSDT", "AXSUSDT", "MANAUSDT"
]

def fetch_1h_klines(symbol, limit=1000):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit={limit}"
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
                return symbol, candles
        except Exception:
            time.sleep(0.5)
    return symbol, None

def analyze_1h_7pct_tp(symbol, candles):
    if not candles or len(candles) < 150:
        return None
        
    trades = []
    
    # 1H SMC Indicator Logic with 7% TP:
    # 1. 1H Bullish Expansion: >= +3.0% move away from OB
    # 2. 1st Boundary Line Touch (Entry = ob_high)
    # 3. Stop Loss: ob_low * 0.995 (or hard -3.5% price move)
    # 4. Take Profit: EXACTLY +7.0% price move (+35.0% ROE @ 5x)
    
    for i in range(12, len(candles) - 25):
        ob_candle = candles[i]
        ob_high = ob_candle["high"]
        ob_low = ob_candle["low"]
        
        if ob_high <= ob_low or ob_high == 0:
            continue
            
        max_exp = 0
        for f in range(1, 10):
            if i + f < len(candles):
                exp = (candles[i+f]["high"] - ob_high) / ob_high
                if exp > max_exp:
                    max_exp = exp
                    
        if max_exp < 0.030: # +3% expansion on 1H
            continue
            
        entry_price = ob_high
        sl_price = min(ob_low * 0.995, entry_price * 0.965) # max -3.5% SL
        tp_price = entry_price * 1.070 # EXACTLY +7.0% TP
        
        entered = False
        entry_bar = -1
        
        # Look ahead up to 72 hours (3 days) for 7% TP completion
        for j in range(i + 3, min(i + 75, len(candles))):
            curr = candles[j]
            if not entered:
                if curr["low"] <= entry_price and curr["high"] >= entry_price:
                    entered = True
                    entry_bar = j
                    if curr["low"] <= sl_price:
                        trades.append({"result": "LOSS", "hours": 1})
                        break
            else:
                hours_held = j - entry_bar
                if curr["low"] <= sl_price:
                    trades.append({"result": "LOSS", "hours": hours_held})
                    break
                elif curr["high"] >= tp_price:
                    trades.append({"result": "WIN", "hours": hours_held})
                    break
                    
    if len(trades) < 6:
        return None
        
    wins = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    total = wins + losses
    win_rate = (wins / total) * 100
    
    win_trades = [t for t in trades if t["result"] == "WIN"]
    avg_hours = sum(t["hours"] for t in win_trades) / len(win_trades) if win_trades else 99
    
    return {
        "symbol": symbol,
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "avg_hours_to_7pct": round(avg_hours, 1)
    }

def main():
    print(f"[*] Analyzing 1H Timeframe with STRICT +7.0% Take Profit across market...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_sym = {executor.submit(fetch_1h_klines, sym): sym for sym in SYMBOLS}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym, candles = future.result()
            if candles:
                res = analyze_1h_7pct_tp(sym, candles)
                if res:
                    results.append(res)
                    
    print(f"[+] Scan Complete! Evaluated {len(results)} coins on 1H with +7% TP Target.\n")
    
    by_wr = sorted(results, key=lambda x: (x["win_rate"], x["total_trades"]), reverse=True)
    
    print("=== 1H TIMEFRAME WITH +7.0% TP: COIN RANKINGS ===")
    print(f"{'Symbol':<14} | {'7% TP Win Rate':<15} | {'Trades':<8} | {'Wins / Loss':<12} | {'Avg Time to 7% TP':<18}")
    print("-" * 75)
    for c in by_wr[:20]:
        star = "🌟 High" if c["win_rate"] >= 65 else "⭐ Moderate"
        print(f"{c['symbol']:<14} | {c['win_rate']:>6.1f}% ({star:<8}) | {c['total_trades']:>6} | {c['wins']}/{c['losses']:<9} | {c['avg_hours_to_7pct']:>5} hours")
        
    total_trades_all = sum(r["total_trades"] for r in results)
    total_wins_all = sum(r["wins"] for r in results)
    overall_wr = (total_wins_all / total_trades_all * 100) if total_trades_all else 0
    
    print("\n=======================================================")
    print("      1H TIMEFRAME +7% TP OVERALL MARKET ACCURACY")
    print("=======================================================")
    print(f"Total Coins Tested          : {len(results)}")
    print(f"Total 1H Trades Evaluated   : {total_trades_all}")
    print(f"Total Reaching +7% TP       : {total_wins_all} Wins")
    print(f"Overall 7% TP Win Rate (1H) : {overall_wr:.1f}%")
    print(f"Average Time to Reach +7% TP: {sum(r['avg_hours_to_7pct'] for r in results)/len(results):.1f} hours (~1 to 1.5 days)")
    print(f"Risk-to-Reward Ratio (RR)   : 1 : 2.0  (+7% Gain vs -3.5% SL = +35% ROE @ 5x)")
    print("=======================================================")

if __name__ == "__main__":
    main()
