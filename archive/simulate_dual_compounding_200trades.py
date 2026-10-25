import json
import os
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_4year")

def load_candles(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for c in data:
            c["high"] = float(c["high"])
            c["low"] = float(c["low"])
            c["open"] = float(c["open"])
            c["close"] = float(c["close"])
        return data

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_map = {}
    for c in btc_4h:
        btc_map[c["time"]] = c
    return btc_map

def extract_all_setups():
    btc_map_4h = build_btc_map()
    long_setups = []
    short_setups = []

    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < 40:
                continue

            max_tap_window = 28
            max_hold = 40 if tf == "1h" else 30

            for i in range(20, n - 2):
                # ---------------- LONG SETUP (HERMES 2.0 APEX) ----------------
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
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
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            sentry1_clean = btc_dump < 0.020

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt and sentry1_clean:
                                                long_setups.append({
                                                    "sym": sym,
                                                    "side": "LONG",
                                                    "tf": tf,
                                                    "entry": dec_top,
                                                    "tap_idx": t,
                                                    "time": tap_c["time"],
                                                    "candles": candles,
                                                    "max_hold": max_hold
                                                })
                                            break

                # ---------------- SHORT SETUP (HERMES 3.0-C DYNAMIC ARMOR) ----------------
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
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
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False

                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            sentry1_clean = btc_pump < 0.020

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt and sentry1_clean:
                                                short_setups.append({
                                                    "sym": sym,
                                                    "side": "SHORT",
                                                    "tf": tf,
                                                    "entry": dec_bot,
                                                    "tap_idx": t,
                                                    "time": tap_c["time"],
                                                    "candles": candles,
                                                    "max_hold": max_hold
                                                })
                                            break

    long_setups.sort(key=lambda x: x["time"])
    short_setups.sort(key=lambda x: x["time"])
    return long_setups, short_setups

def evaluate_compounding(setups, target_roi_pct, sl_roe_pct, max_trades=200, is_short=False):
    """
    Evaluates compounding with:
    - 5x Isolated Leverage
    - Starting Capital: $50.00 USDT
    - target_roi_pct: ROE gain on winning trade (e.g. +4.0% ROE or +14.0% ROE)
    - sl_roe_pct: ROE loss on losing trade (e.g. -14.0% ROE @ -2.8% price move)
    """
    target_price_pct = target_roi_pct / 5.0 / 100.0 # Price move required for target ROE
    sl_price_pct = sl_roe_pct / 5.0 / 100.0

    completed_trades = []
    current_balance = 50.0
    busy_until = 0

    for s in setups:
        if s["time"] < busy_until:
            continue # Sequential execution: 1 trade at a time

        entry = s["entry"]
        candles = s["candles"]
        t = s["tap_idx"]
        max_hold = s["max_hold"]
        n = len(candles)

        if not is_short:
            # LONG
            tp_p = entry * (1.0 + target_price_pct)
            sl_p = entry * (1.0 - sl_price_pct)
            res = None
            exit_time = candles[min(t + max_hold, n - 1)]["time"]

            for m in range(t, min(t + max_hold, n)):
                if candles[m]["high"] >= tp_p:
                    res = "WIN"
                    exit_time = candles[m]["time"]
                    break
                if candles[m]["low"] <= sl_p:
                    res = "LOSS"
                    exit_time = candles[m]["time"]
                    break

            if not res:
                fc = candles[min(t + max_hold, n - 1)]["close"]
                res = "WIN" if fc >= entry else "LOSS"

        else:
            # SHORT
            tp_p = entry * (1.0 - target_price_pct)
            sl_p = entry * (1.0 + sl_price_pct)
            res = None
            exit_time = candles[min(t + max_hold, n - 1)]["time"]

            for m in range(t, min(t + max_hold, n)):
                if candles[m]["low"] <= tp_p:
                    res = "WIN"
                    exit_time = candles[m]["time"]
                    break
                if candles[m]["high"] >= sl_p:
                    res = "LOSS"
                    exit_time = candles[m]["time"]
                    break

            if not res:
                fc = candles[min(t + max_hold, n - 1)]["close"]
                res = "WIN" if fc <= entry else "LOSS"

        busy_until = exit_time
        deployed = current_balance

        if res == "WIN":
            profit = deployed * (target_roi_pct / 100.0)
            current_balance += profit
        else:
            loss = deployed * (sl_roe_pct / 100.0)
            current_balance = max(0.50, current_balance - loss)

        completed_trades.append({
            "sym": s["sym"],
            "side": s["side"],
            "tf": s["tf"],
            "time": s["time"],
            "res": res,
            "balance": current_balance
        })

        if len(completed_trades) >= max_trades:
            break

    wins = len([t for t in completed_trades if t["res"] == "WIN"])
    losses = len([t for t in completed_trades if t["res"] == "LOSS"])
    total = len(completed_trades)
    wr = (wins / total * 100.0) if total > 0 else 0.0

    return {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": wr,
        "final_balance": current_balance,
        "trades": completed_trades
    }

def main():
    print("Extracting clean setups from 339,512 candles...")
    long_setups, short_setups = extract_all_setups()
    print(f"Total Long Setups: {len(long_setups)} | Total Short Setups: {len(short_setups)}")

    print("\n" + "="*80)
    print("   SCENARIO 1: ROI Target = +4.0% ROE per trade (5x leverage -> 0.80% price move)")
    print("   SL = -14.0% ROE (2.80% price stop)")
    print("="*80)

    res_long_4roe = evaluate_compounding(long_setups, target_roi_pct=4.0, sl_roe_pct=14.0, max_trades=200, is_short=False)
    res_short_4roe = evaluate_compounding(short_setups, target_roi_pct=4.0, sl_roe_pct=14.0, max_trades=200, is_short=True)

    print(f"LONG Account (200 Trades @ 4% ROE):")
    print(f"  Trades: {res_long_4roe['total_trades']} | Wins: {res_long_4roe['wins']} | Losses: {res_long_4roe['losses']}")
    print(f"  Accuracy (Win Rate): {res_long_4roe['win_rate']:.2f}%")
    print(f"  $50 Growth: ${res_long_4roe['final_balance']:.2f} USDT")

    print(f"\nSHORT Account (200 Trades @ 4% ROE):")
    print(f"  Trades: {res_short_4roe['total_trades']} | Wins: {res_short_4roe['wins']} | Losses: {res_short_4roe['losses']}")
    print(f"  Accuracy (Win Rate): {res_short_4roe['win_rate']:.2f}%")
    print(f"  $50 Growth: ${res_short_4roe['final_balance']:.2f} USDT")

    print("\n" + "="*80)
    print("   SCENARIO 2: Target Price Move = +4.0% (+20.0% ROE per trade @ 5x leverage)")
    print("   SL = -14.0% ROE (2.80% price stop)")
    print("="*80)

    res_long_4price = evaluate_compounding(long_setups, target_roi_pct=20.0, sl_roe_pct=14.0, max_trades=200, is_short=False)
    res_short_4price = evaluate_compounding(short_setups, target_roi_pct=20.0, sl_roe_pct=14.0, max_trades=200, is_short=True)

    print(f"LONG Account (200 Trades @ 4% Price Move / 20% ROE):")
    print(f"  Trades: {res_long_4price['total_trades']} | Wins: {res_long_4price['wins']} | Losses: {res_long_4price['losses']}")
    print(f"  Accuracy (Win Rate): {res_long_4price['win_rate']:.2f}%")
    print(f"  $50 Growth: ${res_long_4price['final_balance']:.2f} USDT")

    print(f"\nSHORT Account (200 Trades @ 4% Price Move / 20% ROE):")
    print(f"  Trades: {res_short_4price['total_trades']} | Wins: {res_short_4price['wins']} | Losses: {res_short_4price['losses']}")
    print(f"  Accuracy (Win Rate): {res_short_4price['win_rate']:.2f}%")
    print(f"  $50 Growth: ${res_short_4price['final_balance']:.2f} USDT")

    print("\n" + "="*80)
    print("   SCENARIO 3: Standard Hermes 2.5 Hybrid Target (+2.8% 4H / +14% ROE, +2.2% 1H / +11% ROE)")
    print("="*80)

    res_long_std = evaluate_compounding(long_setups, target_roi_pct=14.0, sl_roe_pct=14.0, max_trades=200, is_short=False)
    res_short_std = evaluate_compounding(short_setups, target_roi_pct=14.0, sl_roe_pct=14.0, max_trades=200, is_short=True)

    print(f"LONG Account (Standard Hermes 2.0 Apex Target):")
    print(f"  Trades: {res_long_std['total_trades']} | Wins: {res_long_std['wins']} | Losses: {res_long_std['losses']}")
    print(f"  Accuracy (Win Rate): {res_long_std['win_rate']:.2f}%")
    print(f"  $50 Growth: ${res_long_std['final_balance']:.2f} USDT")

    print(f"\nSHORT Account (Standard Hermes 3.0-C Dynamic Armor Target):")
    print(f"  Trades: {res_short_std['total_trades']} | Wins: {res_short_std['wins']} | Losses: {res_short_std['losses']}")
    print(f"  Accuracy (Win Rate): {res_short_std['win_rate']:.2f}%")
    print(f"  $50 Growth: ${res_short_std['final_balance']:.2f} USDT")

    # Output detailed report json
    out = {
        "scenario_1_4roe": {
            "long": {"wr": res_long_4roe["win_rate"], "wins": res_long_4roe["wins"], "losses": res_long_4roe["losses"], "final_balance": res_long_4roe["final_balance"]},
            "short": {"wr": res_short_4roe["win_rate"], "wins": res_short_4roe["wins"], "losses": res_short_4roe["losses"], "final_balance": res_short_4roe["final_balance"]}
        },
        "scenario_2_4price": {
            "long": {"wr": res_long_4price["win_rate"], "wins": res_long_4price["wins"], "losses": res_long_4price["losses"], "final_balance": res_long_4price["final_balance"]},
            "short": {"wr": res_short_4price["win_rate"], "wins": res_short_4price["wins"], "losses": res_short_4price["losses"], "final_balance": res_short_4price["final_balance"]}
        },
        "scenario_3_standard": {
            "long": {"wr": res_long_std["win_rate"], "wins": res_long_std["wins"], "losses": res_long_std["losses"], "final_balance": res_long_std["final_balance"]},
            "short": {"wr": res_short_std["win_rate"], "wins": res_short_std["wins"], "losses": res_short_std["losses"], "final_balance": res_short_std["final_balance"]}
        }
    }
    with open("dual_compounding_200trades_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
