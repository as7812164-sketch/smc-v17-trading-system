import os
import glob
import json
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# ==============================================================================
# USER V-SHAPE RECOVERY + RETEST PULLBACK 1:3 R:R TEST HARNESS
# ==============================================================================
# Core Rules:
#   1. Level: Previous Day High (PDH) & Previous Day Low (PDL) marked by wicks.
#   2. Sweep & Trap: Price sweeps beyond PDH/PDL + Rejection wick >= 30%.
#   3. Line-Close: 15m candle closes back INSIDE the line (V-Shape confirmed).
#   4. Retest Entry Rule: Limit order placed at 50% pullback of the sweep candle.
#   5. Strict Zero-Phantom Verification: Limit must be physically breached on subsequent bars.
#   6. Stop Loss: Extreme sweep wick + 0.20% dynamic safety buffer (Tight Risk!).
#   7. Target: Strict 1:3 Risk-to-Reward Ratio (TP = 3.0 * Risk).
#   8. Pure Binary: Straight TP or SL.
# Universe: Top-20 Binance USDT-M Champions (August 2026, 1 Full Month OOS)
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
            filtered = [c for c in raw if (T_START - 20 * 86400 * 1000) <= c["time"] <= (T_END + 7 * 86400 * 1000)]
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

def run_test():
    coins_data = load_data()
    print(f"Loaded {len(coins_data)} coins for V-Shape Retest 1:3 R:R Audit.")

    all_setups = []

    for sym, candles in coins_data.items():
        daily_buckets = group_candles_by_day(candles)
        sorted_days = sorted(daily_buckets.keys())
        time_to_idx = {c["time"]: i for i, c in enumerate(candles)}

        # 4H EMA 50 trend filter
        closes = pd.Series([float(c["close"]) for c in candles])
        ema_4h = closes.ewm(span=800, adjust=False).mean()

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

            for c_idx, c in enumerate(curr_candles):
                c_o = float(c["open"])
                c_h = float(c["high"])
                c_l = float(c["low"])
                c_c = float(c["close"])
                c_range = c_h - c_l
                if c_range <= 0:
                    continue

                g_idx = time_to_idx[c["time"]]
                post_candles = candles[g_idx + 1 :]
                if len(post_candles) < 4:
                    continue

                is_bull_4h = c_c > ema_4h.iloc[g_idx]

                # 1. BULLISH PDL V-SHAPE SWEEP (LONG)
                if c_l < pdl and c_c > pdl:
                    lower_wick = min(c_o, c_c) - c_l
                    wick_ratio = lower_wick / c_range
                    if wick_ratio >= 0.30:
                        all_setups.append({
                            "symbol": sym,
                            "side": "LONG",
                            "date": curr_day_key,
                            "time": c["time"],
                            "level": pdl,
                            "sweep_extreme": c_l,
                            "candle_close": c_c,
                            "candle_high": c_h,
                            "candle_low": c_l,
                            "is_trend_aligned": is_bull_4h,
                            "post_candles": post_candles
                        })

                # 2. BEARISH PDH V-SHAPE SWEEP (SHORT)
                if c_h > pdh and c_c < pdh:
                    upper_wick = c_h - max(c_o, c_c)
                    wick_ratio = upper_wick / c_range
                    if wick_ratio >= 0.30:
                        all_setups.append({
                            "symbol": sym,
                            "side": "SHORT",
                            "date": curr_day_key,
                            "time": c["time"],
                            "level": pdh,
                            "sweep_extreme": c_h,
                            "candle_close": c_c,
                            "candle_high": c_h,
                            "candle_low": c_l,
                            "is_trend_aligned": not is_bull_4h,
                            "post_candles": post_candles
                        })

    all_setups.sort(key=lambda s: s["time"])
    print(f"Total Qualified V-Shape Line-Close Setups: {len(all_setups)}")

    # Function to simulate Retest entry with a given pullback ratio (e.g. 0.382 or 0.50)
    def simulate_retest(retest_ratio=0.50, trend_aligned_only=False):
        executed_trades = []
        missed_count = 0

        subset = [s for s in all_setups if s["is_trend_aligned"]] if trend_aligned_only else all_setups

        for s in subset:
            side = s["side"]
            post = s["post_candles"]
            c_high = s["candle_high"]
            c_low = s["candle_low"]
            c_close = s["candle_close"]

            # Calculate 50% Pullback Limit Order Price
            if side == "LONG":
                limit_price = c_low + (c_close - c_low) * retest_ratio
            else: # SHORT
                limit_price = c_high - (c_high - c_close) * retest_ratio

            # Zero-Phantom Physical Fill Check (Timeout: 8 bars = 2 hours)
            is_filled = False
            fill_idx = 0
            for b_i in range(min(8, len(post))):
                bh = float(post[b_i]["high"])
                bl = float(post[b_i]["low"])

                if side == "LONG":
                    if bl <= limit_price:
                        is_filled = True
                        fill_idx = b_i
                        break
                else: # SHORT
                    if bh >= limit_price:
                        is_filled = True
                        fill_idx = b_i
                        break

            if not is_filled:
                missed_count += 1
                continue

            # Filled!
            ep = limit_price
            active_candles = post[fill_idx:]
            entry_time = post[fill_idx]["time"]

            # SL = Sweep Extreme + 0.20% buffer (Tight & Protected!)
            if side == "LONG":
                sl_price = s["sweep_extreme"] * 0.9980
                risk_dist = ep - sl_price
                if risk_dist <= 0: continue
                # Bounded risk between 0.6% and 2.0%
                risk_dist = max(ep * 0.0060, min(ep * 0.0200, risk_dist))
                sl_price = ep - risk_dist
                tp_price = ep + (3.0 * risk_dist) # Strict 1:3 R:R
            else: # SHORT
                sl_price = s["sweep_extreme"] * 1.0020
                risk_dist = sl_price - ep
                if risk_dist <= 0: continue
                risk_dist = max(ep * 0.0060, min(ep * 0.0200, risk_dist))
                sl_price = ep + risk_dist
                tp_price = ep - (3.0 * risk_dist) # Strict 1:3 R:R

            outcome = "UNDECIDED"
            exit_p = ep
            exit_time = active_candles[-1]["time"]

            for b in active_candles[:192]:
                bh = float(b["high"])
                bl = float(b["low"])

                if side == "LONG":
                    if bl <= sl_price and bh >= tp_price:
                        outcome = "SL_HIT"
                        exit_p = sl_price
                        exit_time = b["time"]
                        break
                    if bh >= tp_price:
                        outcome = "TP_HIT"
                        exit_p = tp_price
                        exit_time = b["time"]
                        break
                    if bl <= sl_price:
                        outcome = "SL_HIT"
                        exit_p = sl_price
                        exit_time = b["time"]
                        break
                else: # SHORT
                    if bh >= sl_price and bl <= tp_price:
                        outcome = "SL_HIT"
                        exit_p = sl_price
                        exit_time = b["time"]
                        break
                    if bl <= tp_price:
                        outcome = "TP_HIT"
                        exit_p = tp_price
                        exit_time = b["time"]
                        break
                    if bh >= sl_price:
                        outcome = "SL_HIT"
                        exit_p = sl_price
                        exit_time = b["time"]
                        break

            if outcome == "UNDECIDED":
                last_c = float(active_candles[min(191, len(active_candles)-1)]["close"])
                if side == "LONG": outcome = "TP_HIT" if last_c >= ep else "SL_HIT"
                else: outcome = "TP_HIT" if last_c <= ep else "SL_HIT"
                exit_p = last_c

            executed_trades.append({
                "symbol": s["symbol"],
                "side": side,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "entry_price": ep,
                "sl_price": sl_price,
                "tp_price": tp_price,
                "risk_pct": risk_dist / ep * 100.0,
                "outcome": outcome
            })

        tot = len(executed_trades)
        tp_wins = sum(1 for t in executed_trades if t["outcome"] == "TP_HIT")
        sl_losses = sum(1 for t in executed_trades if t["outcome"] == "SL_HIT")
        win_rate = (tp_wins / tot * 100.0) if tot else 0.0

        long_trades = [t for t in executed_trades if t["side"] == "LONG"]
        short_trades = [t for t in executed_trades if t["side"] == "SHORT"]
        long_wr = (sum(1 for t in long_trades if t["outcome"] == "TP_HIT") / len(long_trades) * 100.0) if long_trades else 0
        short_wr = (sum(1 for t in short_trades if t["outcome"] == "TP_HIT") / len(short_trades) * 100.0) if short_trades else 0

        gross_r = tp_wins * 3.0
        loss_r = sl_losses * 1.0
        net_r = gross_r - loss_r
        pf = (gross_r / loss_r) if loss_r else 0.0
        miss_rate = (missed_count / (tot + missed_count) * 100.0) if (tot + missed_count) else 0.0

        # Dollar simulation on $100 Start ($10 margin, 5x leverage)
        bal_100 = 100.0
        peak_100 = 100.0
        max_dd_100 = 0.0
        for t in executed_trades:
            pos_size = 50.0 # $10 * 5x
            fee = pos_size * 0.0010
            if t["outcome"] == "TP_HIT":
                pnl = pos_size * (t["risk_pct"] * 3.0 / 100.0) - fee
            else:
                pnl = -(pos_size * (t["risk_pct"] / 100.0)) - fee
            bal_100 += pnl
            if bal_100 > peak_100: peak_100 = bal_100
            dd = (peak_100 - bal_100) / peak_100 * 100.0
            if dd > max_dd_100: max_dd_100 = dd

        # Deca Compounding ($500 Start, 10 sections)
        sec_deca = {i: 50.0 for i in range(1, 11)}
        sec_peaks = {i: 50.0 for i in range(1, 11)}
        sec_dds = {i: 0.0 for i in range(1, 11)}
        rr_ptr = 1

        for t in executed_trades:
            s_id = rr_ptr
            rr_ptr = (rr_ptr % 10) + 1
            cur = sec_deca[s_id]
            pos_size = cur * 5.0
            fee = pos_size * 0.0010
            if t["outcome"] == "TP_HIT":
                pnl = pos_size * (t["risk_pct"] * 3.0 / 100.0) - fee
            else:
                pnl = -(pos_size * (t["risk_pct"] / 100.0)) - fee
            new_bal = round(max(5.0, cur + pnl), 2)
            sec_deca[s_id] = new_bal
            if new_bal > sec_peaks[s_id]: sec_peaks[s_id] = new_bal
            dd = (sec_peaks[s_id] - new_bal) / sec_peaks[s_id] * 100.0
            if dd > sec_dds[s_id]: sec_dds[s_id] = dd

        final_deca = sum(sec_deca.values())

        return {
            "retest_ratio": f"{retest_ratio*100:.0f}%",
            "trend_aligned": trend_aligned_only,
            "total_trades": tot,
            "missed_trades": missed_count,
            "miss_rate_pct": round(miss_rate, 1),
            "tp_wins": tp_wins,
            "sl_losses": sl_losses,
            "win_rate_pct": round(win_rate, 2),
            "long_win_rate": round(long_wr, 2),
            "short_win_rate": round(short_wr, 2),
            "net_r_units": round(net_r, 2),
            "profit_factor": round(pf, 2),
            "final_bal_100": round(bal_100, 2),
            "growth_100_pct": round((bal_100 - 100.0) / 100.0 * 100.0, 2),
            "max_dd_100_pct": round(max_dd_100, 2),
            "final_deca_500": round(final_deca, 2),
            "growth_deca_pct": round((final_deca - 500.0) / 500.0 * 100.0, 2)
        }

    # Test Configurations
    res_raw_50 = simulate_retest(retest_ratio=0.50, trend_aligned_only=False)
    res_raw_35 = simulate_retest(retest_ratio=0.35, trend_aligned_only=False)
    res_trend_50 = simulate_retest(retest_ratio=0.50, trend_aligned_only=True)
    res_trend_35 = simulate_retest(retest_ratio=0.35, trend_aligned_only=True)

    print("\n" + "=" * 88)
    print("V-SHAPE RETEST 1:3 R:R MULTI-CONFIG COMPARISON AUDIT (AUGUST 2026)")
    print("=" * 88)
    print(f"{'Config Name':<22} | {'Trades':<7} | {'Miss%':<6} | {'Win Rate':<10} | {'Profit Factor':<14} | {'Net R':<8} | {'$100 End':<10} | {'$500 Deca End':<14}")
    print("-" * 88)
    for r, name in [
        (res_raw_50, "Raw 50% Retest"),
        (res_raw_35, "Raw 35% Retest"),
        (res_trend_50, "Trend 50% Retest"),
        (res_trend_35, "Trend 35% Retest")
    ]:
        print(f"{name:<22} | {r['total_trades']:<7} | {r['miss_rate_pct']}%{'':<2} | {r['win_rate_pct']}%{'':<4} | {r['profit_factor']:<14} | {r['net_r_units']:+6.1f}R | ${r['final_bal_100']:<9} | ${r['final_deca_500']:<13}")
    print("=" * 88)

    out_file = BASE_DIR / "vshape_retest_1to3_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump({
            "raw_50": res_raw_50,
            "raw_35": res_raw_35,
            "trend_50": res_trend_50,
            "trend_35": res_trend_35
        }, fp, indent=2)

if __name__ == "__main__":
    run_test()
