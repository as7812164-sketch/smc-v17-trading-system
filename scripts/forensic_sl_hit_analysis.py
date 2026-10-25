import os
import sys
import glob
import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "market_data_cache_15m"

def run_forensic():
    files = glob.glob(str(DATA_DIR / "*_15m.json"))[:5] # sample 5 coins for quick forensic
    print("Running deep forensic autopsy on Stop Loss hits...")

    total_sl = 0
    sl_after_going_in_profit_1r = 0 # Reached +1.0R but reversed to SL
    sl_after_going_in_profit_half_r = 0 # Reached +0.5R but reversed to SL
    immediate_sl_within_2_bars = 0 # Breakout continuation trap

    for f in files:
        with open(f, "r") as fp:
            candles = json.load(fp)
        for c in candles:
            c["open"] = float(c["open"])
            c["high"] = float(c["high"])
            c["low"] = float(c["low"])
            c["close"] = float(c["close"])

        # Group by day
        days = {}
        for idx, c in enumerate(candles):
            dt = datetime.datetime.fromtimestamp(c["time"] / 1000.0, tz=datetime.timezone.utc)
            k = dt.strftime("%Y-%m-%d")
            if k not in days:
                days[k] = []
            days[k].append((idx, c))

        sorted_days = sorted(days.keys())
        for d_i in range(1, len(sorted_days)):
            p_list = days[sorted_days[d_i - 1]]
            c_list = days[sorted_days[d_i]]
            if len(p_list) < 80 or len(c_list) < 80:
                continue

            pdh = max(c[1]["high"] for c in p_list)
            pdl = min(c[1]["low"] for c in p_list)

            for idx_in_day, (g_idx, c) in enumerate(c_list):
                c_o = c["open"]
                c_h = c["high"]
                c_l = c["low"]
                c_c = c["close"]

                # LONG PDL SWEEP
                if c_l < pdl and c_c > pdl:
                    entry = c_c
                    sl = c_l
                    risk = entry - sl
                    if risk > 0:
                        tp = entry + (risk * 2.0)
                        max_fav_r = 0.0
                        bars_to_sl = 0
                        hit_sl = False

                        for f_i in range(g_idx + 1, min(g_idx + 97, len(candles))):
                            b = candles[f_i]
                            fav_r = (b["high"] - entry) / risk
                            if fav_r > max_fav_r:
                                max_fav_r = fav_r

                            if b["low"] <= sl:
                                hit_sl = True
                                bars_to_sl = f_i - g_idx
                                break
                            if b["high"] >= tp:
                                break

                        if hit_sl:
                            total_sl += 1
                            if max_fav_r >= 1.0:
                                sl_after_going_in_profit_1r += 1
                            if max_fav_r >= 0.5:
                                sl_after_going_in_profit_half_r += 1
                            if bars_to_sl <= 2:
                                immediate_sl_within_2_bars += 1

    print(f"Sampled Stop Loss Hits: {total_sl}")
    print(f"1. Trades that reached >= +1.0R profit before reversing into SL: {sl_after_going_in_profit_1r} ({sl_after_going_in_profit_1r/total_sl*100:.1f}%)")
    print(f"2. Trades that reached >= +0.5R profit before reversing into SL: {sl_after_going_in_profit_half_r} ({sl_after_going_in_profit_half_r/total_sl*100:.1f}%)")
    print(f"3. Immediate Breakout Traps (stopped out within 1-2 candles):    {immediate_sl_within_2_bars} ({immediate_sl_within_2_bars/total_sl*100:.1f}%)")

if __name__ == "__main__":
    run_forensic()
