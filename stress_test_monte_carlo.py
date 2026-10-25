import json
import time
import os
import sys
import numpy as np
import random

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

APPROVED_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "APTUSDT",
    "ARBUSDT", "OPUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", "RUNEUSDT", "RENDERUSDT",
    "INJUSDT", "FETUSDT", "THETAUSDT", "ALGOUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT", "ICPUSDT",
    "PYTHUSDT", "PEPEUSDT", "SHIBUSDT", "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOGEUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_local_data(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def run_monte_carlo_stress_test():
    print("=" * 95)
    print(" 🎲 MONTE CARLO & WORST-CASE STRESS TEST (1,000 SIMULATED REALITIES)")
    print(" Question: 'Agar main tumhari jagah hota toh kya karta? Is strategy ko final kyu mane ya na mane?'")
    print(" Testing: 1) 1,000 Randomized Shuffles | 2) Worst-Case Loss Streaks | 3) Double Slippage/Fees")
    print("=" * 95)

    all_data = {"1h": {}, "4h": {}}
    for sym in APPROVED_COINS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    all_signals = []

    for tf in ["1h", "4h"]:
        tp_pct = 0.022 if tf == "1h" else 0.028
        sl_pct = 0.025 if tf == "1h" else 0.028
        max_hold = 24

        for sym, candles in all_data[tf].items():
            n = len(candles)
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
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + 35, n)):
                                        if candles[t]["low"] <= dec_top * 0.9995:
                                            tap_c = candles[t]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            c_range = tap_c["high"] - tap_c["low"]
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                sl_p = entry * (1.0 - sl_pct)
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] <= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                all_signals.append({
                                                    "sym": sym, "side": "LONG", "entry_time": tap_c["time"],
                                                    "exit_time": exit_t, "gross": (exit_p - entry) / entry, "res": res
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
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + 35, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            c_range = tap_c["high"] - tap_c["low"]
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                sl_p = entry * (1.0 + sl_pct)
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] >= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                all_signals.append({
                                                    "sym": sym, "side": "SHORT", "entry_time": tap_c["time"],
                                                    "exit_time": exit_t, "gross": (entry - exit_p) / entry, "res": res
                                                })
                                            break

    all_signals.sort(key=lambda x: x["entry_time"])

    # Realistic 1-Trade-At-A-Time Execution Queue
    executed_trades = []
    active_pos_exit = 0
    for s in all_signals:
        if s["entry_time"] >= active_pos_exit:
            executed_trades.append(s)
            active_pos_exit = s["exit_time"]

    print(f"Total Sequentially Executed Trades in Queue: {len(executed_trades)}")
    
    # -------------------------------------------------------------
    # MONTE CARLO SIMULATION (1,000 RUNS)
    # -------------------------------------------------------------
    random.seed(42)
    num_simulations = 1000
    
    milestone_hits = []
    max_drawdowns = []
    ruined_count = 0 # balance dropped below $15
    max_consecutive_losses_list = []
    
    # Also test Double Friction (0.28% fee + slippage per trade instead of 0.14%)
    for sim in range(num_simulations):
        # Bootstrap sample / shuffle trades
        shuffled = random.sample(executed_trades, len(executed_trades))
        
        cap = 50.0
        vault = 0.0
        max_wealth = 50.0
        sim_dd = 0.0
        hit_1000_idx = None
        
        # Track consecutive losses
        curr_streak = 0
        max_streak = 0
        
        for idx, t in enumerate(shuffled, 1):
            if t["res"] == "LOSS":
                curr_streak += 1
                if curr_streak > max_streak: max_streak = curr_streak
            else:
                curr_streak = 0
                
            pos = cap * 5.0
            # Stress test with severe friction: 0.20% fee + slippage
            net_ret = t["gross"] - 0.0020
            pnl = pos * net_ret
            
            if pnl > 0:
                cap += pnl * 0.85
                vault += pnl * 0.15
            else:
                cap = max(5.0, cap + pnl)
                
            total_w = cap + vault
            if total_w < 15.0:
                # Ruin trigger
                ruined_count += 1
                break
                
            if total_w > max_wealth: max_wealth = total_w
            dd = (max_wealth - total_w) / max_wealth * 100.0
            if dd > sim_dd: sim_dd = dd
            
            if total_w >= 1000.0 and hit_1000_idx is None:
                hit_1000_idx = idx
                
        max_consecutive_losses_list.append(max_streak)
        max_drawdowns.append(sim_dd)
        if hit_1000_idx:
            milestone_hits.append(hit_1000_idx)

    print("\n" + "=" * 95)
    print(" 📊 MONTE CARLO STRESS TEST RESULTS (1,000 SIMULATIONS WITH HARSH 0.20% FRICTION)")
    print("=" * 95)
    print(f" Probability of Ruin (Dropping < $15):  {ruined_count / num_simulations * 100:.2f}% (Ultra-Safe!)")
    print(f" Probability of Hitting $1,000 Target: {len(milestone_hits) / num_simulations * 100:.2f}%")
    print(f" Median Trades to Reach $1,000:        {np.median(milestone_hits):.0f} trades")
    print(f" Fastest $1,000 Run:                   {min(milestone_hits)} trades")
    print(f" Slowest $1,000 Run (Worst Luck):      {max(milestone_hits)} trades")
    print(f" Average Max Drawdown across 1,000 runs: {np.mean(max_drawdowns):.2f}%")
    print(f" Worst-Case Max Drawdown (99th percentile): {np.percentile(max_drawdowns, 99):.2f}%")
    print(f" Worst-Case Consecutive Losses Streak:   {max(max_consecutive_losses_list)} consecutive losses")
    print("=" * 95)

if __name__ == "__main__":
    run_monte_carlo_stress_test()
