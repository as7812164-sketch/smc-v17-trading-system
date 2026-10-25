import os
import sys
import json
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")

def load_candles(sym, interval):
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
    return data

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    return {c["time"]: c for c in btc_4h}

def extract_2year_sl_hits():
    btc_map_4h = build_btc_map()
    all_trades = []
    
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
                                                entry = dec_top
                                                tp_p = entry * (1.0 + std_tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)
                                                
                                                res = None
                                                exit_p = entry
                                                exit_t = tap_c["time"]
                                                curr_sl = soft_sl_p
                                                be_locked = False
                                                sl_type = None
                                                
                                                for m in range(t, min(t + max_hold, n)):
                                                    high_m = candles[m]["high"]
                                                    if high_m >= entry * 1.016:
                                                        curr_sl = max(curr_sl, entry * 1.002)
                                                        be_locked = True
                                                    if high_m >= tp_p:
                                                        res = "WIN"
                                                        exit_p = tp_p
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res = "LOSS"
                                                        exit_p = min(hard_sl_p, candles[m]["open"])
                                                        exit_t = candles[m]["time"]
                                                        sl_type = "HARD_SL"
                                                        break
                                                    if candles[m]["close"] <= curr_sl:
                                                        res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                                                        exit_p = candles[m]["close"]
                                                        exit_t = candles[m]["time"]
                                                        sl_type = "BE_EXIT" if be_locked and curr_sl > entry else "SOFT_SL"
                                                        break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                    sl_type = "TIME_EXPIRY"
                                                    
                                                all_trades.append({
                                                    "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t,
                                                    "entry": entry, "exit": exit_p, "gross": (exit_p - entry) / entry,
                                                    "res": res, "side": "LONG", "sl_type": sl_type
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
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - std_tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)
                                                
                                                res_s = None
                                                exit_p_s = entry
                                                exit_t_s = tap_c["time"]
                                                curr_effective_sl = soft_sl_p
                                                sl_type_s = None
                                                
                                                for m in range(t, min(t + max_hold, n)):
                                                    low_m = candles[m]["low"]
                                                    if low_m <= entry * (1.0 - 0.016):
                                                        curr_effective_sl = min(curr_effective_sl, entry * (1.0 - 0.002))
                                                    if low_m <= entry * (1.0 - 0.022):
                                                        curr_effective_sl = min(curr_effective_sl, entry * (1.0 - 0.012))
                                                        
                                                    if low_m <= tp_p:
                                                        res_s = "WIN"
                                                        exit_p_s = tp_p
                                                        exit_t_s = candles[m]["time"]
                                                        break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res_s = "LOSS"
                                                        exit_p_s = max(hard_sl_p, candles[m]["open"])
                                                        exit_t_s = candles[m]["time"]
                                                        sl_type_s = "HARD_SL"
                                                        break
                                                    if candles[m]["close"] >= curr_effective_sl:
                                                        res_s = "WIN" if curr_effective_sl < entry else "LOSS"
                                                        exit_p_s = candles[m]["close"]
                                                        exit_t_s = candles[m]["time"]
                                                        sl_type_s = "ARMOR_PROFIT_EXIT" if curr_effective_sl < entry else "SOFT_SL"
                                                        break
                                                if not res_s:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res_s = "WIN" if fc <= entry else "LOSS"
                                                    exit_p_s = fc
                                                    exit_t_s = candles[min(t + max_hold, n - 1)]["time"]
                                                    sl_type_s = "TIME_EXPIRY"
                                                    
                                                all_trades.append({
                                                    "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t_s,
                                                    "entry": entry, "exit": exit_p_s, "gross": (entry - exit_p_s) / entry,
                                                    "res": res_s, "side": "SHORT", "sl_type": sl_type_s
                                                })
                                            break

    # Sort sequentially
    all_trades.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for t in all_trades:
        if t["time"] >= active_exit:
            executed.append(t)
            active_exit = t["exit_time"]

    sl_hits = [t for t in executed if t["res"] == "LOSS"]
    wins = [t for t in executed if t["res"] == "WIN"]
    
    print(f"Total Executed Trades: {len(executed)}")
    print(f"Total Wins:            {len(wins)} ({len(wins)/len(executed)*100:.2f}%)")
    print(f"Total SL Hits (Loss):  {len(sl_hits)} ({len(sl_hits)/len(executed)*100:.2f}%)")
    
    # Analyze SL hits by side
    sl_long = [t for t in sl_hits if t["side"] == "LONG"]
    sl_short = [t for t in sl_hits if t["side"] == "SHORT"]
    print(f"  • Long SL Hits:  {len(sl_long)}")
    print(f"  • Short SL Hits: {len(sl_short)}")
    
    # Analyze by timeframe
    sl_4h = [t for t in sl_hits if t["tf"] == "4h"]
    sl_1h = [t for t in sl_hits if t["tf"] == "1h"]
    print(f"  • 4H SL Hits:    {len(sl_4h)}")
    print(f"  • 1H SL Hits:    {len(sl_1h)}")
    
    # Group by Coin
    coin_sl = defaultdict(int)
    for t in sl_hits:
        coin_sl[t["sym"]] += 1
    print("\nSL Hits Grouped by Coin:")
    for c, cnt in sorted(coin_sl.items(), key=lambda x: x[1], reverse=True):
        print(f"  {c:<12}: {cnt} SL Hits")
        
    # Group by Month
    m_sl = defaultdict(int)
    for t in sl_hits:
        dt = datetime.fromtimestamp(t["time"]/1000)
        m_sl[dt.strftime("%Y-%m")] += 1
    print("\nSL Hits Grouped by Month:")
    for m, cnt in sorted(m_sl.items()):
        print(f"  {m}: {cnt} SL Hits")

    # Save detailed JSON of SL hits
    output = []
    for idx, t in enumerate(sl_hits, 1):
        dt_in = datetime.fromtimestamp(t["time"]/1000).strftime("%Y-%m-%d %H:%M")
        dt_out = datetime.fromtimestamp(t["exit_time"]/1000).strftime("%Y-%m-%d %H:%M")
        output.append({
            "num": idx,
            "date": dt_in,
            "exit_date": dt_out,
            "symbol": t["sym"],
            "side": t["side"],
            "timeframe": t["tf"].upper(),
            "entry_price": round(t["entry"], 4),
            "exit_price": round(t["exit"], 4),
            "loss_pct": round(t["gross"] * 100.0, 2),
            "roe_loss_5x": round(t["gross"] * 500.0, 2),
            "exit_type": t.get("sl_type", "SL_HIT")
        })
        
    with open("hermes25_2year_sl_hits.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved all {len(output)} SL hits to hermes25_2year_sl_hits.json")

if __name__ == "__main__":
    extract_2year_sl_hits()
