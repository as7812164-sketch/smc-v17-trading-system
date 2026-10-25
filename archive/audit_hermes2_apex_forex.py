import json
import time
import os
import sys
import numpy as np
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOREX_DATA_DIR = os.path.join(BASE_DIR, "historical_data_forex")

FOREX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"
]

def load_forex_candles(sym, interval):
    fpath = os.path.join(FOREX_DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def run_forex_engine(interval, mode="calibrated", leverage=20.0):
    """
    Executes HERMES 2.0 APEX on Forex dataset.
    mode='raw_crypto': uses raw crypto 5% displacement and 2.8% TP/SL.
    mode='calibrated': uses Forex volatility scaled displacement and TP/SL.
    """
    dxy_4h = load_forex_candles("DX_Y_NYB", "4h")
    dxy_map_4h = {c["time"]: c for c in dxy_4h}

    candles_map = {}
    for sym in FOREX_PAIRS:
        k = load_forex_candles(sym, interval)
        if len(k) >= 500:
            candles_map[sym] = k

    if mode == "raw_crypto":
        # Unmodified Crypto parameters
        min_displacement = 0.050
        tp_pct = 0.022 if interval == "1h" else 0.028
        soft_sl_pct = 0.025 if interval == "1h" else 0.028
        hard_sl_pct = 0.036 if interval == "1h" else 0.038
    else:
        # Forex Volatility-Calibrated parameters
        min_displacement = 0.0035 if interval == "1h" else 0.0050 # 35 pips (1h) / 50 pips (4h)
        tp_pct = 0.0035 if interval == "1h" else 0.0048           # 35 pips (1h) / 48 pips (4h)
        soft_sl_pct = 0.0028 if interval == "1h" else 0.0038      # 28 pips (1h) / 38 pips (4h)
        hard_sl_pct = 0.0045 if interval == "1h" else 0.0060      # 45 pips (1h) / 60 pips (4h)

    max_hold = 24
    max_tap_window = 28 # Strict 28-Bar Freshness Guard

    raw_signals = []

    for sym, candles in candles_map.items():
        n = len(candles)
        # Pip multiplier for MAE/MFE display
        pip_mult = 100.0 if "JPY" in sym else 10000.0

        for i in range(25, n - 35):
            # -----------------------------------------------------------------
            # BULLISH SETUP
            # -----------------------------------------------------------------
            if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 3:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= min_displacement:
                        idm_low = candles[high_idx - 1]["low"]
                        best_mid = -1; max_bg = 0.0
                        for mid in range(i+1, high_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg; best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = max(dec_c["open"], dec_c["close"])
                            dec_bot = dec_c["low"]
                            has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                            if has_fvg:
                                for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                    if candles[t]["low"] <= dec_top * 0.9998:
                                        tap_c = candles[t]
                                        
                                        # Macro Forex DXY Sentry:
                                        # If symbol is EURUSD, GBPUSD, AUDUSD, NZDUSD (USD is quote):
                                        # Strong DXY pump (>=0.30%) vetoes Longs!
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        dxy_c = dxy_map_4h.get(prev_4h_ts)
                                        if dxy_c:
                                            dxy_move = (dxy_c["close"] - dxy_c["open"]) / dxy_c["open"]
                                            if sym in ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"] and dxy_move >= 0.0030:
                                                break
                                            if sym in ["USDJPY", "USDCAD", "USDCHF"] and dxy_move <= -0.0030:
                                                break

                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0
                                        
                                        # Sentry 3: IDM Sweep + >=18% Wick Absorption + 50% MT
                                        if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                            entry = dec_top
                                            tp_p = entry * (1.0 + tp_pct)
                                            soft_sl_p = entry * (1.0 - soft_sl_pct)
                                            hard_sl_p = entry * (1.0 - hard_sl_pct)

                                            res = None; exit_p = entry; exit_t = tap_c["time"]
                                            bars_held = 1
                                            trade_lows = [tap_c["low"]]
                                            trade_highs = [tap_c["high"]]

                                            for m in range(t, min(t + max_hold, n)):
                                                bars_held = m - t + 1
                                                trade_lows.append(candles[m]["low"])
                                                trade_highs.append(candles[m]["high"])

                                                if candles[m]["high"] >= tp_p:
                                                    res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                if candles[m]["low"] <= hard_sl_p:
                                                    res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                if candles[m]["close"] <= soft_sl_p:
                                                    res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break

                                            if not res:
                                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                                res = "WIN" if fc >= entry else "LOSS"
                                                exit_p = fc
                                                exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                bars_held = max_hold

                                            deepest_low = min(trade_lows)
                                            highest_high = max(trade_highs)
                                            mae = (entry - deepest_low) / entry * 100.0
                                            mfe = (highest_high - entry) / entry * 100.0
                                            mae_pips = (entry - deepest_low) * pip_mult
                                            mfe_pips = (highest_high - entry) * pip_mult

                                            raw_signals.append({
                                                "sym": sym, "side": "LONG", "interval": interval,
                                                "entry_time": tap_c["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross": (exit_p - entry) / entry,
                                                "res": res, "bars_held": bars_held,
                                                "mae_pct": mae, "mfe_pct": mfe,
                                                "mae_pips": mae_pips, "mfe_pips": mfe_pips
                                            })
                                        break

            # -----------------------------------------------------------------
            # BEARISH SETUP
            # -----------------------------------------------------------------
            if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                lows = [c["low"] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)
                if low_idx > i + 3:
                    drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                    if drop >= min_displacement:
                        idm_high = candles[low_idx - 1]["high"]
                        best_mid = -1; max_bg = 0.0
                        for mid in range(i+1, low_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                            fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg; best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = dec_c["high"]
                            dec_bot = min(dec_c["open"], dec_c["close"])
                            has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                            if has_bear_fvg:
                                for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                    if candles[t]["high"] >= dec_bot * 1.0002:
                                        tap_c = candles[t]
                                        
                                        # Macro DXY Sentry
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        dxy_c = dxy_map_4h.get(prev_4h_ts)
                                        if dxy_c:
                                            dxy_move = (dxy_c["close"] - dxy_c["open"]) / dxy_c["open"]
                                            if sym in ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"] and dxy_move <= -0.0030:
                                                break
                                            if sym in ["USDJPY", "USDCAD", "USDCHF"] and dxy_move >= 0.0030:
                                                break

                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                        u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0

                                        if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                            entry = dec_bot
                                            tp_p = entry * (1.0 - tp_pct)
                                            soft_sl_p = entry * (1.0 + soft_sl_pct)
                                            hard_sl_p = entry * (1.0 + hard_sl_pct)

                                            res = None; exit_p = entry; exit_t = tap_c["time"]
                                            bars_held = 1
                                            trade_highs = [tap_c["high"]]
                                            trade_lows = [tap_c["low"]]

                                            for m in range(t, min(t + max_hold, n)):
                                                bars_held = m - t + 1
                                                trade_highs.append(candles[m]["high"])
                                                trade_lows.append(candles[m]["low"])

                                                if candles[m]["low"] <= tp_p:
                                                    res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                if candles[m]["high"] >= hard_sl_p:
                                                    res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                if candles[m]["close"] >= soft_sl_p:
                                                    res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break

                                            if not res:
                                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                                res = "WIN" if fc <= entry else "LOSS"
                                                exit_p = fc
                                                exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                bars_held = max_hold

                                            highest_high = max(trade_highs)
                                            deepest_low = min(trade_lows)
                                            mae = (highest_high - entry) / entry * 100.0
                                            mfe = (entry - deepest_low) / entry * 100.0
                                            mae_pips = (highest_high - entry) * pip_mult
                                            mfe_pips = (entry - deepest_low) * pip_mult

                                            raw_signals.append({
                                                "sym": sym, "side": "SHORT", "interval": interval,
                                                "entry_time": tap_c["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross": (entry - exit_p) / entry,
                                                "res": res, "bars_held": bars_held,
                                                "mae_pct": mae, "mfe_pct": mfe,
                                                "mae_pips": mae_pips, "mfe_pips": mfe_pips
                                            })
                                        break

    raw_signals.sort(key=lambda x: x["entry_time"])

    # Strict 1-Trade Sequential Queue
    executed = []
    active_exit = 0
    for s in raw_signals:
        if s["entry_time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    # Compounding Simulation: $50 USDT -> $2,000 USDT Target
    target_cap = 2000.0
    cap = 50.0
    vault = 0.0
    peak_wealth = 50.0
    max_dd = 0.0
    hit_2k_trade = None
    hit_2k_days = None
    start_time = executed[0]["entry_time"] if executed else 0

    wins = 0; losses = 0; gp = 0.0; gl = 0.0
    long_wins = 0; long_losses = 0
    short_wins = 0; short_losses = 0
    trade_logs = []

    # Realistic Forex Spread/Commission: 0.02% (2 pips on major pairs)
    forex_fee_pct = 0.0002

    for idx, t in enumerate(executed):
        pos_size = cap * leverage
        net_move = t["gross"] - forex_fee_pct
        pnl = pos_size * net_move

        if t["res"] == "WIN":
            wins += 1; gp += pnl
            if t["side"] == "LONG": long_wins += 1
            else: short_wins += 1
            cap += (pnl * 0.85); vault += (pnl * 0.15)
        else:
            losses += 1; gl += abs(pnl)
            if t["side"] == "LONG": long_losses += 1
            else: short_losses += 1
            cap += pnl
            if cap < 2.0: cap = 0.0

        total_wealth = cap + vault
        if total_wealth > peak_wealth:
            peak_wealth = total_wealth
        dd = (peak_wealth - total_wealth) / peak_wealth if peak_wealth > 0 else 0
        if dd > max_dd:
            max_dd = dd

        if total_wealth >= target_cap and hit_2k_trade is None:
            hit_2k_trade = idx + 1
            hit_2k_days = (t["exit_time"] - start_time) / (1000 * 3600 * 24)

        entry_dt = datetime.utcfromtimestamp(t["entry_time"] / 1000).strftime("%Y-%m-%d %H:%M")
        exit_dt = datetime.utcfromtimestamp(t["exit_time"] / 1000).strftime("%Y-%m-%d %H:%M")

        trade_logs.append({
            "trade_num": idx + 1,
            "sym": t["sym"],
            "side": t["side"],
            "entry_time_utc": entry_dt,
            "exit_time_utc": exit_dt,
            "entry_price": round(t["entry"], 5),
            "exit_price": round(t["exit"], 5),
            "gross_move_pct": round(t["gross"] * 100.0, 3),
            "result": t["res"],
            "pnl_usdt": round(pnl, 2),
            "mae_pct": round(t["mae_pct"], 3),
            "mfe_pct": round(t["mfe_pct"], 3),
            "mae_pips": round(t["mae_pips"], 1),
            "mfe_pips": round(t["mfe_pips"], 1),
            "bars_held": t["bars_held"],
            "active_cap": round(cap, 2),
            "vault_stash": round(vault, 2),
            "total_wealth": round(total_wealth, 2),
            "current_dd_pct": round(dd * 100.0, 2)
        })

        if cap <= 0: break

    wr = (wins / len(executed) * 100.0) if executed else 0.0
    pf = (gp / gl) if gl > 0 else 99.0

    maes = [t["mae_pct"] for t in executed]
    mfes = [t["mfe_pct"] for t in executed]
    mae_pips_list = [t["mae_pips"] for t in executed]
    mfe_pips_list = [t["mfe_pips"] for t in executed]
    winner_maes = [t["mae_pct"] for t in executed if t["res"] == "WIN"]
    loser_maes = [t["mae_pct"] for t in executed if t["res"] == "LOSS"]

    return {
        "mode": mode,
        "interval": interval,
        "leverage": leverage,
        "coins_tested": len(candles_map),
        "total_trades": len(executed),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "long_trades": long_wins + long_losses,
        "long_wr": round((long_wins / (long_wins + long_losses) * 100.0), 2) if (long_wins + long_losses) > 0 else 0.0,
        "short_trades": short_wins + short_losses,
        "short_wr": round((short_wins / (short_wins + short_losses) * 100.0), 2) if (short_wins + short_losses) > 0 else 0.0,
        "max_dd": round(max_dd * 100.0, 2),
        "hit_2k_trade": hit_2k_trade,
        "hit_2k_days": round(hit_2k_days, 1) if hit_2k_days else None,
        "final_wealth": round(cap + vault, 2),
        "vault_stash": round(vault, 2),
        "profit_factor": round(pf, 2),
        "mae_stats": {
            "median_pct": round(float(np.median(maes)), 3) if maes else 0.0,
            "median_pips": round(float(np.median(mae_pips_list)), 1) if mae_pips_list else 0.0,
            "median_winners_pct": round(float(np.median(winner_maes)), 3) if winner_maes else 0.0,
            "median_losers_pct": round(float(np.median(loser_maes)), 3) if loser_maes else 0.0,
        },
        "mfe_stats": {
            "median_pct": round(float(np.median(mfes)), 3) if mfes else 0.0,
            "median_pips": round(float(np.median(mfe_pips_list)), 1) if mfe_pips_list else 0.0,
        },
        "trade_logs": trade_logs
    }

def main():
    print("=" * 115)
    print(" 🌍 HERMES 2.0 APEX: REAL FOREX 2-YEAR QUANT AUDIT (1H & 4H)")
    print(" 10 Top Currency Pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, EURGBP, EURJPY, GBPJPY")
    print(" Testing: Raw Crypto Parameters vs Forex Volatility-Calibrated Edition")
    print(" Target: $50 USDT Compounding to $2,000 USDT (40x Target) with Exact MAE/MFE in % and Pips")
    print("=" * 115)

    experiments = [
        # 1. Raw Crypto parameters on Forex (to demonstrate why raw 5% crypto floor doesn't fit Forex)
        ("raw_crypto", "4h", 5.0),
        ("raw_crypto", "1h", 5.0),
        # 2. Calibrated Forex parameters at 5x leverage (Conservative)
        ("calibrated", "4h", 5.0),
        ("calibrated", "1h", 5.0),
        # 3. Calibrated Forex parameters at 20x leverage (Standard Forex retail/prop firm baseline)
        ("calibrated", "4h", 20.0),
        ("calibrated", "1h", 20.0),
        # 4. Calibrated Forex parameters at 30x leverage (Regulated Max)
        ("calibrated", "4h", 30.0),
        ("calibrated", "1h", 30.0)
    ]

    all_results = {}

    for mode, interval, lev in experiments:
        tag = f"{mode}_{interval}_{int(lev)}x"
        print(f"\n⏳ Running: [{mode.upper()}] [{interval.upper()}] Leverage {int(lev)}x...")
        res = run_forex_engine(interval, mode, lev)
        all_results[tag] = res

        # Save trade log for key runs
        if mode == "calibrated":
            log_file = os.path.join(BASE_DIR, f"hermes2_apex_forex_trades_{interval}_{int(lev)}x.json")
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(res["trade_logs"], f, indent=2)

        hit_txt = f"Trade #{res['hit_2k_trade']} in {res['hit_2k_days']} days" if res['hit_2k_trade'] else "❌ NOT REACHED"
        print(f"  • Trades: {res['total_trades']:<4} | Win Rate: {res['win_rate']:>6.2f}% (Long: {res['long_wr']}%, Short: {res['short_wr']}%) | Max DD: {res['max_dd']:>5.2f}%")
        print(f"  • $2,000 Milestone: {hit_txt} | Final Wealth: ${res['final_wealth']:,.2f} | PF: {res['profit_factor']}")
        if res['total_trades'] > 0:
            print(f"  • MAE: {res['mae_stats']['median_pct']}% ({res['mae_stats']['median_pips']} pips) | MFE: {res['mfe_stats']['median_pct']}% ({res['mfe_stats']['median_pips']} pips)")

    master_path = os.path.join(BASE_DIR, "hermes2_apex_forex_audit.json")
    with open(master_path, "w", encoding="utf-8") as f:
        summary = {k: {sub_k: v[sub_k] for sub_k in v if sub_k != "trade_logs"} for k, v in all_results.items()}
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 115)
    print("✅ Forex Backtest Audit Complete! Master summary saved to:")
    print(f"  {master_path}")
    print("=" * 115)

if __name__ == "__main__":
    main()
