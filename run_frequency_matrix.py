import json
import os
import sys

from run_full_quant_buy_1year_backtest import load_data_with_quant_features, build_btc_map, simulate_compounding

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

all_data = {"1h": {}, "4h": {}}
for sym in TOP_22_CHAMPIONS:
    for tf in ["1h", "4h"]:
        k = load_data_with_quant_features(sym, tf)
        if len(k) >= 500:
            all_data[tf][sym] = k
            
btc_map_4h = build_btc_map()

def run_parametric_scan(disp_1h=0.030, disp_4h=0.045, min_wick=0.20, delta_ratio=0.45, max_slots=2):
    signals = []
    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        min_disp = disp_4h if tf == "4h" else disp_1h
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
                if high_idx <= i + 3: continue
                gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                if gain < min_disp: continue
                idm_low = candles[high_idx - 1]["low"]
                
                best_mid = -1; max_bg = 0.0
                for mid in range(i+1, high_idx):
                    bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                    fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                    if 0.25 <= fib <= 0.75 and bg > max_bg:
                        max_bg = bg; best_mid = mid
                if best_mid == -1: continue
                
                dec_c = candles[best_mid - 1]
                dec_top = max(dec_c["open"], dec_c["close"])
                dec_bot = dec_c["low"]
                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                if not has_fvg: continue
                
                ob_fib = (dec_top - candles[i]["low"]) / (max_high - candles[i]["low"])
                if ob_fib > 0.70: continue # Discount zone
                
                for t in range(high_idx + 1, min(high_idx + 28, n)):
                    if candles[t]["low"] <= dec_top * 1.0005:
                        tap_c = candles[t]
                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                        btc_c = btc_map_4h.get(prev_4h_ts)
                        btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                        if btc_dump >= 0.018: break
                        
                        c_range = tap_c["high"] - tap_c["low"]
                        swept_idm = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                        mt = (dec_top + dec_bot) / 2.0
                        
                        cvd_prev = candles[t - 3]["cvd"] if t >= 3 else candles[0]["cvd"]
                        cvd_curl = (tap_c["cvd"] - cvd_prev) >= 0
                        cvd_absorbed = (tap_c["delta_ratio"] >= delta_ratio or tap_c["delta"] > 0)
                        
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
    
    active_positions = []
    executed = []
    for s in signals:
        active_positions = [t for t in active_positions if t > s["time"]]
        if len(active_positions) < max_slots:
            active_positions.append(s["exit_time"])
            executed.append(s)
            
    w = sum(1 for x in executed if x["res"] == "WIN")
    l = len(executed) - w
    wr = (w / len(executed) * 100.0) if executed else 0.0
    return len(signals), len(executed), w, l, wr, executed

print("=========================================================================================")
print(f"{'Profile':<25} | {'Disp 1H':<8} | {'Wick':<5} | {'Slots':<5} | {'Signals':<8} | {'Executed':<8} | {'Wins/Loss':<10} | {'Win Rate':<8}")
print("=========================================================================================")

profiles = [
    ("Ultra Conservative (Previous)", 0.050, 0.28, 1),
    ("Balanced Pro (1-Slot)", 0.032, 0.20, 1),
    ("Balanced Pro (2-Slots)", 0.032, 0.20, 2),
    ("Balanced Pro (3-Slots)", 0.032, 0.20, 3),
    ("High Frequency (2-Slots)", 0.025, 0.18, 2),
    ("High Frequency (3-Slots)", 0.025, 0.18, 3),
    ("Full Velocity (All Signals)", 0.025, 0.18, 999),
]

for name, d1, wk, sl in profiles:
    sig, exe, w, l, wr, ex = run_parametric_scan(disp_1h=d1, min_wick=wk, max_slots=sl)
    print(f"{name:<25} | {d1*100:.1f}%    | {wk*100:.0f}%  | {sl:<5} | {sig:<8} | {exe:<8} | {w:>3}W / {l:>2}L  | {wr:6.2f}%")
