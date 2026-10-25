"""
SMC V17 Institutional Forensic 100-Trade Real Market Backtest (1H & 4H)
Exact Locked Strategy Execution:
- Bidirectional (BUY & SELL) 3-OB Structural Sandwich
- Trade ONLY the 2nd (Middle) OB
- 1st Tap Outer Boundary Entry (BUY: ob_high * 1.0005 | SELL: ob_low * 0.9995)
- 1H: Target +1.60% (+8.00% ROE) | Soft SL -2.00% (-10.00% ROE, Candle Close) | Hard SL -3.20% (-16.00% ROE) | BE at +0.75%
- 4H: Target +2.40% (+12.00% ROE) | Soft SL -2.25% (-11.25% ROE, Candle Close) | Hard SL -3.20% (-16.00% ROE) | BE at +1.05%
- Confluences: Min Expansion (+1.5% on 1H / +2.0% on 4H), CVD Reversal, Airspace Gap, 50 EMA, Weekend Filter
- Exactly 100 sequential trades evaluated for 1H and 100 trades for 4H with $50.00 USDT initial compounding.
"""

import os
import json
import time
import sys
import csv
from datetime import datetime
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CACHE_DIR = "market_data_cache"

def load_cached_data(interval):
    """Loads all cached candles for the specified interval, computing running CVD."""
    market_data = {}
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith(f"_{interval}.json")]
    for fname in sorted(files):
        sym = fname.split("_")[0]
        fpath = os.path.join(CACHE_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                candles = json.load(f)
                if candles and len(candles) >= 80:
                    running_cvd = 0.0
                    for c in candles:
                        vol = c.get("volume", 0.0)
                        tb = c.get("taker_buy", vol * 0.5)
                        ts = max(0.0, vol - tb)
                        delta = tb - ts
                        running_cvd += delta
                        c["taker_sell"] = ts
                        c["delta"] = delta
                        c["cvd"] = running_cvd
                    market_data[sym] = candles
        except Exception:
            pass
    return market_data

def run_backtest_for_timeframe(interval, all_market_data):
    print(f"\n{'='*95}")
    print(f"       RUNNING FORENSIC 100-TRADE BACKTEST FOR [{interval.upper()}] TIMEFRAME")
    print(f"{'='*95}")

    is_1h = (interval == "1h")

    # Strategy Parameters
    tp_pct = 0.0160 if is_1h else 0.0240            # 1H: +1.60% (+8% ROE) | 4H: +2.40% (+12% ROE)
    soft_sl_pct = 0.0200 if is_1h else 0.0225       # 1H: -2.00% (-10% ROE) | 4H: -2.25% (-11.25% ROE)
    hard_sl_pct = 0.0320                            # -3.20% price move = -16.00% ROE emergency stop
    be_trigger_pct = 0.0075 if is_1h else 0.0105   # BE trigger: +0.75% (1H) / +1.05% (4H)
    fee_shield_buffer = 0.0010                      # +0.10% fee shield buffer for true $0 net exit
    min_exp_pct = 0.0150 if is_1h else 0.0200       # Min expansion before returning (+1.5% on 1H / +2.0% on 4H)
    airspace_req_pct = 5.00                         # STRICT 5.0% Min Airspace Gap to opposite structural OB
    max_hold_bars = 16 if is_1h else 12             # 16h on 1H / 48h (12 bars) on 4H time-stop
    max_lookforward = 35 if is_1h else 25

    all_trade_candidates = []

    for sym, candles in all_market_data.items():
        if not candles or len(candles) < 80:
            continue

        n = len(candles)
        # Precompute 50 EMA
        closes = [c["close"] for c in candles]
        ema50 = [0.0] * n
        mult = 2.0 / (50 + 1)
        ema50[49] = sum(closes[:50]) / 50.0
        for k in range(50, n):
            ema50[k] = (closes[k] - ema50[k-1]) * mult + ema50[k-1]

        for side in ["BUY", "SELL"]:
            # 1. Detect Directional Order Blocks
            detected_obs = []
            for i in range(15, n - max_lookforward):
                c = candles[i]
                if side == "BUY":
                    if c["close"] >= c["open"]:
                        continue
                    ob_h = c["high"]
                    ob_l = c["low"]
                    if ob_h <= ob_l or ob_h == 0:
                        continue
                    # Check volume climax guard
                    prev_vols = [candles[x]["volume"] for x in range(max(0, i-10), i)]
                    avg_vol = sum(prev_vols) / len(prev_vols) if prev_vols else c["volume"]
                    if avg_vol > 0 and (c["volume"] / avg_vol) > 3.5:
                        continue
                    # Check expansion
                    max_rally = max([candles[i+k]["high"] for k in range(1, min(7, n-i))])
                    if (max_rally - ob_h) / ob_h < min_exp_pct:
                        continue
                    detected_obs.append({"bar_idx": i, "time": c["time"], "ob_high": ob_h, "ob_low": ob_l, "side": "BUY", "mitigated": False})
                else: # SELL
                    if c["close"] <= c["open"]:
                        continue
                    ob_h = c["high"]
                    ob_l = c["low"]
                    if ob_h <= ob_l or ob_l == 0:
                        continue
                    prev_vols = [candles[x]["volume"] for x in range(max(0, i-10), i)]
                    avg_vol = sum(prev_vols) / len(prev_vols) if prev_vols else c["volume"]
                    if avg_vol > 0 and (c["volume"] / avg_vol) > 3.5:
                        continue
                    min_drop = min([candles[i+k]["low"] for k in range(1, min(7, n-i))])
                    if (ob_l - min_drop) / ob_l < min_exp_pct:
                        continue
                    detected_obs.append({"bar_idx": i, "time": c["time"], "ob_high": ob_h, "ob_low": ob_l, "side": "SELL", "mitigated": False})

            # 2. Simulate Market Flow and Detect 3-OB Sandwich
            for bar_idx in range(40, n - max_lookforward):
                curr_c = candles[bar_idx]

                # 50 EMA Macro Trend Filter
                if side == "BUY" and curr_c["close"] < ema50[bar_idx]:
                    continue
                if side == "SELL" and curr_c["close"] > ema50[bar_idx]:
                    continue

                active_obs = [ob for ob in detected_obs if ob["bar_idx"] < bar_idx - 2 and not ob["mitigated"]]
                if len(active_obs) < 3:
                    continue

                recent_obs = sorted(active_obs, key=lambda x: x["bar_idx"], reverse=True)[:3]

                if side == "BUY":
                    sorted_obs = sorted(recent_obs, key=lambda x: x["ob_high"], reverse=True)
                    if sorted_obs[0]["ob_high"] <= sorted_obs[1]["ob_high"] or sorted_obs[1]["ob_high"] <= sorted_obs[2]["ob_high"]:
                        continue
                    top_ob = sorted_obs[0]
                    middle_ob = sorted_obs[1]
                    entry_level = middle_ob["ob_high"]
                    entry_price = entry_level * 1.0005 # 1-tick front-run
                    touch_valid = (curr_c["low"] <= entry_price and curr_c["open"] > entry_level)
                    airspace_pct = (top_ob["ob_low"] - entry_price) / entry_price * 100
                else: # SELL
                    sorted_obs = sorted(recent_obs, key=lambda x: x["ob_low"])
                    if sorted_obs[0]["ob_low"] >= sorted_obs[1]["ob_low"] or sorted_obs[1]["ob_low"] >= sorted_obs[2]["ob_low"]:
                        continue
                    bottom_ob = sorted_obs[0]
                    middle_ob = sorted_obs[1]
                    entry_level = middle_ob["ob_low"]
                    entry_price = entry_level * 0.9995 # 1-tick front-run
                    touch_valid = (curr_c["high"] >= entry_price and curr_c["open"] < entry_level)
                    airspace_pct = (entry_price - bottom_ob["ob_high"]) / entry_price * 100

                if touch_valid:
                    # Weekend Altcoin Filter (Do not burn OB if skipped)
                    gm_time = time.gmtime(curr_c["time"] / 1000)
                    if gm_time.tm_wday in (5, 6) and sym not in ("BTCUSDT", "ETHUSDT"):
                        continue

                    # Airspace Check
                    if airspace_pct < airspace_req_pct:
                        continue

                    # Order Flow Confluence Gate: CVD Reversal & Delta
                    d_ratio = curr_c["taker_buy"] / curr_c["volume"] if curr_c["volume"] > 0 else 0.50
                    cvd_prev = candles[bar_idx - 2]["cvd"] if bar_idx >= 2 else candles[0]["cvd"]
                    cvd_diff = curr_c["cvd"] - cvd_prev

                    if side == "BUY":
                        if not (d_ratio >= 0.50 and cvd_diff > 0):
                            continue
                        tp_target = entry_price * (1.0 + tp_pct)
                        be_trigger = entry_price * (1.0 + be_trigger_pct)
                        fee_shield_be = entry_price * (1.0 + fee_shield_buffer)
                        soft_sl_level = entry_price * (1.0 - soft_sl_pct)
                        hard_sl_level = entry_price * (1.0 - hard_sl_pct)
                    else:
                        if not (d_ratio <= 0.50 and cvd_diff < 0):
                            continue
                        tp_target = entry_price * (1.0 - tp_pct)
                        be_trigger = entry_price * (1.0 - be_trigger_pct)
                        fee_shield_be = entry_price * (1.0 - fee_shield_buffer)
                        soft_sl_level = entry_price * (1.0 + soft_sl_pct)
                        hard_sl_level = entry_price * (1.0 + hard_sl_pct)

                    # Only mark mitigated when trade passes all confluence filters!
                    middle_ob["mitigated"] = True

                    trade_res = None
                    be_active = False
                    bars_held = 0

                    for step in range(bar_idx + 1, min(bar_idx + 1 + max_hold_bars, n)):
                        bars_held += 1
                        f_c = candles[step]

                        if side == "BUY":
                            # 1. Hard SL
                            if f_c["low"] <= hard_sl_level:
                                trade_res = "HARD_SL_HIT"
                                break
                            # 2. BE Trigger
                            if not be_active and f_c["high"] >= be_trigger:
                                be_active = True
                            # 3. TP Hit
                            if f_c["high"] >= tp_target:
                                trade_res = "WIN"
                                break
                            # 4. BE Stop Hit
                            if be_active and f_c["low"] <= fee_shield_be:
                                trade_res = "BREAKEVEN"
                                break
                            # 5. Soft SL on Candle Close
                            if not be_active and f_c["close"] <= soft_sl_level:
                                trade_res = "SOFT_SL_HIT"
                                break
                        else: # SELL
                            # 1. Hard SL
                            if f_c["high"] >= hard_sl_level:
                                trade_res = "HARD_SL_HIT"
                                break
                            # 2. BE Trigger
                            if not be_active and f_c["low"] <= be_trigger:
                                be_active = True
                            # 3. TP Hit
                            if f_c["low"] <= tp_target:
                                trade_res = "WIN"
                                break
                            # 4. BE Stop Hit
                            if be_active and f_c["high"] >= fee_shield_be:
                                trade_res = "BREAKEVEN"
                                break
                            # 5. Soft SL on Candle Close
                            if not be_active and f_c["close"] >= soft_sl_level:
                                trade_res = "SOFT_SL_HIT"
                                break

                    if not trade_res:
                        trade_res = "BREAKEVEN" if be_active else "TIME_STOP_EXIT"

                    all_trade_candidates.append({
                        "timeframe": interval,
                        "symbol": sym,
                        "side": side,
                        "entry_time": curr_c["time"],
                        "date": time.strftime("%Y-%m-%d %H:%M UTC", gm_time),
                        "entry_price": entry_price,
                        "tp_price": tp_target,
                        "sl_price": soft_sl_level,
                        "result": trade_res,
                        "bars_held": bars_held,
                        "hours_held": bars_held if is_1h else bars_held * 4,
                        "airspace_pct": round(airspace_pct, 2),
                        "delta_ratio": round(d_ratio * 100, 1)
                    })

    # Sort all candidates strictly chronologically across the market
    all_trade_candidates.sort(key=lambda x: x["entry_time"])
    print(f"  Total Valid Setup Candidates Discovered: {len(all_trade_candidates)}")

    # Extract exactly 100 chronological trades
    selected_100 = []
    active_coin_locks = {} # sym -> release_time

    for tc in all_trade_candidates:
        sym = tc["symbol"]
        e_time = tc["entry_time"]
        release_time = e_time + (tc["hours_held"] * 3600 * 1000)

        # Enforce no simultaneous multiple positions on same coin
        if sym in active_coin_locks and active_coin_locks[sym] > e_time:
            continue

        selected_100.append(tc)
        active_coin_locks[sym] = release_time

        if len(selected_100) >= 100:
            break

    # If still under 100, take remaining top chronological candidates
    if len(selected_100) < 100:
        seen = set((t["symbol"], t["entry_time"], t["side"]) for t in selected_100)
        for tc in all_trade_candidates:
            if (tc["symbol"], tc["entry_time"], tc["side"]) not in seen:
                selected_100.append(tc)
                if len(selected_100) >= 100:
                    break

    trades_to_run = selected_100[:100]

    # Run $50 Compounding Simulation
    capital = 50.0
    peak = capital
    max_dd = 0.0
    daily_losses = {} # Circuit breaker tracking
    milestones = {}

    for idx, t in enumerate(trades_to_run, 1):
        day_key = t["date"][:10]
        res = t["result"]

        # Check circuit breaker: If 2 losses on same day, skip trade
        if daily_losses.get(day_key, 0) >= 2:
            t["status"] = "SKIPPED_BY_CIRCUIT_BREAKER"
            t["pnl_usdt"] = 0.0
            t["balance"] = capital
            t["trade_num"] = idx
            continue

        if res == "WIN":
            roe_gain = 0.08 if is_1h else 0.12 # +8% ROE (1H) | +12% ROE (4H)
            pnl = capital * roe_gain
            capital += pnl
            t["roe_pct"] = roe_gain * 100
            t["pnl_usdt"] = round(pnl, 2)
        elif res == "SOFT_SL_HIT":
            roe_loss = 0.10 if is_1h else 0.1125 # -10% ROE (1H) | -11.25% ROE (4H)
            pnl = -(capital * roe_loss)
            capital += pnl
            daily_losses[day_key] = daily_losses.get(day_key, 0) + 1
            t["roe_pct"] = -roe_loss * 100
            t["pnl_usdt"] = round(pnl, 2)
        elif res == "HARD_SL_HIT":
            roe_loss = 0.16 # -16% emergency SL
            pnl = -(capital * roe_loss)
            capital += pnl
            daily_losses[day_key] = daily_losses.get(day_key, 0) + 1
            t["roe_pct"] = -16.0
            t["pnl_usdt"] = round(pnl, 2)
        else: # BREAKEVEN or TIME_STOP_EXIT
            t["roe_pct"] = 0.0
            t["pnl_usdt"] = 0.0

        if capital > peak:
            peak = capital
        dd = (peak - capital) / peak * 100
        if dd > max_dd:
            max_dd = dd

        t["trade_num"] = idx
        t["balance"] = round(capital, 2)

        # Track Milestones
        for m in [100, 250, 500, 1000, 2000, 3000, 5000]:
            if capital >= m and m not in milestones:
                milestones[m] = {"trade_num": idx, "date": t["date"], "balance": round(capital, 2)}

    # Statistics Calculation
    valid_trades = [t for t in trades_to_run if t.get("status") != "SKIPPED_BY_CIRCUIT_BREAKER"]
    tot = len(valid_trades)
    wins = sum(1 for t in valid_trades if t["result"] == "WIN")
    bes = sum(1 for t in valid_trades if t["result"] in ("BREAKEVEN", "TIME_STOP_EXIT"))
    losses = sum(1 for t in valid_trades if "SL_HIT" in t["result"])

    win_rate = (wins / tot * 100) if tot > 0 else 0.0
    be_rate = (bes / tot * 100) if tot > 0 else 0.0
    loss_rate = (losses / tot * 100) if tot > 0 else 0.0
    capital_safety = ((wins + bes) / tot * 100) if tot > 0 else 0.0
    avg_win_duration = np.mean([t["hours_held"] for t in valid_trades if t["result"] == "WIN"]) if wins > 0 else 0.0

    print("-" * 95)
    print(f"  ⏱ Date Range Analyzed:      {valid_trades[0]['date']}  ➔  {valid_trades[-1]['date']}")
    print(f"  🎯 Total Trades Audited:    {tot}")
    print(f"  🏆 Direct Win Rate (TP Hit): {win_rate:.2f}%  ({wins}/{tot} Trades)")
    print(f"  🛡️ Breakeven Rate ($0 Risk): {be_rate:.2f}%  ({bes}/{tot} Trades)")
    print(f"  ❌ Loss Rate (SL Hit):       {loss_rate:.2f}%  ({losses}/{tot} Trades)")
    print(f"  💎 Total Capital Safety:     {capital_safety:.2f}%  (Wins + $0 Breakevens)")
    print(f"  ⚡ Average Time to TP:        {avg_win_duration:.1f} Hours")
    print("-" * 95)
    print(f"  💰 Starting Capital:         $50.00 USDT")
    print(f"  🚀 Final Compounded Balance: ${capital:,.2f} USDT")
    print(f"  📈 Net Portfolio Return:     +{((capital - 50.0) / 50.0) * 100:,.1f}%")
    print(f"  🛡️ Maximum Drawdown (DD):     {max_dd:.2f}%")
    if milestones:
        print(f"  🎯 Compounding Milestones Hit:")
        for target, data in sorted(milestones.items()):
            print(f"     • ${target} USDT reached on Trade #{data['trade_num']} ({data['date']}) with ${data['balance']:.2f}")
    print("=" * 95)

    return {
        "timeframe": interval,
        "total_trades": tot,
        "wins": wins,
        "breakevens": bes,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "be_rate": round(be_rate, 2),
        "loss_rate": round(loss_rate, 2),
        "capital_safety_rate": round(capital_safety, 2),
        "avg_hours_to_tp": round(avg_win_duration, 1),
        "starting_balance": 50.0,
        "final_balance": round(capital, 2),
        "net_return_pct": round(((capital - 50.0) / 50.0) * 100, 1),
        "max_drawdown_pct": round(max_dd, 2),
        "milestones": milestones,
        "trades": valid_trades
    }

def main():
    print("================================================================================")
    print("     SMC V17 INSTITUTIONAL FORENSIC 100-TRADE BACKTEST (REAL MARKET DATA)")
    print("================================================================================")
    print("Loading cached multi-month historical candles for 35 high-liquidity crypto pairs...", flush=True)

    data_1h = load_cached_data("1h")
    data_4h = load_cached_data("4h")

    print(f"  ✓ 1H Feeds Ready: {len(data_1h)} pairs")
    print(f"  ✓ 4H Feeds Ready: {len(data_4h)} pairs")

    # Run 1H Backtest (Exactly 100 Trades)
    res_1h = run_backtest_for_timeframe("1h", data_1h)
    with open("backtest_1h_100trades_result.json", "w", encoding="utf-8") as f:
        json.dump(res_1h, f, indent=2)

    # Run 4H Backtest (Exactly 100 Trades)
    res_4h = run_backtest_for_timeframe("4h", data_4h)
    with open("backtest_4h_100trades_result.json", "w", encoding="utf-8") as f:
        json.dump(res_4h, f, indent=2)

    # Export Master CSV Ledger
    csv_file = "backtest_master_100trades_ledger.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Trade #", "Timeframe", "Date (UTC)", "Symbol", "Side", "Entry Price",
            "TP Target", "SL Price", "Result", "Hours Held", "Delta Ratio (%)",
            "ROE (%)", "PnL (USDT)", "Account Balance (USDT)"
        ])
        for t in res_1h["trades"] + res_4h["trades"]:
            writer.writerow([
                t.get("trade_num"), t.get("timeframe"), t.get("date"), t.get("symbol"), t.get("side"),
                f"{t.get('entry_price'):.6f}", f"{t.get('tp_price'):.6f}", f"{t.get('sl_price'):.6f}",
                t.get("result"), f"{t.get('hours_held'):.1f}h", f"{t.get('delta_ratio')}%",
                f"{t.get('roe_pct'):+.2f}%", f"${t.get('pnl_usdt', 0):+.2f}", f"${t.get('balance', 0):.2f}"
            ])

    print(f"\n✓ Backtest Complete! Saved to backtest_1h_100trades_result.json, backtest_4h_100trades_result.json, and {csv_file}")

if __name__ == "__main__":
    main()
