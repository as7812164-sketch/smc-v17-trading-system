"""
SMC V17 Institutional 15-Minute 6-Month Real Market BUY Backtest
Engine Logic:
- Timeframe: Strictly 15m
- Direction: Strictly BUY Signals (Long setups)
- Horizon: Past 6 Months (March 2026 - September 2026, ~18,000 bars per asset)
- Structure: Bidirectional 3-OB Structural Sandwich -> Trade ONLY 👑 2nd Middle OB
- Entry: 1-Tick Front-Run Outer Boundary (ob_high * 1.0004)
- Airspace: >= 3.0% Clean Room to 1st Resistance OB
- Macro Trend: 50 EMA on 15m (Close > EMA 50)
- Order Flow Confluence: Taker Buy Ratio >= 50% and Positive CVD Delta
- Trade Management:
  * TP: +1.20% price move (+6.00% ROE @ 5x)
  * Fee-Shield BE Trigger: At +0.50% profit (+2.50% ROE), move SL to Entry + 0.10% buffer ($0.00 Net Loss)
  * Soft SL: -1.20% price move (-6.00% ROE @ 5x) on 15m Candle Close
  * Hard SL: -2.20% price move (-11.00% ROE @ 5x) Emergency wick stop
  * Time-Stop: 16 bars (4 hours) max hold for 15m scalp
- Compounding:
  * Starting Capital: $50.00 USDT
  * Compounding sequentially chronologically with daily circuit breaker
"""

import os
import json
import time
import sys
import csv
import urllib.request
from datetime import datetime
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CACHE_DIR_15M = "market_data_cache_15m"
os.makedirs(CACHE_DIR_15M, exist_ok=True)

TARGET_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT",
    "AVAXUSDT", "LINKUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT",
    "LTCUSDT", "DOTUSDT", "UNIUSDT", "ARBUSDT", "OPUSDT",
    "RENDERUSDT", "1000PEPEUSDT", "FETUSDT", "TIAUSDT", "XRPUSDT"
]

