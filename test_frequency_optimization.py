import json
import os
import sys
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_data(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    running_cvd = 0.0
    vol_window = []
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        v = float(c.get("volume", 0.0))
        c["volume"] = v
        rng = c["high"] - c["low"]
        d_ratio = (c["close"] - c["low"]) / rng if rng > 0 else 0.5
        delta = v * (2.0 * d_ratio - 1.0)
        running_cvd += delta
        c["delta"] = delta
        c["delta_ratio"] = d_ratio
        c["cvd"] = running_cvd
        vol_window.append(v)
        if len(vol_window) > 20: vol_window.pop(0)
        c["vol_sma20"] = sum(vol_window) / len(vol_window) if vol_window else 1.0
    return data

btc_4h = load_data("BTCUSDT", "4h")
btc_map_4h = {c["time"]: c for c in btc_4h}

all_data = {"1h": {}, "4h": {}}
for s in TOP_22_CHAMPIONS:
    for tf in ["1h", "4h"]:
        k = load_data(s, tf)
        if len(k) >= 500:
            all_data[tf][s] = k

def test_filters(min_disp_1h, min_disp_4h, min_wick, min_delta_ratio, max_slots=1):
    signals = []
    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        min_disp = min_disp_4h if tf == "4h" else min_disp_1h
        max_hold = 30 if tf == "4h" else 40
        
        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                if candles[i]["low"] != min(c["low"] for c in candles[i-15:i+1]):
                    continue
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx <= i + 3:
                    continue
                gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                if gain < min_disp:
                    continue
                idm_low = candles[high_idx - 1]["low"]
                
                best_mid = -1; max_bg = 0.0
                for mid in range(i+1, high_idx):
                    bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                    fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                    if 0.30 <= fib <= 0.75 and bg > max_bg:
                        max_bg = bg; best_mid = mid
                if best_mid == -1: continue
                
                dec_c = candles[best_mid - 1]
                dec_top = max(dec_c["open"], dec_c["close"])
                dec_bot = dec_c["low"]
                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                if not has_fvg: continue
                
                for t in range(high_idx + 1, min(high_idx + 28, n)):
                    if candles[t]["low"] <= dec_top * 1.0005:
                        tap_c = candles[t]
                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                        btc_c = btc_map_4h.get(prev_4h_ts)
                        btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                        if btc_dump >= 0.018: # BTC dumping >= 1.8%
                            break
                            
                        c_range = tap_c["high"] - tap_c["low"]
                        swept_idm = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                        mt = (dec_top + dec_bot) / 2.0
                        
                        # Absorption check
                        cvd_prev = candles[t - 3]["cvd"] if t >= 3 else candles[0]["cvd"]
                        cvd_curl = (tap_c["cvd"] - cvd_prev) >= 0
                        cvd_absorbed = (tap_c["delta_ratio"] >= min_delta_ratio or tap_c["delta"] > 0)
                        
                        if swept_idm and w_ratio >= min_wick and cvd_absorbed and tap_c["close"] >= mt:
                            entry = dec_top
                            tp_p = entry * (1.0 + std_tp_pct)
                            soft_sl_p = entry * (1.0 - soft_sl_pct)
                            hard_sl_p = entry * (1.0 - hard_sl_pct)
                            
                            res = None; exit_p = entry; exit_t = tap_c["time"]
                            curr_sl = soft_sl_p; be_locked = False
                            for m in range(t, min(t + max_hold, n)):
                                high_m = candles[m]["high"]
                                if high_m >= entry * 1.016:
                                    curr_sl = max(curr_sl, entry * 1.002)
                                    be_locked = True
                                if high_m >= tp_p:
                                    res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                if candles[m]["low"] <= hard_sl_p:
                                    res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                if candles[m]["close"] <= curr_sl:
                                    res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                                    exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                            if not res:
                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                res = "WIN" if fc >= entry else "LOSS"
                                exit_p = fc; exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                
                            signals.append({
                                "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t,
                                "entry": entry, "exit": exit_p, "gross": (exit_p - entry) / entry,
                                "res": res
                            })
                            break
    signals.sort(key=lambda x: x["time"])
    
    # Simulate execution with max_slots concurrent positions
    active_positions = [] # list of exit_time
    executed = []
    for s in signals:
        active_positions = [t for t in active_positions if t > s["time"]]
        if len(active_positions) < max_slots:
            active_positions.append(s["exit_time"])
            executed.append(s)
            
    tot = len(executed)
    w = sum(1 for x in executed if x["res"] == "WIN")
    l = tot - w
    wr = (w / tot * 100.0) if tot > 0 else 0.0
    return len(signals), tot, w, l, wr, executed

print("=" * 95)
print(f"{'Config Name':<30} | {'Disp 1H/4H':<11} | {'Wick':<5} | {'Slots':<5} | {'Raw Sig':<8} | {'Exec':<5} | {'Wins':<5} | {'Loss':<5} | {'Win Rate':<8}")
print("-" * 95)

configs = [
    ("Strict 1-Slot (Previous)", 0.050, 0.050, 0.28, 0.48, 1),
    ("Strict 2-Slots", 0.050, 0.050, 0.28, 0.48, 2),
    ("Strict 3-Slots", 0.050, 0.050, 0.28, 0.48, 3),
    ("Optimized Disp (3.5% 1H, 1-Slot)", 0.035, 0.050, 0.20, 0.45, 1),
    ("Optimized Disp (3.5% 1H, 2-Slots)", 0.035, 0.050, 0.20, 0.45, 2),
    ("Optimized Disp (3.5% 1H, 3-Slots)", 0.035, 0.050, 0.20, 0.45, 3),
    ("High Frequency (3.0% 1H, 2-Slots)", 0.030, 0.045, 0.18, 0.45, 2),
    ("High Frequency (3.0% 1H, 3-Slots)", 0.030, 0.045, 0.18, 0.45, 3),
    ("All Signals (No Slot Limit)", 0.035, 0.050, 0.20, 0.45, 999),
]

for name, d1, d4, wk, dr, sl in configs:
    raw_s, exec_s, w, l, wr, ex = test_filters(d1, d4, wk, dr, sl)
    print(f"{name:<30} | {d1*100:.1f}%/{d4*100:.1f}%   | {wk*100:.0f}%  | {sl:<5} | {raw_s:<8} | {exec_s:<5} | {w:<5} | {l:<5} | {wr:6.2f}%")
