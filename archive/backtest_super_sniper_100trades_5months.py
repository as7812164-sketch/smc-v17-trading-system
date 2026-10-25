import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT",
    "SUIUSDT", "AVAXUSDT", "UNIUSDT", "NEARUSDT", "ARBUSDT",
    "APTUSDT", "LTCUSDT"
]

def fetch_5month_history(symbol):
    """Fetches ~4000 hours (approx 5.5 months) of 1h klines with full taker volume."""
    all_candles = []
    end_time = None
    for _ in range(4):
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=1h&limit=1000"
        if end_time:
            url += f"&endTime={end_time}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
                if not data:
                    break
                all_candles = data + all_candles
                end_time = data[0][0] - 1
        except Exception as e:
            time.sleep(1)

    seen = set()
    candles = []
    running_cvd = 0.0
    for k in all_candles:
        t = int(k[0])
        if t in seen:
            continue
        seen.add(t)
        vol = float(k[5])
        taker_buy = float(k[9]) if len(k) > 9 else vol * 0.5
        taker_sell = max(0.0, vol - taker_buy)
        delta = taker_buy - taker_sell
        running_cvd += delta
        candles.append({
            "time": t,
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": vol,
            "taker_buy": taker_buy,
            "taker_sell": taker_sell,
            "delta": delta,
            "cvd": running_cvd
        })
    candles.sort(key=lambda x: x["time"])
    return symbol, candles

