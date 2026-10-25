import os
import sys
import glob
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# INTEGRATED MASTER LIQUIDITY SWEEP STRATEGY (ALL 4 FIXES INTEGRATED)
# 1. 0.15% Stop Loss Buffer beyond sweep extreme (Anti-Secondary Hunt)
# 2. V-Shape Rejection Wick >= 25% + 7% Volatility Anchor (Day or Wave Move >= 7%)
# 3. Stepped Trailing SL (+1.0R -> +0.2R lock, +1.5R -> +1.0R lock, etc.)
# 4. London & New York Killzones (07:00-11:00 UTC & 13:00-17:00 UTC)
#
# Compared across:
#   - Market Regimes: UPTREND, DOWNTREND, SIDEWAYS
#   - Sides: LONG (PDL Support) vs SHORT (PDH Resistance)
#   - Methods: Method 1 (Direct 15m Close) vs Method 2 (50% FVG Retest Limit)
#   - Exits: Fixed 1:2 R:R (Old Baseline) vs Stepped Trailing SL (New Integrated)
# Dataset: Top-20 Champions across 6 Months (March to September 2026, 15m data)
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
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0, tz=datetime.timezone.utc)
    hour = dt.hour
    return (7 <= hour <= 11) or (13 <= hour <= 17)

def classify_market_regime(price, e50, e200):
    diff_pct = abs(e50 - e200) / e200 * 100.0
    if diff_pct < 0.60:
        return "SIDEWAYS"
    elif e50 > e200 and price >= e50 * 0.998:
        return "UPTREND"
    elif e50 < e200 and price <= e50 * 1.002:
        return "DOWNTREND"
    else:
        return "SIDEWAYS"

