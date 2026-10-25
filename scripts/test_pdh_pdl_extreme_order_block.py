import os
import sys
import glob
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# EXPERIMENT: PREVIOUS DAY EXTREME (PDH / PDL) ORDER BLOCK STRATEGY
# Core Logic:
# 1. Mark Previous Day High (PDH = Top Resistance) & Low (PDL = Bottom Support).
# 2. When price reaches near PDH (Top) or PDL (Bottom):
#    - Identify if an Extreme Origin Order Block (OB) is formed:
#      * Bullish OB at Bottom (PDL): Last bearish candle before a strong displacement pump with FVG.
#      * Bearish OB at Top (PDH): Last bullish candle before a strong displacement drop with FVG.
# 3. Entry: When price retraces back to mitigate the Order Block (at 50% Mean Threshold of OB).
# 4. Stop Loss: Placed strictly beyond the extreme wick of the Order Block (+0.15% buffer).
# 5. Take Profit:
#    - Model A: 1:2 R:R
#    - Model B: 1:3 R:R
#    - Model C: Stepped Trailing SL Engine
# Dataset: Top-20 Binance USDT-M Champions (March to September 2026, 15m candles)
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

def find_extreme_order_blocks(candles, pdh, pdl, day_indices):
    """
    Scans for Order Blocks formed at the extreme Top (near PDH) or extreme Bottom (near PDL).
    """
    n = len(candles)
    obs = []

    # day_indices is list of (global_idx, candle)
    for i in range(len(day_indices) - 4):
        g_idx, c = day_indices[i]
        if g_idx + 3 >= n:
            break

        c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
        next_c = candles[g_idx + 1]
        next_c2 = candles[g_idx + 2]

        # ---------------------------------------------------------------------
        # 1. BULLISH ORDER BLOCK AT BOTTOM (NEAR PDL SUPPORT)
        # Price is at/near PDL (within 1.5% of PDL or swept PDL)
        # ---------------------------------------------------------------------
        dist_to_pdl = abs(c_l - pdl) / pdl
        if dist_to_pdl <= 0.015 or c_l <= pdl:
            # Bearish candle followed by strong displacement up
            is_bearish_candle = c_c < c_o
            gain = (next_c["high"] - c_l) / c_l
            gain_2bar = (next_c2["high"] - c_l) / c_l

            # Check FVG: next_c2 low > c high
            has_fvg = next_c2["low"] > c_h

            if (is_bearish_candle or (c_h - c_l) > 0) and (gain >= 0.015 or gain_2bar >= 0.020) and has_fvg:
                ob_high = c_h
                ob_low = c_l
                mt = (ob_high + ob_low) / 2.0
                obs.append({
                    "side": "LONG",
                    "ob_idx": g_idx,
                    "time": c["time"],
                    "ob_high": ob_high,
                    "ob_low": ob_low,
                    "mt": mt,
                    "sl": ob_low * 0.9985, # 0.15% buffer below OB low
                    "anchor": "PDL_BOTTOM"
                })

        # ---------------------------------------------------------------------
        # 2. BEARISH ORDER BLOCK AT TOP (NEAR PDH RESISTANCE)
        # Price is at/near PDH (within 1.5% of PDH or swept PDH)
        # ---------------------------------------------------------------------
        dist_to_pdh = abs(c_h - pdh) / pdh
        if dist_to_pdh <= 0.015 or c_h >= pdh:
            is_bullish_candle = c_c > c_o
            drop = (c_h - next_c["low"]) / c_h
            drop_2bar = (c_h - next_c2["low"]) / c_h

            # Check Bearish FVG: next_c2 high < c low
            has_bear_fvg = next_c2["high"] < c_l

            if (is_bullish_candle or (c_h - c_l) > 0) and (drop >= 0.015 or drop_2bar >= 0.020) and has_bear_fvg:
                ob_high = c_h
                ob_low = c_l
                mt = (ob_high + ob_low) / 2.0
                obs.append({
                    "side": "SHORT",
                    "ob_idx": g_idx,
                    "time": c["time"],
                    "ob_high": ob_high,
                    "ob_low": ob_low,
                    "mt": mt,
                    "sl": ob_high * 1.0015, # 0.15% buffer above OB high
                    "anchor": "PDH_TOP"
                })

    return obs

