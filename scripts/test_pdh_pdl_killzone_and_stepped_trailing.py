import os
import sys
import glob
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# ADVANCED PDH / PDL LIQUIDITY SWEEP AUDIT
# Enhancements:
#   1. Session Timing Filter: London (07:00-11:00 UTC) & New York (13:00-17:00 UTC) Killzones
#   2. Stepped Trailing SL Engine vs Fixed 1:2 R:R
#   3. 7% Volatility Anchor (Previous Day Range >= 7% & Wave Move >= 7%)
# Across:
#   Option A (Trend-Aligned) vs Option B (Both Sides)
#   Method 1 (Direct 15m Close) vs Method 2 (50% Mitigation Retest)
# Dataset: Top-20 Champions (March to September 2026, 15m candles)
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "market_data_cache_15m"

def load_data():
    files = glob.glob(str(DATA_DIR / "*_15m.json"))
    coins_data = {}
    for f in sorted(files):
        sym = Path(f).name.replace("_15m.json", "")
        with open(f, "r", encoding="utf-8") as fp:
            raw = json.load(fp)
            for c in raw:
                c["open"] = float(c["open"])
                c["high"] = float(c["high"])
                c["low"] = float(c["low"])
                c["close"] = float(c["close"])
            if len(raw) >= 1000:
                coins_data[sym] = raw
    return coins_data

def group_by_day(candles):
    days = {}
    for idx, c in enumerate(candles):
        dt = datetime.datetime.fromtimestamp(c["time"] / 1000.0, tz=datetime.timezone.utc)
        k = dt.strftime("%Y-%m-%d")
        if k not in days:
            days[k] = []
        days[k].append((idx, c))
    return days

def compute_ema(prices, period):
    if len(prices) < period:
        return [prices[-1]] * len(prices)
    ema = []
    multiplier = 2 / (period + 1)
    sma = sum(prices[:period]) / period
    for _ in range(period - 1):
        ema.append(sma)
    ema.append(sma)
    for p in prices[period:]:
        cur_ema = (p - ema[-1]) * multiplier + ema[-1]
        ema.append(cur_ema)
    return ema

def is_killzone(timestamp_ms):
    """
    London Open: 07:00 - 11:00 UTC (12:30 - 16:30 IST)
    New York Open: 13:00 - 17:00 UTC (18:30 - 22:30 IST)
    """
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0, tz=datetime.timezone.utc)
    hour = dt.hour
    return (7 <= hour <= 11) or (13 <= hour <= 17)

