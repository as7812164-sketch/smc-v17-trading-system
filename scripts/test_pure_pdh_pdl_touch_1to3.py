import os
import glob
import json
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# ==============================================================================
# PURE TOUCH PDH/PDL 1:3 R:R BENCHMARK
# Rule: NO CANDLE CLOSING. Direct limit touch entry at PDH (SHORT) and PDL (LONG).
# Outcomes: Straight TP (1:3 R:R) or SL. Nothing else. No BE lock.
# Test Scope:
#   Mode A: Exactly 2 Trades per Coin (1st Short at PDH, 1st Long at PDL)
#   Mode B: Daily 2 Trades per Coin (Max 1 Short + 1 Long per day across August 2026)
# Tested across all 20 coins in market_data_cache_15m.
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "market_data_cache_15m"

T_START = int(datetime.datetime(2026, 8, 1, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_END   = int(datetime.datetime(2026, 8, 31, 23, 59, tzinfo=datetime.timezone.utc).timestamp() * 1000)

def load_data():
    files = sorted(glob.glob(str(DATA_DIR / "*_15m.json")))
    coins_data = {}
    for f in files:
        sym = Path(f).name.replace("_15m.json", "")
        with open(f, "r", encoding="utf-8") as fp:
            raw = json.load(fp)
            # Filter August 2026 plus prior 4 days and post 7 days
            filtered = [c for c in raw if (T_START - 4 * 86400 * 1000) <= c["time"] <= (T_END + 7 * 86400 * 1000)]
            if len(filtered) >= 1500:
                coins_data[sym] = filtered
    return coins_data

def group_candles_by_day(candles):
    days = {}
    for c in candles:
        dt = datetime.datetime.fromtimestamp(c["time"] / 1000.0, tz=datetime.timezone.utc)
        day_key = dt.strftime("%Y-%m-%d")
        if day_key not in days:
            days[day_key] = []
        days[day_key].append(c)
    return days

def simulate_trade(entry_price, side, post_candles, sl_pct=0.012, max_bars=192):
    """
    Simulates straight 1:3 R:R trade.
    TP = 3 * SL.
    Returns: outcome ('TP_HIT' or 'SL_HIT'), exit_price, exit_time
    """
    tp_pct = sl_pct * 3.0

    if side == "LONG":
        tp_price = entry_price * (1.0 + tp_pct)
        sl_price = entry_price * (1.0 - sl_pct)
    else: # SHORT
        tp_price = entry_price * (1.0 - tp_pct)
        sl_price = entry_price * (1.0 + sl_pct)

    outcome = "UNDECIDED"
    exit_price = entry_price
    exit_time = post_candles[-1]["time"]

    for b in post_candles[:max_bars]:
        bh = float(b["high"])
        bl = float(b["low"])

        if side == "LONG":
            # Conservative conflict check: If both hit, SL hits first
            if bl <= sl_price and bh >= tp_price:
                outcome = "SL_HIT"
                exit_price = sl_price
                exit_time = b["time"]
                break
            if bh >= tp_price:
                outcome = "TP_HIT"
                exit_price = tp_price
                exit_time = b["time"]
                break
            if bl <= sl_price:
                outcome = "SL_HIT"
                exit_price = sl_price
                exit_time = b["time"]
                break
        else: # SHORT
            if bh >= sl_price and bl <= tp_price:
                outcome = "SL_HIT"
                exit_price = sl_price
                exit_time = b["time"]
                break
            if bl <= tp_price:
                outcome = "TP_HIT"
                exit_price = tp_price
                exit_time = b["time"]
                break
            if bh >= sl_price:
                outcome = "SL_HIT"
                exit_price = sl_price
                exit_time = b["time"]
                break

    if outcome == "UNDECIDED":
        # At expiration, evaluate current close
        last_close = float(post_candles[min(max_bars-1, len(post_candles)-1)]["close"])
        if side == "LONG":
            outcome = "TP_HIT" if last_close >= entry_price else "SL_HIT"
        else:
            outcome = "TP_HIT" if last_close <= entry_price else "SL_HIT"
        exit_price = last_close

    return outcome, exit_price, exit_time

def run_pure_touch_audit(sl_pct=0.012):
    coins_data = load_data()
    print(f"Loaded {len(coins_data)} coins for Pure Touch 1:3 R:R Audit (SL={sl_pct*100:.1f}%, TP={sl_pct*300:.1f}%).\n")

    # Mode A: Exactly 2 trades per coin (1st Short, 1st Long)
    mode_a_results = {}
    
    # Mode B: Daily 2 trades per coin
    mode_b_all_trades = []

    for sym, candles in coins_data.items():
        daily_buckets = group_candles_by_day(candles)
        sorted_days = sorted(daily_buckets.keys())
        time_to_idx = {c["time"]: i for i, c in enumerate(candles)}

        first_short_taken = False
        first_long_taken = False
        coin_record = {
            "symbol": sym,
            "short_trade": None,
            "long_trade": None
        }

        for idx in range(1, len(sorted_days)):
            prev_day_key = sorted_days[idx - 1]
            curr_day_key = sorted_days[idx]

            if not curr_day_key.startswith("2026-08"):
                continue

            prev_candles = daily_buckets[prev_day_key]
            curr_candles = daily_buckets[curr_day_key]
            if len(prev_candles) < 80 or len(curr_candles) < 80:
                continue

            pdh = max(float(c["high"]) for c in prev_candles)
            pdl = min(float(c["low"]) for c in prev_candles)
            if (pdh - pdl) / pdl < 0.010:
                continue

            day_short_taken = False
            day_long_taken = False

            for c_idx, c in enumerate(curr_candles):
                ch = float(c["high"])
                cl = float(c["low"])
                g_idx = time_to_idx[c["time"]]
                post_candles = candles[g_idx + 1 :]
                if len(post_candles) < 4:
                    continue

                # 1. SHORT TOUCH AT PDH
                if ch >= pdh and not day_short_taken:
                    day_short_taken = True
                    outcome, exit_p, exit_t = simulate_trade(pdh, "SHORT", post_candles, sl_pct=sl_pct)
                    trade_info = {
                        "symbol": sym, "side": "SHORT", "date": curr_day_key,
                        "time": c["time"], "entry_price": pdh, "outcome": outcome,
                        "exit_price": exit_p, "exit_time": exit_t
                    }
                    mode_b_all_trades.append(trade_info)
                    if not first_short_taken:
                        first_short_taken = True
                        coin_record["short_trade"] = trade_info

                # 2. LONG TOUCH AT PDL
                if cl <= pdl and not day_long_taken:
                    day_long_taken = True
                    outcome, exit_p, exit_t = simulate_trade(pdl, "LONG", post_candles, sl_pct=sl_pct)
                    trade_info = {
                        "symbol": sym, "side": "LONG", "date": curr_day_key,
                        "time": c["time"], "entry_price": pdl, "outcome": outcome,
                        "exit_price": exit_p, "exit_time": exit_t
                    }
                    mode_b_all_trades.append(trade_info)
                    if not first_long_taken:
                        first_long_taken = True
                        coin_record["long_trade"] = trade_info

        mode_a_results[sym] = coin_record

    return mode_a_results, mode_b_all_trades

def main():
    for sl_val in [0.010, 0.012, 0.015]:
        mode_a, mode_b = run_pure_touch_audit(sl_pct=sl_val)
        
        # Analyze Mode A: Exactly 2 trades per coin
        a_trades = []
        for sym, rec in mode_a.items():
            if rec["short_trade"]: a_trades.append(rec["short_trade"])
            if rec["long_trade"]: a_trades.append(rec["long_trade"])

        a_tp = sum(1 for t in a_trades if t["outcome"] == "TP_HIT")
        a_sl = sum(1 for t in a_trades if t["outcome"] == "SL_HIT")
        a_wr = (a_tp / len(a_trades) * 100.0) if a_trades else 0

        # Analyze Mode B: All days (Daily 2 trades)
        b_tp = sum(1 for t in mode_b if t["outcome"] == "TP_HIT")
        b_sl = sum(1 for t in mode_b if t["outcome"] == "SL_HIT")
        b_wr = (b_tp / len(mode_b) * 100.0) if mode_b else 0

        print("=" * 80)
        print(f"SL={sl_val*100:.1f}% | TP={sl_val*300:.1f}% (1:3 R:R)")
        print(f"  MODE A (Strict 2 Trades / Coin): Total={len(a_trades)} | TP={a_tp} | SL={a_sl} | WinRate={a_wr:.1f}%")
        print(f"  MODE B (Daily 1 Long + 1 Short / Coin): Total={len(mode_b)} | TP={b_tp} | SL={b_sl} | WinRate={b_wr:.1f}%")

    # Save detailed Mode A breakdown for sl_val = 0.012 to json
    mode_a, mode_b = run_pure_touch_audit(sl_pct=0.012)
    out_file = BASE_DIR / "pure_touch_1to3_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump({"mode_a_per_coin": mode_a, "mode_b_total_trades": len(mode_b)}, fp, indent=2)
    print("\nSaved detailed audit to pure_touch_1to3_audit_results.json")

if __name__ == "__main__":
    main()
