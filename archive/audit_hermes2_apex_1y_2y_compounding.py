import json
import time
import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_1Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")
DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")

def load_data(sym, interval, dataset="1y"):
    folder = DATA_DIR_1Y if dataset == "1y" else DATA_DIR_2Y
    fpath = os.path.join(folder, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def run_hermes2_apex_engine(interval, dataset="1y"):
    """
    Executes HERMES 2.0 APEX engine on a specific timeframe and duration.
    Calculates exact MAE, MFE, and real candle close gap slippage.
    """
    btc_4h = load_data("BTCUSDT", "4h", dataset)
    btc_map_4h = {c["time"]: c for c in btc_4h}

    candles_map = {}
    for sym in TOP_22_CHAMPIONS:
        k = load_data(sym, interval, dataset)
        if len(k) >= 400:
            candles_map[sym] = k

    tp_pct = 0.022 if interval == "1h" else 0.028
    soft_sl_pct = 0.025 if interval == "1h" else 0.028
    hard_sl_pct = 0.036 if interval == "1h" else 0.038
    max_hold = 24
    min_displacement = 0.050 # Sentry 2: 5.0% Institutional Floor
    max_tap_window = 28      # Sentry 4: Freshness Guard (Strict 28-Bar Cap)

    raw_signals = []

    for sym, candles in candles_map.items():
        n = len(candles)
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
                                    if candles[t]["low"] <= dec_top * 0.9995:
                                        tap_c = candles[t]
                                        
                                        # Sentry 1: Macro Causal BTC Dump Brake
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        if btc_c and (btc_c["open"] - btc_c["close"]) / btc_c["open"] >= 0.020:
                                            break # Macro dump veto!

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

                                            # Calculate exact MAE & MFE
                                            deepest_low = min(trade_lows)
                                            highest_high = max(trade_highs)
                                            mae = (entry - deepest_low) / entry * 100.0 # Adverse dip %
                                            mfe = (highest_high - entry) / entry * 100.0 # Favorable run %

                                            raw_signals.append({
                                                "sym": sym, "side": "LONG", "interval": interval,
                                                "entry_time": tap_c["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross": (exit_p - entry) / entry,
                                                "res": res, "bars_held": bars_held,
                                                "mae": mae, "mfe": mfe
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
                                    if candles[t]["high"] >= dec_bot * 1.0005:
                                        tap_c = candles[t]
                                        
                                        # Sentry 1: Macro Causal BTC Pump Brake
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        if btc_c and (btc_c["close"] - btc_c["open"]) / btc_c["open"] >= 0.020:
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
                                            mae = (highest_high - entry) / entry * 100.0 # Adverse rise %
                                            mfe = (entry - deepest_low) / entry * 100.0 # Favorable drop %

                                            raw_signals.append({
                                                "sym": sym, "side": "SHORT", "interval": interval,
                                                "entry_time": tap_c["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross": (entry - exit_p) / entry,
                                                "res": res, "bars_held": bars_held,
                                                "mae": mae, "mfe": mfe
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

    # Compounding Simulation to $2,000 USDT (40x Target)
    target_cap = 2000.0
    cap = 50.0
    vault = 0.0
    peak_wealth = 50.0
    max_dd = 0.0
    hit_2k_trade = None
    hit_2k_days = None
    start_time = executed[0]["entry_time"] if executed else 0

    wins = 0; losses = 0; gp = 0.0; gl = 0.0
    trade_logs = []

    for idx, t in enumerate(executed):
        pos_size = cap * 5.0 # 5x leverage
        net_move = t["gross"] - 0.0016 # 0.16% round-trip fee
        pnl = pos_size * net_move

        if trade_res := (t["res"] == "WIN"):
            wins += 1; gp += pnl
            cap += (pnl * 0.85); vault += (pnl * 0.15)
        else:
            losses += 1; gl += abs(pnl)
            cap += pnl
            if cap < 2.0: cap = 0.0

        total_wealth = cap + vault
        if total_wealth > peak_wealth:
            peak_wealth = total_wealth
        dd = (peak_wealth - total_wealth) / peak_wealth if peak_wealth > 0 else 0
        if dd > max_dd:
            max_dd = dd

        # Check $2,000 milestone
        if total_wealth >= target_cap and hit_2k_trade is None:
            hit_2k_trade = idx + 1
            hit_2k_days = (t["exit_time"] - start_time) / (1000 * 3600 * 24)

        trade_logs.append({
            "trade_num": idx + 1,
            "sym": t["sym"],
            "side": t["side"],
            "entry_time": t["entry_time"],
            "exit_time": t["exit_time"],
            "entry_price": t["entry"],
            "exit_price": t["exit"],
            "gross_move_pct": round(t["gross"] * 100.0, 3),
            "result": t["res"],
            "pnl_usdt": round(pnl, 2),
            "mae_pct": round(t["mae"], 3),
            "mfe_pct": round(t["mfe"], 3),
            "bars_held": t["bars_held"],
            "active_cap": round(cap, 2),
            "vault_stash": round(vault, 2),
            "total_wealth": round(total_wealth, 2),
            "current_dd_pct": round(dd * 100.0, 2)
        })

        if cap <= 0: break

    wr = (wins / len(executed) * 100.0) if executed else 0.0
    pf = (gp / gl) if gl > 0 else 99.0

    maes = [t["mae"] for t in executed]
    mfes = [t["mfe"] for t in executed]
    winner_maes = [t["mae"] for t in executed if t["res"] == "WIN"]
    loser_maes = [t["mae"] for t in executed if t["res"] == "LOSS"]

    return {
        "interval": interval,
        "dataset": dataset,
        "total_trades": len(executed),
        "wins": wins,
        "losses": losses,
        "win_rate": wr,
        "max_dd": max_dd * 100.0,
        "hit_2k_trade": hit_2k_trade,
        "hit_2k_days": round(hit_2k_days, 1) if hit_2k_days else None,
        "final_wealth": round(cap + vault, 2),
        "profit_factor": round(pf, 2),
        "median_mae_all": round(float(np.median(maes)), 3) if maes else 0.0,
        "median_mae_winners": round(float(np.median(winner_maes)), 3) if winner_maes else 0.0,
        "median_mae_losers": round(float(np.median(loser_maes)), 3) if loser_maes else 0.0,
        "median_mfe_all": round(float(np.median(mfes)), 3) if mfes else 0.0,
        "trade_logs": trade_logs
    }

def main():
    print("=" * 115)
    print(" 🚀 HERMES 2.0 APEX: REAL-MARKET 1-YEAR & 2-YEAR COMPREHENSIVE COMPASS AUDIT")
    print(" Target: $50 USDT Compounding to $2,000 USDT (40x Target) on 1H vs 4H Separately")
    print(" Exact MAE & MFE Analytics | Real Candle Close Exits | 0.16% Fees | Strict 1-Trade Queue")
    print("=" * 115)

    experiments = [
        ("1h", "1y"),
        ("4h", "1y"),
        ("1h", "2y"),
        ("4h", "2y")
    ]

    all_results = {}

    for interval, dataset in experiments:
        print(f"\n⏳ Processing [{interval.upper()} - {dataset.upper()}] dataset...")
        res = run_hermes2_apex_engine(interval, dataset)
        tag = f"{interval}_{dataset}"
        all_results[tag] = res

        # Save individual trade logs
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"hermes2_apex_trades_{tag}.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(res["trade_logs"], f, indent=2)

        print(f"  • Trades: {res['total_trades']:<4} | Win Rate: {res['win_rate']:>6.2f}% | Max DD: {res['max_dd']:>5.2f}%")
        hit_txt = f"Trade #{res['hit_2k_trade']} in {res['hit_2k_days']} days" if res['hit_2k_trade'] else "❌ FAILED"
        print(f"  • $2,000 Milestone: {hit_txt} | Final Wealth: ${res['final_wealth']:,.2f} USDT | PF: {res['profit_factor']}")
        print(f"  • MAE (Med Winners): {res['median_mae_winners']}% | MFE (Med All): {res['median_mfe_all']}%")
        print(f"  • Trade log saved to: {log_path}")

    # Summary JSON (excluding full trade logs for compact size)
    summary_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hermes2_apex_1y_2y_master_audit.json")
    compact = {k: {x: y for x, y in v.items() if x != "trade_logs"} for k, v in all_results.items()}
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(compact, f, indent=2)

    print("\n" + "=" * 115)
    print(" 🏆 FINAL 1Y vs 2Y & 1H vs 4H COMPARISON TABLE ($50 ➔ $2,000 USDT COMPOUNDING)")
    print("=" * 115)
    print(f"{'EXPERIMENT':<12} | {'TRADES':<7} | {'WIN RATE':<9} | {'MAX DD':<8} | {'$2,000 HIT AT':<25} | {'MED MAE (WIN)':<14} | {'PF':<5}")
    print("-" * 115)
    for tag, r in compact.items():
        hit_str = f"Trade #{r['hit_2k_trade']} ({r['hit_2k_days']} days)" if r['hit_2k_trade'] else "❌ FAILED"
        print(f"{tag.upper():<12} | {r['total_trades']:<7} | {r['win_rate']:>6.2f}%   | {r['max_dd']:>6.2f}% | {hit_str:<25} | {r['median_mae_winners']:>5.2f}%         | {r['profit_factor']:>4.2f}")
    print("=" * 115)
    print(f"✅ Full Audit Data & Summary Saved to: {summary_path}")

if __name__ == "__main__":
    main()