def simulate_trade_stepped_trailing(setup, mode="METHOD_1", exit_strategy="STEPPED_TRAILING", max_hold=120):
    """
    Simulates a trade with either:
    1. 'FIXED_1_TO_2': Fixed 1:2 R:R target with 1:1 Break-Even armor.
    2. 'STEPPED_TRAILING': Stepped Trailing SL Ladder:
       - Touch +1.0R -> Shift SL to +0.2R (Fee-Protection / Micro-Green)
       - Touch +1.5R -> Shift SL to +1.0R
       - Touch +2.0R -> Shift SL to +1.5R
       - Touch +2.5R -> Shift SL to +2.0R
       - Touch +3.0R -> Shift SL to +2.5R
       - Continues dynamically as long as trend runs!
    """
    candles = setup["candles"]
    sweep_idx = setup["sweep_idx"]
    side = setup["side"]
    c = candles[sweep_idx]
    n = len(candles)

    c_h = c["high"]
    c_l = c["low"]
    c_c = c["close"]

    buffer_pct = 0.0015
    if side == "LONG":
        initial_sl = c_l * (1.0 - buffer_pct)
    else:
        initial_sl = c_h * (1.0 + buffer_pct)

    if mode == "METHOD_1":
        entry_price = c_c
        entry_idx = sweep_idx + 1
    elif mode == "METHOD_2":
        if side == "LONG":
            entry_price = c_l + (c_c - c_l) * 0.50
        else:
            entry_price = c_h - (c_h - c_c) * 0.50

        filled = False
        entry_idx = sweep_idx + 1
        for f_i in range(sweep_idx + 1, min(sweep_idx + 9, n)):
            bar = candles[f_i]
            if side == "LONG" and bar["low"] <= entry_price:
                filled = True
                entry_idx = f_i
                break
            elif side == "SHORT" and bar["high"] >= entry_price:
                filled = True
                entry_idx = f_i
                break
        if not filled:
            return {"outcome": "MISSED", "pnl_r": 0.0}

    risk = abs(entry_price - initial_sl)
    if risk <= 0:
        return None

    # Track Stepped Trailing Ladder
    current_tier = 0
    active_sl = initial_sl
    outcome = "TIMEOUT"
    realized_r = 0.0

    for idx in range(entry_idx, min(entry_idx + max_hold, n)):
        b = candles[idx]
        b_h = b["high"]
        b_l = b["low"]
        b_c = b["close"]

        if side == "LONG":
            max_favorable_r = (b_h - entry_price) / risk

            if exit_strategy == "FIXED_1_TO_2":
                # BE at 1:1
                if current_tier == 0 and max_favorable_r >= 1.0:
                    current_tier = 1
                    active_sl = entry_price
                # Check Hard SL / BE
                if b_l <= active_sl:
                    outcome = "BE_SAVE" if current_tier > 0 else "SL_HIT"
                    realized_r = 0.0 if current_tier > 0 else -1.0
                    break
                # Check Fixed 1:2 TP
                if max_favorable_r >= 2.0:
                    outcome = "TP_HIT"
                    realized_r = 2.0
                    break

            elif exit_strategy == "STEPPED_TRAILING":
                # Stepped Trailing Ladder
                # Tier 1: +1.0R -> Lock +0.2R
                # Tier 2: +1.5R -> Lock +1.0R
                # Tier 3: +2.0R -> Lock +1.5R
                # Tier 4: +2.5R -> Lock +2.0R
                # Tier 5: +3.0R -> Lock +2.5R
                # Tier K: +(0.5*K + 0.5)R -> Lock +(0.5*(K-1) + 0.5)R
                if max_favorable_r >= 1.0:
                    tier_candidate = int((max_favorable_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry_price + (locked_r * risk)

                # Check SL / Trailing SL touch
                if b_l <= active_sl:
                    if current_tier == 0:
                        outcome = "SL_HIT"
                        realized_r = -1.0
                    elif current_tier == 1:
                        outcome = "FEE_PROTECT_HIT"
                        realized_r = 0.2
                    else:
                        outcome = f"TRAILING_SL_HIT_T{current_tier}"
                        realized_r = (current_tier - 1) * 0.5
                    break

        else: # SHORT
            max_favorable_r = (entry_price - b_l) / risk

            if exit_strategy == "FIXED_1_TO_2":
                if current_tier == 0 and max_favorable_r >= 1.0:
                    current_tier = 1
                    active_sl = entry_price
                if b_h >= active_sl:
                    outcome = "BE_SAVE" if current_tier > 0 else "SL_HIT"
                    realized_r = 0.0 if current_tier > 0 else -1.0
                    break
                if max_favorable_r >= 2.0:
                    outcome = "TP_HIT"
                    realized_r = 2.0
                    break

            elif exit_strategy == "STEPPED_TRAILING":
                if max_favorable_r >= 1.0:
                    tier_candidate = int((max_favorable_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry_price - (locked_r * risk)

                if b_h >= active_sl:
                    if current_tier == 0:
                        outcome = "SL_HIT"
                        realized_r = -1.0
                    elif current_tier == 1:
                        outcome = "FEE_PROTECT_HIT"
                        realized_r = 0.2
                    else:
                        outcome = f"TRAILING_SL_HIT_T{current_tier}"
                        realized_r = (current_tier - 1) * 0.5
                    break

    if outcome == "TIMEOUT":
        last_c = candles[min(entry_idx + max_hold - 1, n - 1)]["close"]
        if side == "LONG":
            realized_r = (last_c - entry_price) / risk
        else:
            realized_r = (entry_price - last_c) / risk
        outcome = "TIMEOUT_GREEN" if realized_r >= 0 else "TIMEOUT_RED"

    return {
        "symbol": setup["symbol"],
        "side": side,
        "entry_price": entry_price,
        "initial_sl": initial_sl,
        "outcome": outcome,
        "pnl_r": realized_r,
        "trailing_tier": current_tier,
        "time": candles[entry_idx]["time"]
    }

def run_suite():
    coins_data = load_data()
    print("==========================================================================================")
    print("🏛️ ADVANCED PDH/PDL LIQUIDITY AUDIT: KILLZONE TIMING + STEPPED TRAILING SL")
    print("==========================================================================================")
    print(f"Loaded {len(coins_data)} coins across 6 Months (March to September 2026, 15m dataset)\n")

    setups_day7 = [] # Previous Day >= 7%
    setups_wave7 = [] # Wave Move >= 7%

    for sym, candles in coins_data.items():
        n = len(candles)
        closes = [c["close"] for c in candles]
        ema50 = compute_ema(closes, 50)
        ema200 = compute_ema(closes, 200)

        daily = group_by_day(candles)
        sorted_days = sorted(daily.keys())

        for d_i in range(1, len(sorted_days)):
            p_day = sorted_days[d_i - 1]
            c_day = sorted_days[d_i]

            p_list = daily[p_day]
            c_list = daily[c_day]

            if len(p_list) < 80 or len(c_list) < 80:
                continue

            pdh = max(c[1]["high"] for c in p_list)
            pdl = min(c[1]["low"] for c in p_list)
            pd_range_pct = (pdh - pdl) / pdl if pdl > 0 else 0

            for idx_in_day, (g_idx, c) in enumerate(c_list):
                c_o = c["open"]
                c_h = c["high"]
                c_l = c["low"]
                c_c = c["close"]
                c_rng = c_h - c_l
                if c_rng <= 0:
                    continue

                lookback_bars = c_list[max(0, idx_in_day - 16):idx_in_day + 1]
                wave_high = max(x[1]["high"] for x in lookback_bars)
                wave_low = min(x[1]["low"] for x in lookback_bars)
                wave_move_pct = (wave_high - wave_low) / wave_low if wave_low > 0 else 0

                is_bullish = ema50[g_idx] > ema200[g_idx]
                is_bearish = ema50[g_idx] < ema200[g_idx]
                in_kz = is_killzone(c["time"])

                # 1. Bullish PDL Sweep (LONG)
                if c_l < pdl and c_c > pdl:
                    sweep_depth = (pdl - c_l) / pdl
                    if 0.0010 <= sweep_depth <= 0.040:
                        lower_wick = min(c_o, c_c) - c_l
                        if (lower_wick / c_rng) >= 0.25:
                            s_data = {
                                "symbol": sym,
                                "side": "LONG",
                                "candles": candles,
                                "sweep_idx": g_idx,
                                "is_trend_aligned": is_bullish,
                                "is_killzone": in_kz,
                                "pd_range_pct": pd_range_pct,
                                "wave_move_pct": wave_move_pct
                            }
                            if pd_range_pct >= 0.070:
                                setups_day7.append(s_data)
                            if wave_move_pct >= 0.070:
                                setups_wave7.append(s_data)

                # 2. Bearish PDH Sweep (SHORT)
                if c_h > pdh and c_c < pdh:
                    sweep_depth = (c_h - pdh) / pdh
                    if 0.0010 <= sweep_depth <= 0.040:
                        upper_wick = c_h - max(c_o, c_c)
                        if (upper_wick / c_rng) >= 0.25:
                            s_data = {
                                "symbol": sym,
                                "side": "SHORT",
                                "candles": candles,
                                "sweep_idx": g_idx,
                                "is_trend_aligned": is_bearish,
                                "is_killzone": in_kz,
                                "pd_range_pct": pd_range_pct,
                                "wave_move_pct": wave_move_pct
                            }
                            if pd_range_pct >= 0.070:
                                setups_day7.append(s_data)
                            if wave_move_pct >= 0.070:
                                setups_wave7.append(s_data)

    print(f"Total Setups with Previous Day Range >= 7%: {len(setups_day7)} (Killzone: {sum(1 for s in setups_day7 if s['is_killzone'])})")
    print(f"Total Setups with Wave Move >= 7%:          {len(setups_wave7)} (Killzone: {sum(1 for s in setups_wave7 if s['is_killzone'])})\n")

    def run_matrix(setups_subset, label):
        print("==========================================================================================")
        print(f"🎯 {label}")
        print("==========================================================================================")
        print(f"{'CONFIGURATION & EXIT':<45} | {'TRADES':<6} | {'WINS':<4} | {'SAVES':<5} | {'LOSS':<4} | {'GREEN%':<7} | {'NET EXP (R)'}")
        print("-" * 88)

        combos = [
            ("Option A (Trend) - Method 1 - Fixed 1:2", [s for s in setups_subset if s["is_trend_aligned"]], "METHOD_1", "FIXED_1_TO_2"),
            ("Option A (Trend) - Method 1 - Stepped Trailing", [s for s in setups_subset if s["is_trend_aligned"]], "METHOD_1", "STEPPED_TRAILING"),
            ("Option A (Trend) - Method 2 - Fixed 1:2", [s for s in setups_subset if s["is_trend_aligned"]], "METHOD_2", "FIXED_1_TO_2"),
            ("Option A (Trend) - Method 2 - Stepped Trailing", [s for s in setups_subset if s["is_trend_aligned"]], "METHOD_2", "STEPPED_TRAILING"),
            ("Option B (Both)  - Method 1 - Fixed 1:2", setups_subset, "METHOD_1", "FIXED_1_TO_2"),
            ("Option B (Both)  - Method 1 - Stepped Trailing", setups_subset, "METHOD_1", "STEPPED_TRAILING"),
            ("Option B (Both)  - Method 2 - Fixed 1:2", setups_subset, "METHOD_2", "FIXED_1_TO_2"),
            ("Option B (Both)  - Method 2 - Stepped Trailing", setups_subset, "METHOD_2", "STEPPED_TRAILING"),
        ]

        results = {}
        for c_name, s_pool, mode, exit_strat in combos:
            executed = []
            busy_until = {}
            for s in sorted(s_pool, key=lambda x: x["candles"][x["sweep_idx"]]["time"]):
                sym = s["symbol"]
                t = s["candles"][s["sweep_idx"]]["time"]
                if busy_until.get(sym, 0) > t:
                    continue
                res = simulate_trade_stepped_trailing(s, mode=mode, exit_strategy=exit_strat)
                if res and res["outcome"] != "MISSED":
                    executed.append(res)
                    busy_until[sym] = res["time"] + (4 * 3600 * 1000)

            total = len(executed)
            wins = sum(1 for x in executed if x["pnl_r"] >= 0.5)
            saves = sum(1 for x in executed if 0.0 <= x["pnl_r"] < 0.5)
            loss = sum(1 for x in executed if x["pnl_r"] < 0.0)
            green_pct = ((wins + saves) / total * 100.0) if total > 0 else 0.0
            net_r = sum(x["pnl_r"] for x in executed)

            print(f"{c_name:<45} | {total:<6} | {wins:<4} | {saves:<5} | {loss:<4} | {green_pct:5.1f}% | {net_r:+7.1f} R")
            results[c_name] = {"total": total, "wins": wins, "saves": saves, "loss": loss, "green_pct": green_pct, "net_r": net_r}

        print("-" * 88 + "\n")
        return results

    # 1. Day Range >= 7% (All Hours)
    res_day7_all = run_matrix(setups_day7, "PREVIOUS DAY >= 7% (ALL HOURS)")

    # 2. Day Range >= 7% (LONDON & NY KILLZONES ONLY)
    res_day7_kz = run_matrix([s for s in setups_day7 if s["is_killzone"]], "PREVIOUS DAY >= 7% (LONDON & NY KILLZONES ONLY)")

    # 3. Wave Move >= 7% (LONDON & NY KILLZONES ONLY)
    res_wave7_kz = run_matrix([s for s in setups_wave7 if s["is_killzone"]], "PRE-SWEEP WAVE >= 7% (LONDON & NY KILLZONES ONLY)")

    # Save to json
    with open("pdh_pdl_advanced_killzone_trailing_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "day7_all": res_day7_all,
            "day7_killzone": res_day7_kz,
            "wave7_killzone": res_wave7_kz
        }, f, indent=2)

if __name__ == "__main__":
    run_suite()
