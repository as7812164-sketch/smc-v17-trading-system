import os
import json
import sys
from datetime import datetime, timezone, timedelta

# Set utf-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Run an analysis on candidate signals and SL hits
# Let's import the same logic from run_deca_1year_timely_managed_test.py and check why SL happened!
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from config import TOP_22_CHAMPIONS
DATA_DIR = os.path.join(root_dir, "historical_data")

def calculate_ema(values, period: int):
    if not values: return []
    k = 2.0 / (period + 1.0)
    ema = [values[0]]
    for v in values[1:]:
        ema.append(v * k + ema[-1] * (1.0 - k))
    return ema

# Load BTC
with open(os.path.join(DATA_DIR, "BTCUSDT_4h.json"), "r", encoding="utf-8") as f:
    btc_4h = json.load(f)

btc_closes = [float(c["close"]) for c in btc_4h]
btc_ema50 = calculate_ema(btc_closes, 50)
btc_macro_map = {}
for idx, c in enumerate(btc_4h):
    btc_macro_map[c["time"]] = (c["close"] >= btc_ema50[idx])

btc_times = sorted(btc_macro_map.keys())
def get_btc_is_bull(timestamp_ms: int) -> bool:
    latest_bull = True
    for t in btc_times:
        if t <= timestamp_ms:
            latest_bull = btc_macro_map[t]
        else:
            break
    return latest_bull

