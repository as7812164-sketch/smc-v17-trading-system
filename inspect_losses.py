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

def inspect_losses():
    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    btc_4h = load_local_data("BTCUSDT", "4h")
    btc_map_4h = {c["time"]: c for c in btc_4h}
    btc_1h = load_local_data("BTCUSDT", "1h")
    btc_map_1h = {c["time"]: c for c in btc_1h}

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
                                                loss_reason = "NONE"
                                                bars_to_exit = 0
                                                max_mfe = 0.0
                                                max_mae = 0.0

                                                for m in range(t, min(t + max_hold, n)):
                                                    bars_to_exit += 1
                                                    mfe = (candles[m]["high"] - entry) / entry
                                                    mae = (entry - candles[m]["low"]) / entry
                                                    if mfe > max_mfe: max_mfe = mfe
                                                    if mae > max_mae: max_mae = mae

                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]
                                                        loss_reason = "HARD_SL_SPIKE"
                                                        break
                                                    if candles[m]["close"] <= soft_sl_p:
                                                        res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]
                                                        loss_reason = "SOFT_SL_CLOSE"
                                                        break

                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                    loss_reason = "TIME_EXPIRY"

                                                # Additional features at entry
                                                fvg_gap = (candles[best_mid + 1]["low"] - candles[best_mid - 1]["high"]) / entry
                                                fib_ratio = (candles[best_mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                                tap_delay = t - high_idx
                                                tap_range_pct = c_range / entry

                                                signals.append({
                                                    "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (exit_p - entry) / entry, "res": res,
                                                    "loss_reason": loss_reason, "bars_to_exit": bars_to_exit,
                                                    "mfe": max_mfe, "mae": max_mae, "fvg_gap": fvg_gap,
                                                    "fib_ratio": fib_ratio, "tap_delay": tap_delay,
                                                    "tap_range_pct": tap_range_pct, "w_ratio": w_ratio,
                                                    "gain": gain
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
                                                loss_reason = "NONE"
                                                bars_to_exit = 0
                                                max_mfe = 0.0
                                                max_mae = 0.0

                                                for m in range(t, min(t + max_hold, n)):
                                                    bars_to_exit += 1
                                                    mfe = (entry - candles[m]["low"]) / entry
                                                    mae = (candles[m]["high"] - entry) / entry
                                                    if mfe > max_mfe: max_mfe = mfe
                                                    if mae > max_mae: max_mae = mae

                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]
                                                        loss_reason = "HARD_SL_SPIKE"
                                                        break
                                                    if candles[m]["close"] >= soft_sl_p:
                                                        res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]
                                                        loss_reason = "SOFT_SL_CLOSE"
                                                        break

                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                    loss_reason = "TIME_EXPIRY"

                                                fvg_gap = (candles[best_mid - 1]["low"] - candles[best_mid + 1]["high"]) / entry
                                                fib_ratio = (candles[i]["high"] - candles[best_mid]["high"]) / (candles[i]["high"] - min_low)
                                                tap_delay = t - low_idx
                                                tap_range_pct = c_range / entry

                                                signals.append({
                                                    "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (entry - exit_p) / entry, "res": res,
                                                    "loss_reason": loss_reason, "bars_to_exit": bars_to_exit,
                                                    "mfe": max_mfe, "mae": max_mae, "fvg_gap": fvg_gap,
                                                    "fib_ratio": fib_ratio, "tap_delay": tap_delay,
                                                    "tap_range_pct": tap_range_pct, "w_ratio": w_ratio,
                                                    "gain": drop
                                                })
                                            break

    signals.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for s in signals:
        if s["time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    losses = [t for t in executed if t["res"] == "LOSS"]
    wins = [t for t in executed if t["res"] == "WIN"]
    print(f"Total: {len(executed)} | Wins: {len(wins)} | Losses: {len(losses)}")
    
    # Analyze losses
    print("\n--- LOSS BREAKDOWN ---")
    reasons = {}
    for l in losses:
        reasons[l["loss_reason"]] = reasons.get(l["loss_reason"], 0) + 1
    for r, count in reasons.items():
        print(f"  {r}: {count} ({count/len(losses)*100:.1f}%)")

    # MFE of losses: Did losing trades go into profit first?
    mfe_vals = [l["mfe"] * 100 for l in losses]
    print(f"\nMFE of Losses:")
    print(f"  Mean MFE: {np.mean(mfe_vals):.2f}%")
    print(f"  Median MFE: {np.median(mfe_vals):.2f}%")
    print(f"  Losses that reached >= +1.0% MFE before failing: {sum(1 for x in mfe_vals if x >= 1.0)} ({sum(1 for x in mfe_vals if x >= 1.0)/len(losses)*100:.1f}%)")
    print(f"  Losses that reached >= +1.5% MFE before failing: {sum(1 for x in mfe_vals if x >= 1.5)} ({sum(1 for x in mfe_vals if x >= 1.5)/len(losses)*100:.1f}%)")
    print(f"  Losses that reached >= +1.8% MFE before failing: {sum(1 for x in mfe_vals if x >= 1.8)} ({sum(1 for x in mfe_vals if x >= 1.8)/len(losses)*100:.1f}%)")

    # Bars to exit for losses
    loss_bars = [l["bars_to_exit"] for l in losses]
    win_bars = [w["bars_to_exit"] for w in wins]
    print(f"\nBars to Exit:")
    print(f"  Wins mean bars: {np.mean(win_bars):.1f} bars")
    print(f"  Losses mean bars: {np.mean(loss_bars):.1f} bars")
    print(f"  Losses exiting in <= 3 bars: {sum(1 for b in loss_bars if b <= 3)}")
    print(f"  Losses lingering > 10 bars: {sum(1 for b in loss_bars if b > 10)}")

    # Symbols in losses
    sym_losses = {}
    for l in losses:
        sym_losses[l["sym"]] = sym_losses.get(l["sym"], 0) + 1
    print("\nLosses by Symbol:")
    for sym, count in sorted(sym_losses.items(), key=lambda x: -x[1])[:10]:
        print(f"  {sym}: {count} losses")

if __name__ == "__main__":
    inspect_losses()
