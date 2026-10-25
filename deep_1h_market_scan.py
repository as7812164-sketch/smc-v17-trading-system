import urllib.request
import json
import time
import sys
import concurrent.futures
from config import DEFAULT_COINS, TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_target_symbols():
    symbols = list(set(DEFAULT_COINS + TIER1_COINS))
    extras = [
        "SOLUSDT", "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT",
        "AVAXUSDT", "LINKUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LTCUSDT", "DOTUSDT",
        "UNIUSDT", "INJUSDT", "ARBUSDT", "OPUSDT", "RENDERUSDT", "WIFUSDT", "FILUSDT",
        "ATOMUSDT", "ENAUSDT", "STXUSDT", "SEIUSDT", "AAVEUSDT", "GALAUSDT", "JUPUSDT",
        "PYTHUSDT", "RUNEUSDT", "SANDUSDT", "THETAUSDT", "DYDXUSDT", "PENDLEUSDT", "ZECUSDT",
        "ONEUSDT", "CRVUSDT", "ETHFIUSDT", "ONGUSDT", "LDOUSDT", "PEOPLEUSDT", "AEROUSDT",
        "SUSDT", "XLMUSDT", "VETUSDT", "FETUSDT", "TIAUSDT", "BLURUSDT", "EGLDUSDT",
        "FLOWUSDT", "CHZUSDT", "WLDUSDT", "ALGOUSDT", "AXSUSDT", "MANAUSDT", "TRXUSDT"
    ]
    cleaned = []
    for s in list(set(symbols + extras)):
        if s.startswith("1000"):
            s = s.replace("1000", "")
        cleaned.append(s)
    return list(set(cleaned))

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

def analyze_1h_coin(symbol, candles):
    if not candles or len(candles) < 150:
        return None
        
    trades = []
    
    # 1H SMC Indicator Logic:
    # 1. 1H Bullish Expansion: >= +2.5% move within next 8 candles away from OB
    # 2. 1st Boundary Line Touch (Entry = ob_high)
    # 3. Stop Loss: ob_low * 0.995 (below origin candle low)
    # 4. Quick Scalp TP: +1.5% price move (+7.5% ROE @ 5x)
    # 5. Swing Scalp TP: +3.0% price move (+15.0% ROE @ 5x)
    
    for i in range(12, len(candles) - 15):
        ob_candle = candles[i]
        ob_high = ob_candle["high"]
        ob_low = ob_candle["low"]
        
        if ob_high <= ob_low or ob_high == 0:
            continue
            
        max_exp = 0
        for f in range(1, 9):
            if i + f < len(candles):
                exp = (candles[i+f]["high"] - ob_high) / ob_high
                if exp > max_exp:
                    max_exp = exp
                    
        if max_exp < 0.025:
            continue
            
        entry_price = ob_high
        sl_price = ob_low * 0.995
        quick_tp = entry_price * 1.015 # +1.5% move
        swing_tp = entry_price * 1.030 # +3.0% move
        
        entered = False
        entry_bar = -1
        
        for j in range(i + 3, min(i + 50, len(candles))):
            curr = candles[j]
            if not entered:
                if curr["low"] <= entry_price and curr["high"] >= entry_price:
                    entered = True
                    entry_bar = j
                    if curr["low"] <= sl_price:
                        trades.append({"result": "LOSS", "hours": 1, "is_swing": False})
                        break
            else:
                hours_held = j - entry_bar
                if curr["low"] <= sl_price:
                    trades.append({"result": "LOSS", "hours": hours_held, "is_swing": False})
                    break
                elif curr["high"] >= quick_tp:
                    is_sw = curr["high"] >= swing_tp
                    trades.append({"result": "WIN", "hours": hours_held, "is_swing": is_sw})
                    break
                    
    if len(trades) < 10:
        return None
        
    wins = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    total = wins + losses
    win_rate = (wins / total) * 100
    
    win_trades = [t for t in trades if t["result"] == "WIN"]
    avg_hours = sum(t["hours"] for t in win_trades) / len(win_trades) if win_trades else 99
    
    swing_wins = sum(1 for t in trades if t.get("is_swing", False))
    swing_wr = (swing_wins / total) * 100
    
    superfast = sum(1 for t in trades if t["result"] == "WIN" and t["hours"] <= 3)
    superfast_wr = (superfast / total) * 100
    
    return {
        "symbol": symbol,
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "swing_win_rate": round(swing_wr, 1),
        "superfast_win_rate": round(superfast_wr, 1),
        "avg_hours_to_tp": round(avg_hours, 1)
    }

def main():
    symbols = get_target_symbols()
    print(f"[*] Mike AI Agent Hub: Launching 1H Market-Wide Audit on {len(symbols)} Top Coins...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_sym = {executor.submit(fetch_1h_klines, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym, candles = future.result()
            if candles:
                res = analyze_1h_coin(sym, candles)
                if res:
                    results.append(res)
                    
    print(f"[+] 1H Analysis Complete! Evaluated {len(results)} active coins across 1,000 1H candles (~42 days).\n")
    
    by_wr = sorted(results, key=lambda x: (x["win_rate"], x["total_trades"]), reverse=True)
    by_speed = sorted([r for r in results if r["win_rate"] >= 75.0], key=lambda x: (x["avg_hours_to_tp"], -x["win_rate"]))
    
    print("=== 1H TIMEFRAME: TOP 20 HIGHEST WIN-RATE COINS ===")
    print(f"{'Symbol':<14} | {'1H Win Rate':<12} | {'Trades (42d)':<14} | {'W / L':<10} | {'Avg TP Time':<12} | {'Rating':<12}")
    print("-" * 85)
    for c in by_wr[:20]:
        tier = "🌟 Elite 1H" if c["win_rate"] >= 80 else "⭐ High 1H"
        print(f"{c['symbol']:<14} | {c['win_rate']:>8.1f}%   | {c['total_trades']:>8}      | {c['wins']}/{c['losses']:<7} | {c['avg_hours_to_tp']:>5} hrs    | {tier}")
        
    print("\n=== 1H TIMEFRAME: TOP 15 ULTRA-FAST SCALPING SNIPERS (TP in 1 to 3 Hours) ===")
    print(f"{'Symbol':<14} | {'1H Win Rate':<12} | {'Avg TP Time':<12} | {'Instant Bounce (<3h)':<20} | {'Trades':<8}")
    print("-" * 85)
    for c in by_speed[:15]:
        print(f"{c['symbol']:<14} | {c['win_rate']:>8.1f}%   | {c['avg_hours_to_tp']:>5} hrs    | {c['superfast_win_rate']:>6.1f}% in <3h        | {c['total_trades']:>6}")
        
    total_trades_all = sum(r["total_trades"] for r in results)
    total_wins_all = sum(r["wins"] for r in results)
    overall_wr = (total_wins_all / total_trades_all * 100) if total_trades_all else 0
    
    print("\n=======================================================")
    print("      MIKE AI AGENT 1H TIMEFRAME AUDIT SUMMARY")
    print("=======================================================")
    print(f"Total Coins Evaluated       : {len(results)}")
    print(f"Total 1H Trades (42 Days)   : {total_trades_all}")
    print(f"Total 1H Winning Trades     : {total_wins_all} Wins")
    print(f"Overall Market 1H Win Rate  : {overall_wr:.1f}%")
    print(f"Average Trades per Day      : {total_trades_all / 42:.1f} trades / day across market")
    print("=======================================================")

if __name__ == "__main__":
    main()