def simulate_ob_trade(setup, candles, max_wait_bars=32, max_hold_bars=96, exit_mode="STEPPED_TRAILING"):
    """
    Waits for price to mitigate the OB (tap 50% MT), enters, and executes.
    """
    n = len(candles)
    ob_idx = setup["ob_idx"]
    side = setup["side"]
    entry_target = setup["mt"]
    initial_sl = setup["sl"]

    risk = abs(entry_target - initial_sl)
    if risk <= 0:
        return None

    # Wait for price to pull back to the Order Block Mean Threshold
    filled = False
    fill_idx = -1

    for w_i in range(ob_idx + 2, min(ob_idx + 2 + max_wait_bars, n)):
        b = candles[w_i]
        if side == "LONG":
            # If price violated SL before even tapping, OB invalidated
            if b["low"] <= initial_sl:
                return {"outcome": "INVALIDATED_BEFORE_FILL", "pnl_r": 0.0}
            if b["low"] <= entry_target:
                filled = True
                fill_idx = w_i
                break
        else: # SHORT
            if b["high"] >= initial_sl:
                return {"outcome": "INVALIDATED_BEFORE_FILL", "pnl_r": 0.0}
            if b["high"] >= entry_target:
                filled = True
                fill_idx = w_i
                break

    if not filled:
        return {"outcome": "UNMITIGATED", "pnl_r": 0.0}

    # Trade Execution from fill_idx
    entry_price = entry_target
    active_sl = initial_sl
    current_tier = 0
    outcome = "TIMEOUT"
    realized_r = 0.0
    friction_r = 0.06

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold_bars, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]

        if side == "LONG":
            # Pessimistic SL check first
            if b_l <= active_sl:
                if current_tier == 0:
                    outcome = "SL_HIT"
                    realized_r = -1.0 - friction_r
                elif current_tier == 1:
                    outcome = "FEE_SHIELD_SAVE"
                    realized_r = 0.2 - friction_r
                else:
                    outcome = f"TRAILING_SL_T{current_tier}"
                    realized_r = ((current_tier - 1) * 0.5) - friction_r
                break

            max_fav_r = (b_h - entry_price) / risk
            if exit_mode == "FIXED_1_TO_2":
                if max_fav_r >= 2.0:
                    outcome = "TP_HIT"
                    realized_r = 2.0 - friction_r
                    break
            elif exit_mode == "FIXED_1_TO_3":
                if max_fav_r >= 3.0:
                    outcome = "TP_HIT"
                    realized_r = 3.0 - friction_r
                    break
            elif exit_mode == "STEPPED_TRAILING":
                if max_fav_r >= 1.0:
                    tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry_price + (locked_r * risk)

        else: # SHORT
            if b_h >= active_sl:
                if current_tier == 0:
                    outcome = "SL_HIT"
                    realized_r = -1.0 - friction_r
                elif current_tier == 1:
                    outcome = "FEE_SHIELD_SAVE"
                    realized_r = 0.2 - friction_r
                else:
                    outcome = f"TRAILING_SL_T{current_tier}"
                    realized_r = ((current_tier - 1) * 0.5) - friction_r
                break

            max_fav_r = (entry_price - b_l) / risk
            if exit_mode == "FIXED_1_TO_2":
                if max_fav_r >= 2.0:
                    outcome = "TP_HIT"
                    realized_r = 2.0 - friction_r
                    break
            elif exit_mode == "FIXED_1_TO_3":
                if max_fav_r >= 3.0:
                    outcome = "TP_HIT"
                    realized_r = 3.0 - friction_r
                    break
            elif exit_mode == "STEPPED_TRAILING":
                if max_fav_r >= 1.0:
                    tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry_price - (locked_r * risk)

    if outcome == "TIMEOUT":
        last_c = candles[min(fill_idx + max_hold_bars, n - 1)]["close"]
        raw_r = (last_c - entry_price) / risk if side == "LONG" else (entry_price - last_c) / risk
        realized_r = raw_r - friction_r
        outcome = "TIMEOUT_GREEN" if realized_r >= 0 else "TIMEOUT_RED"

    trade_dt = datetime.datetime.fromtimestamp(candles[fill_idx]["time"] / 1000.0, tz=datetime.timezone.utc)
    return {
        "side": side,
        "entry_price": entry_price,
        "sl": initial_sl,
        "outcome": outcome,
        "pnl_r": round(realized_r, 2),
        "trailing_tier": current_tier,
        "time": candles[fill_idx]["time"],
        "date_str": trade_dt.strftime("%Y-%m-%d %H:%M")
    }

