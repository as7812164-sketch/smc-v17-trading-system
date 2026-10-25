import os
import glob
import json
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# ==============================================================================
# DEEP QUANT FORENSIC SUITE: METHOD 2 (5m FVG RETEST SNIPER)
# Investigates:
#   1. FVG Entry Depth: FVG Edge (38.2%) vs FVG Midpoint (50.0% CE)
#   2. Impact on Miss Rate: Can we reduce the 31% miss rate to <15%?
#   3. Market Structure Shift (MSS) Confirmation Impact on Win Rate
#   4. Multi-Stage Profit Armor: BE Lock at +0.7% vs +1.0%
# Universe: Top-20 Binance USDT-M Champions (August 2026, 1 Full Month OOS)
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "market_data_cache_15m"

T_START = int(datetime.datetime(2026, 8, 1, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_END   = int(datetime.datetime(2026, 8, 31, 23, 59, tzinfo=datetime.timezone.utc).timestamp() * 1000)

def load_data():
    files = glob.glob(str(DATA_DIR / "*_15m.json"))
    coins_data = {}
    for f in sorted(files):
        sym = Path(f).name.replace("_15m.json", "")
        with open(f, "r", encoding="utf-8") as fp:
            raw = json.load(fp)
            filtered = [c for c in raw if (T_START - 16 * 86400 * 1000) <= c["time"] <= (T_END + 4 * 86400 * 1000)]
            if len(filtered) >= 2000:
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

def compute_daily_atrs(daily_buckets):
    sorted_days = sorted(daily_buckets.keys())
    daily_tr = {}
    for i, d in enumerate(sorted_days):
        candles = daily_buckets[d]
        d_high = max(float(c["high"]) for c in candles)
        d_low = min(float(c["low"]) for c in candles)
        if i == 0:
            tr = d_high - d_low
        else:
            prev_d = sorted_days[i - 1]
            prev_close = float(daily_buckets[prev_d][-1]["close"])
            tr = max(d_high - d_low, abs(d_high - prev_close), abs(d_low - prev_close))
        daily_tr[d] = tr

    daily_atr = {}
    tr_series = [daily_tr[d] for d in sorted_days]
    atr_series = pd.Series(tr_series).rolling(14, min_periods=1).mean()
    for i, d in enumerate(sorted_days):
        daily_atr[d] = atr_series.iloc[i]
    return daily_atr

def extract_setups():
    coins_data = load_data()
    all_setups = []

    for sym, candles in coins_data.items():
        daily_buckets = group_candles_by_day(candles)
        sorted_days = sorted(daily_buckets.keys())
        daily_atr = compute_daily_atrs(daily_buckets)
        time_to_idx = {c["time"]: i for i, c in enumerate(candles)}

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
            daily_mid = (pdh + pdl) / 2.0
            pd_range = pdh - pdl
            if pd_range / pdl < 0.010:
                continue

            d_atr = daily_atr.get(prev_day_key, pd_range)
            intraday_running_high = float(curr_candles[0]["high"])
            intraday_running_low = float(curr_candles[0]["low"])

            for c_idx, c in enumerate(curr_candles):
                c_o = float(c["open"])
                c_h = float(c["high"])
                c_l = float(c["low"])
                c_c = float(c["close"])
                c_range = c_h - c_l
                if c_range <= 0:
                    continue

                g_idx = time_to_idx[c["time"]]
                post_candles = candles[g_idx + 1 : g_idx + 1 + 192]
                if len(post_candles) < 12:
                    continue

                # PDL Sweep (Long)
                if c_l < pdl and c_c > pdl and 0.0010 <= (pdl - c_l)/pdl <= 0.0350:
                    lower_wick = min(c_o, c_c) - c_l
                    if lower_wick / c_range >= 0.25:
                        all_setups.append({
                            "symbol": sym, "type": "PDL_SWEEP", "side": "LONG",
                            "time": c["time"], "day": curr_day_key,
                            "level": pdl, "sweep_extreme": c_l, "candle_close": c_c,
                            "target_eq": daily_mid, "target_opposite": pdh,
                            "post_candles": post_candles, "candle": c
                        })

                # PDH Sweep (Short)
                if c_h > pdh and c_c < pdh and 0.0010 <= (c_h - pdh)/pdh <= 0.0350:
                    upper_wick = c_h - max(c_o, c_c)
                    if upper_wick / c_range >= 0.25:
                        all_setups.append({
                            "symbol": sym, "type": "PDH_SWEEP", "side": "SHORT",
                            "time": c["time"], "day": curr_day_key,
                            "level": pdh, "sweep_extreme": c_h, "candle_close": c_c,
                            "target_eq": daily_mid, "target_opposite": pdl,
                            "post_candles": post_candles, "candle": c
                        })

                # CDH/CDL ATR Exhaustion Sweeps
                current_intraday_range = intraday_running_high - intraday_running_low
                exhaustion_ratio = current_intraday_range / d_atr if d_atr > 0 else 0

                if exhaustion_ratio >= 0.70 and c_idx >= 20:
                    if c_h > intraday_running_high and c_c < intraday_running_high:
                        upper_wick = c_h - max(c_o, c_c)
                        if upper_wick / c_range >= 0.25:
                            all_setups.append({
                                "symbol": sym, "type": "CDH_SWEEP", "side": "SHORT",
                                "time": c["time"], "day": curr_day_key,
                                "level": intraday_running_high, "sweep_extreme": c_h, "candle_close": c_c,
                                "target_eq": intraday_running_low + current_intraday_range * 0.50,
                                "target_opposite": intraday_running_low,
                                "post_candles": post_candles, "candle": c
                            })
                    if c_l < intraday_running_low and c_c > intraday_running_low:
                        lower_wick = min(c_o, c_c) - c_l
                        if lower_wick / c_range >= 0.25:
                            all_setups.append({
                                "symbol": sym, "type": "CDL_SWEEP", "side": "LONG",
                                "time": c["time"], "day": curr_day_key,
                                "level": intraday_running_low, "sweep_extreme": c_l, "candle_close": c_c,
                                "target_eq": intraday_running_low + current_intraday_range * 0.50,
                                "target_opposite": intraday_running_high,
                                "post_candles": post_candles, "candle": c
                            })

                intraday_running_high = max(intraday_running_high, c_h)
                intraday_running_low = min(intraday_running_low, c_l)

    all_setups.sort(key=lambda s: s["time"])
    return all_setups

def run_experiment(setups, fvg_retest_depth=0.50, be_trigger=0.0070, tp1_mult=1.0):
    bal = 100.0
    peak_bal = 100.0
    max_dd = 0.0
    tp1_wins, runner_wins, be_saves, sl_losses = 0, 0, 0, 0
    missed, filled = 0, 0
    trades = []
    busy_until = 0

    for s in setups:
        if s["time"] < busy_until:
            continue

        side = s["side"]
        post = s["post_candles"]
        c = s["candle"]
        c_high = float(c["high"])
        c_low = float(c["low"])
        c_close = float(c["close"])

        # Retest Limit target based on depth
        if side == "LONG":
            limit_p = c_low + (c_close - c_low) * fvg_retest_depth
        else:
            limit_p = c_high - (c_high - c_close) * fvg_retest_depth

        is_filled = False
        f_idx = 0
        for b_i in range(min(8, len(post))):
            bh = float(post[b_i]["high"])
            bl = float(post[b_i]["low"])
            if side == "LONG" and bl <= limit_p:
                is_filled = True
                f_idx = b_i
                ep = limit_p
                break
            elif side == "SHORT" and bh >= limit_p:
                is_filled = True
                f_idx = b_i
                ep = limit_p
                break

        if not is_filled:
            missed += 1
            continue

        filled += 1
        active_candles = post[f_idx:]

        # Dynamic Stop Loss Buffer
        if side == "LONG":
            hard_sl = min(ep * 0.9920, s["sweep_extreme"] * 0.9980)
        else:
            hard_sl = max(ep * 1.0080, s["sweep_extreme"] * 1.0020)

        # Targets
        raw_eq_move = abs(s["target_eq"] - ep) / ep
        tp1_move = max(0.0100, min(0.0150, raw_eq_move)) * tp1_mult
        tp1_p = ep * (1.0 + tp1_move) if side == "LONG" else ep * (1.0 - tp1_move)
        tp2_p = ep * 1.0250 if side == "LONG" else ep * 0.9750
        be_trig_p = ep * (1.0 + be_trigger) if side == "LONG" else ep * (1.0 - be_trigger)

        outcome = "UNDECIDED"
        be_locked = False
        curr_sl = hard_sl
        exit_p = ep
        exit_time = active_candles[-1]["time"]

        for b in active_candles[:192]:
            bh = float(b["high"])
            bl = float(b["low"])

            if side == "LONG":
                if bh >= be_trig_p and not be_locked:
                    be_locked = True
                    curr_sl = ep * 1.0010

                if bh >= tp1_p:
                    outcome = "TP1_HIT"
                    exit_p = tp1_p
                    exit_time = b["time"]
                    if bh >= tp2_p:
                        outcome = "TP2_RUNNER_HIT"
                        exit_p = tp2_p
                    break

                if bl <= curr_sl:
                    outcome = "BE_SAVE" if be_locked else "SL_HIT"
                    exit_p = curr_sl
                    exit_time = b["time"]
                    break
            else:
                if bl <= be_trig_p and not be_locked:
                    be_locked = True
                    curr_sl = ep * 0.9990

                if bl <= tp1_p:
                    outcome = "TP1_HIT"
                    exit_p = tp1_p
                    exit_time = b["time"]
                    if bl <= tp2_p:
                        outcome = "TP2_RUNNER_HIT"
                        exit_p = tp2_p
                    break

                if bh >= curr_sl:
                    outcome = "BE_SAVE" if be_locked else "SL_HIT"
                    exit_p = curr_sl
                    exit_time = b["time"]
                    break

        if outcome == "UNDECIDED":
            outcome = "BE_SAVE" if be_locked else "SL_HIT"
            exit_p = curr_sl

        # Isolated $10 margin (5x = $50 notional)
        margin = 10.0
        pos_size = margin * 5.0

        if outcome in ("TP1_HIT", "TP2_RUNNER_HIT"):
            tp_pct = abs(exit_p - ep) / ep
            pnl = pos_size * tp_pct - (pos_size * 0.0010)
            if outcome == "TP2_RUNNER_HIT":
                runner_wins += 1
            else:
                tp1_wins += 1
        elif outcome == "BE_SAVE":
            pnl = 0.0
            be_saves += 1
        else:
            sl_move = abs(ep - exit_p) / ep
            pnl = -(pos_size * sl_move) - (pos_size * 0.0010)
            sl_losses += 1

        bal += pnl
        if bal > peak_bal: peak_bal = bal
        dd = (peak_bal - bal) / peak_bal * 100.0
        if dd > max_dd: max_dd = dd

        busy_until = exit_time
        trades.append({"outcome": outcome, "pnl": pnl, "bal": bal})

    tot_trades = len(trades)
    total_wins = tp1_wins + runner_wins
    pure_wr = (total_wins / tot_trades * 100.0) if tot_trades else 0.0
    eff_wr = ((total_wins + be_saves) / tot_trades * 100.0) if tot_trades else 0.0
    miss_rate = (missed / (tot_trades + missed) * 100.0) if (tot_trades + missed) else 0.0

    return {
        "depth": f"{fvg_retest_depth*100:.0f}%",
        "trades": tot_trades,
        "missed": missed,
        "miss_rate": round(miss_rate, 1),
        "pure_wr": round(pure_wr, 1),
        "eff_wr": round(eff_wr, 1),
        "be_saves": be_saves,
        "sl_losses": sl_losses,
        "max_dd": round(max_dd, 2),
        "final_bal": round(bal, 2),
        "growth": round((bal - 100.0) / 100.0 * 100.0, 2)
    }

def main():
    setups = extract_setups()
    print(f"Total Sweeps: {len(setups)}\n")

    print("=" * 85)
    print("METHOD 2 GRANULAR ANALYSIS: RETEST DEPTH & MISS RATE CALIBRATION")
    print("=" * 85)
    print(f"{'Retest Depth':<14} | {'Trades':<8} | {'Miss Rate':<11} | {'Pure TP%':<10} | {'Eff WR%':<10} | {'Max DD%':<10} | {'Final Bal':<10} | {'Growth%':<10}")
    print("-" * 85)

    # Test retest depths: 25% (Shallow FVG Edge), 35%, 50% (Midpoint), 65% (Deep)
    for depth in [0.20, 0.35, 0.50, 0.65]:
        res = run_experiment(setups, fvg_retest_depth=depth, be_trigger=0.0070)
        print(f"{res['depth']:<14} | {res['trades']:<8} | {res['miss_rate']}%{'':<5} | {res['pure_wr']}%{'':<4} | {res['eff_wr']}%{'':<4} | {res['max_dd']}%{'':<4} | ${res['final_bal']:<9} | {res['growth']:+}%")

    print("=" * 85)

if __name__ == "__main__":
    main()
