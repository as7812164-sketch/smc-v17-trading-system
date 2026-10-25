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

def run_tuning():
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

    def run_sim(cfg):
        min_gain = cfg.get("min_gain", 0.050)
        min_wick = cfg.get("min_wick", 0.18)
        two_stage = cfg.get("two_stage", False)
        tp1_pct = cfg.get("tp1", 0.018)
        tp1_share = cfg.get("tp1_share", 0.50)
        tp2_pct = cfg.get("tp2", 0.028)
        tp2_share = 1.0 - tp1_share
        tp_single_1h = cfg.get("tp_single_1h", 0.022)
        tp_single_4h = cfg.get("tp_single_4h", 0.028)
        soft_sl_1h = cfg.get("soft_sl_1h", 0.025)
        soft_sl_4h = cfg.get("soft_sl_4h", 0.028)
        hard_sl_1h = 0.036; hard_sl_4h = 0.038
        max_hold = cfg.get("max_hold", 24)

        signals = []
        for tf in ["1h", "4h"]:
            tp_pct = tp_single_1h if tf == "1h" else tp_single_4h
            soft_sl_pct = soft_sl_1h if tf == "1h" else soft_sl_4h
            hard_sl_pct = hard_sl_1h if tf == "1h" else hard_sl_4h

            for sym, candles in all_data[tf].items():
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
                                if best_mid != -1:
                                    dec_c = candles[best_mid - 1]
                                    dec_top = max(dec_c["open"], dec_c["close"])
                                    dec_bot = dec_c["low"]
                                    has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                    if has_fvg:
                                        for t in range(high_idx + 1, min(high_idx + 35, n)):
                                            if candles[t]["low"] <= dec_top * 0.9995:
                                                tap_c = candles[t]
                                                c_range = tap_c["high"] - tap_c["low"]

                                                # BTC Flash Brake
                                                if sym != "BTCUSDT":
                                                    t_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                                    btc_c = btc_map_4h.get(t_ts)
                                                    if btc_c and (btc_c["open"] - btc_c["close"]) / btc_c["open"] > 0.020:
                                                        break

                                                swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                                l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0
                                                if swept and w_ratio >= min_wick and tap_c["close"] >= mt:
                                                    entry = dec_top
                                                    soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                    if not two_stage:
                                                        tp_p = entry * (1.0 + tp_pct)
                                                        res = None; exit_p = entry; exit_t = tap_c["time"]
                                                        for m in range(t, min(t + max_hold, n)):
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
                                                        gross = (exit_p - entry) / entry
                                                    else:
                                                        p1_hit = False; p2_hit = False
                                                        tp1_p = entry * (1.0 + tp1_pct)
                                                        tp2_p = entry * (1.0 + tp2_pct)
                                                        curr_soft_sl = soft_sl_p
                                                        exit_t = tap_c["time"]
                                                        gross_legs = []

                                                        for m in range(t, min(t + max_hold, n)):
                                                            if not p1_hit and candles[m]["high"] >= tp1_p:
                                                                p1_hit = True
                                                                gross_legs.append((tp1_share, tp1_pct))
                                                                curr_soft_sl = entry * 1.0020

                                                            if p1_hit and candles[m]["high"] >= tp2_p:
                                                                p2_hit = True
                                                                gross_legs.append((tp2_share, tp2_pct))
                                                                exit_t = candles[m]["time"]
                                                                break

                                                            if not p1_hit and candles[m]["low"] <= hard_sl_p:
                                                                loss_p = min(hard_sl_p, candles[m]["open"])
                                                                gross_legs.append((1.0, (loss_p - entry) / entry))
                                                                exit_t = candles[m]["time"]
                                                                break

                                                            if candles[m]["close"] <= curr_soft_sl:
                                                                close_p = candles[m]["close"]
                                                                ret = (close_p - entry) / entry
                                                                if not p1_hit:
                                                                    gross_legs.append((1.0, ret))
                                                                else:
                                                                    gross_legs.append((tp2_share, ret))
                                                                exit_t = candles[m]["time"]
                                                                break

                                                        if not p2_hit and len(gross_legs) < (2 if p1_hit else 1):
                                                            fc = candles[min(t + max_hold, n - 1)]["close"]
                                                            ret = (fc - entry) / entry
                                                            if not p1_hit:
                                                                gross_legs.append((1.0, ret))
                                                            else:
                                                                gross_legs.append((tp2_share, ret))
                                                            exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                        gross = sum(share * r for share, r in gross_legs)
                                                        res = "WIN" if gross > 0.0016 else "LOSS"

                                                    signals.append({
                                                        "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "gross": gross, "res": res
                                                    })
                                                break

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
                                if best_mid != -1:
                                    dec_c = candles[best_mid - 1]
                                    dec_top = dec_c["high"]
                                    dec_bot = min(dec_c["open"], dec_c["close"])
                                    has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                    if has_bear_fvg:
                                        for t in range(low_idx + 1, min(low_idx + 35, n)):
                                            if candles[t]["high"] >= dec_bot * 1.0005:
                                                tap_c = candles[t]
                                                c_range = tap_c["high"] - tap_c["low"]

                                                if sym != "BTCUSDT":
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
                                                    soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                    if not two_stage:
                                                        tp_p = entry * (1.0 - tp_pct)
                                                        res = None; exit_p = entry; exit_t = tap_c["time"]
                                                        for m in range(t, min(t + max_hold, n)):
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
                                                        gross = (entry - exit_p) / entry
                                                    else:
                                                        p1_hit = False; p2_hit = False
                                                        tp1_p = entry * (1.0 - tp1_pct)
                                                        tp2_p = entry * (1.0 - tp2_pct)
                                                        curr_soft_sl = soft_sl_p
                                                        exit_t = tap_c["time"]
                                                        gross_legs = []

                                                        for m in range(t, min(t + max_hold, n)):
                                                            if not p1_hit and candles[m]["low"] <= tp1_p:
                                                                p1_hit = True
                                                                gross_legs.append((tp1_share, tp1_pct))
                                                                curr_soft_sl = entry * 0.9980

                                                            if p1_hit and candles[m]["low"] <= tp2_p:
                                                                p2_hit = True
                                                                gross_legs.append((tp2_share, tp2_pct))
                                                                exit_t = candles[m]["time"]
                                                                break

                                                            if not p1_hit and candles[m]["high"] >= hard_sl_p:
                                                                loss_p = max(hard_sl_p, candles[m]["open"])
                                                                gross_legs.append((1.0, (entry - loss_p) / entry))
                                                                exit_t = candles[m]["time"]
                                                                break

                                                            if candles[m]["close"] >= curr_soft_sl:
                                                                close_p = candles[m]["close"]
                                                                ret = (entry - close_p) / entry
                                                                if not p1_hit:
                                                                    gross_legs.append((1.0, ret))
                                                                else:
                                                                    gross_legs.append((tp2_share, ret))
                                                                exit_t = candles[m]["time"]
                                                                break

                                                        if not p2_hit and len(gross_legs) < (2 if p1_hit else 1):
                                                            fc = candles[min(t + max_hold, n - 1)]["close"]
                                                            ret = (entry - fc) / entry
                                                            if not p1_hit:
                                                                gross_legs.append((1.0, ret))
                                                            else:
                                                                gross_legs.append((tp2_share, ret))
                                                            exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                        gross = sum(share * r for share, r in gross_legs)
                                                        res = "WIN" if gross > 0.0016 else "LOSS"

                                                    signals.append({
                                                        "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "gross": gross, "res": res
                                                    })
                                                break

        return simulate(signals)

    configs_to_test = [
        {"name": "Hermes Baseline Reference", "min_gain": 0.045, "min_wick": 0.18, "two_stage": False, "btc_brake": False},
        {"name": "AI Contender 1: Min Gain 5.0% + BTC Brake", "min_gain": 0.050, "min_wick": 0.18, "two_stage": False},
        {"name": "AI Contender 2: Min Gain 5.0% + Wick 20% + BTC Brake", "min_gain": 0.050, "min_wick": 0.20, "two_stage": False},
        {"name": "AI Contender 3: Min Gain 5.2% + BTC Brake", "min_gain": 0.052, "min_wick": 0.18, "two_stage": False},
        {"name": "AI Contender 4: Min Gain 5.0% + TP 2.4%/3.0%", "min_gain": 0.050, "tp_single_1h": 0.024, "tp_single_4h": 0.030, "two_stage": False},
        {"name": "AI Contender 5: Two-Stage (50% @ 1.7%, 50% @ 2.7%) + Gain 5.0%", "min_gain": 0.050, "two_stage": True, "tp1": 0.017, "tp2": 0.027},
        {"name": "AI Contender 6: Two-Stage (40% @ 1.6%, 60% @ 2.8%) + Gain 5.0%", "min_gain": 0.050, "two_stage": True, "tp1": 0.016, "tp1_share": 0.40, "tp2": 0.028},
        {"name": "AI Contender 7: Two-Stage (30% @ 1.6%, 70% @ 2.8%) + Gain 5.0%", "min_gain": 0.050, "two_stage": True, "tp1": 0.016, "tp1_share": 0.30, "tp2": 0.028},
        {"name": "AI Contender 8: Two-Stage (25% @ 1.6%, 75% @ 2.8%) + Gain 5.0%", "min_gain": 0.050, "two_stage": True, "tp1": 0.016, "tp1_share": 0.25, "tp2": 0.028},
    ]

    print(f"{'Config Name':<60} | {'Trades':<6} | {'Win Rate':<9} | {'Max DD':<7} | {'1K Hit':<7} | {'PF':<6} | {'Final Wealth'}")
    print("-" * 125)
    for c in configs_to_test:
        perf = run_sim(c)
        h_str = f"#{perf['hit_1k']}" if perf['hit_1k'] else "FAILED"
        print(f"{c['name']:<60} | {perf['trades']:<6} | {perf['win_rate']:>6.2f}%   | {perf['max_dd']:>6.2f}% | {h_str:<7} | {perf['pf']:>6.2f} | ${perf['final_wealth']:>16,.2f}")

if __name__ == "__main__":
    run_tuning()