def run_experiment():
    coins_data = load_data()
    print("=" * 105)
    print("🔬 EXPERIMENT: PREVIOUS DAY EXTREME (PDH/PDL) ORDER BLOCK STRATEGY")
    print("=" * 105)
    print("Hypothesis: When an Extreme Origin Order Block forms at PDH (Top) or PDL (Bottom),")
    print("            trading the 50% Mean Threshold Retest should offer high RR and institutional protection.\n")

    all_setups = []

    for sym, candles in coins_data.items():
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

            obs = find_extreme_order_blocks(candles, pdh, pdl, c_list)
            for ob in obs:
                ob["symbol"] = sym
                ob["candles"] = candles
                all_setups.append(ob)

    print(f"Total Extreme Order Blocks Identified at Top/Bottom: {len(all_setups)}\n")

    # Evaluate across 3 Exit Models
    def evaluate_exit_mode(mode_name):
        executed = []
        busy_until = {}
        for s in sorted(all_setups, key=lambda x: x["time"]):
            sym = s["symbol"]
            t = s["time"]
            if busy_until.get(sym, 0) > t:
                continue
            res = simulate_ob_trade(s, s["candles"], exit_mode=mode_name)
            if res and res["outcome"] not in ["UNMITIGATED", "INVALIDATED_BEFORE_FILL"]:
                res["symbol"] = sym
                executed.append(res)
                busy_until[sym] = res["time"] + (4 * 3600 * 1000)

        tot = len(executed)
        wins = sum(1 for x in executed if x["pnl_r"] >= 0.40)
        saves = sum(1 for x in executed if 0.0 <= x["pnl_r"] < 0.40)
        losses = sum(1 for x in executed if x["pnl_r"] < 0.0)
        pure_wr = (wins / (wins + losses) * 100.0) if (wins + losses) > 0 else 0.0
        green_rate = ((wins + saves) / tot * 100.0) if tot > 0 else 0.0
        net_r = sum(x["pnl_r"] for x in executed)

        print(f"{mode_name:<28} | Filled: {tot:<5} | Wins: {wins:<4} | Saves: {saves:<4} | Loss: {losses:<4} | Pure WR: {pure_wr:5.1f}% | Green%: {green_rate:5.1f}% | Net (R): {net_r:+7.1f} R")
        return executed, {"total": tot, "wins": wins, "saves": saves, "losses": losses, "pure_wr": pure_wr, "green_rate": green_rate, "net_r": net_r}

    print("====================================================================================================")
    print(f"{'EXIT STRATEGY':<28} | {'FILLED':<5} | {'WINS':<4} | {'SAVES':<4} | {'LOSS':<4} | {'WIN%':<9} | {'GREEN%':<8} | {'NET PROFIT'}")
    print("-" * 105)
    ex_1to2, m_1to2 = evaluate_exit_mode("FIXED_1_TO_2")
    ex_1to3, m_1to3 = evaluate_exit_mode("FIXED_1_TO_3")
    ex_trail, m_trail = evaluate_exit_mode("STEPPED_TRAILING")
    print("=" * 105 + "\n")

    # Breakdown of Top (PDH) vs Bottom (PDL) for Stepped Trailing
    longs_bottom = [x for x in ex_trail if x["side"] == "LONG"]
    shorts_top = [x for x in ex_trail if x["side"] == "SHORT"]

    print("====================================================================================================")
    print("🎯 BREAKDOWN: TOP ORDER BLOCKS (PDH SHORT) vs BOTTOM ORDER BLOCKS (PDL LONG)")
    print("====================================================================================================")
    for lbl, subset in [("BOTTOM OBs (PDL Support Longs)", longs_bottom), ("TOP OBs (PDH Resistance Shorts)", shorts_top)]:
        tot = len(subset)
        w = sum(1 for x in subset if x["pnl_r"] >= 0.40)
        s = sum(1 for x in subset if 0.0 <= x["pnl_r"] < 0.40)
        l = sum(1 for x in subset if x["pnl_r"] < 0.0)
        p_wr = (w / (w + l) * 100.0) if (w + l) > 0 else 0.0
        g_rt = ((w + s) / tot * 100.0) if tot > 0 else 0.0
        nR = sum(x["pnl_r"] for x in subset)
        print(f"{lbl:<35} | Filled: {tot:<4} | Wins: {w:<4} | Saves: {s:<4} | Loss: {l:<4} | Pure WR: {p_wr:5.1f}% | Green%: {g_rt:5.1f}% | Net: {nR:+6.1f} R")
    print("=" * 105 + "\n")

    # Save to json
    with open("pdh_pdl_order_block_experiment_results.json", "w", encoding="utf-8") as f:
        json.dump({"1to2": m_1to2, "1to3": m_1to3, "stepped_trailing": m_trail}, f, indent=2)

if __name__ == "__main__":
    run_experiment()
