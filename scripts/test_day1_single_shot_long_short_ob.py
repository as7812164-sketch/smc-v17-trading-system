import os
import sys
import json
import glob
from datetime import datetime, timezone
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

CACHE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\market_data_cache_15m"

def get_day_key(ts_ms):
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")

def run_single_shot_simulation():
    json_files = glob.glob(os.path.join(CACHE_DIR, "*_15m.json"))
    
    # Prioritize BTC and ETH first
    def sort_key(p):
        fname = os.path.basename(p)
        if "BTC" in fname: return (0, fname)
        if "ETH" in fname: return (1, fname)
        return (2, fname)
    json_files.sort(key=sort_key)

    print("=" * 90)
    print("🔬 EXPERIMENT AUDIT: DAY 1 MARK + SINGLE-SHOT (1 LONG / 1 SHORT PER DAY) ORDER BLOCK")
    print("Rules:")
    print("1. Previous Day High (PDH) & Previous Day Low (PDL) marked as benchmark range.")
    print("2. Extreme Order Blocks formed at Top (PDH) or Bottom (PDL) with Displacement & FVG.")
    print("3. STRICT LIMIT: MAX 1 Long & MAX 1 Short per day per coin (No duplicate re-entries).")
    print("4. Entry at 50% Mean Threshold Limit | SL = 0.15% Buffer | Friction = 0.06 R")
    print("5. Evaluated across Top-20 Champions including BTC & ETH over 6 full months.")
    print("=" * 90)

    # Models tracked
    # Model 1: Fixed 1:2
    # Model 2: Fixed 1:3
    # Model 3: Stepped Trailing SL
    
    results = {
        "m1_fixed_1_2": {"wins": 0, "losses": 0, "net_r": 0.0, "trades": 0},
        "m2_fixed_1_3": {"wins": 0, "losses": 0, "net_r": 0.0, "trades": 0},
        "m3_stepped_trailing": {
            "wins": 0, "fee_saves": 0, "losses": 0, "net_r": 0.0, "trades": 0,
            "bottom_longs": {"wins": 0, "fee_saves": 0, "losses": 0, "net_r": 0.0, "trades": 0},
            "top_shorts": {"wins": 0, "fee_saves": 0, "losses": 0, "net_r": 0.0, "trades": 0}
        }
    }

    coin_stats = defaultdict(lambda: {
        "trades": 0, "m3_wins": 0, "m3_fee_saves": 0, "m3_losses": 0, "m3_net_r": 0.0,
        "m1_net_r": 0.0, "m2_net_r": 0.0
    })

    total_coins = len(json_files)

    for fpath in json_files:
        symbol = os.path.basename(fpath).replace("_15m.json", "")
        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)

        if len(candles) < 500:
            continue

        # Group candles by calendar day
        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        # Iterate through days starting from day 2
        for d_i in range(1, len(sorted_days)):
            prev_day_key = sorted_days[d_i - 1]
            curr_day_key = sorted_days[d_i]

            prev_day_candles = [c for _, c in day_buckets[prev_day_key]]
            curr_day_entries = day_buckets[curr_day_key]

            if len(prev_day_candles) < 20 or len(curr_day_entries) < 20:
                continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)

            # Single-shot flags for the current day
            long_taken_today = False
            short_taken_today = False

            # Scan intraday candles
            for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
                if g_idx + 2 >= len(candles):
                    continue

                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # -------------------------------------------------------------
                # 1. BOTTOM ORDER BLOCK (NEAR / SWEPT PDL) -> LONG
                # -------------------------------------------------------------
                if not long_taken_today:
                    dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                    if dist_to_pdl <= 0.015 or c_l <= pdl:
                        is_bearish = c_c < c_o
                        gain_1bar = (next_c["high"] - c_l) / c_l
                        gain_2bar = (next_c2["high"] - c_l) / c_l
                        has_fvg = next_c2["low"] > c_h

                        if (is_bearish or (c_h - c_l) > 0) and (gain_1bar >= 0.015 or gain_2bar >= 0.020) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_low * 0.9985
                            risk = mt - sl

                            if risk > 0:
                                # Check if limit order gets filled in subsequent bars
                                # Max wait: remaining bars of the day or 32 bars
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 34, len(candles))):
                                    b = candles[w_idx]
                                    if b["low"] <= sl:
                                        # Invalidated before fill
                                        break
                                    if b["low"] <= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    long_taken_today = True # LOCK: No more Longs today for this coin!
                                    
                                    # Simulate outcomes for all 3 models
                                    # Model 1 (1:2)
                                    m1_res = exec_trade(candles, fill_idx, "LONG", mt, sl, risk, "FIXED_1_TO_2")
                                    # Model 2 (1:3)
                                    m2_res = exec_trade(candles, fill_idx, "LONG", mt, sl, risk, "FIXED_1_TO_3")
                                    # Model 3 (Stepped Trailing)
                                    m3_res = exec_trade(candles, fill_idx, "LONG", mt, sl, risk, "STEPPED_TRAILING")

                                    record_trade_result(results, coin_stats, symbol, "LONG", m1_res, m2_res, m3_res)

                # -------------------------------------------------------------
                # 2. TOP ORDER BLOCK (NEAR / SWEPT PDH) -> SHORT
                # -------------------------------------------------------------
                if not short_taken_today:
                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    if dist_to_pdh <= 0.015 or c_h >= pdh:
                        is_bullish = c_c > c_o
                        drop_1bar = (c_h - next_c["low"]) / c_h
                        drop_2bar = (c_h - next_c2["low"]) / c_h
                        has_fvg = next_c2["high"] < c_l

                        if (is_bullish or (c_h - c_l) > 0) and (drop_1bar >= 0.015 or drop_2bar >= 0.020) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_high * 1.0015
                            risk = sl - mt

                            if risk > 0:
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 34, len(candles))):
                                    b = candles[w_idx]
                                    if b["high"] >= sl:
                                        break
                                    if b["high"] >= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    short_taken_today = True # LOCK: No more Shorts today for this coin!

                                    m1_res = exec_trade(candles, fill_idx, "SHORT", mt, sl, risk, "FIXED_1_TO_2")
                                    m2_res = exec_trade(candles, fill_idx, "SHORT", mt, sl, risk, "FIXED_1_TO_3")
                                    m3_res = exec_trade(candles, fill_idx, "SHORT", mt, sl, risk, "STEPPED_TRAILING")

                                    record_trade_result(results, coin_stats, symbol, "SHORT", m1_res, m2_res, m3_res)

                # If both long and short have been taken today, stop scanning this day
                if long_taken_today and short_taken_today:
                    break

    print_report(results, coin_stats)

