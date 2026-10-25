import urllib.request
import json
import time
import datetime
import concurrent.futures

TIER1_COINS = [
    "ARBUSDT", "STXUSDT", "LTCUSDT", "ZECUSDT", "ONEUSDT",
    "PENDLEUSDT", "ETHFIUSDT", "UNIUSDT", "CRVUSDT", "1000BONKUSDT",
    "SUIUSDT", "JUPUSDT", "1000PEPEUSDT", "AAVEUSDT", "AVAXUSDT",
    "ETHUSDT", "BNBUSDT", "DOTUSDT", "SOLUSDT", "DOGEUSDT"
]

def fetch_4h_history(symbol, limit=700):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=4h&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
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
        return symbol, None

def extract_all_signals(symbols):
    all_trade_events = []
    now_ms = int(time.time() * 1000)
    cutoff_ms = now_ms - (100 * 24 * 3600 * 1000) # Past 100 days
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_sym = {executor.submit(fetch_4h_history, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym, candles = future.result()
            if not candles:
                continue
                
            for i in range(10, len(candles) - 10):
                ob_candle = candles[i]
                ob_high = ob_candle["high"]
                ob_low = ob_candle["low"]
                
                if ob_high <= ob_low or ob_high == 0:
                    continue
                    
                max_exp = 0
                for f in range(1, 6):
                    if i + f < len(candles):
                        exp = (candles[i+f]["high"] - ob_high) / ob_high
                        if exp > max_exp:
                            max_exp = exp
                if max_exp < 0.06:
                    continue
                    
                entry_price = ob_high
                sl_price = ob_low * 0.992
                tp_price = entry_price * 1.025 # +2.5% move = +12.5% ROE @ 5x
                
                entered = False
                entry_time = 0
                
                for j in range(i + 4, min(i + 45, len(candles))):
                    curr = candles[j]
                    if not entered:
                        if curr["low"] <= entry_price and curr["high"] >= entry_price:
                            if curr["time"] >= cutoff_ms:
                                entered = True
                                entry_time = curr["time"]
                                if curr["low"] <= sl_price:
                                    all_trade_events.append({
                                        "symbol": sym,
                                        "entry_time": entry_time,
                                        "exit_time": curr["time"],
                                        "result": "LOSS",
                                        "roe_pct": -20.0
                                    })
                                    break
                    else:
                        if curr["low"] <= sl_price:
                            all_trade_events.append({
                                "symbol": sym,
                                "entry_time": entry_time,
                                "exit_time": curr["time"],
                                "result": "LOSS",
                                "roe_pct": -20.0
                            })
                            break
                        elif curr["high"] >= tp_price:
                            all_trade_events.append({
                                "symbol": sym,
                                "entry_time": entry_time,
                                "exit_time": curr["time"],
                                "result": "WIN",
                                "roe_pct": +12.5
                            })
                            break
                            
    all_trade_events.sort(key=lambda x: x["entry_time"])
    return all_trade_events

def main():
    trades = extract_all_signals(TIER1_COINS)
    balance = 100.0
    initial_balance = 100.0
    completed_trades = []
    current_trade_exit_time = 0
    
    for t in trades:
        if t["entry_time"] >= current_trade_exit_time:
            current_trade_exit_time = t["exit_time"]
            profit_loss = balance * (t["roe_pct"] / 100.0)
            balance += profit_loss
            completed_trades.append({
                "symbol": t["symbol"],
                "date": datetime.datetime.fromtimestamp(t["entry_time"]/1000).strftime('%Y-%m-%d %H:%M'),
                "result": t["result"],
                "pnl_usd": round(profit_loss, 2),
                "new_balance": round(balance, 2)
            })
            
    wins = sum(1 for t in completed_trades if t["result"] == "WIN")
    losses = sum(1 for t in completed_trades if t["result"] == "LOSS")
    win_rate = (wins / len(completed_trades) * 100) if completed_trades else 0
    
    with open("compounding_100days_result.json", "w") as f:
        json.dump({
            "initial_balance": 100.0,
            "final_balance": round(balance, 2),
            "total_trades": len(completed_trades),
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "trades": completed_trades
        }, f, indent=2)
        
    print(f"Total Sequential Trades: {len(completed_trades)}")
    print(f"Wins: {wins}, Losses: {losses}, Win Rate: {win_rate:.1f}%")
    print(f"Final Balance: ${balance:,.2f}")

if __name__ == "__main__":
    main()
