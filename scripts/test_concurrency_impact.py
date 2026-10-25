import sys
import os
import json
from datetime import datetime, timezone, timedelta

sys.path.append('scripts')
from compare_compounding_vs_stepdouble import (
    load_candles, build_btc_map, TOP_22_CHAMPIONS, DATA_DIR_2Y
)

IST = timezone(timedelta(hours=5, minutes=30))
btc_map_4h, _ = build_btc_map()
raw_setups = []

for tf in ["4h", "1h"]:
    max_tap_window = 28
    max_hold = 36 if tf == "4h" else 48

    for sym in TOP_22_CHAMPIONS:
        candles = load_candles(sym, tf)
        n = len(candles)
        if n < 40:
            continue

        for i in range(20, n - 2):
            # LONG
            if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 2:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= 0.050:
                        idm_low = candles[high_idx - 1]["low"]
                        best_mid = -1
                        max_bg = 0.0
                        for mid in range(i+1, high_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = max(dec_c["open"], dec_c["close"])
                            dec_bot = dec_c["low"]
                            has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                            if has_fvg:
                                mt = (dec_top + dec_bot) / 2.0
                                tp = mt * 1.030
                                soft_sl = mt * (1.0 - 0.015)
                                hard_sl = mt * (1.0 - 0.030)
                                be_trigger = mt * (1.0 + 0.015)

                                for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                    tap_c = candles[t]
                                    t_l, t_h, t_o, t_c = tap_c["low"], tap_c["high"], tap_c["open"], tap_c["close"]
                                    if t_l <= mt * 1.002 and t_c >= mt * 0.995:
                                        c_range = t_h - t_l
                                        swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(t_o, t_c) - t_l
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                        if swept and w_ratio >= 0.18:
                                            btc_c = btc_map_4h.get(tap_c["time"])
                                            btc_ok = True
                                            if btc_c and btc_c["open"] > 0:
                                                drop = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                                                if drop < -0.040:
                                                    btc_ok = False
                                            if btc_ok:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "side": "LONG", "time": tap_c["time"],
                                                    "tap_idx": t, "mt": mt, "tp": tp, "soft_sl": soft_sl,
                                                    "hard_sl": hard_sl, "be_trigger": be_trigger, "max_hold": max_hold
                                                })
                                        break

            # SHORT
            if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                lows = [c["low"] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)
                if low_idx > i + 2:
                    drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                    if drop >= 0.050:
                        idm_high = candles[low_idx - 1]["high"]
                        best_mid = -1
                        max_bg = 0.0
                        for mid in range(i+1, low_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = dec_c["high"]
                            dec_bot = min(dec_c["open"], dec_c["close"])
                            has_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                            if has_fvg:
                                mt = (dec_top + dec_bot) / 2.0
                                tp = mt * (1.0 - 0.030)
                                soft_sl = mt * 1.015
                                hard_sl = mt * 1.030
                                be_trigger = mt * (1.0 - 0.015)

                                for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                    tap_c = candles[t]
                                    t_l, t_h, t_o, t_c = tap_c["low"], tap_c["high"], tap_c["open"], tap_c["close"]
                                    if t_h >= mt * 0.998 and t_c <= mt * 1.005:
                                        c_range = t_h - t_l
                                        swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                        u_wick = t_h - max(t_o, t_c)
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                        if swept and w_ratio >= 0.18:
                                            btc_c = btc_map_4h.get(tap_c["time"])
                                            btc_ok = True
                                            if btc_c and btc_c["open"] > 0:
                                                drop_b = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                                                if drop_b < -0.040:
                                                    btc_ok = False
                                            if btc_ok:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "side": "SHORT", "time": tap_c["time"],
                                                    "tap_idx": t, "mt": mt, "tp": tp, "soft_sl": soft_sl,
                                                    "hard_sl": hard_sl, "be_trigger": be_trigger, "max_hold": max_hold
                                                })
                                        break