# Analyze signals
signals = []
for tf_str, tp_pct, sl_pct, be_pct, trail_pct, harvest_sl_pct in [
    ("4h", 0.0220, 0.0280, 0.0150, 0.0180, 0.0090),
    ("1h", 0.0180, 0.0250, 0.0120, 0.0150, 0.0080)
]:
    for sym in TOP_22_CHAMPIONS:
        path = os.path.join(DATA_DIR, f"{sym}_{tf_str}.json")
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            candles = json.load(f)
        n = len(candles)
        if n < 50:
            continue

        atr_series = [0.0] * n
        for k in range(1, n):
            tr = max(candles[k]["high"] - candles[k]["low"],
                     abs(candles[k]["high"] - candles[k-1]["close"]),
                     abs(candles[k]["low"] - candles[k-1]["close"]))
            atr_series[k] = tr if k < 14 else (atr_series[k-1] * 13 + tr) / 14

        max_tap_window = 35
        for i in range(25, n - 4):
            c3 = candles[i]
            c2 = candles[i+1]
            c1 = candles[i+2]

            # Bullish
            if c3["close"] < c3["open"] and c1["low"] > c3["high"]:
                gain = (max(c2["high"], c1["high"]) - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                if gain >= 0.050:
                    ob_high = c3["high"]
                    ob_low = c3["low"]
                    ob_range = ob_high - ob_low
                    mt = (ob_high + ob_low) / 2.0
                    peak_runway = max(candles[k]["high"] for k in range(i+1, min(i+25, n)))
                    if ((peak_runway - ob_high) / ob_high * 100.0) < 5.0:
                        continue
                    eff_entry = round(ob_high - 0.05 * ob_range, 8)
                    broken = False
                    tap_idx = None
                    idm_low = min(candles[k]["low"] for k in range(max(0, i-3), min(i+4, n)))
                    for t in range(i+3, min(i + max_tap_window, n)):
                        curr_c = candles[t]
                        if curr_c["close"] < ob_low:
                            broken = True
                            break
                        bars_alive = t - (i+2)
                        idm_swept = any(candles[k]["low"] < idm_low for k in range(i+3, t+1)) or (curr_c["low"] < idm_low)
                        if bars_alive >= 3 and idm_swept:
                            if curr_c["low"] <= eff_entry * 1.0005 and curr_c["close"] >= ob_low:
                                c_range = curr_c["high"] - curr_c["low"]
                                l_wick = min(curr_c["open"], curr_c["close"]) - curr_c["low"]
                                if (l_wick / c_range if c_range > 0 else 0) >= 0.18 and curr_c["close"] >= mt:
                                    tap_idx = t
                                    break
                    if not broken and tap_idx is not None:
                        if get_btc_is_bull(candles[tap_idx]["time"]):
                            cur_atr = atr_series[tap_idx]
                            struct_sl = min(ob_low, candles[tap_idx]["low"]) - 0.20 * cur_atr
                            hard_sl = max(min(struct_sl, eff_entry * (1.0 - 0.0380)), eff_entry * 0.9620)
                            soft_sl = (eff_entry + hard_sl) / 2.0
                            signals.append({
                                "symbol": sym, "tf": tf_str, "side": "BUY",
                                "entry_price": eff_entry, "tap_idx": tap_idx,
                                "entry_time": candles[tap_idx]["time"],
                                "soft_sl": soft_sl, "hard_sl": hard_sl, "struct_sl": struct_sl,
                                "ob_high": ob_high, "ob_low": ob_low, "mt": mt,
                                "tp_pct": tp_pct, "candles": candles
                            })

            # Bearish
            if c3["close"] > c3["open"] and c1["high"] < c3["low"]:
                drop = (c3["high"] - min(c2["low"], c1["low"])) / c3["high"] if c3["high"] > 0 else 0.0
                if drop >= 0.050:
                    ob_high = c3["high"]
                    ob_low = c3["low"]
                    ob_range = ob_high - ob_low
                    mt = (ob_high + ob_low) / 2.0
                    peak_runway = min(candles[k]["low"] for k in range(i+1, min(i+25, n)))
                    if ((ob_low - peak_runway) / ob_low * 100.0) < 5.0:
                        continue
                    eff_entry = round(ob_low + 0.05 * ob_range, 8)
                    broken = False
                    tap_idx = None
                    idm_high = max(candles[k]["high"] for k in range(max(0, i-3), min(i+4, n)))
                    for t in range(i+3, min(i + max_tap_window, n)):
                        curr_c = candles[t]
                        if curr_c["close"] > ob_high:
                            broken = True
                            break
                        bars_alive = t - (i+2)
                        idm_swept = any(candles[k]["high"] > idm_high for k in range(i+3, t+1)) or (curr_c["high"] > idm_high)
                        if bars_alive >= 3 and idm_swept:
                            if curr_c["high"] >= eff_entry * 0.9995 and curr_c["close"] <= ob_high:
                                c_range = curr_c["high"] - curr_c["low"]
                                u_wick = curr_c["high"] - max(curr_c["open"], curr_c["close"])
                                if (u_wick / c_range if c_range > 0 else 0) >= 0.18 and curr_c["close"] <= mt:
                                    tap_idx = t
                                    break
                    if not broken and tap_idx is not None:
                        cur_atr = atr_series[tap_idx]
                        struct_sl = max(ob_high, candles[tap_idx]["high"]) + 0.20 * cur_atr
                        hard_sl = min(max(struct_sl, eff_entry * (1.0 + 0.0380)), eff_entry * 1.0380)
                        soft_sl = (eff_entry + hard_sl) / 2.0
                        signals.append({
                            "symbol": sym, "tf": tf_str, "side": "SELL",
                            "entry_price": eff_entry, "tap_idx": tap_idx,
                            "entry_time": candles[tap_idx]["time"],
                            "soft_sl": soft_sl, "hard_sl": hard_sl, "struct_sl": struct_sl,
                            "ob_high": ob_high, "ob_low": ob_low, "mt": mt,
                            "tp_pct": tp_pct, "candles": candles
                        })

signals.sort(key=lambda s: s["entry_time"])

# Check what happened to SL trades:
# Test A: With soft_sl (current implementation in backtest)
# Test B: With hard_sl (real structural stop below OB / wick)
# Test C: What was max adverse excursion (MAE) vs max favorable excursion (MFE)?
results_soft = []
results_hard = []

premature_soft_sl_count = 0
for sig in signals:
    candles = sig["candles"]
    tap_idx = sig["tap_idx"]
    side = sig["side"]
    entry_p = sig["entry_price"]
    soft_sl = sig["soft_sl"]
    hard_sl = sig["hard_sl"]
    tp_p = entry_p * (1.0 + sig["tp_pct"]) if side == "BUY" else entry_p * (1.0 - sig["tp_pct"])
    
    # 1. Track trajectory
    hit_soft_sl_bar = None
    hit_hard_sl_bar = None
    hit_tp_bar = None

    max_fav = 0.0
    max_adv = 0.0

    for k in range(tap_idx, min(tap_idx + 180, len(candles))):
        c = candles[k]
        if side == "BUY":
            fav = (c["high"] - entry_p) / entry_p
            adv = (entry_p - c["low"]) / entry_p
            if fav > max_fav: max_fav = fav
            if adv > max_adv: max_adv = adv

            if hit_tp_bar is None and c["high"] >= tp_p:
                hit_tp_bar = k
            if hit_soft_sl_bar is None and c["low"] <= soft_sl:
                hit_soft_sl_bar = k
            if hit_hard_sl_bar is None and c["low"] <= hard_sl:
                hit_hard_sl_bar = k
        else:
            fav = (entry_p - c["low"]) / entry_p
            adv = (c["high"] - entry_p) / entry_p
            if fav > max_fav: max_fav = fav
            if adv > max_adv: max_adv = adv

            if hit_tp_bar is None and c["low"] <= tp_p:
                hit_tp_bar = k
            if hit_soft_sl_bar is None and c["high"] >= soft_sl:
                hit_soft_sl_bar = k
            if hit_hard_sl_bar is None and c["high"] >= hard_sl:
                hit_hard_sl_bar = k

    # Check if soft_sl died but hard_sl would have survived and hit TP
    if hit_soft_sl_bar is not None and (hit_tp_bar is None or hit_soft_sl_bar < hit_tp_bar):
        # Soft SL died
        if hit_tp_bar is not None and (hit_hard_sl_bar is None or hit_hard_sl_bar > hit_tp_bar):
            premature_soft_sl_count += 1

print(f"Total signals: {len(signals)}")
print(f"Premature Soft SL hits (Trades that hit Soft SL but WOULD HAVE HIT TP if real Hard SL was used): {premature_soft_sl_count}")

# Print MAE & MFE distribution of SL trades
print("\n--- FORENSIC MAE / MFE AUDIT ---")
soft_sl_hits = 0
hard_sl_hits = 0
tp_first_with_hard = 0
sl_first_with_hard = 0

for sig in signals:
    candles = sig["candles"]
    tap_idx = sig["tap_idx"]
    side = sig["side"]
    entry_p = sig["entry_price"]
    hard_sl = sig["hard_sl"]
    tp_p = entry_p * (1.0 + sig["tp_pct"]) if side == "BUY" else entry_p * (1.0 - sig["tp_pct"])
    
    t_tp = 999999
    t_sl = 999999
    for k in range(tap_idx, min(tap_idx + 180, len(candles))):
        c = candles[k]
        if side == "BUY":
            if c["high"] >= tp_p and t_tp == 999999: t_tp = k
            if c["low"] <= hard_sl and t_sl == 999999: t_sl = k
        else:
            if c["low"] <= tp_p and t_tp == 999999: t_tp = k
            if c["high"] >= hard_sl and t_sl == 999999: t_sl = k
        if t_tp != 999999 or t_sl != 999999:
            break
            
    if t_tp < t_sl:
        tp_first_with_hard += 1
    elif t_sl < t_tp:
        sl_first_with_hard += 1

print(f"With HARD SL (real structural SL below OB):")
print(f"TP First: {tp_first_with_hard} ({(tp_first_with_hard/(tp_first_with_hard+sl_first_with_hard)*100):.2f}% Win Rate)")
print(f"SL First: {sl_first_with_hard}")
