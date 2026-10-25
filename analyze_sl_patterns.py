import os
import sys
import json
from datetime import datetime
from collections import defaultdict, Counter

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

def analyze():
    # Pre-cache BTC candles
    btc_4h = {c["time"]: c for c in load_candles("BTCUSDT", "4h")}
    btc_1h_list = load_candles("BTCUSDT", "1h")
    btc_1h_map = {c["time"]: c for c in btc_1h_list}
    
    sl_data = json.load(open("hermes25_2year_sl_hits.json", "r", encoding="utf-8"))
    print(f"Total SL Hits to analyze: {len(sl_data)}")
    
    durations_hours = []
    btc_moves_during_trade = []
    btc_opposing_count = 0
    wick_ratios = []
    cvd_deltas = []
    
    for item in sl_data:
        sym = item["symbol"]
        tf = item["timeframe"].lower()
        side = item["side"]
        
        t_entry = datetime.strptime(item["date"], "%Y-%m-%d %H:%M")
        t_exit = datetime.strptime(item["exit_date"], "%Y-%m-%d %H:%M")
        diff_hours = (t_exit - t_entry).total_seconds() / 3600.0
        durations_hours.append(diff_hours)
        
        candles = load_candles(sym, tf)
        entry_ts = int(t_entry.timestamp() * 1000)
        exit_ts = int(t_exit.timestamp() * 1000)
        
        matched_c = None
        for c in candles:
            if abs(c["time"] - entry_ts) < (3600 * 1000 if tf == "1h" else 4 * 3600 * 1000):
                matched_c = c
                break
        
        if matched_c:
            c_range = matched_c["high"] - matched_c["low"]
            if c_range > 0:
                if side == "LONG":
                    wick = min(matched_c["open"], matched_c["close"]) - matched_c["low"]
                else:
                    wick = matched_c["high"] - max(matched_c["open"], matched_c["close"])
                w_ratio = wick / c_range
                wick_ratios.append(w_ratio)
                
                vol = matched_c["volume"]
                buy_vol = vol * ((matched_c["close"] - matched_c["low"]) / c_range)
                sell_vol = vol * ((matched_c["high"] - matched_c["close"]) / c_range)
                net_delta = (buy_vol - sell_vol) / vol if vol > 0 else 0
                cvd_deltas.append(net_delta)
        
        # Closest 1h BTC candle at entry and exit
        # Find closest timestamp in btc_1h_map
        btc_c_entry = btc_1h_map.get(entry_ts - (entry_ts % (3600*1000)))
        btc_c_exit = btc_1h_map.get(exit_ts - (exit_ts % (3600*1000)))
        
        if btc_c_entry and btc_c_exit:
            btc_ret = (btc_c_exit["close"] - btc_c_entry["open"]) / btc_c_entry["open"]
            btc_moves_during_trade.append(btc_ret)
            if side == "LONG" and btc_ret < -0.005:
                btc_opposing_count += 1
            elif side == "SHORT" and btc_ret > 0.005:
                btc_opposing_count += 1

    print("\n================ FORENSIC PATTERN FINDINGS ================")
    print("--- 1. HOLDING TIME & DURATION PATTERN ---")
    print(f"Average Duration to SL: {sum(durations_hours)/len(durations_hours):.1f} hours")
    print(f"Median Duration: {sorted(durations_hours)[len(durations_hours)//2]:.1f} hours")
    quick_death = sum(1 for h in durations_hours if h <= 4.0)
    slow_grind = sum(1 for h in durations_hours if h > 12.0)
    print(f"Flash Sweep Death (<= 4h): {quick_death} trades ({quick_death/len(durations_hours)*100:.1f}%)")
    print(f"Trend Bleed / Slow Drain (> 12h): {slow_grind} trades ({slow_grind/len(durations_hours)*100:.1f}%)")

    print("\n--- 2. WICK SIZE PATTERN AT ENTRY CANDLE ---")
    if wick_ratios:
        avg_w = sum(wick_ratios)/len(wick_ratios)*100
        print(f"Avg Rejection Wick on SL trades: {avg_w:.1f}%")
        low_wick_border = sum(1 for w in wick_ratios if w < 0.28)
        print(f"SL trades with Borderline Wick (18% <= Wick < 28%): {low_wick_border} / {len(wick_ratios)} ({low_wick_border/len(wick_ratios)*100:.1f}%)")
        ultra_wick = sum(1 for w in wick_ratios if w >= 0.28)
        print(f"SL trades with Strong Wick (>= 28%): {ultra_wick} / {len(wick_ratios)} ({ultra_wick/len(wick_ratios)*100:.1f}%)")

    print("\n--- 3. CVD DELTA / INSTITUTIONAL ABSORPTION PATTERN ---")
    if cvd_deltas:
        avg_d = sum(cvd_deltas)/len(cvd_deltas)
        print(f"Avg CVD Delta: {avg_d:.3f}")
        weak_cvd = sum(1 for d in cvd_deltas if d < 0.15)
        print(f"SL trades with Weak or Negative Delta (< 0.15): {weak_cvd} / {len(cvd_deltas)} ({weak_cvd/len(cvd_deltas)*100:.1f}%)")

    print("\n--- 4. BTC MACRO DRAG PATTERN ---")
    print(f"Analyzed BTC correlation trades: {len(btc_moves_during_trade)}")
    print(f"Trades directly sabotaged by BTC moving against position: {btc_opposing_count} ({btc_opposing_count/len(btc_moves_during_trade)*100:.1f}%)")

    print("\n--- 5. TIMEFRAME RESILIENCE PATTERN ---")
    tf_counter = Counter(item["timeframe"] for item in sl_data)
    print(f"1H Intraday SL hits: {tf_counter['1H']} ({tf_counter['1H']/len(sl_data)*100:.1f}%)")
    print(f"4H Macro SL hits: {tf_counter['4H']} ({tf_counter['4H']/len(sl_data)*100:.1f}%)")

    print("\n--- 6. COIN CONCENTRATION PATTERN ---")
    top_7 = ["RUNEUSDT", "SANDUSDT", "DOGEUSDT", "APTUSDT", "PYTHUSDT", "ALGOUSDT", "FETUSDT"]
    top_7_count = sum(1 for item in sl_data if item["symbol"] in top_7)
    print(f"Top 7 High-Beta Volatile Coins: {top_7_count} SLs ({top_7_count/len(sl_data)*100:.1f}%)")

if __name__ == "__main__":
    analyze()
