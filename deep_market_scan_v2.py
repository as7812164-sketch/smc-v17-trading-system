import urllib.request
import json
import time
import sys
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_liquid_symbols():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    
    pairs = []
    for d in data:
        sym = d["symbol"]
        if sym.endswith("USDT"):
            vol = float(d.get("quoteVolume", 0))
            if vol >= 10_000_000: # 10M USDT 24h volume
                pairs.append((sym, vol))
    
    pairs.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in pairs[:200]]

def fetch_4h_klines(symbol, limit=1000):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=4h&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
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
        return symbol, None

def analyze_coin(symbol, candles):
    if not candles or len(candles) < 100:
        return None
        
    trades = []
    
    for i in range(10, len(candles) - 15):
        ob_candle = candles[i]
        ob_high = ob_candle["high"] # Top Boundary Line (Demand Entry)
        ob_low = ob_candle["low"]   # Bottom Boundary Line
        
        if ob_high <= ob_low or ob_high == 0:
            continue
            
        # Expansion check: >= +6% within next 5 candles
        max_exp = 0
        for f in range(1, 6):
            if i + f < len(candles):
                exp = (candles[i+f]["high"] - ob_high) / ob_high
                if exp > max_exp:
                    max_exp = exp
                    
        if max_exp < 0.06:
            continue
            
        entry_price = ob_high
        sl_price = ob_low * 0.992 # SL 0.8% below box
        # Quick TP: +2.0% price move (+10% ROE @ 5x)
        quick_tp = entry_price * 1.020
        # Swing TP: +6.0% price move (+30% ROE @ 5x)
        swing_tp = entry_price * 1.060
        
        entered = False
        entry_bar = -1
        
        for j in range(i + 4, min(i + 50, len(candles))):
            curr = candles[j]
            if not entered:
                if curr["low"] <= entry_price and curr["high"] >= entry_price:
                    entered = True
                    entry_bar = j
                    if curr["low"] <= sl_price:
                        trades.append({"result": "LOSS", "bars": 1, "swing_win": False, "quick_win": False})
                        break
            else:
                bars = j - entry_bar
                if curr["low"] <= sl_price:
                    trades.append({"result": "LOSS", "bars": bars, "swing_win": False, "quick_win": False})
                    break
                elif curr["high"] >= quick_tp:
                    is_swing = curr["high"] >= swing_tp
                    trades.append({"result": "WIN", "bars": bars, "swing_win": is_swing, "quick_win": True})
                    break
                    
    if len(trades) < 6:
        return None
        
    wins = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    total = wins + losses
    win_rate = (wins / total) * 100
    
    win_trades = [t for t in trades if t["result"] == "WIN"]
    avg_bars = sum(t["bars"] for t in win_trades) / len(win_trades) if win_trades else 99
    avg_hours = avg_bars * 4.0
    
    swing_wins = sum(1 for t in trades if t.get("swing_win", False))
    swing_wr = (swing_wins / total) * 100
    
    # Fast bounce win rate (TP reached in <= 2 bars / 8 hours)
    fast_wins = sum(1 for t in trades if t["result"] == "WIN" and t["bars"] <= 2)
    fast_wr = (fast_wins / total) * 100
    
    return {
        "symbol": symbol,
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "swing_win_rate": round(swing_wr, 1),
        "fast_win_rate": round(fast_wr, 1),
        "avg_hours_to_tp": round(avg_hours, 1)
    }

def main():
    symbols = get_liquid_symbols()
    print(f"Scanning {len(symbols)} futures coins across entire Binance 4H crypto market...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        future_to_sym = {executor.submit(fetch_4h_klines, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym, candles = future.result()
            if candles:
                res = analyze_coin(sym, candles)
                if res:
                    results.append(res)
                    
    print(f"Total valid analyzed coins: {len(results)}\n")
    
    # Sort by Win Rate (Highest Overall Win-Rate Category 1)
    by_wr = sorted(results, key=lambda x: (x["win_rate"], x["total_trades"]), reverse=True)
    
    # Sort by Speed & Quick Bounce (Category 2: Fastest Average Time to TP with high win rate)
    by_speed = sorted([r for r in results if r["win_rate"] >= 75.0], key=lambda x: (x["avg_hours_to_tp"], -x["win_rate"]))
    
    print("=== CATEGORY 1: TOP 20 HIGHEST WIN-RATE SMC SWING COINS ===")
    print(f"{'Symbol':<14} | {'Win Rate':<8} | {'Trades':<8} | {'Wins/Loss':<10} | {'Avg TP Time':<12} | {'Rating':<10}")
    print("-" * 75)
    for c in by_wr[:20]:
        star = "🌟 Tier-1 Elite" if c["win_rate"] >= 80 else "⭐ Tier-1 High"
        print(f"{c['symbol']:<14} | {c['win_rate']:>6}% | {c['total_trades']:>6} | {c['wins']}/{c['losses']:<7} | {c['avg_hours_to_tp']:>5} hrs   | {star}")
        
    print("\n=== CATEGORY 2: TOP 20 QUICK PROFIT / FAST BOUNCE SNIPERS (Fastest Time to TP) ===")
    print(f"{'Symbol':<14} | {'Win Rate':<8} | {'Avg TP Time':<14} | {'Fast Bounce WR':<15} | {'Trades':<8}")
    print("-" * 75)
    for c in by_speed[:20]:
        print(f"{c['symbol']:<14} | {c['win_rate']:>6}% | {c['avg_hours_to_tp']:>5} hrs (FAST) | {c['fast_win_rate']:>5}% in <8h   | {c['total_trades']:>6}")
        
    with open("full_market_scan_summary.json", "w") as f:
        json.dump({"top_wr": by_wr[:30], "top_speed": by_speed[:25]}, f, indent=2)

if __name__ == "__main__":
    main()