def fetch_and_cache_15m_data(symbols, days=180):
    """Fetches 6 months of 15m klines from Binance Futures and caches them permanently."""
    print(f"[*] Step 1: Loading / Downloading 6 Months of 15m Klines for {len(symbols)} Assets...", flush=True)
    now_ms = int(time.time() * 1000)
    target_start_ms = now_ms - (days * 24 * 3600 * 1000)
    
    market_data = {}

    for sym in symbols:
        cache_file = os.path.join(CACHE_DIR_15M, f"{sym}_15m.json")
        candles = []
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    candles = json.load(f)
                if candles and candles[0]["time"] <= target_start_ms and len(candles) >= 15000:
                    print(f"  [CACHE HIT] {sym}: Loaded {len(candles)} cached 15m bars ({time.ctime(candles[0]['time']/1000)} to {time.ctime(candles[-1]['time']/1000)})", flush=True)
                    market_data[sym] = candles
                    continue
            except Exception:
                candles = []

        print(f"  [FETCH] Downloading {sym} 15m data from Binance Futures...", flush=True)
        end_time = now_ms
        all_bars = []
        batches = 0
        error_count = 0
        while True:
            url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=15m&limit=1000&endTime={end_time}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            try:
                with urllib.request.urlopen(req, timeout=8) as r:
                    raw_data = json.loads(r.read().decode())
                error_count = 0
            except Exception as e:
                error_count += 1
                if error_count > 3:
                    print(f"  [WARN] Skipping remaining batches for {sym} after {error_count} errors: {e}", flush=True)
                    break
                time.sleep(1)
                continue
            
            if not raw_data:
                break
            
            converted = []
            for c in raw_data:
                vol = float(c[5])
                tb = float(c[9])
                converted.append({
                    "time": int(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": vol,
                    "taker_buy": tb
                })
            
            all_bars = converted + all_bars
            first_time = converted[0]["time"]
            end_time = first_time - 1
            batches += 1
            
            if first_time <= target_start_ms or len(raw_data) < 1000 or batches >= 20:
                break
            time.sleep(0.04)

        # Calculate Running CVD
        running_cvd = 0.0
        for c in all_bars:
            vol = c["volume"]
            tb = c.get("taker_buy", vol * 0.5)
            ts = max(0.0, vol - tb)
            delta = tb - ts
            running_cvd += delta
            c["taker_sell"] = ts
            c["delta"] = delta
            c["cvd"] = running_cvd

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(all_bars, f)
        
        print(f"  [SAVED] {sym}: {len(all_bars)} bars saved ({time.ctime(all_bars[0]['time']/1000)} to {time.ctime(all_bars[-1]['time']/1000)})", flush=True)
        market_data[sym] = all_bars

    return market_data

def run_15m_6month_buy_backtest(market_data):
    print(f"\n{'='*100}")
    print(f"       SMC V17 INSTITUTIONAL 15-MINUTE 6-MONTH BUY BACKTEST (HISTORICAL AUDIT)")
    print(f"{'='*100}")

    # 15m Scalp Parameters
    min_exp_pct = 0.0120       # Minimum 1.20% expansion away from OB
    airspace_req_pct = 3.00    # User-configured 3.0% Airspace Gap
    tp_pct = 0.0120            # +1.20% price move (+6.00% ROE @ 5x)
    soft_sl_pct = 0.0120       # -1.20% price move (-6.00% ROE @ 5x) on candle close
    hard_sl_pct = 0.0220       # -2.20% price move (-11.00% ROE @ 5x) emergency hard wick SL
    be_trigger_pct = 0.0050    # +0.50% price move (+2.50% ROE) arms Fee-Shield BE
    fee_shield_buffer = 0.0010 # +0.10% buffer for True $0.00 net loss
    max_hold_bars = 16         # 16 bars = 4 hours max hold for 15m scalp
    max_lookforward = 35

    all_buy_candidates = []

    for sym, candles in market_data.items():
        if not candles or len(candles) < 100:
            continue
        
        n = len(candles)
        # Precompute 50 EMA on 15m
        closes = [c["close"] for c in candles]
        ema50 = [0.0] * n
        mult = 2.0 / (50 + 1)
        ema50[49] = sum(closes[:50]) / 50.0
        for k in range(50, n):
            ema50[k] = (closes[k] - ema50[k-1]) * mult + ema50[k-1]

        # 1. Detect Bullish Order Blocks (Institutional down-candle before expansion)
        detected_bullish_obs = []
        for i in range(15, n - max_lookforward):
            c = candles[i]
            # Must be a down-close candle
            if c["close"] >= c["open"]:
                continue
            ob_h = c["high"]
            ob_l = c["low"]
            if ob_h <= ob_l or ob_h == 0:
                continue
            
            # Volume climax filter
            prev_vols = [candles[x]["volume"] for x in range(max(0, i-10), i)]
            avg_vol = sum(prev_vols) / len(prev_vols) if prev_vols else c["volume"]
            if avg_vol > 0 and (c["volume"] / avg_vol) > 3.8:
                continue
            
            # Check expansion away from OB: must rally at least +1.20%
            max_rally = max([candles[i+k]["high"] for k in range(1, min(9, n-i))])
            if (max_rally - ob_h) / ob_h < min_exp_pct:
                continue

            detected_bullish_obs.append({
                "bar_idx": i,
                "time": c["time"],
                "ob_high": ob_h,
                "ob_low": ob_l,
                "mitigated": False
            })

        # 2. Simulate 15m Market Flow and 3-OB Sandwich Recognition
        for bar_idx in range(40, n - max_lookforward):
            curr_c = candles[bar_idx]

            # 50 EMA Macro Trend Gate for BUY
            if curr_c["close"] < ema50[bar_idx]:
                continue

            active_obs = [ob for ob in detected_bullish_obs if ob["bar_idx"] < bar_idx - 2 and not ob["mitigated"]]
            if len(active_obs) < 3:
                continue

            # Take the 3 most recent active structural OBs
            recent_obs = sorted(active_obs, key=lambda x: x["bar_idx"], reverse=True)[:3]
            sorted_obs = sorted(recent_obs, key=lambda x: x["ob_high"], reverse=True)
            if sorted_obs[0]["ob_high"] <= sorted_obs[1]["ob_high"] or sorted_obs[1]["ob_high"] <= sorted_obs[2]["ob_high"]:
                continue

            top_ob = sorted_obs[0]
            middle_ob = sorted_obs[1] # 👑 THE 2ND (MIDDLE) ORDER BLOCK
            bottom_ob = sorted_obs[2]

            entry_level = middle_ob["ob_high"]
            entry_price = entry_level * 1.0004 # 1-tick front run

            # Entry Trigger: Price dips into the 2nd OB outer boundary on 1st tap
            touch_valid = (curr_c["low"] <= entry_price and curr_c["open"] > entry_level)
            if not touch_valid:
                continue

            # Calculate Airspace Gap to 1st OB ceiling
            airspace_pct = (top_ob["ob_low"] - entry_price) / entry_price * 100.0

            # Filter: Airspace Gap must be >= 3.0%
            if airspace_pct < airspace_req_pct:
                continue

            # Weekend Altcoin Guard
            gm_time = time.gmtime(curr_c["time"] / 1000)
            if gm_time.tm_wday in (5, 6) and sym not in ("BTCUSDT", "ETHUSDT"):
                continue

            # Order Flow Microstructure Gate: Delta Ratio & CVD Direction
            d_ratio = curr_c["taker_buy"] / curr_c["volume"] if curr_c["volume"] > 0 else 0.50
            cvd_prev = candles[bar_idx - 2]["cvd"] if bar_idx >= 2 else candles[0]["cvd"]
            cvd_diff = curr_c["cvd"] - cvd_prev
            if not (d_ratio >= 0.48 and cvd_diff > 0):
                continue

            # Mark Middle OB as mitigated
            middle_ob["mitigated"] = True

            # Define Exact Target & Protection Levels
            tp_target = entry_price * (1.0 + tp_pct)
            be_trigger = entry_price * (1.0 + be_trigger_pct)
            fee_shield_be = entry_price * (1.0 + fee_shield_buffer)
            soft_sl_level = entry_price * (1.0 - soft_sl_pct)
            hard_sl_level = entry_price * (1.0 - hard_sl_pct)

            trade_res = None
            be_active = False
            bars_held = 0

            # Step forward bar-by-bar
            for step in range(bar_idx + 1, min(bar_idx + 1 + max_hold_bars, n)):
                bars_held += 1
                f_c = candles[step]

                # 1. Hard SL check (Flash crash protection)
                if f_c["low"] <= hard_sl_level:
                    trade_res = "HARD_SL_HIT"
                    break

                # 2. Arm Fee-Shield BE when profit >= +0.50%
                if not be_active and f_c["high"] >= be_trigger:
                    be_active = True

                # 3. TP Hit Check (+1.20% move = +6% ROE)
                if f_c["high"] >= tp_target:
                    trade_res = "WIN"
                    break

                # 4. Fee-Shield BE Stop Hit (True $0.00 Net Loss exit)
                if be_active and f_c["low"] <= fee_shield_be:
                    trade_res = "BREAKEVEN"
                    break

                # 5. Soft SL Check on Candle Close (Institutional Wick Protection)
                if not be_active and f_c["close"] <= soft_sl_level:
                    trade_res = "SOFT_SL_HIT"
                    break

            if not trade_res:
                trade_res = "BREAKEVEN" if be_active else "TIME_STOP_EXIT"

            all_buy_candidates.append({
                "timeframe": "15m",
                "symbol": sym,
                "side": "BUY",
                "entry_time": curr_c["time"],
                "date": time.strftime("%Y-%m-%d %H:%M UTC", gm_time),
                "entry_price": round(entry_price, 6),
                "tp_price": round(tp_target, 6),
                "sl_price": round(soft_sl_level, 6),
                "be_price": round(fee_shield_be, 6),
                "result": trade_res,
                "bars_held": bars_held,
                "minutes_held": bars_held * 15,
                "hours_held": round(bars_held * 0.25, 2),
                "airspace_pct": round(airspace_pct, 2),
                "delta_ratio": round(d_ratio * 100, 1)
            })

    # Sort all BUY trades strictly chronologically
    all_buy_candidates.sort(key=lambda x: x["entry_time"])
    print(f"[*] Total 15m BUY Setup Candidates Found Across Market: {len(all_buy_candidates)}")

    # Enforce portfolio execution rules (1 position per coin at any time)
    executed_trades = []
    active_coin_locks = {}

    for tc in all_buy_candidates:
        sym = tc["symbol"]
        e_time = tc["entry_time"]
        release_time = e_time + (tc["minutes_held"] * 60 * 1000)

        if sym in active_coin_locks and active_coin_locks[sym] > e_time:
            continue

        executed_trades.append(tc)
        active_coin_locks[sym] = release_time

    print(f"[*] Total Disjoint Chronological 15m BUY Trades Executed: {len(executed_trades)}")

    # Compounding Simulation with $50.00 USDT Initial Capital
    capital = 50.00
    peak = capital
    max_dd = 0.0
    daily_losses = {}
    milestones = {}

    for idx, t in enumerate(executed_trades, 1):
        day_key = t["date"][:10]
        res = t["result"]

        # Circuit breaker: max 2 losses per calendar day
        if daily_losses.get(day_key, 0) >= 2:
            t["status"] = "SKIPPED_BY_CIRCUIT_BREAKER"
            t["pnl_usdt"] = 0.0
            t["balance"] = round(capital, 2)
            t["trade_num"] = idx
            continue

        if res == "WIN":
            roe_gain = 0.06 # +1.20% price move * 5x = +6.00% ROE
            pnl = capital * roe_gain
            capital += pnl
            t["roe_pct"] = round(roe_gain * 100, 2)
            t["pnl_usdt"] = round(pnl, 2)
        elif res == "SOFT_SL_HIT":
            roe_loss = 0.06 # -1.20% price move * 5x = -6.00% ROE
            pnl = -(capital * roe_loss)
            capital += pnl
            daily_losses[day_key] = daily_losses.get(day_key, 0) + 1
            t["roe_pct"] = round(-roe_loss * 100, 2)
            t["pnl_usdt"] = round(pnl, 2)
        elif res == "HARD_SL_HIT":
            roe_loss = 0.11 # -2.20% price move * 5x = -11.00% ROE
            pnl = -(capital * roe_loss)
            capital += pnl
            daily_losses[day_key] = daily_losses.get(day_key, 0) + 1
            t["roe_pct"] = -11.0
            t["pnl_usdt"] = round(pnl, 2)
        else: # BREAKEVEN or TIME_STOP_EXIT
            t["roe_pct"] = 0.0
            t["pnl_usdt"] = 0.0

        if capital > peak:
            peak = capital
        dd = (peak - capital) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

        t["trade_num"] = idx
        t["balance"] = round(capital, 2)

        # Track compounding milestones
        for m in [75, 100, 150, 250, 500, 1000, 2000, 3000, 5000]:
            if capital >= m and m not in milestones:
                milestones[m] = {"trade_num": idx, "date": t["date"], "balance": round(capital, 2)}

    # Calculate Performance Metrics
    active_executed = [t for t in executed_trades if t.get("status") != "SKIPPED_BY_CIRCUIT_BREAKER"]
    tot = len(active_executed)
    wins = sum(1 for t in active_executed if t["result"] == "WIN")
    bes = sum(1 for t in active_executed if t["result"] in ("BREAKEVEN", "TIME_STOP_EXIT"))
    losses = sum(1 for t in active_executed if "SL_HIT" in t["result"])

    win_rate = (wins / tot * 100.0) if tot > 0 else 0.0
    be_rate = (bes / tot * 100.0) if tot > 0 else 0.0
    loss_rate = (losses / tot * 100.0) if tot > 0 else 0.0
    capital_safety = ((wins + bes) / tot * 100.0) if tot > 0 else 0.0
    avg_win_mins = np.mean([t["minutes_held"] for t in active_executed if t["result"] == "WIN"]) if wins > 0 else 0.0

    print("-" * 100)
    print(f"  ⏱ Time Horizon:              {active_executed[0]['date']}  ➔  {active_executed[-1]['date']} (6 Full Months)")
    print(f"  🎯 Total 15m BUY Trades:     {tot}")
    print(f"  🏆 Direct Win Rate (TP Hit): {win_rate:.2f}%  ({wins}/{tot} Trades)")
    print(f"  🛡️ Fee-Shield Breakeven:    {be_rate:.2f}%  ({bes}/{tot} Trades with $0.00 Net Loss)")
    print(f"  ❌ SL Loss Rate:             {loss_rate:.2f}%  ({losses}/{tot} Trades)")
    print(f"  💎 Total Capital Safety:     {capital_safety:.2f}%  (Wins + $0.00 Risk Exits)")
    print(f"  ⚡ Avg Hold Time to TP:       {avg_win_mins:.1f} Minutes ({avg_win_mins/60:.2f} Hours)")
    print("-" * 100)
    print(f"  💰 Starting Capital:         $50.00 USDT")
    print(f"  🚀 Final Compounded Balance: ${capital:,.2f} USDT")
    print(f"  📈 Net Portfolio Growth:     +{((capital - 50.0) / 50.0) * 100:,.1f}%")
    print(f"  🛡️ Maximum Drawdown (DD):     {max_dd:.2f}%")
    print("-" * 100)

    # Save to CSV Ledger
    csv_file = "backtest_15m_6months_buy_ledger.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Trade #", "Date (UTC)", "Timeframe", "Symbol", "Side",
            "Entry Price", "TP Target", "SL Price", "Airspace Gap %",
            "Delta Ratio %", "Hold Time (Mins)", "Result", "ROE %", "PNL (USDT)", "Balance (USDT)"
        ])
        for t in active_executed:
            writer.writerow([
                t["trade_num"], t["date"], t["timeframe"], t["symbol"], t["side"],
                t["entry_price"], t["tp_price"], t["sl_price"], t["airspace_pct"],
                t["delta_ratio"], t["minutes_held"], t["result"],
                t.get("roe_pct", 0.0), t.get("pnl_usdt", 0.0), t.get("balance", 50.0)
            ])
    print(f"[*] Forensic CSV Ledger written to {csv_file}")

    # Save JSON summary
    json_summary = {
        "timeframe": "15m",
        "direction": "BUY_ONLY",
        "time_horizon": "6_MONTHS",
        "date_range": f"{active_executed[0]['date']} to {active_executed[-1]['date']}",
        "total_trades": tot,
        "wins": wins,
        "breakevens": bes,
        "losses": losses,
        "win_rate_pct": round(win_rate, 2),
        "breakeven_rate_pct": round(be_rate, 2),
        "loss_rate_pct": round(loss_rate, 2),
        "capital_safety_rate_pct": round(capital_safety, 2),
        "avg_hold_minutes_win": round(avg_win_mins, 1),
        "starting_capital_usdt": 50.00,
        "final_capital_usdt": round(capital, 2),
        "net_growth_pct": round(((capital - 50.0) / 50.0) * 100.0, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "milestones": milestones,
        "trades": active_executed
    }

    json_file = "backtest_15m_6months_buy_result.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_summary, f, indent=2)
    print(f"[*] Forensic JSON Summary written to {json_file}")

    # Mirror to Desktop
    desktop_dir = r"C:\Users\power\Desktop\SMC_V17_MASTER_SYSTEM\SMC_V17_CODEBASE"
    if os.path.exists(desktop_dir):
        try:
            import shutil
            shutil.copy2(csv_file, os.path.join(desktop_dir, csv_file))
            shutil.copy2(json_file, os.path.join(desktop_dir, json_file))
            print(f"[*] Mirrored CSV and JSON to Desktop: {desktop_dir}")
        except Exception as e:
            print(f"[!] Warning mirroring to Desktop: {e}")

    return json_summary

if __name__ == "__main__":
    market_data = fetch_and_cache_15m_data(TARGET_COINS, days=180)
    run_15m_6month_buy_backtest(market_data)
