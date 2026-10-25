import os
import glob
import json
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# ==============================================================================
# INSTITUTIONAL PDH / PDL LIQUIDITY SWEEP AUDIT & ENHANCEMENT SUITE
# Period: August 1, 2026 to August 31, 2026 (Full Month OOS)
# Universe: Top-20 Binance USDT-M Champions
# Compares:
#   Config A: Baseline Raw (Cross-day holding)
#   Config B: HTF 4H Trend Aligned (Long PDL in Bull, Short PDH in Bear)
#   Config C: HTF Trend + London/NY Killzone Timing
#   Config D: HTF Trend + Killzone + 5m MSS/FVG Retest Sniper
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
            # Filter August 2026 plus prior 4 days and post 4 days
            filtered = [c for c in raw if (T_START - 4 * 86400 * 1000) <= c["time"] <= (T_END + 4 * 86400 * 1000)]
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

def is_killzone(timestamp_ms):
    """
    London Open Killzone: 07:00 - 11:00 UTC (12:30 - 16:30 IST)
    New York Open Killzone: 13:00 - 17:00 UTC (18:30 - 22:30 IST)
    """
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0, tz=datetime.timezone.utc)
    hour = dt.hour
    return (7 <= hour <= 11) or (13 <= hour <= 17)

def run_simulation(setups, mode="METHOD_1", max_hold_bars=192):
    bal = 100.0
    peak_bal = 100.0
    max_dd = 0.0
    tp_wins = 0
    be_saves = 0
    sl_losses = 0
    trades = []
    busy_until = 0

    missed_count = 0
    filled_count = 0

    for s in setups:
        if s["time"] < busy_until:
            continue

        side = s["side"]
        post_candles = s["post_candles"]
        if len(post_candles) < 4:
            continue

        # Decide entry based on Mode
        if mode == "METHOD_1":
            # Direct 15m candle close
            ep = s["candle_close"]
            entry_time = post_candles[0]["time"]
            active_sub = post_candles
        elif mode == "METHOD_2":
            # 5m / Sub-impulse Retest to FVG (50% pullback of the sweep candle)
            c_high = s["sweep_high"] if side == "SHORT" else s["candle_high"]
            c_low = s["sweep_low"] if side == "LONG" else s["candle_low"]
            c_close = s["candle_close"]

            if side == "LONG":
                target_limit = c_low + (c_close - c_low) * 0.50
            else:
                target_limit = c_high - (c_high - c_close) * 0.50

            filled = False
            fill_idx = 0
            for i in range(min(12, len(post_candles))):
                b_high = float(post_candles[i]["high"])
                b_low = float(post_candles[i]["low"])
                if side == "LONG" and b_low <= target_limit:
                    filled = True
                    fill_idx = i
                    ep = target_limit
                    break
                elif side == "SHORT" and b_high >= target_limit:
                    filled = True
                    fill_idx = i
                    ep = target_limit
                    break

            if not filled:
                missed_count += 1
                continue

            filled_count += 1
            entry_time = post_candles[fill_idx]["time"]
            active_sub = post_candles[fill_idx:]
        else:
            raise ValueError(f"Unknown mode: {mode}")

        tp_spot = 0.0250
        sl_spot = 0.0150
        be_spot = 0.0150

        if side == "LONG":
            tp_p = ep * (1.0 + tp_spot)
            # SL strictly at sweep low with 0.1% buffer, bounded between 0.8% and 2.0%
            raw_sl = s["sweep_low"] * 0.9990
            hard_sl = max(ep * (1.0 - 0.0200), min(ep * (1.0 - 0.0080), raw_sl))
            be_trigger_p = ep * (1.0 + be_spot)
        else:
            tp_p = ep * (1.0 - tp_spot)
            raw_sl = s["sweep_high"] * 1.0010
            hard_sl = min(ep * (1.0 + 0.0200), max(ep * (1.0 + 0.0080), raw_sl))
            be_trigger_p = ep * (1.0 - be_spot)

        outcome = "UNDECIDED"
        be_locked = False
        curr_sl = hard_sl
        exit_p = ep
        exit_time = active_sub[-1]["time"]

        for b_idx, b in enumerate(active_sub[:max_hold_bars]):
            b_h = float(b["high"])
            b_l = float(b["low"])

            if side == "LONG":
                if b_h >= be_trigger_p and not be_locked:
                    be_locked = True
                    curr_sl = ep * 1.0010

                if b_h >= tp_p:
                    outcome = "TP_HIT"
                    exit_p = tp_p
                    exit_time = b["time"]
                    break

                if b_l <= curr_sl:
                    outcome = "BE_SAVE" if be_locked else "SL_HIT"
                    exit_p = curr_sl
                    exit_time = b["time"]
                    break
            else:
                if b_l <= be_trigger_p and not be_locked:
                    be_locked = True
                    curr_sl = ep * 0.9990

                if b_l <= tp_p:
                    outcome = "TP_HIT"
                    exit_p = tp_p
                    exit_time = b["time"]
                    break

                if b_h >= curr_sl:
                    outcome = "BE_SAVE" if be_locked else "SL_HIT"
                    exit_p = curr_sl
                    exit_time = b["time"]
                    break

        if outcome == "UNDECIDED":
            outcome = "BE_SAVE" if be_locked else "SL_HIT"
            exit_p = curr_sl

        # Fixed compounding position sizing (5x leverage)
        margin = bal
        pos_size = margin * 5.0

        if outcome == "TP_HIT":
            pnl = pos_size * tp_spot - (pos_size * 0.0010)
            tp_wins += 1
        elif outcome == "BE_SAVE":
            pnl = (pos_size * 0.0010) - (pos_size * 0.0010)  # Fees absorbed
            be_saves += 1
        else:
            sl_move = abs(ep - exit_p) / ep
            pnl = -(pos_size * sl_move) - (pos_size * 0.0010)
            sl_losses += 1

        bal += pnl
        if bal < 5.0:  # Circuit breaker if liquidated
            bal = 5.0
        if bal > peak_bal:
            peak_bal = bal
        dd = (peak_bal - bal) / peak_bal * 100.0
        if dd > max_dd:
            max_dd = dd

        busy_until = exit_time
        trades.append({
            "symbol": s["symbol"],
            "side": side,
            "entry_time": entry_time,
            "outcome": outcome,
            "pnl": pnl,
            "bal": bal
        })

    tot_trades = len(trades)
    pure_wr = (tp_wins / tot_trades * 100.0) if tot_trades else 0.0
    eff_wr = ((tp_wins + be_saves) / tot_trades * 100.0) if tot_trades else 0.0
    growth_pct = (bal - 100.0) / 100.0 * 100.0

    return {
        "total_trades": tot_trades,
        "missed_count": missed_count,
        "filled_count": filled_count,
        "tp_wins": tp_wins,
        "be_saves": be_saves,
        "sl_losses": sl_losses,
        "pure_win_rate": round(pure_wr, 2),
        "effective_win_rate": round(eff_wr, 2),
        "final_balance": round(bal, 2),
        "net_growth_pct": round(growth_pct, 2),
        "max_drawdown_pct": round(max_dd, 2)
    }

