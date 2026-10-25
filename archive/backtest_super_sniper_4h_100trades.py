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
    "APTUSDT", "LTCUSDT", "LINKUSDT", "ADAUSDT", "XRPUSDT"
]

def fetch_4h_history(symbol):
    """Fetches up to 2000 4H candles (~11 months) to guarantee ample 4H setups."""
    all_candles = []
    end_time = None
    for _ in range(2):
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=4h&limit=1000"
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
        except Exception:
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

def run_4h_100trade_backtest():
    print("=" * 95)
    print("      SUPER SNIPER COMBO: 4H TIMEFRAME 100-TRADE BACKTEST ($50 COMPOUNDING)")
    print("=" * 95)
    print("Fetching 4H historical data for top liquid pairs...", flush=True)

    all_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_4h_history, s) for s in SYMBOLS]
        for f in concurrent.futures.as_completed(futures):
            s, c = f.result()
            all_data[s] = c
            days = (c[-1]["time"] - c[0]["time"]) / (86400 * 1000) if c else 0
            print(f"  ✓ {s:<10}: {len(c)} candles ({days:.1f} days / {days/30:.1f} months)", flush=True)

    # EXACT 1H Parameters Applied to 4H (as requested by user)
    # TP: +1.50% price move (+7.50% ROE @ 5x)
    # BE: +0.75% price move (+3.75% ROE)
    # SL: -2.00% price move (-10.00% ROE @ 5x)
    tp_pct = 0.015
    be_pct = 0.0075
    sl_pct = 0.020

    all_trades = []

    # Detect 4H Super Sniper BUY Setups
    for sym, candles in all_data.items():
        if len(candles) < 60:
            continue

        for i in range(15, len(candles) - 20):
            c = candles[i]
            # Order Block condition
            if c["close"] >= c["open"]:
                continue

            ob_high = c["high"]
            ob_low = c["low"]

            # 4H expansion threshold: >= 3.0% move in next 6 candles
            max_rally = max([candles[i+k]["high"] for k in range(1, min(7, len(candles)-i))])
            if (max_rally - ob_high) / ob_high < 0.030:
                continue

            entry_p = ob_high
            tp_target = entry_p * (1.0 + tp_pct)
            be_target = entry_p * (1.0 + be_pct)
            sl_target = entry_p * (1.0 - sl_pct)

            # First tap retest search
            entry_idx = -1
            for k in range(i + 3, min(i + 40, len(candles))):
                if candles[k]["low"] <= entry_p and candles[k]["high"] >= entry_p:
                    entry_idx = k
                    break

            if entry_idx == -1:
                continue

            entry_c = candles[entry_idx]
            entry_time = entry_c["time"]

            # --- SUPER SNIPER ORDER FLOW GATE ON 4H ---
            d_ratio = entry_c["taker_buy"] / entry_c["volume"] if entry_c["volume"] > 0 else 0.50
            cvd_prev = candles[entry_idx - 2]["cvd"] if entry_idx >= 2 else candles[0]["cvd"]
            cvd_reversal = (entry_c["cvd"] - cvd_prev) > 0

            # Filter: Taker Buy Volume Ratio >= 51% + CVD Reversal
            is_super_sniper = (d_ratio >= 0.51) and cvd_reversal
            if not is_super_sniper:
                continue

            # Forward outcome
            trade_res = None
            be_active = False
            bars_held = 0

            for m in range(entry_idx, min(entry_idx + 35, len(candles))):
                curr = candles[m]
                bars_held += 1

                # Check Breakeven Trigger (+0.75% move)
                if not be_active and curr["high"] >= be_target:
                    be_active = True

                # Check TP Hit (+1.50% move = +7.50% ROE)
                if curr["high"] >= tp_target:
                    trade_res = "WIN"
                    break

                # Check Breakeven Stop Hit ($0 loss)
                if be_active and curr["low"] <= entry_p:
                    trade_res = "BREAKEVEN"
                    break

                # Check SL Hit (-2.00% move = -10.00% ROE)
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
                "hours_to_finish": bars_held * 4,
                "delta_ratio": d_ratio,
                "cvd_reversal": cvd_reversal
            })

    # Sort chronologically across the market
    all_trades.sort(key=lambda x: x["entry_time"])

    # Limit to 100 consecutive trades
    trades_100 = all_trades[:100]

    # Run $50 Compounding Simulation
    start_capital = 50.0
    current_capital = start_capital
    peak_capital = start_capital
    max_drawdown_pct = 0.0

    milestones = {}

    for idx, t in enumerate(trades_100, 1):
        if t["result"] == "WIN":
            gain = current_capital * 0.075 # +7.50% ROE
            current_capital += gain
        elif t["result"] == "LOSS":
            loss = current_capital * 0.10 # -10.00% ROE
            current_capital -= loss
        else: # BREAKEVEN
            pass

        if current_capital > peak_capital:
            peak_capital = current_capital

        dd = (peak_capital - current_capital) / peak_capital * 100
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd

        dt_str = time.strftime("%Y-%m-%d %H:%M", time.gmtime(t["entry_time"] / 1000))
        t["date"] = dt_str
        t["balance"] = current_capital

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
    avg_tp_hours = np.mean([t["hours_to_finish"] for t in trades_100 if t["result"] == "WIN"])

    print("\n" + "=" * 95)
    print("                4H TIMEFRAME 100-TRADE QUANTITATIVE PERFORMANCE SUMMARY")
    print("=" * 95)
    print(f"  ⏱ Data Period:             {trades_100[0]['date']}  ➔  {trades_100[-1]['date']}")
    print(f"  🎯 Total Trades Executed:   {total}")
    print(f"  🏆 Direct Win Rate (TP):    {win_rate:.2f}%  ({wins}/{total} Trades)")
    print(f"  🛡️ Breakeven Rate ($0):     {be_rate:.2f}%  ({bes}/{total} Trades)")
    print(f"  ❌ Loss Rate (SL Hit):      {loss_rate:.2f}%  ({losses}/{total} Trades)")
    print(f"  💎 Total Capital Safety:    {capital_safety:.2f}%  (Win + Breakeven)")
    print(f"  ⚡ Average Time to TP:       {avg_tp_hours:.1f} Hours ({avg_tp_hours/4:.1f} 4H Candles)")
    print("-" * 95)
    print(f"  💰 Starting Capital:        ${start_capital:.2f} USDT")
    print(f"  🚀 Final Compounded Balance: ${current_capital:,.2f} USDT")
    print(f"  📈 Net Total Return:        +{((current_capital - start_capital)/start_capital)*100:,.1f}%")
    print(f"  🛡️ Maximum Drawdown:        {max_drawdown_pct:.2f}%")
    print("=" * 95)

    print("\n🎯 4H COMPOUNDING MILESTONES ($50 ➔ $1,000+):")
    print(f"  • $100 (2x Double):    Hit at Trade #{milestones.get(100, {}).get('trade_num', 'N/A')} ({milestones.get(100, {}).get('date', '')})")
    print(f"  • $250 (5x Growth):    Hit at Trade #{milestones.get(250, {}).get('trade_num', 'N/A')} ({milestones.get(250, {}).get('date', '')})")
    print(f"  • $500 (10x Growth):   Hit at Trade #{milestones.get(500, {}).get('trade_num', 'N/A')} ({milestones.get(500, {}).get('date', '')})")
    print(f"  • $1,000 (20x Goal):   Hit at Trade #{milestones.get(1000, {}).get('trade_num', 'N/A')} ({milestones.get(1000, {}).get('date', '')})")
    if 2000 in milestones:
        print(f"  • $2,000 (40x Super):  Hit at Trade #{milestones[2000]['trade_num']} ({milestones[2000]['date']})")
    if 3000 in milestones:
        print(f"  • $3,000 (60x Ultra):  Hit at Trade #{milestones[3000]['trade_num']} ({milestones[3000]['date']})")
    if 5000 in milestones:
        print(f"  • $5,000 (100x Titan): Hit at Trade #{milestones[5000]['trade_num']} ({milestones[5000]['date']})")

    # Save complete detailed 4H trade ledger
    with open("super_sniper_4h_100trades_ledger.json", "w", encoding="utf-8") as f:
        json.dump({
            "timeframe": "4h",
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
    run_4h_100trade_backtest()
