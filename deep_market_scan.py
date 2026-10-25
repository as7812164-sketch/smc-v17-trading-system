import urllib.request
import json
import time
import concurrent.futures
from datetime import datetime

# Fetch 24h ticker to sort by volume
def get_liquid_symbols():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    
    # Filter USDT pairs with > 15M 24h volume
    pairs = []
    for d in data:
        sym = d["symbol"]
        if sym.endswith("USDT"):
            vol = float(d.get("quoteVolume", 0))
            if vol >= 15_000_000: # 15 Million USDT daily volume
                pairs.append((sym, vol))
    
    pairs.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in pairs[:180]] # Top 180 liquid pairs

def fetch_4h_klines(symbol, limit=600):
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

def analyze_buy_strategy(symbol, candles):
    if not candles or len(candles) < 80:
        return None
        
    trades = []
    
    # SMC V17 Indicator Logic for BUY (Demand Order Block)
    # 1. Bullish expansion >= 6.5% over 1 to 4 candles
    # 2. Origin candle high is the 1st Boundary Line (Entry)
    # 3. Origin candle low is the SL (Invalidation)
    
    for i in range(15, len(candles) - 15):
        # Look for expansion starting from candle i
        ob_candle = candles[i]
        ob_high = ob_candle["high"] # 1st Boundary Line (Top of Green Box)
        ob_low = ob_candle["low"]   # Box Bottom / SL Base
        
        if ob_high <= ob_low or ob_high == 0:
            continue
            
        # Check if candle i is followed by an expansion of >= 6.5% within 4 candles
        max_expansion = 0
        for f in range(1, 5):
            if i + f < len(candles):
                exp = (candles[i+f]["high"] - ob_high) / ob_high
                if exp > max_expansion:
                    max_expansion = exp
                    
        if max_expansion < 0.065: # Needs >= 6.5% bullish expansion to qualify as True Origin OB
            continue
            
        # We have a valid True Origin Demand Box: [ob_low, ob_high]
        # Now track future candles for a pullback touching the 1st boundary line (ob_high)
        entry_price = ob_high
        sl_price = ob_low * 0.995 # SL just below the origin box bottom
        quick_tp_price = entry_price * 1.02 # Quick Profit: +2.0% price move (+10% ROE at 5x)
        swing_tp_price = entry_price * 1.06 # Swing Profit: +6.0% price move (+30% ROE at 5x)
        
        entered = False
        entry_bar = -1
        
        # Look ahead for up to 35 candles (~6 days)
        for j in range(i + 4, min(i + 45, len(candles))):
            curr = candles[j]
            
            if not entered:
                # 1st boundary line tap (touching top of demand box)
                if curr["low"] <= entry_price and curr["high"] >= entry_price:
                    entered = True
                    entry_bar = j
                    # Check if candle immediately crashed below SL
                    if curr["low"] <= sl_price:
                        # Loss on entry candle
                        trades.append({
                            "type": "BUY",
                            "entry_bar": entry_bar,
                            "entry_price": entry_price,
                            "exit_result": "LOSS",
                            "bars_to_tp": 999,
                            "quick_hit": False,
                            "swing_hit": False
                        })
                        break
            else:
                # Trade is active
                bars_held = j - entry_bar
                
                # Check SL hit
                if curr["low"] <= sl_price:
                    trades.append({
                        "type": "BUY",
                        "entry_bar": entry_bar,
                        "entry_price": entry_price,
                        "exit_result": "LOSS",
                        "bars_to_tp": 999,
                        "quick_hit": False,
                        "swing_hit": False
                    })
                    break
                    
                # Check Quick TP hit (+2% move / +10% ROE)
                quick_hit = curr["high"] >= quick_tp_price
                # Check Swing TP hit (+6% move / +30% ROE)
                swing_hit = curr["high"] >= swing_tp_price
                
                if quick_hit or swing_hit:
                    trades.append({
                        "type": "BUY",
                        "entry_bar": entry_bar,
                        "entry_price": entry_price,
                        "exit_result": "WIN",
                        "bars_to_tp": bars_held,
                        "quick_hit": quick_hit,
                        "swing_hit": swing_hit
                    })
                    break
                    
    if len(trades) < 6: # Need statistically meaningful sample size
        return None
        
    wins = sum(1 for t in trades if t["exit_result"] == "WIN")
    losses = sum(1 for t in trades if t["exit_result"] == "LOSS")
    total = wins + losses
    win_rate = (wins / total) * 100 if total > 0 else 0
    
    # Calculate Quick Profit metrics (bars to TP)
    win_trades = [t for t in trades if t["exit_result"] == "WIN"]
    avg_bars_to_tp = sum(t["bars_to_tp"] for t in win_trades) / len(win_trades) if win_trades else 999
    quick_wins = sum(1 for t in trades if t.get("quick_hit", False) and t["exit_result"] == "WIN")
    quick_wr = (quick_wins / total) * 100 if total > 0 else 0
    
    # Average hours to profit (each 4h bar = 4 hours)
    avg_hours_to_tp = avg_bars_to_tp * 4.0
    
    return {
        "symbol": symbol,
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "quick_win_rate": round(quick_wr, 1),
        "avg_bars_to_tp": round(avg_bars_to_tp, 1),
        "avg_hours_to_tp": round(avg_hours_to_tp, 1)
    }