def main():
    coins_data = load_data()
    print(f"Loaded {len(coins_data)} coins for institutional analysis.")

    # Collect all setups with complete metadata
    all_raw_setups = []

    for sym, candles in coins_data.items():
        closes = pd.Series([float(c["close"]) for c in candles])
        # 4H EMA 50 on 15m is span=800
        ema_4h = closes.ewm(span=800, adjust=False).mean()

        daily_buckets = group_candles_by_day(candles)
        sorted_days = sorted(daily_buckets.keys())

        # Map each candle to global index
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

            pdh = max(c["high"] for c in prev_candles)
            pdl = min(c["low"] for c in prev_candles)
            pd_range_pct = (pdh - pdl) / pdl
            if pd_range_pct < 0.015:
                continue

            for c_idx, c in enumerate(curr_candles):
                c_o = float(c["open"])
                c_h = float(c["high"])
                c_l = float(c["low"])
                c_c = float(c["close"])
                c_range = c_h - c_l
                if c_range <= 0:
                    continue

                g_idx = time_to_idx[c["time"]]
                is_bull_4h = c_c > ema_4h.iloc[g_idx]

                # 1. LONG PDL Sweep
                if c_l < pdl and c_c > pdl:
                    sweep_depth = (pdl - c_l) / pdl
                    if 0.0010 <= sweep_depth <= 0.0350:
                        lower_wick = min(c_o, c_c) - c_l
                        wick_ratio = lower_wick / c_range
                        if wick_ratio >= 0.25:
                            # Full post-candles across days
                            post_candles = candles[g_idx + 1 : g_idx + 1 + 192]
                            all_raw_setups.append({
                                "symbol": sym,
                                "side": "LONG",
                                "time": c["time"],
                                "pdl": pdl,
                                "pdh": pdh,
                                "sweep_low": c_l,
                                "candle_high": c_h,
                                "candle_low": c_l,
                                "candle_close": c_c,
                                "wick_ratio": wick_ratio,
                                "is_trend_aligned": is_bull_4h,
                                "is_killzone": is_killzone(c["time"]),
                                "post_candles": post_candles
                            })

                # 2. SHORT PDH Sweep
                if c_h > pdh and c_c < pdh:
                    sweep_depth = (c_h - pdh) / pdh
                    if 0.0010 <= sweep_depth <= 0.0350:
                        upper_wick = c_h - max(c_o, c_c)
                        wick_ratio = upper_wick / c_range
                        if wick_ratio >= 0.25:
                            post_candles = candles[g_idx + 1 : g_idx + 1 + 192]
                            all_raw_setups.append({
                                "symbol": sym,
                                "side": "SHORT",
                                "time": c["time"],
                                "pdl": pdl,
                                "pdh": pdh,
                                "sweep_high": c_h,
                                "candle_high": c_h,
                                "candle_low": c_l,
                                "candle_close": c_c,
                                "wick_ratio": wick_ratio,
                                "is_trend_aligned": not is_bull_4h,
                                "is_killzone": is_killzone(c["time"]),
                                "post_candles": post_candles
                            })

    all_raw_setups.sort(key=lambda s: s["time"])
    print(f"Total Raw Sweeps Extracted: {len(all_raw_setups)}")

    # Prepare Subsets
    setups_config_a = all_raw_setups  # Raw Baseline
    setups_config_b = [s for s in all_raw_setups if s["is_trend_aligned"]] # 4H Trend Aligned
    setups_config_c = [s for s in setups_config_b if s["is_killzone"] and s["wick_ratio"] >= 0.30] # Trend + Killzone + 30% Wick
    setups_config_d = setups_config_c # Trend + Killzone + Method 2 Sniper

    print(f"Setups Config A (Raw): {len(setups_config_a)}")
    print(f"Setups Config B (4H Trend Aligned): {len(setups_config_b)}")
    print(f"Setups Config C (Trend + Killzone + 30% Wick): {len(setups_config_c)}")

    res_a = run_simulation(setups_config_a, mode="METHOD_1")
    res_b = run_simulation(setups_config_b, mode="METHOD_1")
    res_c = run_simulation(setups_config_c, mode="METHOD_1")
    res_d = run_simulation(setups_config_d, mode="METHOD_2")

    report = {
        "config_a_raw": res_a,
        "config_b_trend_aligned": res_b,
        "config_c_trend_killzone_m1": res_c,
        "config_d_trend_killzone_m2": res_d
    }

    out_file = BASE_DIR / "institutional_pdh_pdl_audit_report.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2)

    print("\n" + "=" * 85)
    print("INSTITUTIONAL PDH / PDL ENHANCEMENT AUDIT: AUGUST 2026")
    print("=" * 85)
    print(f"{'Metric':<25} | {'Raw Baseline':<12} | {'4H Aligned':<12} | {'Trend+Killzone':<14} | {'Sniper Retest':<14}")
    print("-" * 85)
    print(f"{'Total Trades':<25} | {res_a['total_trades']:<12} | {res_b['total_trades']:<12} | {res_c['total_trades']:<14} | {res_d['total_trades']:<14}")
    print(f"{'Pure Win Rate (TP)':<25} | {res_a['pure_win_rate']:<11}% | {res_b['pure_win_rate']:<11}% | {res_c['pure_win_rate']:<13}% | {res_d['pure_win_rate']:<13}%")
    print(f"{'Effective WR (TP+BE)':<25} | {res_a['effective_win_rate']:<11}% | {res_b['effective_win_rate']:<11}% | {res_c['effective_win_rate']:<13}% | {res_d['effective_win_rate']:<13}%")
    print(f"{'Stop Loss Rate':<25} | {round(res_a['sl_losses']/res_a['total_trades']*100, 1) if res_a['total_trades'] else 0:<11}% | {round(res_b['sl_losses']/res_b['total_trades']*100, 1) if res_b['total_trades'] else 0:<11}% | {round(res_c['sl_losses']/res_c['total_trades']*100, 1) if res_c['total_trades'] else 0:<13}% | {round(res_d['sl_losses']/res_d['total_trades']*100, 1) if res_d['total_trades'] else 0:<13}%")
    print(f"{'Max Drawdown':<25} | {res_a['max_drawdown_pct']:<11}% | {res_b['max_drawdown_pct']:<11}% | {res_c['max_drawdown_pct']:<13}% | {res_d['max_drawdown_pct']:<13}%")
    print(f"{'Final Balance ($100)':<25} | ${res_a['final_balance']:<11} | ${res_b['final_balance']:<11} | ${res_c['final_balance']:<13} | ${res_d['final_balance']:<13}")
    print(f"{'Net Capital Growth':<25} | {res_a['net_growth_pct']:<11}% | {res_b['net_growth_pct']:<11}% | {res_c['net_growth_pct']:<13}% | {res_d['net_growth_pct']:<13}%")
    print("=" * 85)

if __name__ == "__main__":
    main()
