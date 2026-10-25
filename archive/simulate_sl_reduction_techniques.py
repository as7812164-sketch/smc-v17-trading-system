import os
import sys
import json
from datetime import datetime

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")
TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

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
    return {c["time"]: c for c in btc_4h}

def test_techniques():
    btc_map_4h = build_btc_map()
    
    # We want to compare:
    # 1. Baseline Hermes 2.5 (Entry at OB top/bot edge, fixed 2.5%/3.6% SL)
    # 2. Technique A: Mean Threshold Entry (Entry at 50% of OB depth)
    # 3. Technique B: ATR Structural SL (SL placed beyond structural sweep low/high with 0.2*ATR buffer, position sized dynamically)
    # 4. Technique C: Hybrid Mean-Threshold + Structural ATR SL
    
    print("Testing SL reduction techniques on 2-Year Dataset without cutting trade frequency...")
    
    results = {}
    
    for mode in ["baseline", "mean_threshold_entry", "structural_atr_sl", "combo_advanced"]:
        total_trades = 0
        wins = 0
        losses = 0
        long_trades = 0
        long_wins = 0
        long_losses = 0
        
        for tf in ["4h", "1h"]:
            std_tp_pct = 0.028 if tf == "4h" else 0.022
            soft_sl_pct = 0.028 if tf == "4h" else 0.025
            hard_sl_pct = 0.038 if tf == "4h" else 0.036
            max_tap_window = 28
            max_hold = 30 if tf == "4h" else 40
            
            for sym in TOP_22_CHAMPIONS:
                candles = load_candles(sym, tf)
                n = len(candles)
                if n < 40:
                    continue
                
                # Compute ATR 14
                atr = [0.0] * n
                for k in range(1, n):
                    tr = max(candles[k]["high"] - candles[k]["low"],
                             abs(candles[k]["high"] - candles[k-1]["close"]),
                             abs(candles[k]["low"] - candles[k-1]["close"]))
                    if k < 14:
                        atr[k] = tr
                    else:
                        atr[k] = (atr[k-1] * 13 + tr) / 14
                
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
                                        for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                            if candles[t]["low"] <= dec_top * 1.0005:
                                                tap_c = candles[t]
                                                c_range = tap_c["high"] - tap_c["low"]
                                                swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                                l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0
                                                
                                                curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                                prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                                btc_c = btc_map_4h.get(prev_4h_ts)
                                                btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                                btc_clean = btc_dump < 0.020
                                                
                                                if btc_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                    # Entry logic based on mode:
                                                    if mode in ["mean_threshold_entry", "combo_advanced"]:
                                                        # Enter at 50% Mean Threshold or if candle low dipped into it
                                                        entry = mt if tap_c["low"] <= mt else (dec_top + mt) / 2.0
                                                    else:
                                                        entry = dec_top
                                                    
                                                    tp_p = entry * (1.0 + std_tp_pct)
                                                    
                                                    # SL logic based on mode:
                                                    if mode in ["structural_atr_sl", "combo_advanced"]:
                                                        # Structural SL: below dec_bot or tap_c low - 0.25*ATR
                                                        struct_low = min(dec_bot, tap_c["low"])
                                                        hard_sl_p = min(struct_low - 0.25 * atr[t], entry * (1.0 - hard_sl_pct))
                                                        # Cap maximum loss distance to 4.2% so risk is defined
                                                        hard_sl_p = max(hard_sl_p, entry * 0.958)
                                                        soft_sl_p = (entry + hard_sl_p) / 2.0
                                                    else:
                                                        soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                        hard_sl_p = entry * (1.0 - hard_sl_pct)
                                                    
                                                    res = None
                                                    curr_sl = soft_sl_p
                                                    be_locked = False
                                                    
                                                    for m in range(t, min(t + max_hold, n)):
                                                        high_m = candles[m]["high"]
                                                        if high_m >= entry * 1.016:
                                                            curr_sl = max(curr_sl, entry * 1.002)
                                                            be_locked = True
                                                        if high_m >= tp_p:
                                                            res = "WIN"
                                                            break
                                                        if candles[m]["low"] <= hard_sl_p:
                                                            res = "LOSS"
                                                            break
                                                        if candles[m]["close"] <= curr_sl:
                                                            res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                                                            break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc >= entry else "LOSS"
                                                    
                                                    total_trades += 1
                                                    long_trades += 1
                                                    if res == "WIN":
                                                        wins += 1
                                                        long_wins += 1
                                                    else:
                                                        losses += 1
                                                        long_losses += 1
                                                    break
                    
                    # SHORT (same structure)
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
                                    bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                    fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                                        max_bg = bg
                                        best_mid = mid
                                if best_mid != -1:
                                    dec_c = candles[best_mid - 1]
                                    dec_top = dec_c["high"]
                                    dec_bot = min(dec_c["open"], dec_c["close"])
                                    has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                    if has_bear_fvg:
                                        for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                            if candles[t]["high"] >= dec_bot * 0.9995:
                                                tap_c = candles[t]
                                                c_range = tap_c["high"] - tap_c["low"]
                                                swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                                u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                                w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0
                                                
                                                curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                                prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                                btc_c = btc_map_4h.get(prev_4h_ts)
                                                btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                                btc_clean_short = btc_pump < 0.020
                                                
                                                if btc_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                    if mode in ["mean_threshold_entry", "combo_advanced"]:
                                                        entry = mt if tap_c["high"] >= mt else (dec_bot + mt) / 2.0
                                                    else:
                                                        entry = dec_bot
                                                    
                                                    tp_p = entry * (1.0 - std_tp_pct)
                                                    
                                                    if mode in ["structural_atr_sl", "combo_advanced"]:
                                                        struct_high = max(dec_top, tap_c["high"])
                                                        hard_sl_p = max(struct_high + 0.25 * atr[t], entry * (1.0 + hard_sl_pct))
                                                        hard_sl_p = min(hard_sl_p, entry * 1.042)
                                                        soft_sl_p = (entry + hard_sl_p) / 2.0
                                                    else:
                                                        soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                        hard_sl_p = entry * (1.0 + hard_sl_pct)
                                                    
                                                    res = None
                                                    curr_sl = soft_sl_p
                                                    be_locked = False
                                                    
                                                    for m in range(t, min(t + max_hold, n)):
                                                        low_m = candles[m]["low"]
                                                        if low_m <= entry * 0.984:
                                                            curr_sl = min(curr_sl, entry * 0.998)
                                                            be_locked = True
                                                        if low_m <= tp_p:
                                                            res = "WIN"
                                                            break
                                                        if candles[m]["high"] >= hard_sl_p:
                                                            res = "LOSS"
                                                            break
                                                        if candles[m]["close"] >= curr_sl:
                                                            res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                                                            break
                                                    if not res:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res = "WIN" if fc <= entry else "LOSS"
                                                    
                                                    total_trades += 1
                                                    if res == "WIN":
                                                        wins += 1
                                                    else:
                                                        losses += 1
                                                    break
        
        wr = (wins / total_trades * 100) if total_trades else 0
        long_wr = (long_wins / long_trades * 100) if long_trades else 0
        results[mode] = {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wr, 2),
            "long_trades": long_trades,
            "long_losses": long_losses,
            "long_wr": round(long_wr, 2)
        }
        print(f"[{mode.upper()}] Trades: {total_trades}, Losses: {losses} (Long Losses: {long_losses}), Win Rate: {wr:.2f}%")

    with open("sl_reduction_techniques_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    test_techniques()