def run_market_scan():
    symbols = get_liquid_symbols()
    print(f"[*] Scanning {len(symbols)} high-volume Crypto Futures coins across Binance 4H market...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_sym = {executor.submit(fetch_4h_klines, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym, candles = future.result()
            if candles:
                res = analyze_buy_strategy(sym, candles)
                if res:
                    results.append(res)
                    
    print(f"[+] Scan complete! Analyzed {len(results)} valid coins.\n")
    
    # Filter 90%+ Win Rate
    elite_90 = [r for r in results if r["win_rate"] >= 89.9]
    
    # Category 1: Highest Win-rate Swing Champions (Sorted by WR desc, then total trades)
    cat1_swing = sorted(elite_90, key=lambda x: (x["win_rate"], x["total_trades"]), reverse=True)
    
    # Category 2: Quick Profit / High Velocity Scalpers (90%+ WR, Sorted by fastest avg_hours_to_tp)
    cat2_quick = sorted([r for r in elite_90 if r["avg_hours_to_tp"] <= 12.0], key=lambda x: (x["avg_hours_to_tp"], -x["win_rate"]))
    if not cat2_quick:
        cat2_quick = sorted(elite_90, key=lambda x: x["avg_hours_to_tp"])[:15]
        
    print("=== CATEGORY 1: 90%+ WIN-RATE SMC SWING CHAMPIONS ===")
    for c in cat1_swing[:20]:
        print(f"{c['symbol']:<14} | WR: {c['win_rate']:>5}% | Trades: {c['total_trades']:>2} (W:{c['wins']} L:{c['losses']}) | Avg Time to TP: {c['avg_hours_to_tp']} hrs")
        
    print("\n=== CATEGORY 2: QUICK PROFIT / FAST BOUNCE SNIPERS (90%+ WR & Fastest TP) ===")
    for c in cat2_quick[:20]:
        print(f"{c['symbol']:<14} | WR: {c['win_rate']:>5}% | Avg Time to TP: {c['avg_hours_to_tp']:>4} hrs | Trades: {c['total_trades']:>2} | Quick WR: {c['quick_win_rate']}%")

    # Save to json for reference
    with open("market_scan_90wr_results.json", "w") as f:
        json.dump({"category1_swing": cat1_swing, "category2_quick": cat2_quick, "all_elite": elite_90}, f, indent=2)

if __name__ == "__main__":
    run_market_scan()
