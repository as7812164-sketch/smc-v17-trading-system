import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import scripts.test_1year_bb20_model3_full as bb_test

ROOT_DIR = bb_test.ROOT_DIR
DATA_DIR = bb_test.DATA_DIR
CHAMPIONS = bb_test.CHAMPIONS

all_trades = []
for sym in CHAMPIONS:
    fpath = os.path.join(DATA_DIR, f"{sym}_1h.json")
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        candles = json.load(f)
    if len(candles) < 1000:
        continue
    
    day_buckets = defaultdict(list)
    for idx, c in enumerate(candles):
        d_key = bb_test.get_day_key(c["time"])
        day_buckets[d_key].append((idx, c))
    sorted_days = sorted(day_buckets.keys())
    
    for d_i in range(1, len(sorted_days)):
        prev_day_key = sorted_days[d_i - 1]
        curr_day_key = sorted_days[d_i]
        prev_day_candles = [c for _, c in day_buckets[prev_day_key]]
        curr_day_entries = day_buckets[curr_day_key]
        if len(prev_day_candles) < 12 or len(curr_day_entries) < 12:
            continue
        pdh = max(c["high"] for c in prev_day_candles)
        pdl = min(c["low"] for c in prev_day_candles)
        long_taken_today = False
        short_taken_today = False
        
        for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
            if g_idx + 2 >= len(candles):
                continue
            c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
            next_c = candles[g_idx + 1]
            next_c2 = candles[g_idx + 2]
            
            # 1. BOTTOM OB (PDL) -> LONG
            if not long_taken_today:
                dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                if dist_to_pdl <= 0.015 or c_l <= pdl:
                    is_bearish = c_c < c_o
                    gain_1bar = (next_c["high"] - c_l) / c_l
                    gain_2bar = (next_c2["high"] - c_l) / c_l
                    has_fvg = next_c2["low"] > c_h
                    if (is_bearish or (c_h - c_l) > 0) and (gain_1bar >= 0.012 or gain_2bar >= 0.018) and has_fvg:
                        ob_h = c_h
                        ob_l = c_l
                        mt = (ob_h + ob_l) / 2.0
                        sl = ob_l * 0.9985
                        risk = mt - sl
                        if risk > 0:
                            fill_idx = -1
                            for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                b = candles[w_idx]
                                if b["low"] <= sl:
                                    break
                                if b["low"] <= mt:
                                    fill_idx = w_idx
                                    break
                            if fill_idx != -1:
                                long_taken_today = True
                                trade = bb_test.evaluate_trade(candles, fill_idx, "LONG", mt, sl, risk, sym, curr_day_key)
                                all_trades.append(trade)
                                
            # 2. TOP OB (PDH) -> SHORT
            if not short_taken_today:
                dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                if dist_to_pdh <= 0.015 or c_h >= pdh:
                    is_bullish = c_c > c_o
                    drop_1bar = (c_h - next_c["low"]) / c_h
                    drop_2bar = (c_h - next_c2["low"]) / c_h
                    has_fvg = next_c2["high"] < c_l
                    if (is_bullish or (c_h - c_l) > 0) and (drop_1bar >= 0.012 or drop_2bar >= 0.018) and has_fvg:
                        ob_h = c_h
                        ob_l = c_l
                        mt = (ob_h + ob_l) / 2.0
                        sl = ob_h * 1.0015
                        risk = sl - mt
                        if risk > 0:
                            fill_idx = -1
                            for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                b = candles[w_idx]
                                if b["high"] >= sl:
                                    break
                                if b["high"] >= mt:
                                    fill_idx = w_idx
                                    break
                            if fill_idx != -1:
                                short_taken_today = True
                                trade = bb_test.evaluate_trade(candles, fill_idx, "SHORT", mt, sl, risk, sym, curr_day_key)
                                all_trades.append(trade)
                                
            if long_taken_today and short_taken_today:
                break

print(f"Total 1-Year Trades Found: {len(all_trades)}")

sessions = {
    "Asian Session (05:30 - 13:30 IST)": {"wins": 0, "saves": 0, "losses": 0, "pnl_r": 0.0},
    "London Session (13:30 - 18:30 IST)": {"wins": 0, "saves": 0, "losses": 0, "pnl_r": 0.0},
    "New York Session (18:30 - 02:30 IST)": {"wins": 0, "saves": 0, "losses": 0, "pnl_r": 0.0},
    "Pacific / Off-Hours (02:30 - 05:30 IST)": {"wins": 0, "saves": 0, "losses": 0, "pnl_r": 0.0}
}

for t in all_trades:
    ft = t["fill_time"] / 1000.0
    ist_dt = datetime.fromtimestamp(ft, tz=timezone(timedelta(hours=5, minutes=30)))
    mins = ist_dt.hour * 60 + ist_dt.minute
    
    if 330 <= mins < 810:
        s_name = "Asian Session (05:30 - 13:30 IST)"
    elif 810 <= mins < 1110:
        s_name = "London Session (13:30 - 18:30 IST)"
    elif mins >= 1110 or mins < 150:
        s_name = "New York Session (18:30 - 02:30 IST)"
    else:
        s_name = "Pacific / Off-Hours (02:30 - 05:30 IST)"
        
    s = sessions[s_name]
    s["pnl_r"] += t["pnl_r"]
    if "WIN" in t["outcome"]:
        s["wins"] += 1
    elif "SAVE" in t["outcome"]:
        s["saves"] += 1
    else:
        s["losses"] += 1

print("\n" + "=" * 80)
print("🏆 BB 3.0: 1-YEAR (365 DAYS) SESSION PERFORMANCE REPORT")
print("=" * 80)

for s_name, data in sessions.items():
    tot = data["wins"] + data["saves"] + data["losses"]
    wr = (data["wins"] / tot * 100) if tot > 0 else 0
    safe_wr = ((data["wins"] + data["saves"]) / tot * 100) if tot > 0 else 0
    avg_r = (data["pnl_r"] / tot) if tot > 0 else 0
    print(f"\n📍 {s_name}:")
    print(f"   Trades Count     : {tot} trades ({tot/len(all_trades)*100:.1f}% of total market activity)")
    print(f"   Pure Wins        : {data['wins']} ({wr:.1f}%)")
    print(f"   Fee-Shield Saves : {data['saves']} ({data['saves']/tot*100:.1f}%)")
    print(f"   Full Losses      : {data['losses']} ({data['losses']/tot*100:.1f}%)")
    print(f"   Capital Protection: {safe_wr:.1f}%")
    print(f"   Net PnL (R-Mult) : {data['pnl_r']:+.2f} R (Avg: {avg_r:+.2f} R per trade)")