raw_setups.sort(key=lambda s: s["time"])
print(f"Total raw setups found across 2 years: {len(raw_setups)}")

def resolve_with_concurrency(max_slots=1):
    active_slots = []  # list of exit_time_ms
    executed = []
    fee_rate = 0.0010

    for s in raw_setups:
        # Remove expired slots
        active_slots = [exp for exp in active_slots if exp > s["time"]]
        if len(active_slots) >= max_slots:
            continue

        sym = s["sym"]
        tf = s["tf"]
        side = s["side"]
        candles = load_candles(sym, tf)
        n = len(candles)
        t = s["tap_idx"]

        entry_price = s["mt"]
        tp_price = s["tp"]
        soft_sl_price = s["soft_sl"]
        hard_sl_price = s["hard_sl"]
        be_trigger_price = s["be_trigger"]

        be_activated = False
        outcome = None
        exit_price = entry_price
        exit_time = s["time"]

        for bar_idx in range(t + 1, min(t + s["max_hold"] + 1, n)):
            c = candles[bar_idx]
            bar_time = c["time"]

            if side == "LONG":
                if not be_activated and c["high"] >= be_trigger_price:
                    be_activated = True
                if c["low"] <= hard_sl_price:
                    outcome = "HARD_SL"; exit_price = hard_sl_price; exit_time = bar_time; break
                if c["high"] >= tp_price:
                    outcome = "TP_HIT"; exit_price = tp_price; exit_time = bar_time; break
                if be_activated and c["low"] <= entry_price:
                    outcome = "BE_SAVE"; exit_price = entry_price; exit_time = bar_time; break
                if not be_activated and c["low"] <= soft_sl_price:
                    if c["close"] <= soft_sl_price:
                        outcome = "SOFT_SL"; exit_price = c["close"]; exit_time = bar_time; break
            else:
                if not be_activated and c["low"] <= be_trigger_price:
                    be_activated = True
                if c["high"] >= hard_sl_price:
                    outcome = "HARD_SL"; exit_price = hard_sl_price; exit_time = bar_time; break
                if c["low"] <= tp_price:
                    outcome = "TP_HIT"; exit_price = tp_price; exit_time = bar_time; break
                if be_activated and c["high"] >= entry_price:
                    outcome = "BE_SAVE"; exit_price = entry_price; exit_time = bar_time; break
                if not be_activated and c["high"] >= soft_sl_price:
                    if c["close"] <= soft_sl_price:
                        outcome = "SOFT_SL"; exit_price = c["close"]; exit_time = bar_time; break

        if not outcome:
            last_c = candles[min(t + s["max_hold"], n - 1)]
            exit_price = last_c["close"]
            exit_time = last_c["time"]
            if side == "LONG":
                outcome = "TP_HIT" if exit_price > entry_price else ("BE_SAVE" if be_activated else "SOFT_SL")
            else:
                outcome = "TP_HIT" if exit_price < entry_price else ("BE_SAVE" if be_activated else "SOFT_SL")

        active_slots.append(exit_time)

        if side == "LONG":
            raw_move = (exit_price - entry_price) / entry_price
        else:
            raw_move = (entry_price - exit_price) / entry_price

        net_move = raw_move - fee_rate
        roe_pct = net_move * 500.0

        executed.append({
            "time": s["time"],
            "exit_time": exit_time,
            "roe_pct": round(roe_pct, 2),
            "outcome": outcome
        })

    return executed

print("\n--- CONCURRENCY CAPACITY TEST (2-YEAR WINDOW) ---")
for slots in [1, 2, 3, 4, 5]:
    ex = resolve_with_concurrency(slots)
    wins = sum(1 for x in ex if x["roe_pct"] > 0)
    wr = (wins / len(ex) * 100) if ex else 0
    trades_per_month = len(ex) / 24.0
    print(f"Slots: {slots} | Trades Executed in 2Y: {len(ex)} | Per Month: {trades_per_month:.1f} trades | Win Rate: {wr:.1f}%")
