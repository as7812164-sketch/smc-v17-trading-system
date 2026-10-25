import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Standalone loader for 4-compounding simulation
TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_data_with_quant_features(sym, interval):
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

print("[*] Loading historical data for Top-22 Champions...")
all_data = {"1h": {}, "4h": {}}
for s in TOP_22_CHAMPIONS:
    for tf in ["1h", "4h"]:
        k = load_data_with_quant_features(s, tf)
        if len(k) >= 500:
            all_data[tf][s] = k

btc_4h = load_data_with_quant_features("BTCUSDT", "4h")
btc_map_4h = {c["time"]: c for c in btc_4h}

# 1. Generate Full Quant Long Signals
print("[*] Generating Full Quant BUY Signals...")
long_signals = []
for tf in ["4h", "1h"]:
    std_tp_pct = 0.028 if tf == "4h" else 0.022
    soft_sl_pct = 0.028 if tf == "4h" else 0.025
    hard_sl_pct = 0.038 if tf == "4h" else 0.036
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
            if gain < 0.050: continue
            idm_low = candles[high_idx - 1]["low"]

            best_mid = -1; max_bg = 0.0
            for mid in range(i+1, high_idx):
                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                if 0.30 <= fib <= 0.70 and bg > max_bg:
                    max_bg = bg; best_mid = mid
            if best_mid == -1: continue

            dec_c = candles[best_mid - 1]
            dec_top = max(dec_c["open"], dec_c["close"])
            dec_bot = dec_c["low"]
            has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
            if not has_fvg: continue

            ob_fib = (dec_top - candles[i]["low"]) / (max_high - candles[i]["low"])
            if ob_fib > 0.65: continue

            for t in range(high_idx + 1, min(high_idx + 28, n)):
                if candles[t]["low"] <= dec_top * 1.0005:
                    tap_c = candles[t]
                    curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                    prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                    btc_c = btc_map_4h.get(prev_4h_ts)
                    btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                    if btc_dump >= 0.015: break

                    c_range = tap_c["high"] - tap_c["low"]
                    swept_idm = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                    l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                    w_ratio = (l_wick / c_range) if c_range > 0 else 0
                    mt = (dec_top + dec_bot) / 2.0

                    cvd_prev = candles[t - 3]["cvd"] if t >= 3 else candles[0]["cvd"]
                    cvd_curl = (tap_c["cvd"] - cvd_prev) >= 0
                    cvd_absorbed = (tap_c["delta_ratio"] >= 0.48 or tap_c["delta"] > 0) and cvd_curl
                    vol_healthy = tap_c["volume"] >= 0.85 * tap_c["vol_sma20"]

                    if swept_idm and (w_ratio >= 0.28) and cvd_absorbed and vol_healthy and tap_c["close"] >= mt:
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

                        long_signals.append({
                            "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t,
                            "entry": entry, "exit": exit_p, "gross": (exit_p - entry) / entry,
                            "res": res, "side": "LONG"
                        })
                        break

# 2. Generate Hermes 2.5 Short Signals
print("[*] Generating Hermes 2.5 SHORT Signals...")
short_signals = []
for tf in ["4h", "1h"]:
    std_tp_pct = 0.028 if tf == "4h" else 0.022
    soft_sl_pct = 0.028 if tf == "4h" else 0.025
    hard_sl_pct = 0.038 if tf == "4h" else 0.036
    max_hold = 30 if tf == "4h" else 40

    for sym, candles in all_data[tf].items():
        n = len(candles)
        for i in range(25, n - 35):
            if candles[i]["high"] != max(c["high"] for c in candles[i-15:i+1]):
                continue
            sub_w = candles[i:min(i+16, n)]
            lows = [c["low"] for c in sub_w]
            min_low = min(lows)
            low_idx = i + lows.index(min_low)
            if low_idx <= i + 3: continue
            drop = (candles[i]["high"] - min_low) / candles[i]["high"]
            if drop < 0.050: continue
            idm_high = candles[low_idx - 1]["high"]

            best_mid = -1; max_bg = 0.0
            for mid in range(i+1, low_idx):
                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                if 0.30 <= fib <= 0.70 and bg > max_bg:
                    max_bg = bg; best_mid = mid
            if best_mid == -1: continue

            dec_c = candles[best_mid - 1]
            dec_top = dec_c["high"]
            dec_bot = min(dec_c["open"], dec_c["close"])
            has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
            if not has_bear_fvg: continue

            for t in range(low_idx + 1, min(low_idx + 28, n)):
                if candles[t]["high"] >= dec_bot * 0.9995:
                    tap_c = candles[t]
                    curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                    prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                    btc_c = btc_map_4h.get(prev_4h_ts)
                    btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                    if btc_pump >= 0.020: break

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

                        res = None; exit_p = entry; exit_t = tap_c["time"]
                        curr_sl = soft_sl_p; be_locked = False
                        for m in range(t, min(t + max_hold, n)):
                            low_m = candles[m]["low"]
                            if low_m <= entry * 0.984: # +1.6% MFE lock
                                curr_sl = min(curr_sl, entry * 0.998)
                                be_locked = True
                            if low_m <= tp_p:
                                res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                            if candles[m]["high"] >= hard_sl_p:
                                res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                            if candles[m]["close"] >= curr_sl:
                                res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                                exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                        if not res:
                            fc = candles[min(t + max_hold, n - 1)]["close"]
                            res = "WIN" if fc <= entry else "LOSS"
                            exit_p = fc; exit_t = candles[min(t + max_hold, n - 1)]["time"]

                        short_signals.append({
                            "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t,
                            "entry": entry, "exit": exit_p, "gross": (entry - exit_p) / entry,
                            "res": res, "side": "SHORT"
                        })
                        break

