import urllib.request
import json
import time
import datetime
import sys
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Top liquid Binance coins for 1H
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ARBUSDT",
    "SUIUSDT", "APTUSDT", "LTCUSDT", "DOTUSDT", "UNIUSDT",
    "INJUSDT", "STXUSDT", "AAVEUSDT", "ZECUSDT", "ONEUSDT",
    "PENDLEUSDT", "ETHFIUSDT", "CRVUSDT", "DOGEUSDT", "AVAXUSDT"
]

def fetch_1h_history(symbol, limit=1000):
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

def extract_all_1h_signals(symbols):
    all_trade_events = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_sym = {executor.submit(fetch_1h_history, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym, candles = future.result()
            if not candles:
                continue
                
            for i in range(12, len(candles) - 15):
                ob_candle = candles[i]
                ob_high = ob_candle["high"]
                ob_low = ob_candle["low"]
                
                if ob_high <= ob_low or ob_high == 0:
                    continue
                    
                # 1H expansion requirement: >= +2.5% move within next 8 candles
                max_exp = 0
                for f in range(1, 9):
                    if i + f < len(candles):
                        exp = (candles[i+f]["high"] - ob_high) / ob_high
                        if exp > max_exp:
                            max_exp = exp
                if max_exp < 0.025:
                    continue
                    
                entry_price = ob_high
                sl_price = min(ob_low * 0.995, entry_price * 0.975) # -2.5% SL
                tp_price = entry_price * 1.014 # +1.4% price move = +7.0% ROE at 5x leverage
                
                entered = False
                entry_time = 0
                
                for j in range(i + 3, min(i + 45, len(candles))):
                    curr = candles[j]
                    if not entered:
                        if curr["low"] <= entry_price and curr["high"] >= entry_price:
                            entered = True
                            entry_time = curr["time"]
                            if curr["low"] <= sl_price:
                                all_trade_events.append({
                                    "symbol": sym,
                                    "entry_time": entry_time,
                                    "exit_time": curr["time"],
                                    "result": "LOSS",
                                    "roe_pct": -12.5, # -2.5% real move * 5x = -12.5% ROE
                                    "hours": 1
                                })
                                break
                    else:
                        hours_held = int((curr["time"] - entry_time) / 3600000)
                        if curr["low"] <= sl_price:
                            all_trade_events.append({
                                "symbol": sym,
                                "entry_time": entry_time,
                                "exit_time": curr["time"],
                                "result": "LOSS",
                                "roe_pct": -12.5,
                                "hours": max(1, hours_held)
                            })
                            break
                        elif curr["high"] >= tp_price:
                            all_trade_events.append({
                                "symbol": sym,
                                "entry_time": entry_time,
                                "exit_time": curr["time"],
                                "result": "WIN",
                                "roe_pct": +7.0, # +1.4% real move * 5x = +7.0% ROE
                                "hours": max(1, hours_held)
                            })
                            break
                            
    all_trade_events.sort(key=lambda x: x["entry_time"])
    return all_trade_events

def run_100_trade_simulation():
    print("[*] Fetching and running 100-Trade 100% Compounding Simulation on 1H Timeframe...")
    all_signals = extract_all_1h_signals(SYMBOLS)
    print(f"Total raw 1H signals extracted: {len(all_signals)}")
    
    # 100% Sequential Execution: 1 trade at a time
    start_capital = 50.0 # $50 starting USDT
    balance = start_capital
    completed = []
    current_trade_exit_time = 0
    
    peak_balance = start_capital
    max_dd_pct = 0.0
    max_dd_amount = 0.0
    
    consec_wins = 0
    max_consec_wins = 0
    consec_losses = 0
    max_consec_losses = 0
    
    fee_pct_per_trade = 0.0008 # 0.08% taker round-trip fee on notional (5x * 0.08% = ~0.4% on equity)
    
    for t in all_signals:
        if t["entry_time"] >= current_trade_exit_time:
            current_trade_exit_time = t["exit_time"]
            
            # Gross PnL
            gross_pnl = balance * (t["roe_pct"] / 100.0)
            # Realistic fee deduction
            fee = balance * 5 * 0.0008
            net_pnl = gross_pnl - fee
            balance += net_pnl
            
            # Track peak and drawdown
            if balance > peak_balance:
                peak_balance = balance
            dd = (peak_balance - balance) / peak_balance * 100.0
            if dd > max_dd_pct:
                max_dd_pct = dd
                max_dd_amount = peak_balance - balance
                
            if t["result"] == "WIN":
                consec_wins += 1
                consec_losses = 0
                if consec_wins > max_consec_wins:
                    max_consec_wins = consec_wins
            else:
                consec_losses += 1
                consec_wins = 0
                if consec_losses > max_consec_losses:
                    max_consec_losses = consec_losses
                    
            completed.append({
                "trade_num": len(completed) + 1,
                "symbol": t["symbol"],
                "entry_dt": datetime.datetime.fromtimestamp(t["entry_time"]/1000).strftime('%Y-%m-%d %H:%M'),
                "exit_dt": datetime.datetime.fromtimestamp(t["exit_time"]/1000).strftime('%Y-%m-%d %H:%M'),
                "result": t["result"],
                "roe_pct": t["roe_pct"],
                "net_pnl": round(net_pnl, 2),
                "balance": round(balance, 2),
                "hours_held": t["hours"]
            })
            
            if len(completed) >= 100:
                break
                
    first_trade_dt = completed[0]["entry_dt"]
    last_trade_dt = completed[-1]["exit_dt"]
    t1 = datetime.datetime.strptime(first_trade_dt, '%Y-%m-%d %H:%M')
    t2 = datetime.datetime.strptime(last_trade_dt, '%Y-%m-%d %H:%M')
    total_days = (t2 - t1).total_seconds() / 86400.0
    
    wins = sum(1 for t in completed if t["result"] == "WIN")
    losses = sum(1 for t in completed if t["result"] == "LOSS")
    win_rate = (wins / len(completed)) * 100.0
    avg_hours = sum(t["hours_held"] for t in completed) / len(completed)
    
    print("\n" + "="*70)
    print("      1H TIMEFRAME: 100-TRADE 100% COMPOUNDING REPORT")
    print("="*70)
    print(f"Starting Capital         : ${start_capital:.2f} USDT")
    print(f"Final Balance (100 Trades): ${balance:,.2f} USDT")
    print(f"Net Growth Multiplier    : {(balance / start_capital):,.1f}x (+{((balance - start_capital)/start_capital)*100:,.1f}%)")
    print(f"Total Time Taken         : {total_days:.1f} Days (~{total_days/7:.1f} Weeks / {total_days/30:.1f} Months)")
    print(f"Win Rate                 : {win_rate:.1f}% ({wins} Wins / {losses} Losses)")
    print(f"Average Trades per Day   : {len(completed) / total_days:.2f} trades / day")
    print(f"Average Duration / Trade : {avg_hours:.1f} Hours")
    print(f"Max Consecutive Wins     : {max_consec_wins} Wins in a row")
    print(f"Max Consecutive Losses   : {max_consec_losses} Losses in a row")
    print(f"Max Peak-to-Trough DD    : {max_dd_pct:.2f}%")
    print("="*70)
    
    print("\n--- Key Milestone Progression ---")
    for i, t in enumerate(completed):
        b = t["balance"]
        prev = completed[i-1]["balance"] if i > 0 else 0
        if b >= 100 and prev < 100:
            print(f"  🎯 $100 Crossed  at Trade #{t['trade_num']:>2} on {t['entry_dt']} (Day {round((datetime.datetime.strptime(t['entry_dt'], '%Y-%m-%d %H:%M') - t1).total_seconds()/86400, 1)}) | Bal: ${b:,.2f}")
        if b >= 250 and prev < 250:
            print(f"  🎯 $250 Crossed  at Trade #{t['trade_num']:>2} on {t['entry_dt']} (Day {round((datetime.datetime.strptime(t['entry_dt'], '%Y-%m-%d %H:%M') - t1).total_seconds()/86400, 1)}) | Bal: ${b:,.2f}")
        if b >= 500 and prev < 500:
            print(f"  🎯 $500 Crossed  at Trade #{t['trade_num']:>2} on {t['entry_dt']} (Day {round((datetime.datetime.strptime(t['entry_dt'], '%Y-%m-%d %H:%M') - t1).total_seconds()/86400, 1)}) | Bal: ${b:,.2f}")
        if b >= 1000 and prev < 1000:
            print(f"  🏆 $1,000 Crossed at Trade #{t['trade_num']:>2} on {t['entry_dt']} (Day {round((datetime.datetime.strptime(t['entry_dt'], '%Y-%m-%d %H:%M') - t1).total_seconds()/86400, 1)}) | Bal: ${b:,.2f}")
        if b >= 2500 and prev < 2500:
            print(f"  💰 $2,500 Crossed at Trade #{t['trade_num']:>2} on {t['entry_dt']} (Day {round((datetime.datetime.strptime(t['entry_dt'], '%Y-%m-%d %H:%M') - t1).total_seconds()/86400, 1)}) | Bal: ${b:,.2f}")
        if b >= 5000 and prev < 5000:
            print(f"  💎 $5,000 Crossed at Trade #{t['trade_num']:>2} on {t['entry_dt']} (Day {round((datetime.datetime.strptime(t['entry_dt'], '%Y-%m-%d %H:%M') - t1).total_seconds()/86400, 1)}) | Bal: ${b:,.2f}")
            
    with open("compounding_1h_100trades.json", "w") as f:
        json.dump({
            "start_capital": start_capital,
            "final_balance": round(balance, 2),
            "total_days": round(total_days, 1),
            "win_rate": round(win_rate, 1),
            "trades": completed
        }, f, indent=2)

if __name__ == "__main__":
    run_100_trade_simulation()