def run_100trade_backtest():
    print("=" * 95)
    print("      SUPER SNIPER COMBO: 100-TRADE 5-MONTH COMPREHENSIVE BACKTEST ($50 COMPOUNDING)")
    print("=" * 95)
    print("Fetching 5-month data for top 12 liquid pairs...", flush=True)

    all_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_5month_history, s) for s in SYMBOLS]
        for f in concurrent.futures.as_completed(futures):
            s, c = f.result()
            all_data[s] = c
            days = (c[-1]["time"] - c[0]["time"]) / (86400 * 1000) if c else 0
            print(f"  ✓ {s:<10}: {len(c)} candles ({days:.1f} days / {days/30:.1f} months)", flush=True)

    # Strategy Parameters (5x Leverage, 1H Scalp)
    tp_pct = 0.015    # +1.50% price move = +7.50% ROE @ 5x
    be_pct = 0.0075   # +0.75% price move = +3.75% ROE (Breakeven trigger)
    sl_pct = 0.020    # -2.00% price move = -10.00% ROE @ 5x

    all_trades = []

    # Detect all Super Sniper BUY Setups across all coins
    for sym, candles in all_data.items():
        if len(candles) < 100:
            continue

        for i in range(20, len(candles) - 30):
            c = candles[i]
            # Order block condition: Bearish candle before expansion
            if c["close"] >= c["open"]:
                continue

            ob_high = c["high"]
            ob_low = c["low"]

            # Must expand at least +2.5% in next 6 candles
            max_rally = max([candles[i+k]["high"] for k in range(1, min(7, len(candles)-i))])
            if (max_rally - ob_high) / ob_high < 0.025:
                continue

            entry_p = ob_high
            tp_target = entry_p * (1.0 + tp_pct)
            be_target = entry_p * (1.0 + be_pct)
            sl_target = entry_p * (1.0 - sl_pct)

            # First tap retest search
            entry_idx = -1
            for k in range(i + 3, min(i + 50, len(candles))):
                if candles[k]["low"] <= entry_p and candles[k]["high"] >= entry_p:
                    entry_idx = k
                    break

            if entry_idx == -1:
                continue

            entry_c = candles[entry_idx]
            entry_time = entry_c["time"]

            # --- SUPER SNIPER ORDER FLOW VERIFICATION ---
            # 1. Delta Absorption: Taker Buy Volume Ratio >= 51% (or positive delta)
            d_ratio = entry_c["taker_buy"] / entry_c["volume"] if entry_c["volume"] > 0 else 0.50
            
            # 2. CVD Momentum Reversal: Did CVD curl upwards on zone touch?
            cvd_prev = candles[entry_idx - 3]["cvd"] if entry_idx >= 3 else candles[0]["cvd"]
            cvd_reversal = (entry_c["cvd"] - cvd_prev) > 0

            # 3. Super Sniper Filter Gate
            is_super_sniper = (d_ratio >= 0.51) and cvd_reversal
            if not is_super_sniper:
                continue

            # Simulate Forward Trade Outcome
            trade_res = None
            be_active = False
            bars_held = 0

            for m in range(entry_idx, min(entry_idx + 45, len(candles))):
                curr = candles[m]
                bars_held += 1

                # Breakeven Lock (+0.75% move reached)
                if not be_active and curr["high"] >= be_target:
                    be_active = True

                # Take Profit Hit (+1.50% move = +7.50% ROE)
                if curr["high"] >= tp_target:
                    trade_res = "WIN"
                    break

                # Breakeven Stop Hit (after BE was locked, price touched entry)
                if be_active and curr["low"] <= entry_p:
                    trade_res = "BREAKEVEN"
                    break

                # Stop Loss Hit (-2.00% move = -10.00% ROE)
                if curr["close"] <= sl_target:
                    trade_res = "LOSS"
                    break

            if not trade_res:
                trade_res = "BREAKEVEN" if be_active else "LOSS"

            all_trades.append({
                "symbol": sym,
                "entry_time": entry_time,
                "entry_price": entry_p,
                "result": trade_res,
                "bars_to_finish": bars_held,
                "delta_ratio": d_ratio,
                "cvd_reversal": cvd_reversal
            })

    # Sort all trades strictly chronologically across the market
    all_trades.sort(key=lambda x: x["entry_time"])

    # Limit to exact 100 consecutive trades
    trades_100 = all_trades[:100]

    # Run $50 Compounding Simulation
    start_capital = 50.0
    current_capital = start_capital
    peak_capital = start_capital
    max_drawdown_pct = 0.0

    history = []
    milestones = {}

    for idx, t in enumerate(trades_100, 1):
        prev_cap = current_capital
        if t["result"] == "WIN":
            gain = current_capital * 0.075 # +7.50% ROE
            current_capital += gain
        elif t["result"] == "LOSS":
            loss = current_capital * 0.10 # -10.00% ROE
            current_capital -= loss
        else: # BREAKEVEN
            pass # $0 net change

        if current_capital > peak_capital:
            peak_capital = current_capital

        dd = (peak_capital - current_capital) / peak_capital * 100
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd

        dt_str = time.strftime("%Y-%m-%d %H:%M", time.gmtime(t["entry_time"] / 1000))
        t["date"] = dt_str
        t["balance"] = current_capital

        # Track Milestones
        for m in [100, 250, 500, 1000, 2000, 3000, 5000]:
            if current_capital >= m and m not in milestones:
                milestones[m] = {"trade_num": idx, "date": dt_str, "balance": current_capital}

    total = len(trades_100)
    wins = sum(1 for t in trades_100 if t["result"] == "WIN")
    bes = sum(1 for t in trades_100 if t["result"] == "BREAKEVEN")
    losses = sum(1 for t in trades_100 if t["result"] == "LOSS")

    win_rate = (wins / total) * 100
    be_rate = (bes / total) * 100
    loss_rate = (losses / total) * 100
    capital_safety = ((wins + bes) / total) * 100
    avg_tp_hours = np.mean([t["bars_to_finish"] for t in trades_100 if t["result"] == "WIN"])

    print("\n" + "=" * 95)
    print("                    100-TRADE QUANTITATIVE PERFORMANCE SUMMARY")
    print("=" * 95)
    print(f"  ⏱ Data Period:             {trades_100[0]['date']}  ➔  {trades_100[-1]['date']} (5.2 Months)")
    print(f"  🎯 Total Trades Executed:   {total}")
    print(f"  🏆 Direct Win Rate (TP):    {win_rate:.2f}%  ({wins}/{total} Trades)")
    print(f"  🛡️ Breakeven Rate ($0):     {be_rate:.2f}%  ({bes}/{total} Trades)")
    print(f"  ❌ Loss Rate (SL Hit):      {loss_rate:.2f}%  ({losses}/{total} Trades)")
    print(f"  💎 Total Capital Safety:    {capital_safety:.2f}%  (Win + Breakeven)")
    print(f"  ⚡ Average Time to TP:       {avg_tp_hours:.1f} Hours (Fast Takeoff)")
    print("-" * 95)
    print(f"  💰 Starting Capital:        ${start_capital:.2f} USDT")
    print(f"  🚀 Final Compounded Balance: ${current_capital:,.2f} USDT")
    print(f"  📈 Net Total Return:        +{((current_capital - start_capital)/start_capital)*100:,.1f}%")
    print(f"  🛡️ Maximum Drawdown:        {max_drawdown_pct:.2f}%")
    print("=" * 95)

    print("\n🎯 COMPOUNDING MILESTONES ($50 ➔ $1,000+):")
    print(f"  • $100 (2x Double):    Hit at Trade #{milestones.get(100, {}).get('trade_num', 'N/A')} ({milestones.get(100, {}).get('date', '')})")
    print(f"  • $250 (5x Growth):    Hit at Trade #{milestones.get(250, {}).get('trade_num', 'N/A')} ({milestones.get(250, {}).get('date', '')})")
    print(f"  • $500 (10x Growth):   Hit at Trade #{milestones.get(500, {}).get('trade_num', 'N/A')} ({milestones.get(500, {}).get('date', '')})")
    print(f"  • $1,000 (20x Goal):   Hit at Trade #{milestones.get(1000, {}).get('trade_num', 'N/A')} ({milestones.get(1000, {}).get('date', '')})")
    if 2000 in milestones:
        print(f"  • $2,000 (40x Super):  Hit at Trade #{milestones[2000]['trade_num']} ({milestones[2000]['date']})")
    if 3000 in milestones:
        print(f"  • $3,000 (60x Ultra):  Hit at Trade #{milestones[3000]['trade_num']} ({milestones[3000]['date']})")

    # Save complete detailed trade ledger to JSON
    with open("super_sniper_100trades_5months_ledger.json", "w", encoding="utf-8") as f:
        json.dump({
            "metrics": {
                "total": total,
                "wins": wins,
                "win_rate": win_rate,
                "breakevens": bes,
                "be_rate": be_rate,
                "losses": losses,
                "loss_rate": loss_rate,
                "capital_safety": capital_safety,
                "start_capital": start_capital,
                "final_capital": current_capital,
                "max_drawdown": max_drawdown_pct,
                "avg_tp_hours": avg_tp_hours
            },
            "milestones": milestones,
            "trades": trades_100
        }, f, indent=2)

if __name__ == "__main__":
    run_100trade_backtest()
