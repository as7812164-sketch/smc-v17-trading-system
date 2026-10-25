import os
import sys
import json
import time
import numpy as np
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

BASE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
DATA_DIR = os.path.join(BASE_DIR, "historical_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "independent_ict_research")

def load_candles(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

all_data = {"1h": {}, "4h": {}}
for sym in TOP_22_CHAMPIONS:
    for tf in ["1h", "4h"]:
        c = load_candles(sym, tf)
        if len(c) >= 500:
            all_data[tf][sym] = c

def run_simulation(golden_min=0.0, golden_max=1.0, name="BASELINE"):
    trades = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.022 if tf == "1h" else 0.028
        soft_sl_pct = 0.025 if tf == "1h" else 0.028
        hard_sl_pct = 0.036 if tf == "1h" else 0.038
        max_hold = 24

        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 60: continue
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
                            best_retrace_fib = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                # Retracement from high down to OB
                                retrace_fib = (max_high - candles[mid]["low"]) / (max_high - candles[i]["low"])
                                if golden_min <= retrace_fib <= golden_max and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                                    best_retrace_fib = retrace_fib
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + 35, n)):
                                        if candles[t]["low"] <= dec_top * 0.9995:
                                            tap_c = candles[t]
                                            c_range = max(tap_c["high"] - tap_c["low"], 1e-6)
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = l_wick / c_range
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] <= soft_sl_p:
                                                        res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc; exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                trades.append({
                                                    "strategy": name, "sym": sym, "side": "LONG", "tf": tf,
                                                    "time": tap_c["time"], "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (exit_p - entry) / entry, "res": res, "fib": best_retrace_fib
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
                            best_retrace_fib = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                # Retracement from low up to OB
                                retrace_fib = (candles[mid]["high"] - min_low) / (candles[i]["high"] - min_low)
                                if golden_min <= retrace_fib <= golden_max and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                                    best_retrace_fib = retrace_fib
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + 35, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            c_range = max(tap_c["high"] - tap_c["low"], 1e-6)
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = u_wick / c_range
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] >= soft_sl_p:
                                                        res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc; exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                trades.append({
                                                    "strategy": name, "sym": sym, "side": "SHORT", "tf": tf,
                                                    "time": tap_c["time"], "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (entry - exit_p) / entry, "res": res, "fib": best_retrace_fib
                                                })
                                            break

    # Sequential queue
    trades.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for t in trades:
        if t["time"] >= active_exit:
            executed.append(t)
            active_exit = t["exit_time"]

    # Compounding
    cap = 50.0; vault = 0.0; peak = 50.0; max_dd = 0.0; hit_1k = None
    wins = 0; losses = 0; gp = 0.0; gl = 0.0
    long_w = 0; long_l = 0; short_w = 0; short_l = 0

    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - 0.0016
        pos_size = cap * 5.0
        pnl = pos_size * net_move

        if trade["res"] == "WIN":
            wins += 1; gp += max(0.0, pnl)
            cap += (pnl * 0.85); vault += (pnl * 0.15)
            if trade["side"] == "LONG": long_w += 1
            else: short_w += 1
        else:
            losses += 1; gl += abs(pnl)
            cap += pnl
            if cap < 2.0: cap = 0.0
            if trade["side"] == "LONG": long_l += 1
            else: short_l += 1

        tot = cap + vault
        if tot > peak: peak = tot
        dd = (peak - tot) / peak if peak > 0 else 0
        if dd > max_dd: max_dd = dd
        if tot >= 1000.0 and hit_1k is None: hit_1k = idx + 1
        if cap <= 0: break

    wr = (wins / len(executed) * 100.0) if executed else 0.0
    long_wr = (long_w / (long_w + long_l) * 100.0) if (long_w + long_l) > 0 else 0.0
    short_wr = (short_w / (short_w + short_l) * 100.0) if (short_w + short_l) > 0 else 0.0
    pf = (gp / gl) if gl > 0 else (99.0 if gp > 0 else 0.0)

    return {
        "name": name,
        "total_setups": len(trades),
        "executed_trades": len(executed),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(wr, 2),
        "long_wins": long_w,
        "long_losses": long_l,
        "long_win_rate_pct": round(long_wr, 2),
        "short_wins": short_w,
        "short_losses": short_l,
        "short_win_rate_pct": round(short_wr, 2),
        "profit_factor": round(pf, 2),
        "max_drawdown_pct": round(max_dd * 100.0, 2),
        "hit_1k_trade": hit_1k,
        "final_wealth_usdt": round(cap + vault, 2)
    }

def main():
    print("=" * 85)
    print("🔬 TESTING HERMES 3.5 SINGLE TIER WITH FIBONACCI GOLDEN POCKET OB SELECTION")
    print("=" * 85)

    # 1. Baseline Hermes 3.5 Single Tier (Fib 0.30 to 0.70)
    res_base = run_simulation(golden_min=0.30, golden_max=0.70, name="HERMES 3.5 BASELINE (Fib 0.30-0.70)")

    # 2. Strict Golden Pocket (Fib 0.618 to 0.786)
    res_strict_gp = run_simulation(golden_min=0.618, golden_max=0.786, name="STRICT GOLDEN POCKET (Fib 0.618-0.786)")

    # 3. Expanded Golden Pocket / OTE (Fib 0.500 to 0.786)
    res_ote_gp = run_simulation(golden_min=0.500, golden_max=0.786, name="EXPANDED GOLDEN POCKET / OTE (Fib 0.500-0.786)")

    # 4. Shallow Zone (Fib 0.300 to 0.500)
    res_shallow = run_simulation(golden_min=0.300, golden_max=0.500, name="SHALLOW RETRACE (Fib 0.300-0.500)")

    results = [res_base, res_strict_gp, res_ote_gp, res_shallow]

    for r in results:
        print(f"\n--- {r['name']} ---")
        print(f"Setups: {r['total_setups']} | Executed: {r['executed_trades']}")
        print(f"Overall Win Rate : {r['win_rate_pct']}% ({r['wins']}W / {r['losses']}L)")
        print(f"• LONG Win Rate  : {r['long_win_rate_pct']}% ({r['long_wins']}W / {r['long_losses']}L)")
        print(f"• SHORT Win Rate : {r['short_win_rate_pct']}% ({r['short_wins']}W / {r['short_losses']}L)")
        print(f"Profit Factor    : {r['profit_factor']}")
        print(f"Max Drawdown     : {r['max_drawdown_pct']}%")
        print(f"Hit $1,000       : {'Trade #' + str(r['hit_1k_trade']) if r['hit_1k_trade'] else 'Never'}")
        print(f"Final Wealth     : ${r['final_wealth_usdt']:,.2f}")

    # Save to file
    out_file = os.path.join(OUTPUT_DIR, "HERMES35_FIBONACCI_GOLDEN_POCKET_TEST.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Full results saved to: {out_file}")
    print("=" * 85)

if __name__ == "__main__":
    main()