print(f"Total Available Signals: {len(long_signals)} Longs | {len(short_signals)} Shorts")

# Merge & simulate 4-slot execution: 2 Short Slots + 2 Long Slots
all_sig = long_signals + short_signals
all_sig.sort(key=lambda x: x["time"])

active_shorts = []
active_longs = []
executed_100 = []

for s in all_sig:
    active_shorts = [t for t in active_shorts if t > s["time"]]
    active_longs = [t for t in active_longs if t > s["time"]]

    if s["side"] == "SHORT" and len(active_shorts) < 2:
        active_shorts.append(s["exit_time"])
        executed_100.append(s)
    elif s["side"] == "LONG" and len(active_longs) < 2:
        active_longs.append(s["exit_time"])
        executed_100.append(s)

    if len(executed_100) >= 100:
        break

print(f"\n================================================================================")
print(f"   🎯 100-TRADE AUDIT: 4 COMPOUNDING SLOTS (2 SHORTS + 2 LONGS) FROM $50 USDT   ")
print(f"================================================================================")

tot_trades = len(executed_100)
wins = sum(1 for x in executed_100 if x["res"] == "WIN")
losses = tot_trades - wins
wr = (wins / tot_trades * 100.0) if tot_trades > 0 else 0.0

shorts_in_100 = [x for x in executed_100 if x["side"] == "SHORT"]
longs_in_100  = [x for x in executed_100 if x["side"] == "LONG"]

s_wins = sum(1 for x in shorts_in_100 if x["res"] == "WIN")
s_losses = len(shorts_in_100) - s_wins
s_wr = (s_wins / len(shorts_in_100) * 100.0) if shorts_in_100 else 0.0

l_wins = sum(1 for x in longs_in_100 if x["res"] == "WIN")
l_losses = len(longs_in_100) - l_wins
l_wr = (l_wins / len(longs_in_100) * 100.0) if longs_in_100 else 0.0

print(f"Total Executed Trades: {tot_trades}")
print(f"Overall Accuracy:      {wins} WINS / {losses} LOSSES = {wr:.2f}% WIN RATE 🔥")
print(f"  • Shorts Breakdown:  {s_wins} Wins / {s_losses} Losses = {s_wr:.2f}% Win Rate ({len(shorts_in_100)} trades)")
print(f"  • Longs Breakdown:   {l_wins} Wins / {l_losses} Losses = {l_wr:.2f}% Win Rate ({len(longs_in_100)} trades)")

# Compounding calculation
# 4 Slots: Each trade uses 25% of current equity * 5x leverage. 85% reinvested, 15% secure vault reserve
cap = 50.0
vault = 0.0
peak = 50.0
max_dd = 0.0
hit_500 = None
hit_1k = None
hit_2k = None
hit_5k = None

print("\n" + "-" * 75)
print(f"{'Trade #':<8} | {'Side':<6} | {'Symbol':<10} | {'Result':<6} | {'Margin ($)':<10} | {'P&L ($)':<10} | {'Total Equity ($)':<15}")
print("-" * 75)

for idx, t in enumerate(executed_100):
    net_move = t["gross"] - 0.0016
    margin = cap * 0.25 # 25% allocated per slot
    pos_size = margin * 5.0
    pnl = pos_size * net_move

    is_win = (t["res"] == "WIN")
    if is_win:
        cap += (pnl * 0.85)
        vault += (pnl * 0.15)
    else:
        cap += pnl
        if cap < 2.0: cap = 2.0

    tot = cap + vault
    if tot > peak: peak = tot
    dd = (peak - tot) / peak * 100.0 if peak > 0 else 0.0
    if dd > max_dd: max_dd = dd

    if tot >= 500 and hit_500 is None: hit_500 = idx + 1
    if tot >= 1000 and hit_1k is None: hit_1k = idx + 1
    if tot >= 2000 and hit_2k is None: hit_2k = idx + 1
    if tot >= 5000 and hit_5k is None: hit_5k = idx + 1

    if (idx + 1) in [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        print(f"#{idx+1:<7} | {t['side']:<6} | {t['sym']:<10} | {t['res']:<6} | ${margin:>8.2f} | ${pnl:>8.2f} | ${tot:>13.2f}")

print("-" * 75)
print(f"\n📊 FINAL SUMMARY AFTER 100 TRADES:")
print(f"  • Starting Capital:     $50.00 USDT")
print(f"  • Final Active Wallet:  ${cap:,.2f} USDT")
print(f"  • Final Secure Vault:   ${vault:,.2f} USDT (Guaranteed banked profit)")
print(f"  • TOTAL ENDING BALANCE: ${cap + vault:,.2f} USDT 🚀")
print(f"  • Total Growth:         {((cap + vault - 50.0) / 50.0 * 100.0):,.1f}%")
print(f"  • Max Drawdown:         {max_dd:.2f}%")
print(f"  • Milestone Checkpoints:")
print(f"      - $500 Target Hit:  Trade #{hit_500}")
print(f"      - $1,000 Milestone: Trade #{hit_1k}")
print(f"      - $2,000 Target:    Trade #{hit_2k}")
if hit_5k:
    print(f"      - $5,000 Milestone: Trade #{hit_5k}")
