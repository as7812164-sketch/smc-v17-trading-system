import json, os, sys
sys.path.append(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system")
from run_battle_hermes2_vs_hermes3_cvd_oi import load_local_data, TOP_22_CHAMPIONS

print("Tracing exact progression of Hermes 2.0 Apex on historical_data (1 Year)...")
all_data = {"1h": {}, "4h": {}}
for sym in TOP_22_CHAMPIONS:
    for tf in ["1h", "4h"]:
        k = load_local_data(sym, tf)
        if len(k) >= 500:
            all_data[tf][sym] = k

btc_4h = load_local_data("BTCUSDT", "4h")
btc_map_4h = {c["time"]: c for c in btc_4h}

signals = []
for tf in ["1h", "4h"]:
    std_tp_pct = 0.022 if tf == "1h" else 0.028
    soft_sl_pct = 0.025 if tf == "1h" else 0.028
    hard_sl_pct = 0.036 if tf == "1h" else 0.038
    max_tap_window = 28
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
                    if gain >= 0.050:
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
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                        if btc_dump < 0.020:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + std_tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)
                                                res2 = None; exit_p2 = entry; exit_t2 = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res2 = "WIN"; exit_p2 = tp_p; exit_t2 = candles[m]["time"]; break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res2 = "LOSS"; exit_p2 = min(hard_sl_p, candles[m]["open"]); exit_t2 = candles[m]["time"]; break
                                                    if candles[m]["close"] <= soft_sl_p:
                                                        res2 = "LOSS"; exit_p2 = candles[m]["close"]; exit_t2 = candles[m]["time"]; break
                                                if not res2:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res2 = "WIN" if fc >= entry else "LOSS"
                                                    exit_p2 = fc
                                                    exit_t2 = candles[min(t + max_hold, n - 1)]["time"]
                                                signals.append({"sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"], "exit_time": exit_t2, "gross": (exit_p2 - entry) / entry, "res": res2})
                                                break
            # Bearish
            if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                lows = [c["low"] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)
                if low_idx > i + 3:
                    drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                    if drop >= 0.050:
                        idm_high = candles[low_idx - 1]["high"]
                        best_mid = -1; max_bg = 0.0
                        for mid in range(i+1, low_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg; best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_bot = min(dec_c["open"], dec_c["close"])
                            dec_top = dec_c["high"]
                            has_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                            if has_fvg:
                                for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                    if candles[t]["high"] >= dec_bot * 1.0005:
                                        tap_c = candles[t]
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                        if btc_pump < 0.020:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - std_tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)
                                                res2 = None; exit_p2 = entry; exit_t2 = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["low"] <= tp_p:
                                                        res2 = "WIN"; exit_p2 = tp_p; exit_t2 = candles[m]["time"]; break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res2 = "LOSS"; exit_p2 = max(hard_sl_p, candles[m]["open"]); exit_t2 = candles[m]["time"]; break
                                                    if candles[m]["close"] >= soft_sl_p:
                                                        res2 = "LOSS"; exit_p2 = candles[m]["close"]; exit_t2 = candles[m]["time"]; break
                                                if not res2:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res2 = "WIN" if fc <= entry else "LOSS"
                                                    exit_p2 = fc
                                                    exit_t2 = candles[min(t + max_hold, n - 1)]["time"]
                                                signals.append({"sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"], "exit_time": exit_t2, "gross": (entry - exit_p2) / entry, "res": res2})
                                                break

signals.sort(key=lambda x: x["time"])
executed = []
active_exit = 0
for s in signals:
    if s["time"] >= active_exit:
        executed.append(s)
        active_exit = s["exit_time"]

cap = 50.0
vault = 0.0
for idx, trade in enumerate(executed):
    net_move = trade["gross"] - 0.0016
    pos = cap * 5.0
    pnl = pos * net_move
    if trade["res"] == "WIN":
        cap += (pnl * 0.85)
        vault += (pnl * 0.15)
    else:
        cap += pnl
    tot = cap + vault
    if idx + 1 in [10, 20, 30, 40, 50, 55, 57, 58, 59, 60, 65, 66]:
        print(f"Trade #{idx+1:>2}: res={trade['res']:<4} pnl=${pnl:>7.2f} | cap=${cap:>8.2f} vault=${vault:>8.2f} tot=${tot:>8.2f}")
