import os
import sys
import json
import glob
from datetime import datetime, timezone, timedelta
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

IST = timezone(timedelta(hours=5, minutes=30))
CACHE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\market_data_cache_15m"
TARGET_1CR = 115000.0  # ₹1 Crore INR ≈ $115,000 USDT

def get_day_key(ts_ms):
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")

def harvest_bb_trades():
    json_files = glob.glob(os.path.join(CACHE_DIR, "*_15m.json"))
    raw_trades = []

    print(f"Loading 15m candle files from {CACHE_DIR}...")
    for fpath in json_files:
        symbol = os.path.basename(fpath).replace("_15m.json", "")
        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)

        if len(candles) < 500:
            continue

        for c in candles:
            c["open"] = float(c["open"])
            c["high"] = float(c["high"])
            c["low"] = float(c["low"])
            c["close"] = float(c["close"])

        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            prev_day_key = sorted_days[d_i - 1]
            curr_day_key = sorted_days[d_i]

            prev_day_candles = [c for _, c in day_buckets[prev_day_key]]
            curr_day_entries = day_buckets[curr_day_key]

            if len(prev_day_candles) < 20 or len(curr_day_entries) < 20:
                continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)

            long_taken_today = False
            short_taken_today = False

            for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
                if g_idx + 2 >= len(candles):
                    continue

                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # 1. BOTTOM OB (PDL SWEEP / DEFENSE) -> LONG
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
                            sl = ob_low * 0.9985  # 0.15% Anti-hunt buffer
                            risk = mt - sl

                            if risk > 0:
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 34, len(candles))):
                                    b = candles[w_idx]
                                    if b["low"] <= sl:
                                        break
                                    if b["low"] <= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    long_taken_today = True
                                    trade_res = resolve_bb_trade(candles, fill_idx, "LONG", mt, sl, risk, symbol)
                                    raw_trades.append(trade_res)

                # 2. TOP OB (PDH SWEEP / DEFENSE) -> SHORT
                if not short_taken_today:
                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    if dist_to_pdh <= 0.015 or c_h >= pdh:
                        is_bullish = c_c > c_o
                        drop_1bar = (c_h - next_c["low"]) / c_h
                        drop_2bar = (c_h - next_c2["low"]) / c_h
                        has_fvg = next_c2["high"] < c_l

                        if (is_bullish or (c_h - c_l) > 0) and (drop_1bar >= 0.012 or drop_2bar >= 0.018) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_high * 1.0015  # 0.15% Anti-hunt buffer
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
                                    short_taken_today = True
                                    trade_res = resolve_bb_trade(candles, fill_idx, "SHORT", mt, sl, risk, symbol)
                                    raw_trades.append(trade_res)

                if long_taken_today and short_taken_today:
                    break

    raw_trades.sort(key=lambda t: t["fill_time"])
    print(f"Total resolved BB trade setups: {len(raw_trades)}")
    return raw_trades

