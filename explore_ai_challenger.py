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

def run_exploration():
    print("=" * 110)
    print(" 🔬 PROTOTYPING THE AI CHALLENGER: MULTI-AGENT ENSEMBLE SYSTEM")
    print(" Dataset: 1 Full Year (339,512 Candlesticks) across Top-22 Champions")
    print("=" * 110)

    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    btc_4h = load_local_data("BTCUSDT", "4h")
    btc_map_4h = {c["time"]: c for c in btc_4h}

    # Baseline Hermes 20X implementation
    def run_hermes_baseline():
        signals = []
        for tf in ["1h", "4h"]:
            tp_pct = 0.022 if tf == "1h" else 0.028
            soft_sl_pct = 0.025 if tf == "1h" else 0.028
            hard_sl_pct = 0.036 if tf == "1h" else 0.038
            max_hold = 24

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
                            if gain >= 0.045:
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
                                                swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                                l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0
                                                if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                    entry = dec_top
                                                    tp_p = entry * (1.0 + tp_pct)
                                                    soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 - hard_sl_pct)
                                                    
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

                                                    signals.append({
                                                        "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (exit_p - entry) / entry, "res": res
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
                            if drop >= 0.045:
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

                                                    signals.append({
                                                        "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (entry - exit_p) / entry, "res": res
                                                    })
                                                break
        return signals

    # Compounding simulator
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

            if trade["res"] == "WIN":
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

    h_sigs = run_hermes_baseline()
    h_perf = simulate(h_sigs)
    print("👑 Baseline HERMES 20X Performance:")
    print(f"  Trades: {h_perf['trades']}, WR: {h_perf['win_rate']:.2f}%, MaxDD: {h_perf['max_dd']:.2f}%, 1K Hit: Trade #{h_perf['hit_1k']}, Final: ${h_perf['final_wealth']:,.2f}, PF: {h_perf['pf']:.2f}\n")

    # Experiments on candidate AI upgrades
    # Let's test different combinations of:
    # - max_tap_bars (e.g. 18, 22, 28, 35)
    # - be_trigger (None, 0.012, 0.014, 0.016)
    # - max_tap_candle_pct (None, 0.024, 0.026)
    # - disp_vol_mult (None, 1.10, 1.15)
    # - btc_flash_brake (True, False)
    # - tp_pct (1H: 0.022, 0.024, 0.026; 4H: 0.028, 0.030, 0.032)
    # - time_stop_bars (None, 12, 16)

    def test_ai_candidate(cfg):
        signals = []
        max_tap_bars = cfg.get("max_tap_bars", 35)
        be_trigger = cfg.get("be_trigger", None)
        be_lock = cfg.get("be_lock", 0.0015)
        max_tap_pct = cfg.get("max_tap_pct", None)
        min_disp_vol = cfg.get("min_disp_vol", None)
        btc_brake = cfg.get("btc_brake", False)
        time_stop = cfg.get("time_stop", None)
        tp_1h = cfg.get("tp_1h", 0.022)
        tp_4h = cfg.get("tp_4h", 0.028)
        soft_sl_1h = cfg.get("soft_sl_1h", 0.025)
        soft_sl_4h = cfg.get("soft_sl_4h", 0.028)
        include_extreme = cfg.get("include_extreme", False)

        for tf in ["1h", "4h"]:
            tp_pct = tp_1h if tf == "1h" else tp_4h
            soft_sl_pct = soft_sl_1h if tf == "1h" else soft_sl_4h
            hard_sl_pct = 0.036 if tf == "1h" else 0.038
            max_hold = 24

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
                            if gain >= 0.045:
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
                                    
                                    if min_disp_vol:
                                        avg_vol = np.mean([c["volume"] for c in candles[i-20:i]])
                                        if candles[best_mid]["volume"] < min_disp_vol * avg_vol:
                                            has_fvg = False

                                    if has_fvg:
                                        for t in range(high_idx + 1, min(high_idx + max_tap_bars, n)):
                                            if candles[t]["low"] <= dec_top * 0.9995:
                                                tap_c = candles[t]
                                                c_range = tap_c["high"] - tap_c["low"]
                                                
                                                if max_tap_pct and (c_range / dec_top > max_tap_pct):
                                                    break # Falling knife

                                                if btc_brake and sym != "BTCUSDT":
                                                    t_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                                    btc_c = btc_map_4h.get(t_ts)
                                                    if btc_c and (btc_c["open"] - btc_c["close"]) / btc_c["open"] > 0.020:
                                                        break # Flash dump brake

                                                swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                                l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0
                                                if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                    entry = dec_top
                                                    tp_p = entry * (1.0 + tp_pct)
                                                    soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                    hard_sl_p = entry * (1.0 - hard_sl_pct)
                                                    
                                                    res = None; exit_p = entry; exit_t = tap_c["time"]
                                                    be_activated = False
                                                    curr_soft_sl = soft_sl_p

                                                    for m in range(t, min(t + max_hold, n)):
                                                        # Breakeven trigger check
                                                        if be_trigger and not be_activated:
                                                            if candles[m]["high"] >= entry * (1.0 + be_trigger):
                                                                be_activated = True
                                                                curr_soft_sl = entry * (1.0 + be_lock)

                                                        if candles[m]["high"] >= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["low"] <= hard_sl_p:
                                                            res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] <= curr_soft_sl:
                                                            exit_p = candles[m]["close"]
                                                            exit_t = candles[m]["time"]
                                                            res = "WIN" if (be_activated and exit_p >= entry) else "LOSS"
                                                            break
                                                        
                                                        # Time stop check
                                                        if time_stop and (m - t >= time_stop) and candles[m]["close"] < entry:
                                                            res = "LOSS"
                                                            exit_p = candles[m]["close"]
                                                            exit_t = candles[m]["time"]
                                                            break

                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc >= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    signals.append({
                                                        "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (exit_p - entry) / entry, "res": res
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
                            if drop >= 0.045:
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
                                    
                                    if min_disp_vol:
                                        avg_vol = np.mean([c["volume"] for c in candles[i-20:i]])
                                        if candles[best_mid]["volume"] < min_disp_vol * avg_vol:
                                            has_bear_fvg = False

                                    if has_bear_fvg:
                                        for t in range(low_idx + 1, min(low_idx + max_tap_bars, n)):
                                            if candles[t]["high"] >= dec_bot * 1.0005:
                                                tap_c = candles[t]
                                                c_range = tap_c["high"] - tap_c["low"]

                                                if max_tap_pct and (c_range / dec_bot > max_tap_pct):
                                                    break

                                                if btc_brake and sym != "BTCUSDT":
                                                    t_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                                    btc_c = btc_map_4h.get(t_ts)
                                                    if btc_c and (btc_c["close"] - btc_c["open"]) / btc_c["open"] > 0.020:
                                                        break

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
                                                    be_activated = False
                                                    curr_soft_sl = soft_sl_p

                                                    for m in range(t, min(t + max_hold, n)):
                                                        if be_trigger and not be_activated:
                                                            if candles[m]["low"] <= entry * (1.0 - be_trigger):
                                                                be_activated = True
                                                                curr_soft_sl = entry * (1.0 - be_lock)

                                                        if candles[m]["low"] <= tp_p:
                                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                        if candles[m]["high"] >= hard_sl_p:
                                                            res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                        if candles[m]["close"] >= curr_soft_sl:
                                                            exit_p = candles[m]["close"]
                                                            exit_t = candles[m]["time"]
                                                            res = "WIN" if (be_activated and exit_p <= entry) else "LOSS"
                                                            break

                                                        if time_stop and (m - t >= time_stop) and candles[m]["close"] > entry:
                                                            res = "LOSS"
                                                            exit_p = candles[m]["close"]
                                                            exit_t = candles[m]["time"]
                                                            break

                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc <= entry else "LOSS"
                                                        exit_p = fc
                                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                    signals.append({
                                                        "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                        "gross": (entry - exit_p) / entry, "res": res
                                                    })
                                                break
        return signals

    # Let's test a battery of configurations
    configs = [
        {"name": "Hermes Baseline (Reference)", "max_tap_bars": 35},
        {"name": "AI Test 1: Freshness 22 bars", "max_tap_bars": 22},
        {"name": "AI Test 2: Freshness 18 bars", "max_tap_bars": 18},
        {"name": "AI Test 3: Anti-Knife (max_tap 2.5%)", "max_tap_pct": 0.025},
        {"name": "AI Test 4: BTC Flash Dump Brake", "btc_brake": True},
        {"name": "AI Test 5: Fee-Shield BE trigger +1.5%", "be_trigger": 0.015, "be_lock": 0.0015},
        {"name": "AI Test 6: Fee-Shield BE trigger +1.8%", "be_trigger": 0.018, "be_lock": 0.0015},
        {"name": "AI Test 7: Higher TP (2.4% 1H / 3.0% 4H)", "tp_1h": 0.024, "tp_4h": 0.030},
        {"name": "AI Test 8: Synergy (Fresh 22 + Anti-Knife + BTC Brake)", "max_tap_bars": 22, "max_tap_pct": 0.025, "btc_brake": True},
        {"name": "AI Test 9: Synergy + Fee-Shield BE +1.8%", "max_tap_bars": 22, "max_tap_pct": 0.025, "btc_brake": True, "be_trigger": 0.018, "be_lock": 0.0015},
        {"name": "AI Test 10: Synergy + Higher TP (2.4% / 3.0%)", "max_tap_bars": 22, "max_tap_pct": 0.025, "btc_brake": True, "tp_1h": 0.024, "tp_4h": 0.030},
        {"name": "AI Test 11: Pure Multi-Agent Alpha Matrix", "max_tap_bars": 20, "max_tap_pct": 0.024, "btc_brake": True, "tp_1h": 0.023, "tp_4h": 0.029, "be_trigger": 0.017, "be_lock": 0.0015},
    ]

    print(f"{'Config Name':<45} | {'Trades':<6} | {'Win %':<7} | {'Max DD':<7} | {'1K Hit':<8} | {'Profit Factor':<13} | {'Final Wealth'}")
    print("-" * 120)
    for c in configs:
        sigs = test_ai_candidate(c)
        perf = simulate(sigs)
        h_str = f"#{perf['hit_1k']}" if perf['hit_1k'] else "FAILED"
        print(f"{c['name']:<45} | {perf['trades']:<6} | {perf['win_rate']:>6.2f}% | {perf['max_dd']:>6.2f}% | {h_str:<8} | {perf['pf']:>13.2f} | ${perf['final_wealth']:>16,.2f}")


if __name__ == "__main__":
    run_exploration()
