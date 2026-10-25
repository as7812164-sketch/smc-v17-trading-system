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

def run_test():
    btc_map_4h = build_btc_map()
    
    # Generate all candidate setups across all coins
    raw_trades = []
    
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
                                                raw_trades.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct, "hard_sl_pct": hard_sl_pct,
                                                    "max_hold": max_hold
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
                                                raw_trades.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct, "hard_sl_pct": hard_sl_pct,
                                                    "max_hold": max_hold
                                                })
                                                break
    
    # Sort all setups chronologically
    raw_trades.sort(key=lambda x: x["time"])
    print(f"Total chronological candidate setups: {len(raw_trades)}")
    
    for mode in ["current_baseline", "mean_threshold_entry"]:
        executed = []
        busy_until = 0
        
        for trade in raw_trades:
            if trade["time"] < busy_until:
                continue
            
            sym = trade["sym"]
            tf = trade["tf"]
            t = trade["t_idx"]
            candles = load_candles(sym, tf)
            n = len(candles)
            side = trade["side"]
            
            if side == "LONG":
                if mode == "current_baseline":
                    entry = trade["dec_top"]
                else:
                    # If candle dipped into MT, enter at MT, else midpoint of dec_top and MT
                    entry = trade["mt"] if trade["tap_low"] <= trade["mt"] else (trade["dec_top"] + trade["mt"]) / 2.0
                
                tp_p = entry * (1.0 + trade["std_tp_pct"])
                soft_sl_p = entry * (1.0 - trade["soft_sl_pct"])
                hard_sl_p = entry * (1.0 - trade["hard_sl_pct"])
                
                res = None
                exit_time = trade["time"]
                curr_sl = soft_sl_p
                be_locked = False
                
                for m in range(t, min(t + trade["max_hold"], n)):
                    high_m = candles[m]["high"]
                    if high_m >= entry * 1.016:
                        curr_sl = max(curr_sl, entry * 1.002)
                        be_locked = True
                    if high_m >= tp_p:
                        res = "WIN"
                        exit_time = candles[m]["time"]
                        break
                    if candles[m]["low"] <= hard_sl_p:
                        res = "LOSS"
                        exit_time = candles[m]["time"]
                        break
                    if candles[m]["close"] <= curr_sl:
                        res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                        exit_time = candles[m]["time"]
                        break
                if not res:
                    fc = candles[min(t + trade["max_hold"], n - 1)]["close"]
                    res = "WIN" if fc >= entry else "LOSS"
                    exit_time = candles[min(t + trade["max_hold"], n - 1)]["time"]
            else: # SHORT
                if mode == "current_baseline":
                    entry = trade["dec_bot"]
                else:
                    entry = trade["mt"] if trade["tap_high"] >= trade["mt"] else (trade["dec_bot"] + trade["mt"]) / 2.0
                
                tp_p = entry * (1.0 - trade["std_tp_pct"])
                soft_sl_p = entry * (1.0 + trade["soft_sl_pct"])
                hard_sl_p = entry * (1.0 + trade["hard_sl_pct"])
                
                res = None
                exit_time = trade["time"]
                curr_sl = soft_sl_p
                be_locked = False
                
                for m in range(t, min(t + trade["max_hold"], n)):
                    low_m = candles[m]["low"]
                    if low_m <= entry * 0.984:
                        curr_sl = min(curr_sl, entry * 0.998)
                        be_locked = True
                    if low_m <= tp_p:
                        res = "WIN"
                        exit_time = candles[m]["time"]
                        break
                    if candles[m]["high"] >= hard_sl_p:
                        res = "LOSS"
                        exit_time = candles[m]["time"]
                        break
                    if candles[m]["close"] >= curr_sl:
                        res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                        exit_time = candles[m]["time"]
                        break
                if not res:
                    fc = candles[min(t + trade["max_hold"], n - 1)]["close"]
                    res = "WIN" if fc <= entry else "LOSS"
                    exit_time = candles[min(t + trade["max_hold"], n - 1)]["time"]
            
            busy_until = exit_time
            executed.append({"res": res, "side": side})
            
        wins = sum(1 for e in executed if e["res"] == "WIN")
        losses = sum(1 for e in executed if e["res"] == "LOSS")
        long_losses = sum(1 for e in executed if e["res"] == "LOSS" and e["side"] == "LONG")
        long_wins = sum(1 for e in executed if e["res"] == "WIN" and e["side"] == "LONG")
        total = len(executed)
        print(f"\n[{mode.upper()}] Sequential Queue Results:")
        print(f"Total Executed: {total} trades")
        print(f"Wins: {wins} | Losses (SL hits): {losses} (Long Losses: {long_losses})")
        print(f"Win Rate: {wins/total*100:.2f}% | Loss Rate: {losses/total*100:.2f}%")
        print(f"Long Win Rate: {long_wins/(long_wins+long_losses)*100:.2f}%")

if __name__ == "__main__":
    run_test()