def resolve_bb_trade(candles, fill_idx, side, entry, sl, risk, symbol, max_hold=96):
    """
    Simulates exact Stepped Trailing Profit Armor according to BB 2.0 / 3.0:
    - Initial SL at sl
    - When favorable excursion reaches:
      >= 1.0R: SL moves to +0.2R (Fee Shield / Breakeven)
      >= 1.5R: SL moves to +1.0R (Profit Locked)
      >= 2.0R: SL moves to +1.5R (Profit Locked)
      >= 2.5R: SL moves to +2.0R (Profit Locked)
      >= 3.0R: Take Profit hits (+3.0R exit)!
    """
    leverage = 5.0
    fee_rate = 0.0010  # 0.10% taker fee round-trip
    active_sl = sl
    current_tier = 0
    n = len(candles)
    fill_time = candles[fill_idx]["time"]
    highest_fav_r = 0.0
    exit_price = entry
    exit_time = fill_time
    outcome = None
    locked_r = -1.0

    tp_price = entry + (risk * 3.0) if side == "LONG" else entry - (risk * 3.0)

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]
        exit_time = b["time"]

        if side == "LONG":
            cur_r = (b_h - entry) / risk
            if cur_r > highest_fav_r:
                highest_fav_r = cur_r

            # Check TP hit
            if b_h >= tp_price:
                outcome = "TP_HIT"
                exit_price = tp_price
                locked_r = 3.0
                break

            # Check SL or Trailing SL hit
            if b_l <= active_sl:
                exit_price = active_sl
                if current_tier == 0:
                    outcome = "HARD_SL_HIT"
                    locked_r = -1.0
                elif current_tier == 1:
                    outcome = "TRAILING_FEE_SHIELD"
                    locked_r = 0.2
                else:
                    outcome = "TRAILING_SL_HIT"
                    locked_r = (current_tier - 1) * 0.5
                break

            # Upgrade Trailing SL ladder
            if cur_r >= 1.0:
                if cur_r >= 1.5:
                    tier_cand = int((cur_r - 1.0) / 0.5) + 1
                    if tier_cand > current_tier:
                        current_tier = tier_cand
                        locked_r = (current_tier - 1) * 0.5
                        active_sl = entry + (locked_r * risk)
                elif current_tier < 1:
                    current_tier = 1
                    locked_r = 0.2
                    active_sl = entry + (0.2 * risk)

        else: # SHORT
            cur_r = (entry - b_l) / risk
            if cur_r > highest_fav_r:
                highest_fav_r = cur_r

            # Check TP hit
            if b_l <= tp_price:
                outcome = "TP_HIT"
                exit_price = tp_price
                locked_r = 3.0
                break

            # Check SL or Trailing SL hit
            if b_h >= active_sl:
                exit_price = active_sl
                if current_tier == 0:
                    outcome = "HARD_SL_HIT"
                    locked_r = -1.0
                elif current_tier == 1:
                    outcome = "TRAILING_FEE_SHIELD"
                    locked_r = 0.2
                else:
                    outcome = "TRAILING_SL_HIT"
                    locked_r = (current_tier - 1) * 0.5
                break

            # Upgrade Trailing SL ladder
            if cur_r >= 1.0:
                if cur_r >= 1.5:
                    tier_cand = int((cur_r - 1.0) / 0.5) + 1
                    if tier_cand > current_tier:
                        current_tier = tier_cand
                        locked_r = (current_tier - 1) * 0.5
                        active_sl = entry - (locked_r * risk)
                elif current_tier < 1:
                    current_tier = 1
                    locked_r = 0.2
                    active_sl = entry - (0.2 * risk)

    if not outcome:
        last_c = candles[min(fill_idx + max_hold, n - 1)]
        exit_price = last_c["close"]
        exit_time = last_c["time"]
        r_move = ((exit_price - entry) / risk) if side == "LONG" else ((entry - exit_price) / risk)
        outcome = "TIMEOUT_EXIT"
        locked_r = r_move

    # Convert to spot move and ROE at 5x leverage
    spot_move = ((exit_price - entry) / entry) if side == "LONG" else ((entry - exit_price) / entry)
    net_spot_move = spot_move - fee_rate
    roe_pct = net_spot_move * leverage * 100.0

    return {
        "symbol": symbol,
        "side": side,
        "fill_time": fill_time,
        "exit_time": exit_time,
        "entry_price": entry,
        "exit_price": exit_price,
        "outcome": outcome,
        "locked_r": locked_r,
        "highest_r": round(highest_fav_r, 2),
        "roe_pct": round(roe_pct, 2)
    }

if __name__ == "__main__":
    bb_trades = harvest_bb_trades()
    with open("scripts/resolved_bb_trades.json", "w") as f:
        json.dump(bb_trades, f, indent=2)
    print("Saved resolved BB trades to scripts/resolved_bb_trades.json")