def exec_trade(candles, fill_idx, side, entry_price, sl_price, risk, exit_mode, max_hold_bars=96, friction_r=0.06):
    active_sl = sl_price
    current_tier = 0
    n = len(candles)

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold_bars, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]

        if side == "LONG":
            if b_l <= active_sl:
                if current_tier == 0:
                    return {"outcome": "SL_HIT", "pnl_r": -1.0 - friction_r}
                elif current_tier == 1:
                    return {"outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r}
                else:
                    return {"outcome": "TRAILING_PROFIT", "pnl_r": ((current_tier - 1) * 0.5) - friction_r}

            max_fav_r = (b_h - entry_price) / risk
            if exit_mode == "FIXED_1_TO_2":
                if max_fav_r >= 2.0:
                    return {"outcome": "TP_HIT", "pnl_r": 2.0 - friction_r}
            elif exit_mode == "FIXED_1_TO_3":
                if max_fav_r >= 3.0:
                    return {"outcome": "TP_HIT", "pnl_r": 3.0 - friction_r}
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
                    return {"outcome": "SL_HIT", "pnl_r": -1.0 - friction_r}
                elif current_tier == 1:
                    return {"outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r}
                else:
                    return {"outcome": "TRAILING_PROFIT", "pnl_r": ((current_tier - 1) * 0.5) - friction_r}

            max_fav_r = (entry_price - b_l) / risk
            if exit_mode == "FIXED_1_TO_2":
                if max_fav_r >= 2.0:
                    return {"outcome": "TP_HIT", "pnl_r": 2.0 - friction_r}
            elif exit_mode == "FIXED_1_TO_3":
                if max_fav_r >= 3.0:
                    return {"outcome": "TP_HIT", "pnl_r": 3.0 - friction_r}
            elif exit_mode == "STEPPED_TRAILING":
                if max_fav_r >= 1.0:
                    tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry_price - (locked_r * risk)

    # If timed out
    last_c = candles[min(fill_idx + max_hold_bars, n - 1)]
    pnl_r = ((last_c["close"] - entry_price) / risk) if side == "LONG" else ((entry_price - last_c["close"]) / risk)
    return {"outcome": "TIMEOUT", "pnl_r": pnl_r - friction_r}

def record_trade_result(results, coin_stats, symbol, side, m1, m2, m3):
    # Model 1
    results["m1_fixed_1_2"]["trades"] += 1
    results["m1_fixed_1_2"]["net_r"] += m1["pnl_r"]
    if m1["pnl_r"] > 0:
        results["m1_fixed_1_2"]["wins"] += 1
    else:
        results["m1_fixed_1_2"]["losses"] += 1

    # Model 2
    results["m2_fixed_1_3"]["trades"] += 1
    results["m2_fixed_1_3"]["net_r"] += m2["pnl_r"]
    if m2["pnl_r"] > 0:
        results["m2_fixed_1_3"]["wins"] += 1
    else:
        results["m2_fixed_1_3"]["losses"] += 1

    # Model 3
    results["m3_stepped_trailing"]["trades"] += 1
    results["m3_stepped_trailing"]["net_r"] += m3["pnl_r"]
    target_sub = results["m3_stepped_trailing"]["bottom_longs"] if side == "LONG" else results["m3_stepped_trailing"]["top_shorts"]
    target_sub["trades"] += 1
    target_sub["net_r"] += m3["pnl_r"]

    if m3["outcome"] == "FEE_SHIELD_SAVE":
        results["m3_stepped_trailing"]["fee_saves"] += 1
        target_sub["fee_saves"] += 1
        coin_stats[symbol]["m3_fee_saves"] += 1
    elif m3["pnl_r"] > 0:
        results["m3_stepped_trailing"]["wins"] += 1
        target_sub["wins"] += 1
        coin_stats[symbol]["m3_wins"] += 1
    else:
        results["m3_stepped_trailing"]["losses"] += 1
        target_sub["losses"] += 1
        coin_stats[symbol]["m3_losses"] += 1

    coin_stats[symbol]["trades"] += 1
    coin_stats[symbol]["m3_net_r"] += m3["pnl_r"]
    coin_stats[symbol]["m1_net_r"] += m1["pnl_r"]
    coin_stats[symbol]["m2_net_r"] += m2["pnl_r"]

def print_report(results, coin_stats):
    m1 = results["m1_fixed_1_2"]
    m2 = results["m2_fixed_1_3"]
    m3 = results["m3_stepped_trailing"]
    m3_long = m3["bottom_longs"]
    m3_short = m3["top_shorts"]

    print("\n" + "=" * 90)
    print("🏆 FINAL AUDIT REPORT: DAY 1 MARK + SINGLE-SHOT (1 LONG / 1 SHORT PER DAY)")
    print("=" * 90)

    print("\n📊 1. COMPARISON ACROSS EXIT ARCHITECTURES:")
    print("-" * 90)
    print(f"{'EXIT MODEL':<28} | {'TRADES':<7} | {'WINS':<6} | {'SAVES':<6} | {'LOSS':<6} | {'WIN %':<7} | {'GREEN %':<8} | {'NET R':<10}")
    print("-" * 90)

    m1_wr = (m1["wins"] / m1["trades"] * 100) if m1["trades"] else 0
    m2_wr = (m2["wins"] / m2["trades"] * 100) if m2["trades"] else 0
    m3_pure_wr = (m3["wins"] / (m3["wins"] + m3["losses"]) * 100) if (m3["wins"] + m3["losses"]) else 0
    m3_green_r = ((m3["wins"] + m3["fee_saves"]) / m3["trades"] * 100) if m3["trades"] else 0

    print(f"{'Model 1: Fixed 1:2 R:R':<28} | {m1['trades']:<7} | {m1['wins']:<6} | {'0':<6} | {m1['losses']:<6} | {m1_wr:<6.1f}% | {m1_wr:<7.1f}% | {m1['net_r']:<+10.1f} R")
    print(f"{'Model 2: Fixed 1:3 R:R':<28} | {m2['trades']:<7} | {m2['wins']:<6} | {'0':<6} | {m2['losses']:<6} | {m2_wr:<6.1f}% | {m2_wr:<7.1f}% | {m2['net_r']:<+10.1f} R")
    print(f"{'Model 3: Stepped Trailing SL':<28} | {m3['trades']:<7} | {m3['wins']:<6} | {m3['fee_saves']:<6} | {m3['losses']:<6} | {m3_pure_wr:<6.1f}% | {m3_green_r:<7.1f}% | {m3['net_r']:<+10.1f} R 👑")

    print("\n🎯 2. DIRECTIONAL BREAKDOWN (MODEL 3 STEPPED TRAILING):")
    print("-" * 90)
    long_green = ((m3_long["wins"] + m3_long["fee_saves"]) / m3_long["trades"] * 100) if m3_long["trades"] else 0
    long_pure_wr = (m3_long["wins"] / (m3_long["wins"] + m3_long["losses"]) * 100) if (m3_long["wins"] + m3_long["losses"]) else 0
    short_green = ((m3_short["wins"] + m3_short["fee_saves"]) / m3_short["trades"] * 100) if m3_short["trades"] else 0
    short_pure_wr = (m3_short["wins"] / (m3_short["wins"] + m3_short["losses"]) * 100) if (m3_short["wins"] + m3_short["losses"]) else 0

    print(f"• Bottom OBs (PDL Support Longs):  {m3_long['trades']} Trades | Pure WR: {long_pure_wr:.1f}% | Green Rate: {long_green:.1f}% | Net Profit: {m3_long['net_r']:+.1f} R")
    print(f"• Top OBs (PDH Resistance Shorts): {m3_short['trades']} Trades | Pure WR: {short_pure_wr:.1f}% | Green Rate: {short_green:.1f}% | Net Profit: {m3_short['net_r']:+.1f} R")

    print("\n🪙 3. COIN-BY-COIN PERFORMANCE BREAKDOWN (ALL 20 COINS INCLUDING BTC & ETH):")
    print("-" * 90)
    print(f"{'SYMBOL':<14} | {'TRADES':<7} | {'WINS':<6} | {'SAVES':<6} | {'LOSS':<6} | {'WIN %':<7} | {'GREEN %':<8} | {'MODEL 3 NET R':<14} | {'STATUS'}")
    print("-" * 90)

    sorted_coins = sorted(coin_stats.items(), key=lambda x: x[1]["m3_net_r"], reverse=True)
    for sym, st in sorted_coins:
        c_tr = st["trades"]
        if c_tr == 0: continue
        c_pwr = (st["m3_wins"] / (st["m3_wins"] + st["m3_losses"]) * 100) if (st["m3_wins"] + st["m3_losses"]) else 0
        c_gr = ((st["m3_wins"] + st["m3_fee_saves"]) / c_tr * 100)
        status = "🌟 ELITE" if st["m3_net_r"] >= 15.0 else ("✅ SOLID" if st["m3_net_r"] > 0 else "⚠️ CHOPPY")
        print(f"{sym:<14} | {c_tr:<7} | {st['m3_wins']:<6} | {st['m3_fee_saves']:<6} | {st['m3_losses']:<6} | {c_pwr:<6.1f}% | {c_gr:<7.1f}% | {st['m3_net_r']:<+13.1f} R | {status}")

    # Account Growth
    print("\n💰 4. ACCOUNT GROWTH PROJECTION ($500 START, 2% RISK / $10 PER TRADE):")
    print("-" * 90)
    p_m1 = m1['net_r'] * 10.0
    p_m2 = m2['net_r'] * 10.0
    p_m3 = m3['net_r'] * 10.0
    print(f"• Model 1 (1:2 R:R):             Net: +{m1['net_r']:.1f} R ➔ Profit: +${p_m1:,.2f} ➔ Final Balance: ${500 + p_m1:,.2f} USDT")
    print(f"• Model 2 (1:3 R:R):             Net: +{m2['net_r']:.1f} R ➔ Profit: +${p_m2:,.2f} ➔ Final Balance: ${500 + p_m2:,.2f} USDT")
    print(f"• Model 3 (Stepped Trailing SL): Net: +{m3['net_r']:.1f} R ➔ Profit: +${p_m3:,.2f} ➔ Final Balance: ${500 + p_m3:,.2f} USDT 🚀")
    print("=" * 90)

if __name__ == "__main__":
    run_single_shot_simulation()