def simulate_trade(setup, mode="METHOD_2", exit_strategy="STEPPED_TRAILING", max_hold=120):
    candles = setup["candles"]
    sweep_idx = setup["sweep_idx"]
    side = setup["side"]
    c = candles[sweep_idx]
    n = len(candles)

    c_h = c["high"]
    c_l = c["low"]
    c_c = c["close"]

    # FIX #3: 0.15% Buffer beyond extreme wick (Anti-Hunt Buffer)
    buffer_pct = 0.0015
    if side == "LONG":
        initial_sl = c_l * (1.0 - buffer_pct)
    else:
        initial_sl = c_h * (1.0 + buffer_pct)

    if mode == "METHOD_1":
        entry_price = c_c
        entry_idx = sweep_idx + 1
    elif mode == "METHOD_2":
        # 50% FVG Discount Limit Entry
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

    # Track trade execution
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
                # Fixed 1:2 without trailing
                if b_l <= initial_sl:
                    outcome = "SL_HIT"
                    realized_r = -1.0
                    break
                if max_favorable_r >= 2.0:
                    outcome = "TP_HIT"
                    realized_r = 2.0
                    break

            elif exit_strategy == "STEPPED_TRAILING":
                # FIX #1: Stepped Trailing Ladder
                # Tier 1 (+1.0R): Shift SL to +0.2R (Fee Shield / Micro-Green)
                # Tier 2 (+1.5R): Shift SL to +1.0R (1 Full R locked!)
                # Tier 3 (+2.0R): Shift SL to +1.5R
                # Tier 4 (+2.5R): Shift SL to +2.0R
                # Tier 5 (+3.0R): Shift SL to +2.5R
                if max_favorable_r >= 1.0:
                    tier_candidate = int((max_favorable_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry_price + (locked_r * risk)

                if b_l <= active_sl:
                    if current_tier == 0:
                        outcome = "SL_HIT"
                        realized_r = -1.0
                    elif current_tier == 1:
                        outcome = "FEE_SHIELD_SAVE"
                        realized_r = 0.2
                    else:
                        outcome = f"TRAILING_SL_T{current_tier}"
                        realized_r = (current_tier - 1) * 0.5
                    break

        else: # SHORT
            max_favorable_r = (entry_price - b_l) / risk

            if exit_strategy == "FIXED_1_TO_2":
                if b_h >= initial_sl:
                    outcome = "SL_HIT"
                    realized_r = -1.0
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
                        outcome = "FEE_SHIELD_SAVE"
                        realized_r = 0.2
                    else:
                        outcome = f"TRAILING_SL_T{current_tier}"
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
        "regime": setup["regime"],
        "entry_price": entry_price,
        "initial_sl": initial_sl,
        "outcome": outcome,
        "pnl_r": realized_r,
        "trailing_tier": current_tier,
        "time": candles[entry_idx]["time"]
    }

def run_integrated_audit():
    coins_data = load_data()
    print("=" * 100)
    print("🏛️ INTEGRATED MASTER LIQUIDITY SWEEP AUDIT (ALL 4 FORENSIC FIXES INTEGRATED)")
    print("=" * 100)
    print(f"Dataset Scope: Top-20 Champions across 6 Months (March to September 2026, 15m dataset)")
    print(f"Fixes Active: 0.15% SL Buffer | Rejection Wick >= 25% | 7% Volatility Anchor | London/NY Killzones\n")

    setups = []

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

            pdh = max(c[1]["high"] for c in p_list) # Resistance
            pdl = min(c[1]["low"] for c in p_list)  # Support
            pd_range_pct = (pdh - pdl) / pdl if pdl > 0 else 0

            for idx_in_day, (g_idx, c) in enumerate(c_list):
                c_o = c["open"]
                c_h = c["high"]
                c_l = c["low"]
                c_c = c["close"]
                c_rng = c_h - c_l
                if c_rng <= 0:
                    continue

                # FIX #4: Killzone Session Timing
                if not is_killzone(c["time"]):
                    continue

                # FIX #2: 7% Volatility Anchor Check
                lookback_bars = c_list[max(0, idx_in_day - 16):idx_in_day + 1]
                wave_high = max(x[1]["high"] for x in lookback_bars)
                wave_low = min(x[1]["low"] for x in lookback_bars)
                wave_move_pct = (wave_high - wave_low) / wave_low if wave_low > 0 else 0

                is_vol_anchor = (pd_range_pct >= 0.070) or (wave_move_pct >= 0.070)
                if not is_vol_anchor:
                    continue

                regime = classify_market_regime(c_c, ema50[g_idx], ema200[g_idx])
                is_bullish = ema50[g_idx] > ema200[g_idx]
                is_bearish = ema50[g_idx] < ema200[g_idx]

                # 1. LONG PDL Support Sweep
                if c_l < pdl and c_c > pdl:
                    sweep_depth = (pdl - c_l) / pdl
                    if 0.0010 <= sweep_depth <= 0.040:
                        lower_wick = min(c_o, c_c) - c_l
                        wick_ratio = lower_wick / c_rng
                        # FIX #2: Rejection Wick >= 25% (V-Shape Trap Confirmation)
                        if wick_ratio >= 0.25:
                            setups.append({
                                "symbol": sym,
                                "side": "LONG",
                                "candles": candles,
                                "sweep_idx": g_idx,
                                "regime": regime,
                                "is_trend_aligned": is_bullish
                            })

                # 2. SHORT PDH Resistance Sweep
                if c_h > pdh and c_c < pdh:
                    sweep_depth = (c_h - pdh) / pdh
                    if 0.0010 <= sweep_depth <= 0.040:
                        upper_wick = c_h - max(c_o, c_c)
                        wick_ratio = upper_wick / c_rng
                        if wick_ratio >= 0.25:
                            setups.append({
                                "symbol": sym,
                                "side": "SHORT",
                                "candles": candles,
                                "sweep_idx": g_idx,
                                "regime": regime,
                                "is_trend_aligned": is_bearish
                            })

    print(f"Total Qualified High-Conviction Institutional Setups: {len(setups)}\n")

    # Simulation Runner
    def run_simulation_matrix(mode="METHOD_2", exit_strat="STEPPED_TRAILING"):
        executed = []
        busy_until = {}
        for s in sorted(setups, key=lambda x: x["candles"][x["sweep_idx"]]["time"]):
            sym = s["symbol"]
            t = s["candles"][s["sweep_idx"]]["time"]
            if busy_until.get(sym, 0) > t:
                continue
            res = simulate_trade(s, mode=mode, exit_strategy=exit_strat)
            if res and res["outcome"] != "MISSED":
                executed.append(res)
                busy_until[sym] = res["time"] + (4 * 3600 * 1000)
        return executed

    # 1. Run Baseline Old Model (Fixed 1:2 without trailing)
    old_trades = run_simulation_matrix(mode="METHOD_1", exit_strat="FIXED_1_TO_2")
    # 2. Run New Integrated Model with Method 1 (Direct Close + Stepped Trailing)
    new_m1_trades = run_simulation_matrix(mode="METHOD_1", exit_strat="STEPPED_TRAILING")
    # 3. Run New Integrated Master Model with Method 2 (50% FVG Limit + Stepped Trailing)
    new_m2_trades = run_simulation_matrix(mode="METHOD_2", exit_strat="STEPPED_TRAILING")

    def format_row(name, t_list):
        total = len(t_list)
        if total == 0:
            return
        wins = sum(1 for x in t_list if x["pnl_r"] >= 0.5)
        saves = sum(1 for x in t_list if 0.0 <= x["pnl_r"] < 0.5)
        losses = sum(1 for x in t_list if x["pnl_r"] < 0.0)
        win_rate = (wins / (wins + losses) * 100.0) if (wins + losses) > 0 else 0.0
        green_rate = ((wins + saves) / total * 100.0) if total > 0 else 0.0
        net_r = sum(x["pnl_r"] for x in t_list)

        print(f"{name:<45} | {total:<6} | {wins:<4} | {saves:<5} | {losses:<5} | {green_rate:5.1f}% | {win_rate:5.1f}% | {net_r:+7.1f} R")
        return {"total": total, "wins": wins, "saves": saves, "losses": losses, "green_rate": green_rate, "win_rate": win_rate, "net_r": net_r}

    print("=" * 100)
    print("📊 1. BEFORE vs AFTER: TRANSFORMATION COMPARISON MATRIX")
    print("=" * 100)
    print(f"{'CONFIGURATION':<45} | {'TRADES':<6} | {'WINS':<4} | {'SAVES':<5} | {'LOSS':<5} | {'GREEN%':<7} | {'WIN%':<7} | {'NET EXP (R)'}")
    print("-" * 100)
    format_row("OLD BASELINE (Raw Sweeps, Fixed 1:2 R:R)", old_trades)
    format_row("INTEGRATED METHOD 1 (Direct Close + Stepped SL)", new_m1_trades)
    format_row("INTEGRATED MASTER METHOD 2 (50% FVG + Stepped SL) 👑", new_m2_trades)
    print("=" * 100 + "\n")

    # Granular Breakdown of the Integrated Master Model (Method 2 + Stepped Trailing)
    print("=" * 100)
    print("🎯 2. MASTER INTEGRATED MODEL: REGIME & SIDE BREAKDOWN (METHOD 2 + STEPPED TRAILING)")
    print("=" * 100)
    print(f"{'MARKET REGIME & SIDE':<45} | {'TRADES':<6} | {'WINS':<4} | {'SAVES':<5} | {'LOSS':<5} | {'GREEN%':<7} | {'WIN%':<7} | {'NET EXP (R)'}")
    print("-" * 100)
    format_row("SIDEWAYS REGIME (Ranging Market) 🏆", [t for t in new_m2_trades if t["regime"] == "SIDEWAYS"])
    format_row("DOWNTREND REGIME (Bearish Market) 🏆", [t for t in new_m2_trades if t["regime"] == "DOWNTREND"])
    format_row("UPTREND REGIME (Bullish Market) 🏆", [t for t in new_m2_trades if t["regime"] == "UPTREND"])
    print("-" * 100)
    format_row("ALL LONGS (Day Support Sweeps)", [t for t in new_m2_trades if t["side"] == "LONG"])
    format_row("ALL SHORTS (Day Resistance Sweeps)", [t for t in new_m2_trades if t["side"] == "SHORT"])
    print("-" * 100)
    format_row("OVERALL INTEGRATED MASTER PORTFOLIO 👑", new_m2_trades)
    print("=" * 100 + "\n")

    # Save to JSON
    with open("integrated_master_liquidity_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "old_baseline": [x for x in old_trades[:50]],
            "master_m2": [x for x in new_m2_trades[:50]]
        }, f, indent=2)

if __name__ == "__main__":
    run_integrated_audit()
