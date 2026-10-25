import os
import sys
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "historical_data_2year")
CANDLE_CACHE = {}

def load_candles(sym, interval):
    key = f"{sym}_{interval}"
    if key in CANDLE_CACHE:
        return CANDLE_CACHE[key]
    fpath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        c["volume"] = float(c.get("volume", 0.0))
    CANDLE_CACHE[key] = data
    return data

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_1h = load_candles("BTCUSDT", "1h")
    return {c["time"]: c for c in btc_4h}, {c["time"]: c for c in btc_1h}

def harvest_and_resolve_all_trades():
    """
    Harvests all valid Hermes 3.0 Model 2A trade setups and resolves each candle-by-candle
    using the exact live execution rules (Stepped Trailing SL, Soft SL, Hard SL, TP).
    """
    btc_map_4h, _ = build_btc_map()
    all_resolved_trades = []

    for tf in ["4h", "1h"]:
        max_tap_window = 28
        max_hold = 36 if tf == "4h" else 48
        tf_ms = (4 * 3600 * 1000) if tf == "4h" else (3600 * 1000)

        for sym in TOP_22_CHAMPIONS:
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < 40:
                continue

            for i in range(20, n - 2):
                # -------------------------------------------------------------
                # 1. BULLISH SETUP (LONG)
                # -------------------------------------------------------------
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
                                                    # Candle-by-candle simulation of trade
                                                    entry_price = mt
                                                    entry_time = tap_c["time"]
                                                    active_sl = soft_sl
                                                    locked_roi = 0.0
                                                    peak_roi = 0.0
                                                    step = 0
                                                    be_locked = False
                                                    outcome = None
                                                    exit_price = entry_price
                                                    exit_time = entry_time

                                                    for bar_idx in range(t + 1, min(t + max_hold + 1, n)):
                                                        c = candles[bar_idx]
                                                        bar_time = c["time"]

                                                        # Update peak ROI
                                                        c_high_roi = ((c["high"] - entry_price) / entry_price) * 500.0
                                                        if c_high_roi > peak_roi:
                                                            peak_roi = c_high_roi

                                                        # Stepped Trailing SL Ladder
                                                        target_locked_roi = locked_roi
                                                        target_step = step
                                                        if peak_roi >= 5.0 and target_locked_roi < 1.0:
                                                            target_locked_roi = 1.0; target_step = 1
                                                        if peak_roi >= 9.5 and target_locked_roi < 5.0:
                                                            target_locked_roi = 5.0; target_step = 2
                                                        if peak_roi >= 14.5 and target_locked_roi < 10.0:
                                                            target_locked_roi = 10.0; target_step = 3
                                                        if peak_roi >= 19.5 and target_locked_roi < 15.0:
                                                            target_locked_roi = 15.0; target_step = 4
                                                        if peak_roi >= 24.5 and target_locked_roi < 20.0:
                                                            target_locked_roi = 20.0; target_step = 5
                                                        if peak_roi >= 29.5 and target_locked_roi < 25.0:
                                                            target_locked_roi = 25.0; target_step = 6
                                                        if peak_roi >= 34.5 and target_locked_roi < 30.0:
                                                            target_locked_roi = 30.0; target_step = 7
                                                        if peak_roi >= 39.5:
                                                            extra = int((peak_roi - 34.5) // 5.0)
                                                            ext_target = 30.0 + (extra * 5.0)
                                                            if ext_target > target_locked_roi:
                                                                target_locked_roi = ext_target
                                                                target_step = 7 + extra

                                                        if target_locked_roi > locked_roi:
                                                            locked_roi = target_locked_roi
                                                            step = target_step
                                                            be_locked = True
                                                            active_sl = round(entry_price * (1.0 + (locked_roi / 500.0)), 8)

                                                        # Check Exits
                                                        if c["high"] >= tp:
                                                            outcome = "TP_HIT"
                                                            exit_price = tp
                                                            exit_time = bar_time
                                                            break

                                                        if be_locked and c["low"] <= active_sl:
                                                            outcome = "TRAILING_SL_HIT"
                                                            exit_price = active_sl
                                                            exit_time = bar_time
                                                            break

                                                        if c["low"] <= hard_sl:
                                                            outcome = "HARD_SL_HIT"
                                                            exit_price = hard_sl
                                                            exit_time = bar_time
                                                            break

                                                        if not be_locked and c["close"] <= soft_sl:
                                                            outcome = "SOFT_SL_HIT"
                                                            exit_price = c["close"]
                                                            exit_time = bar_time
                                                            break

                                                    if not outcome:
                                                        last_c = candles[min(t + max_hold, n - 1)]
                                                        exit_price = last_c["close"]
                                                        exit_time = last_c["time"]
                                                        if exit_price >= entry_price:
                                                            outcome = "TIMEOUT_PROFIT"
                                                        else:
                                                            outcome = "TIMEOUT_LOSS"

                                                    fee_rate = 0.0010
                                                    raw_move = (exit_price - entry_price) / entry_price
                                                    net_move = raw_move - fee_rate
                                                    roe_pct = net_move * 500.0

                                                    all_resolved_trades.append({
                                                        "sym": sym,
                                                        "tf": tf,
                                                        "side": "LONG",
                                                        "entry_time": entry_time,
                                                        "exit_time": exit_time,
                                                        "entry_price": entry_price,
                                                        "exit_price": exit_price,
                                                        "outcome": outcome,
                                                        "locked_roi": locked_roi,
                                                        "peak_roi": peak_roi,
                                                        "trailing_step": step,
                                                        "roe_pct": round(roe_pct, 2)
                                                    })
                                            break

                # -------------------------------------------------------------
                # 2. BEARISH SETUP (SHORT)
                # -------------------------------------------------------------
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
                                                    # Candle-by-candle simulation of trade
                                                    entry_price = mt
                                                    entry_time = tap_c["time"]
                                                    active_sl = soft_sl
                                                    locked_roi = 0.0
                                                    peak_roi = 0.0
                                                    step = 0
                                                    be_locked = False
                                                    outcome = None
                                                    exit_price = entry_price
                                                    exit_time = entry_time

                                                    for bar_idx in range(t + 1, min(t + max_hold + 1, n)):
                                                        c = candles[bar_idx]
                                                        bar_time = c["time"]

                                                        # Update peak ROI
                                                        c_low_roi = ((entry_price - c["low"]) / entry_price) * 500.0
                                                        if c_low_roi > peak_roi:
                                                            peak_roi = c_low_roi

                                                        # Stepped Trailing SL Ladder
                                                        target_locked_roi = locked_roi
                                                        target_step = step
                                                        if peak_roi >= 5.0 and target_locked_roi < 1.0:
                                                            target_locked_roi = 1.0; target_step = 1
                                                        if peak_roi >= 9.5 and target_locked_roi < 5.0:
                                                            target_locked_roi = 5.0; target_step = 2
                                                        if peak_roi >= 14.5 and target_locked_roi < 10.0:
                                                            target_locked_roi = 10.0; target_step = 3
                                                        if peak_roi >= 19.5 and target_locked_roi < 15.0:
                                                            target_locked_roi = 15.0; target_step = 4
                                                        if peak_roi >= 24.5 and target_locked_roi < 20.0:
                                                            target_locked_roi = 20.0; target_step = 5
                                                        if peak_roi >= 29.5 and target_locked_roi < 25.0:
                                                            target_locked_roi = 25.0; target_step = 6
                                                        if peak_roi >= 34.5 and target_locked_roi < 30.0:
                                                            target_locked_roi = 30.0; target_step = 7
                                                        if peak_roi >= 39.5:
                                                            extra = int((peak_roi - 34.5) // 5.0)
                                                            ext_target = 30.0 + (extra * 5.0)
                                                            if ext_target > target_locked_roi:
                                                                target_locked_roi = ext_target
                                                                target_step = 7 + extra

                                                        if target_locked_roi > locked_roi:
                                                            locked_roi = target_locked_roi
                                                            step = target_step
                                                            be_locked = True
                                                            active_sl = round(entry_price * (1.0 - (locked_roi / 500.0)), 8)

                                                        # Check Exits
                                                        if c["low"] <= tp:
                                                            outcome = "TP_HIT"
                                                            exit_price = tp
                                                            exit_time = bar_time
                                                            break

                                                        if be_locked and c["high"] >= active_sl:
                                                            outcome = "TRAILING_SL_HIT"
                                                            exit_price = active_sl
                                                            exit_time = bar_time
                                                            break

                                                        if c["high"] >= hard_sl:
                                                            outcome = "HARD_SL_HIT"
                                                            exit_price = hard_sl
                                                            exit_time = bar_time
                                                            break

                                                        if not be_locked and c["close"] >= soft_sl:
                                                            outcome = "SOFT_SL_HIT"
                                                            exit_price = c["close"]
                                                            exit_time = bar_time
                                                            break

                                                    if not outcome:
                                                        last_c = candles[min(t + max_hold, n - 1)]
                                                        exit_price = last_c["close"]
                                                        exit_time = last_c["time"]
                                                        if exit_price <= entry_price:
                                                            outcome = "TIMEOUT_PROFIT"
                                                        else:
                                                            outcome = "TIMEOUT_LOSS"

                                                    fee_rate = 0.0010
                                                    raw_move = (entry_price - exit_price) / entry_price
                                                    net_move = raw_move - fee_rate
                                                    roe_pct = net_move * 500.0

                                                    all_resolved_trades.append({
                                                        "sym": sym,
                                                        "tf": tf,
                                                        "side": "SHORT",
                                                        "entry_time": entry_time,
                                                        "exit_time": exit_time,
                                                        "entry_price": entry_price,
                                                        "exit_price": exit_price,
                                                        "outcome": outcome,
                                                        "locked_roi": locked_roi,
                                                        "peak_roi": peak_roi,
                                                        "trailing_step": step,
                                                        "roe_pct": round(roe_pct, 2)
                                                    })
                                            break

    all_resolved_trades.sort(key=lambda x: x["entry_time"])
    print(f"Total resolved trade setups across 2 years: {len(all_resolved_trades)}")
    return all_resolved_trades

if __name__ == "__main__":
    trades = harvest_and_resolve_all_trades()
    with open("scripts/resolved_apex_setups.json", "w") as f:
        json.dump(trades, f, indent=2)
    print("Saved to scripts/resolved_apex_setups.json")
