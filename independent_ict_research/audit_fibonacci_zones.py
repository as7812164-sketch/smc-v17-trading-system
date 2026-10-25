import os
import sys
import json
import time
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

BASE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
DATA_DIR = os.path.join(BASE_DIR, "historical_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "independent_ict_research")

def load_candles(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

# Load data
all_data = {"1h": {}, "4h": {}}
for sym in TOP_22_CHAMPIONS:
    for tf in ["1h", "4h"]:
        c = load_candles(sym, tf)
        if len(c) >= 500:
            all_data[tf][sym] = c

# Generate Hermes 3.5 trades with full Fibonacci tracking
trades = []
for tf in ["1h", "4h"]:
    tp_pct = 0.022 if tf == "1h" else 0.028
    soft_sl_pct = 0.025 if tf == "1h" else 0.028
    hard_sl_pct = 0.036 if tf == "1h" else 0.038
    max_hold = 24

    for sym, candles in all_data[tf].items():
        n = len(candles)
        if n < 60: continue
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
                        best_mid = -1
                        max_bg = 0.0
                        best_fib = 0.0
                        for mid in range(i+1, high_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid
                                best_fib = fib
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = max(dec_c["open"], dec_c["close"])
                            dec_bot = dec_c["low"]
                            has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                            if has_fvg:
                                for t in range(high_idx + 1, min(high_idx + 35, n)):
                                    if candles[t]["low"] <= dec_top * 0.9995:
                                        tap_c = candles[t]
                                        c_range = max(tap_c["high"] - tap_c["low"], 1e-6)
                                        swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                        w_ratio = l_wick / c_range
                                        mt = (dec_top + dec_bot) / 2.0
                                        if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                            entry = dec_top
                                            tp_p = entry * (1.0 + tp_pct)
                                            soft_sl_p = entry * (1.0 - soft_sl_pct)
                                            hard_sl_p = entry * (1.0 - hard_sl_pct)

                                            # Calculate 40-bar Dealing Range Fib
                                            w40 = candles[max(0, t-40):t+1]
                                            r_low = min(c["low"] for c in w40)
                                            r_high = max(c["high"] for c in w40)
                                            range_span = max(r_high - r_low, 1e-6)
                                            range_fib = (entry - r_low) / range_span  # 0.0 = Range Low, 1.0 = Range High

                                            # Impulse Retracement Fib at tap
                                            impulse_span = max(max_high - candles[i]["low"], 1e-6)
                                            retrace_fib = (max_high - entry) / impulse_span # 0.0 = top, 1.0 = bottom

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
                                                exit_p = fc; exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                            trades.append({
                                                "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                "exit_time": exit_t, "entry": entry, "exit": exit_p, "res": res,
                                                "range_fib": range_fib, "retrace_fib": retrace_fib, "ob_fib": best_fib
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
                        best_mid = -1
                        max_bg = 0.0
                        best_fib = 0.0
                        for mid in range(i+1, low_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                            fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid
                                best_fib = fib
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = dec_c["high"]
                            dec_bot = min(dec_c["open"], dec_c["close"])
                            has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                            if has_bear_fvg:
                                for t in range(low_idx + 1, min(low_idx + 35, n)):
                                    if candles[t]["high"] >= dec_bot * 1.0005:
                                        tap_c = candles[t]
                                        c_range = max(tap_c["high"] - tap_c["low"], 1e-6)
                                        swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                        u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                        w_ratio = u_wick / c_range
                                        mt = (dec_top + dec_bot) / 2.0
                                        if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                            entry = dec_bot
                                            tp_p = entry * (1.0 - tp_pct)
                                            soft_sl_p = entry * (1.0 + soft_sl_pct)
                                            hard_sl_p = entry * (1.0 + hard_sl_pct)

                                            w40 = candles[max(0, t-40):t+1]
                                            r_low = min(c["low"] for c in w40)
                                            r_high = max(c["high"] for c in w40)
                                            range_span = max(r_high - r_low, 1e-6)
                                            range_fib = (entry - r_low) / range_span

                                            impulse_span = max(candles[i]["high"] - min_low, 1e-6)
                                            retrace_fib = (entry - min_low) / impulse_span

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
                                                exit_p = fc; exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                            trades.append({
                                                "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                "exit_time": exit_t, "entry": entry, "exit": exit_p, "res": res,
                                                "range_fib": range_fib, "retrace_fib": retrace_fib, "ob_fib": best_fib
                                            })
                                        break

# Sort sequential queue
trades.sort(key=lambda x: x["time"])
executed = []
active_exit = 0
for t in trades:
    if t["time"] >= active_exit:
        executed.append(t)
        active_exit = t["exit_time"]

losses = [t for t in executed if t["res"] == "LOSS"]
wins = [t for t in executed if t["res"] == "WIN"]

print(f"Total Sequential Trades: {len(executed)} | Wins: {len(wins)} | Losses: {len(losses)} (WR: {len(wins)/len(executed)*100:.2f}%)")

# =============================================================================
# FIBONACCI AUDIT 1: DEALING RANGE FIBONACCI (DISCOUNT VS PREMIUM)
# =============================================================================
# Rule:
# LONG is valid if Range Fib < 0.50 (Discount). If Range Fib >= 0.50, it is in PREMIUM (WRONG!).
# SHORT is valid if Range Fib > 0.50 (Premium). If Range Fib <= 0.50, it is in DISCOUNT (WRONG!).

wrong_zone_losses = []
correct_zone_losses = []

for t in losses:
    rf = t["range_fib"]
    if t["side"] == "LONG":
        if rf >= 0.50:
            wrong_zone_losses.append((t, f"LONG in Premium (Range Fib = {rf:.3f})"))
        else:
            correct_zone_losses.append((t, f"LONG in Discount (Range Fib = {rf:.3f})"))
    elif t["side"] == "SHORT":
        if rf <= 0.50:
            wrong_zone_losses.append((t, f"SHORT in Discount (Range Fib = {rf:.3f})"))
        else:
            correct_zone_losses.append((t, f"SHORT in Premium (Range Fib = {rf:.3f})"))

print("\n" + "="*80)
print("🎯 1. DEALING RANGE FIBONACCI AUDIT (PREMIUM VS DISCOUNT)")
print("="*80)
print(f"Total Losses Over 1 Year: {len(losses)}")
print(f"• Losses Taken in WRONG Zone (Long in Premium / Short in Discount) : {len(wrong_zone_losses)} ({len(wrong_zone_losses)/len(losses)*100:.2f}%)")
print(f"• Losses Taken in CORRECT Zone (Long in Discount / Short in Premium) : {len(correct_zone_losses)} ({len(correct_zone_losses)/len(losses)*100:.2f}%)")

# =============================================================================
# FIBONACCI AUDIT 2: IMPULSE RETRACEMENT FIBONACCI ZONES (OTE VS EXTREME VS SHALLOW)
# =============================================================================
# Zones of Retracement:
# Zone A: Shallow Retrace (< 0.382 Fib)
# Zone B: Golden Pocket / OTE (0.500 to 0.786 Fib)
# Zone C: Deep Breakdown (> 0.786 Fib)

zone_stats = {
    "Shallow (< 0.382)": {"trades": 0, "wins": 0, "losses": 0},
    "Equilibrium (0.382 - 0.500)": {"trades": 0, "wins": 0, "losses": 0},
    "Golden Pocket / OTE (0.500 - 0.786)": {"trades": 0, "wins": 0, "losses": 0},
    "Deep Extreme (> 0.786)": {"trades": 0, "wins": 0, "losses": 0}
}

for t in executed:
    rf = t["retrace_fib"]
    if rf < 0.382:
        k = "Shallow (< 0.382)"
    elif 0.382 <= rf < 0.500:
        k = "Equilibrium (0.382 - 0.500)"
    elif 0.500 <= rf <= 0.786:
        k = "Golden Pocket / OTE (0.500 - 0.786)"
    else:
        k = "Deep Extreme (> 0.786)"
    
    zone_stats[k]["trades"] += 1
    if t["res"] == "WIN":
        zone_stats[k]["wins"] += 1
    else:
        zone_stats[k]["losses"] += 1

print("\n" + "="*80)
print("📊 2. IMPULSE RETRACEMENT FIBONACCI PERFORMANCE BREAKDOWN")
print("="*80)
for k, v in zone_stats.items():
    wr = (v["wins"] / v["trades"] * 100.0) if v["trades"] > 0 else 0
    share_of_losses = (v["losses"] / len(losses) * 100.0) if len(losses) > 0 else 0
    print(f"• {k:<36} | Trades: {v['trades']:>3} | Wins: {v['wins']:>3} | Losses: {v['losses']:>3} | Win Rate: {wr:>5.2f}% | Share of Total SLs: {share_of_losses:>5.1f}%")

# Save report
out_path = os.path.join(OUTPUT_DIR, "FIBONACCI_ZONE_AUDIT_REPORT.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "total_trades": len(executed),
        "total_losses": len(losses),
        "wrong_range_zone_losses_count": len(wrong_zone_losses),
        "wrong_range_zone_losses_pct": round(len(wrong_zone_losses)/len(losses)*100, 2),
        "zone_breakdown": zone_stats
    }, f, indent=2)

print(f"\n📁 Audit report saved to: {out_path}")
print("="*80)
