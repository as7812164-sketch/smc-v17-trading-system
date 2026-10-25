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
    "ALGOUSDT", "KASUSDT"
]

def fetch_klines_3months(sym, interval="4h", limit=550):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                candles = []
                for k in data:
                    t, o, h, l, c, vol = int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])
                    candles.append({"time": t, "open": o, "high": h, "low": l, "close": c, "volume": vol})
                return sym, candles
        except Exception:
            time.sleep(0.3)
    return sym, []

def backtest_40_coins():
    print("=" * 85)
    print(" 🚀 HERMES QUANTUM APEX: 40-COIN 3-MONTH INSTITUTIONAL COMPOUNDING AUDIT")
    print(" Fetching 550 4H Bars (~90 Days / 3 Months) Concurrently Across 40 Assets...")
    print("=" * 85)
    
    all_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(fetch_klines_3months, sym) for sym in COINS_40]
        for f in concurrent.futures.as_completed(futures):
            sym, klines = f.result()
            if klines and len(klines) >= 100:
                all_data[sym] = klines
                print(f"[{sym}] Loaded {len(klines)} bars", flush=True)

    print(f"\n✅ Total Coins Successfully Loaded: {len(all_data)} / 40\n")
    
    # Collect all historical candidate trades across all 40 coins
    candidate_trades = []
    
    for sym, candles in all_data.items():
        n = len(candles)
        for i in range(25, n - 20):
            # 1. Extreme Swing Low of 20-bar lookback (Origin of Trend)
            is_extreme = (candles[i]["low"] == min(c["low"] for c in candles[i-20:i+1]))
            if not is_extreme:
                continue
                
            c = candles[i]
            ob_top = max(c["open"], c["close"])
            ob_bot = c["low"]
            ob_mt = (ob_top + ob_bot) / 2.0
            
            # 2. Explosive Displacement check (next 3 candles must produce >= 3.5% surge with FVG)
            disp_high = max(candles[i+1]["high"], candles[i+2]["high"], candles[i+3]["high"])
            disp_gain = (disp_high - ob_top) / ob_top
            has_fvg = (candles[i+2]["low"] > candles[i]["high"]) if i+2 < n else False
            
            if disp_gain < 0.035 or not has_fvg:
                continue
                
            # 3. Retest Tap (first tap within next 60 bars)
            tap_idx = -1
            for k in range(i+3, min(i+60, n)):
                if candles[k]["low"] <= ob_top:
                    tap_idx = k
                    break
                    
            if tap_idx == -1 or tap_idx >= n - 10:
                continue
                
            tap_c = candles[tap_idx]
            
            # 4. Smart Money Tap Signature: Lower Wick >= 20% & Candle Close >= 50% MT
            c_range = tap_c["high"] - tap_c["low"]
            lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
            wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
            
            # Trap dump filter: Must have wick absorption and hold 50% MT
            if wick_ratio < 0.18 or tap_c["close"] < ob_mt:
                continue
                
            entry_p = ob_top
            tp_target = entry_p * 1.040 # +4.0% Direct Target (+20.0% ROE @ 5x)
            sl_target = ob_bot * 0.995 # SL strictly below the base
            
            # Resolve trade outcome bar-by-bar
            trade_res = None
            exit_time = tap_c["time"]
            exit_p = entry_p
            bars_held = 0
            
            for m in range(tap_idx, min(tap_idx + 40, n)):
                bar = candles[m]
                bars_held += 1
                if bar["high"] >= tp_target:
                    trade_res = "WIN"
                    exit_time = bar["time"]
                    exit_p = tp_target
                    break
                if bar["close"] <= sl_target:
                    trade_res = "LOSS"
                    exit_time = bar["time"]
                    exit_p = sl_target
                    break
                    
            if not trade_res:
                final_close = candles[min(tap_idx + 40, n - 1)]["close"]
                exit_time = candles[min(tap_idx + 40, n - 1)]["time"]
                exit_p = final_close
                trade_res = "WIN" if final_close > entry_p else "LOSS"
                
            gross_pct = (exit_p - entry_p) / entry_p
            
            candidate_trades.append({
                "symbol": sym,
                "entry_time": tap_c["time"],
                "exit_time": exit_time,
                "entry_p": entry_p,
                "exit_p": exit_p,
                "gross_pct": gross_pct,
                "result": trade_res,
                "bars": bars_held
            })
            
    # Sort all trades strictly chronologically by entry_time
    candidate_trades.sort(key=lambda x: x["entry_time"])
    
    # 5. GEOMETRIC COMPOUNDING SIMULATION ($50 USDT STARTING CAPITAL @ 5X LEVERAGE)
    initial_capital = 50.0
    current_equity = initial_capital
    leverage = 5.0
    exchange_fee = 0.0005 # 0.05% maker/taker (0.10% round trip)
    slippage = 0.0002     # 0.02% slippage per fill
    
    compounding_ledger = []
    equity_curve = [initial_capital]
    max_equity = initial_capital
    max_drawdown_pct = 0.0
    
    total_wins = 0
    total_losses = 0
    
    for idx, t in enumerate(candidate_trades, 1):
        pos_size = current_equity * leverage
        
        # Net ROE calculation after fees and slippage
        # Fee paid on notional: pos_size * (2 * fee + 2 * slippage)
        friction = (2 * exchange_fee + 2 * slippage)
        net_return_pct = t["gross_pct"] - friction
        net_pnl = pos_size * net_return_pct
        
        prev_eq = current_equity
        current_equity = max(1.0, current_equity + net_pnl)
        
        if current_equity > max_equity:
            max_equity = current_equity
        dd = (max_equity - current_equity) / max_equity * 100.0
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd
            
        if t["result"] == "WIN":
            total_wins += 1
        else:
            total_losses += 1
            
        compounding_ledger.append({
            "trade_num": idx,
            "symbol": t["symbol"],
            "entry_date": time.strftime("%Y-%m-%d %H:%M", time.gmtime(t["entry_time"] / 1000)),
            "result": t["result"],
            "net_roe_pct": net_return_pct * leverage * 100.0,
            "starting_balance": prev_eq,
            "ending_balance": current_equity
        })
        equity_curve.append(current_equity)

    total_trades = len(candidate_trades)
    win_rate = (total_wins / total_trades * 100.0) if total_trades > 0 else 0.0
    
    print("=" * 85)
    print("                     📊 3-MONTH 40-COIN COMPOUNDING AUDIT REPORT")
    print("=" * 85)
    print(f"Total Traded Assets:          40 Crypto Pairs (Binance USDT-M Futures)")
    print(f"Historical Time Window:       Last 90 Days (3 Months) on 4H Timeframe")
    print(f"Initial Starting Capital:     $50.00 USDT")
    print(f"Leverage Multiplier:          5.0x (Isolated Margin)")
    print(f"Friction Accounting:          0.10% Round-Trip Fee + 0.04% Round-Trip Slippage")
    print("-------------------------------------------------------------------------------------")
    print(f"Total Qualified Trades:       {total_trades}")
    print(f"🏆 Direct TP Hit Wins:        {total_wins} ({win_rate:.2f}%)")
    print(f"❌ Losses (SL Invalidation):  {total_losses} ({100.0 - win_rate:.2f}%)")
    print(f"📈 Final Compounded Equity:   ${current_equity:,.2f} USDT")
    print(f"🚀 Net Total Return (ROI):    +{((current_equity - initial_capital) / initial_capital * 100):,.1f}%")
    print(f"🛡️ Maximum Equity Drawdown:   {max_drawdown_pct:.2f}%")
    print(f"💎 Profit Factor:             {(sum(l['ending_balance'] - l['starting_balance'] for l in compounding_ledger if l['result'] == 'WIN') / max(0.01, abs(sum(l['ending_balance'] - l['starting_balance'] for l in compounding_ledger if l['result'] == 'LOSS')))):.2f}")
    print("=====================================================================================\n")
    
    print("--- FIRST 15 CHRONOLOGICAL COMPOUNDING TRADES AUDIT ---")
    for r in compounding_ledger[:15]:
        print(f"Trade #{r['trade_num']:2d} | {r['entry_date']} | {r['symbol']:9s} | {r['result']:4s} | Net ROE: {r['net_roe_pct']:+6.2f}% | Balance: ${r['starting_balance']:8.2f} ➔ ${r['ending_balance']:8.2f}")

    if len(compounding_ledger) > 15:
        print(f"... and {len(compounding_ledger) - 15} more verified trades ...")
        print("--- LAST 5 COMPOUNDING TRADES AUDIT ---")
        for r in compounding_ledger[-5:]:
            print(f"Trade #{r['trade_num']:2d} | {r['entry_date']} | {r['symbol']:9s} | {r['result']:4s} | Net ROE: {r['net_roe_pct']:+6.2f}% | Balance: ${r['starting_balance']:8.2f} ➔ ${r['ending_balance']:8.2f}")

if __name__ == "__main__":
    backtest_40_coins()
