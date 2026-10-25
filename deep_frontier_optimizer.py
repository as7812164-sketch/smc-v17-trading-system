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

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_local_data(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def run_frontier_sweep():
    print("=" * 115)
    print(" 🚀 DEEP FRONTIER OPTIMIZATION: SYSTEMATIC SEARCH FOR THE HERMES 20X CONQUEROR")
    print(" Dataset: 1 Full Year (339,512 Candlesticks) across Top-22 Champions")
    print("=" * 115)

    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    btc_4h = load_local_data("BTCUSDT", "4h")
    btc_map_4h = {c["time"]: c for c in btc_4h}

    def simulate(signals):
        signals.sort(key=lambda x: x["time"])
        executed = []
        active_exit = 0
        for s in signals:
            if s["time"] >= active_exit:
                executed.append(s)
                active_exit = s["exit_time"]

        cap = 50.0; vault = 0.0; peak = 50.0; max_dd = 0.0; hit_1k = None
        wins = 0; losses = 0; gp = 0.0; gl = 0.0

        for idx, trade in enumerate(executed):
            net_move = trade["gross"] - 0.0016
            pos_size = cap * 5.0
            pnl = pos_size * net_move

            if net_move > 0:
                wins += 1; gp += pnl
                cap += (pnl * 0.85); vault += (pnl * 0.15)
            else:
                losses += 1; gl += abs(pnl)
                cap += pnl
                if cap < 2.0: cap = 0.0

            tot = cap + vault
            if tot > peak: peak = tot
            dd = (peak - tot) / peak if peak > 0 else 0
            if dd > max_dd: max_dd = dd

            if tot >= 1000.0 and hit_1k is None:
                hit_1k = idx + 1
            if cap <= 0: break

        wr = (wins / len(executed) * 100.0) if executed else 0.0
        pf = (gp / gl) if gl > 0 else 99.0
        return {
            "trades": len(executed), "wins": wins, "losses": losses, "win_rate": wr,
            "max_dd": max_dd * 100.0, "hit_1k": hit_1k, "final_wealth": cap + vault, "pf": pf
        }

    # Parameterized runner
    def run_strategy(params):
        min_gain = params.get("min_gain", 0.045)
        min_wick = params.get("min_wick", 0.18)
        tp_1h = params.get("tp_1h", 0.022)
        tp_4h = params.get("tp_4h", 0.028)
        soft_sl_1h = params.get("soft_sl_1h", 0.025)
        soft_sl_4h = params.get("soft_sl_4h", 0.028)
        hard_sl_1h = params.get("hard_sl_1h", 0.036)
        hard_sl_4h = params.get("hard_sl_4h", 0.038)
        btc_brake = params.get("btc_brake", False)
        max_tap_bars = params.get("max_tap_bars", 35)
        be_trigger = params.get("be_trigger", None) # e.g. 0.016
        be_lock = params.get("be_lock", 0.0025)     # Entry + 0.25% (ensures net positive after 0.16% fee)
        include_extreme_ob = params.get("include_extreme_ob", False)
        exclude_toxic = params.get("exclude_toxic", [])

        signals = []
        for tf in ["1h", "4h"]:
            tp_pct = tp_1h if tf == "1h" else tp_4h
            soft_sl_pct = soft_sl_1h if tf == "1h" else soft_sl_4h
            hard_sl_pct = hard_sl_1h if tf == "1h" else hard_sl_4h
            max_hold = 24

            for sym, candles in all_data[tf].items():
                if sym in exclude_toxic: continue
                n = len(candles)
                for i in range(25, n - 35):
                    # Bullish
                    if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                        sub_w = candles[i:min(i+16, n)]
                        highs = [c["high"] for c in sub_w]
                        max_high = max(highs)
                        high_idx = i + highs.index(max_high)
                        if high_idx > i + 3:
                            gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                            if gain >= min_gain:
                                idm_low = candles[high_idx - 1]["low"]
                                best_mid = -1; max_bg = 0.0
                                for mid in range(i+1, high_idx):
                                    bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                    fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                                        max_bg = bg; best_mid = mid
                                
                                obs_to_test = []
                                if best_mid != -1:
                                    dec_c = candles[best_mid - 1]
                                    dec_top = max(dec_c["open"], dec_c["close"])
                                    dec_bot = dec_c["low"]
                                    has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                    if has_fvg:
                                        obs_to_test.append(("DECISIONAL", dec_top, dec_bot))

                                if include_extreme_ob:
                                    ext_c = candles[i]
                                    ext_top = max(ext_c["open"], ext_c["close"])
                                    ext_bot = ext_c["low"]
                                    obs_to_test.append(("EXTREME", ext_top, ext_bot))

                                for ob_type, ob_top, ob_bot in obs_to_test:
                                    for t in range(high_idx + 1, min(high_idx + max_tap_bars, n)):
                                        if candles[t]["low"] <= ob_top * 0.9995:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]

                                            if btc_brake and sym != "BTCUSDT":
                                                t_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                                btc_c = btc_map_4h.get(t_ts)
                                                if btc_c and (btc_c["open"] - btc_c["close"]) / btc_c["open"] > 0.020:
                                                    break

                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (ob_top + ob_bot) / 2.0
                                            if swept and w_ratio >= min_wick and tap_c["close"] >= mt:
                                                entry = ob_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)
                                                
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                be_active = False
                                                curr_soft_sl = soft_sl_p

                                                for m in range(t, min(t + max_hold, n)):
                                                    if be_trigger and not be_active:
                                                        if candles[m]["high"] >= entry * (1.0 + be_trigger):
                                                            be_active = True
                                                            curr_soft_sl = entry * (1.0 + be_lock)

                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if not be_active and candles[m]["low"] <= hard_sl_p:
                                                        res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] <= curr_soft_sl:
                                                        exit_p = candles[m]["close"]
                                                        exit_t = candles[m]["time"]
                                                        res = "WIN" if (exit_p > entry * (1.0 + 0.0016)) else "LOSS"
                                                        break

                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc > entry * (1.0 + 0.0016) else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                signals.append({
                                                    "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (exit_p - entry) / entry, "res": res
                                                })
                                            break
                                    if signals and signals[-1]["time"] == candles[t]["time"]:
                                        break # Don't double count both decisional and extreme on same tap

                    # Bearish
                    if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                        sub_w = candles[i:min(i+16, n)]
                        lows = [c["low"] for c in sub_w]
                        min_low = min(lows)
                        low_idx = i + lows.index(min_low)
                        if low_idx > i + 3:
                            drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                            if drop >= min_gain:
                                idm_high = candles[low_idx - 1]["high"]
                                best_mid = -1; max_bg = 0.0
                                for mid in range(i+1, low_idx):
                                    bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                    fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                                        max_bg = bg; best_mid = mid
                                
                                obs_to_test = []
                                if best_mid != -1:
                                    dec_c = candles[best_mid - 1]
                                    dec_top = dec_c["high"]
                                    dec_bot = min(dec_c["open"], dec_c["close"])
                                    has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                    if has_bear_fvg:
                                        obs_to_test.append(("DECISIONAL", dec_top, dec_bot))

                                if include_extreme_ob:
                                    ext_c = candles[i]
                                    ext_top = ext_c["high"]
                                    ext_bot = min(ext_c["open"], ext_c["close"])
                                    obs_to_test.append(("EXTREME", ext_top, ext_bot))

                                for ob_type, dec_top, dec_bot in obs_to_test:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_bars, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]

                                            if btc_brake and sym != "BTCUSDT":
                                                t_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                                btc_c = btc_map_4h.get(t_ts)
                                                if btc_c and (btc_c["close"] - btc_c["open"]) / btc_c["open"] > 0.020:
                                                    break

                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= min_wick and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)
                                                
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                be_active = False
                                                curr_soft_sl = soft_sl_p

                                                for m in range(t, min(t + max_hold, n)):
                                                    if be_trigger and not be_active:
                                                        if candles[m]["low"] <= entry * (1.0 - be_trigger):
                                                            be_active = True
                                                            curr_soft_sl = entry * (1.0 - be_lock)

                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if not be_active and candles[m]["high"] >= hard_sl_p:
                                                        res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] >= curr_soft_sl:
                                                        exit_p = candles[m]["close"]
                                                        exit_t = candles[m]["time"]
                                                        res = "WIN" if (exit_p < entry * (1.0 - 0.0016)) else "LOSS"
                                                        break

                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc < entry * (1.0 - 0.0016) else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                signals.append({
                                                    "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (entry - exit_p) / entry, "res": res
                                                })
                                            break
                                    if signals and signals[-1]["time"] == candles[t]["time"]:
                                        break
        return signals

    # Baseline
    base_params = {}
    base_sigs = run_strategy(base_params)
    base_perf = simulate(base_sigs)
    print("👑 HERMES 20X BASELINE:")
    print(f"  Trades: {base_perf['trades']}, WR: {base_perf['win_rate']:.2f}% ({base_perf['wins']}W/{base_perf['losses']}L), MaxDD: {base_perf['max_dd']:.2f}%, 1K: #{base_perf['hit_1k']}, PF: {base_perf['pf']:.2f}, End: ${base_perf['final_wealth']:,.2f}\n")

    # Sweep grid
    test_suite = [
        {"name": "V1: BTC Flash Brake", "btc_brake": True},
        {"name": "V2: BTC Flash Brake + Max Tap 28 bars", "btc_brake": True, "max_tap_bars": 28},
        {"name": "V3: BTC Flash Brake + Min Wick 20%", "btc_brake": True, "min_wick": 0.20},
        {"name": "V4: BTC Flash Brake + Min Gain 4.8%", "btc_brake": True, "min_gain": 0.048},
        {"name": "V5: BTC Flash Brake + Fee-Shield (BE @ 1.8%, lock +0.25%)", "btc_brake": True, "be_trigger": 0.018, "be_lock": 0.0025},
        {"name": "V6: BTC Flash Brake + Fee-Shield (BE @ 1.9%, lock +0.25%)", "btc_brake": True, "be_trigger": 0.019, "be_lock": 0.0025},
        {"name": "V7: BTC Brake + BE @ 1.8% + Min Wick 20%", "btc_brake": True, "be_trigger": 0.018, "be_lock": 0.0025, "min_wick": 0.20},
        {"name": "V8: BTC Brake + Higher 4H TP (3.0%)", "btc_brake": True, "tp_4h": 0.030},
        {"name": "V9: BTC Brake + Exclude Top Loss Outlier (APTUSDT)", "btc_brake": True, "exclude_toxic": ["APTUSDT"]},
        {"name": "V10: BTC Brake + Exclude 2 Outliers (APT, ICP)", "btc_brake": True, "exclude_toxic": ["APTUSDT", "ICPUSDT"]},
        {"name": "V11: BTC Brake + Exclude 3 Outliers (APT, ICP, SAND)", "btc_brake": True, "exclude_toxic": ["APTUSDT", "ICPUSDT", "SANDUSDT"]},
        {"name": "V12: Master AI Ensemble (BTC Brake + Wick 20% + Fresh 28b + Exclude APT, ICP)", "btc_brake": True, "min_wick": 0.20, "max_tap_bars": 28, "exclude_toxic": ["APTUSDT", "ICPUSDT"]},
        {"name": "V13: Master AI Ensemble + 4H TP 3.0%", "btc_brake": True, "min_wick": 0.20, "max_tap_bars": 28, "exclude_toxic": ["APTUSDT", "ICPUSDT"], "tp_4h": 0.030},
        {"name": "V14: Master AI Ensemble + Extreme OBs", "btc_brake": True, "min_wick": 0.20, "max_tap_bars": 28, "exclude_toxic": ["APTUSDT", "ICPUSDT"], "include_extreme_ob": True},
        {"name": "V15: Master AI Ensemble + Extreme OBs + 4H TP 3.0%", "btc_brake": True, "min_wick": 0.20, "max_tap_bars": 28, "exclude_toxic": ["APTUSDT", "ICPUSDT"], "include_extreme_ob": True, "tp_4h": 0.030},
    ]

    print(f"{'Configuration':<65} | {'Trades':<6} | {'Win Rate':<9} | {'Max DD':<7} | {'1K Hit':<7} | {'PF':<6} | {'Final Wealth'}")
    print("-" * 130)

    for item in test_suite:
        sigs = run_strategy(item)
        perf = simulate(sigs)
        h_str = f"#{perf['hit_1k']}" if perf['hit_1k'] else "FAILED"
        print(f"{item['name']:<65} | {perf['trades']:<6} | {perf['win_rate']:>6.2f}%   | {perf['max_dd']:>6.2f}% | {h_str:<7} | {perf['pf']:>6.2f} | ${perf['final_wealth']:>16,.2f}")

if __name__ == "__main__":
    run_frontier_sweep()
