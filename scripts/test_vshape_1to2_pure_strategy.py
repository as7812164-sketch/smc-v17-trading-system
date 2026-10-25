import os
import glob
import json
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# ==============================================================================
# V-SHAPE LIQUIDITY STRATEGY: 1:2 RISK-TO-REWARD RATIO TEST HARNESS
# ==============================================================================
# Target: Strict 1:2 Risk-to-Reward Ratio (TP = 2.0 * Risk)
# Compares 3 Execution Variations:
#   1. Variation A: Direct 15m Line-Close Entry (SL = Sweep Wick + 0.20% buffer)
#   2. Variation B: 50% Pullback Retest Limit Entry (Zero-Phantom fill)
#   3. Variation C: Pure Touch Limit at PDH/PDL Level (Fixed 1.5% SL -> 3.0% TP)
# Dataset: August 2026 (Full Month OOS, Top-20 Binance USDT-M Champions)
# Capital Simulation: $100 Single Account (5x Isolated) & $500 Deca Compounding (10 Sec)
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

def run_1to2_audit():
    coins_data = load_data()
    print(f"Loaded {len(coins_data)} coins for Strict 1:2 R:R Audit.\n")

    setups_vshape = []
    setups_touch = []

    for sym, candles in coins_data.items():
        daily_buckets = group_candles_by_day(candles)
        sorted_days = sorted(daily_buckets.keys())
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
            if (pdh - pdl) / pdl < 0.010:
                continue

            day_touch_short = False
            day_touch_long = False

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

                # ---------------------------------------------------------
                # Variation C Setups: Pure Touch at PDH / PDL (Max 1 per day)
                # ---------------------------------------------------------
                if c_h >= pdh and not day_touch_short:
                    day_touch_short = True
                    setups_touch.append({
                        "symbol": sym, "side": "SHORT", "date": curr_day_key,
                        "time": c["time"], "entry_price": pdh, "post_candles": post_candles
                    })
                if c_l <= pdl and not day_touch_long:
                    day_touch_long = True
                    setups_touch.append({
                        "symbol": sym, "side": "LONG", "date": curr_day_key,
                        "time": c["time"], "entry_price": pdl, "post_candles": post_candles
                    })

                # ---------------------------------------------------------
                # V-Shape Line-Close Setups: Sweep + Rejection + Close Inside
                # ---------------------------------------------------------
                # Long PDL Sweep
                if c_l < pdl and c_c > pdl:
                    lower_wick = min(c_o, c_c) - c_l
                    if lower_wick / c_range >= 0.30:
                        setups_vshape.append({
                            "symbol": sym, "side": "LONG", "date": curr_day_key,
                            "time": c["time"], "level": pdl, "sweep_extreme": c_l,
                            "candle_close": c_c, "candle_high": c_h, "candle_low": c_l,
                            "post_candles": post_candles
                        })
                # Short PDH Sweep
                if c_h > pdh and c_c < pdh:
                    upper_wick = c_h - max(c_o, c_c)
                    if upper_wick / c_range >= 0.30:
                        setups_vshape.append({
                            "symbol": sym, "side": "SHORT", "date": curr_day_key,
                            "time": c["time"], "level": pdh, "sweep_extreme": c_h,
                            "candle_close": c_c, "candle_high": c_h, "candle_low": c_l,
                            "post_candles": post_candles
                        })

    setups_vshape.sort(key=lambda s: s["time"])
    setups_touch.sort(key=lambda s: s["time"])

    print(f"Total V-Shape Line-Close Setups: {len(setups_vshape)}")
    print(f"Total Pure Touch Setups: {len(setups_touch)}\n")

    # =========================================================================
    # SIMULATION FUNCTION FOR 1:2 R:R
    # =========================================================================
    def simulate_1to2(setups, mode="DIRECT_CLOSE"):
        executed = []
        missed = 0

        for s in setups:
            side = s["side"]
            post = s["post_candles"]

            if mode == "DIRECT_CLOSE":
                ep = s["candle_close"]
                active_candles = post
                entry_time = post[0]["time"]
                # SL = Sweep Extreme + 0.20% buffer
                if side == "LONG":
                    sl_price = s["sweep_extreme"] * 0.9980
                    risk_dist = ep - sl_price
                    if risk_dist <= 0: continue
                    risk_dist = max(ep * 0.0080, min(ep * 0.0250, risk_dist))
                    sl_price = ep - risk_dist
                    tp_price = ep + (2.0 * risk_dist) # 1:2 R:R
                else: # SHORT
                    sl_price = s["sweep_extreme"] * 1.0020
                    risk_dist = sl_price - ep
                    if risk_dist <= 0: continue
                    risk_dist = max(ep * 0.0080, min(ep * 0.0250, risk_dist))
                    sl_price = ep + risk_dist
                    tp_price = ep - (2.0 * risk_dist) # 1:2 R:R

            elif mode == "RETEST_50":
                c_high = s["candle_high"]
                c_low = s["candle_low"]
                c_close = s["candle_close"]
                limit_p = c_low + (c_close - c_low) * 0.50 if side == "LONG" else c_high - (c_high - c_close) * 0.50

                is_filled = False
                f_idx = 0
                for b_i in range(min(8, len(post))):
                    bh = float(post[b_i]["high"])
                    bl = float(post[b_i]["low"])
                    if side == "LONG" and bl <= limit_p:
                        is_filled = True; f_idx = b_i; break
                    elif side == "SHORT" and bh >= limit_p:
                        is_filled = True; f_idx = b_i; break

                if not is_filled:
                    missed += 1
                    continue

                ep = limit_p
                active_candles = post[f_idx:]
                entry_time = post[f_idx]["time"]

                if side == "LONG":
                    sl_price = s["sweep_extreme"] * 0.9980
                    risk_dist = ep - sl_price
                    if risk_dist <= 0: continue
                    risk_dist = max(ep * 0.0060, min(ep * 0.0200, risk_dist))
                    sl_price = ep - risk_dist
                    tp_price = ep + (2.0 * risk_dist)
                else:
                    sl_price = s["sweep_extreme"] * 1.0020
                    risk_dist = sl_price - ep
                    if risk_dist <= 0: continue
                    risk_dist = max(ep * 0.0060, min(ep * 0.0200, risk_dist))
                    sl_price = ep + risk_dist
                    tp_price = ep - (2.0 * risk_dist)

            elif mode == "PURE_TOUCH":
                ep = s["entry_price"]
                active_candles = post
                entry_time = post[0]["time"]
                # Fixed 1.5% SL -> 3.0% TP (1:2 R:R)
                sl_dist = ep * 0.0150
                risk_dist = sl_dist
                if side == "LONG":
                    sl_price = ep - sl_dist
                    tp_price = ep + (2.0 * sl_dist)
                else:
                    sl_price = ep + sl_dist
                    tp_price = ep - (2.0 * sl_dist)

            outcome = "UNDECIDED"
            exit_p = ep
            exit_time = active_candles[-1]["time"]

            for b in active_candles[:192]:
                bh = float(b["high"])
                bl = float(b["low"])

                if side == "LONG":
                    if bl <= sl_price and bh >= tp_price:
                        outcome = "SL_HIT"; exit_p = sl_price; exit_time = b["time"]; break
                    if bh >= tp_price:
                        outcome = "TP_HIT"; exit_p = tp_price; exit_time = b["time"]; break
                    if bl <= sl_price:
                        outcome = "SL_HIT"; exit_p = sl_price; exit_time = b["time"]; break
                else:
                    if bh >= sl_price and bl <= tp_price:
                        outcome = "SL_HIT"; exit_p = sl_price; exit_time = b["time"]; break
                    if bl <= tp_price:
                        outcome = "TP_HIT"; exit_p = tp_price; exit_time = b["time"]; break
                    if bh >= sl_price:
                        outcome = "SL_HIT"; exit_p = sl_price; exit_time = b["time"]; break

            if outcome == "UNDECIDED":
                last_c = float(active_candles[min(191, len(active_candles)-1)]["close"])
                if side == "LONG": outcome = "TP_HIT" if last_c >= ep else "SL_HIT"
                else: outcome = "TP_HIT" if last_c <= ep else "SL_HIT"
                exit_p = last_c

            executed.append({
                "symbol": s["symbol"], "side": side, "entry_time": entry_time,
                "exit_time": exit_time, "entry_price": ep, "risk_pct": risk_dist / ep * 100.0,
                "outcome": outcome
            })

        tot = len(executed)
        tp_wins = sum(1 for t in executed if t["outcome"] == "TP_HIT")
        sl_losses = sum(1 for t in executed if t["outcome"] == "SL_HIT")
        win_rate = (tp_wins / tot * 100.0) if tot else 0.0

        # R-Multiple math for 1:2 R:R (Each win is +2R, each loss is -1R)
        gross_r = tp_wins * 2.0
        loss_r = sl_losses * 1.0
        net_r = gross_r - loss_r
        pf = (gross_r / loss_r) if loss_r else 0.0

        # Compounding Dollar Simulations
        # $100 Start ($10 Margin / 5x Leverage)
        bal_100 = 100.0
        peak_100 = 100.0
        max_dd_100 = 0.0
        for t in executed:
            pos_size = 50.0
            fee = pos_size * 0.0010
            if t["outcome"] == "TP_HIT":
                pnl = pos_size * (t["risk_pct"] * 2.0 / 100.0) - fee
            else:
                pnl = -(pos_size * (t["risk_pct"] / 100.0)) - fee
            bal_100 += pnl
            if bal_100 > peak_100: peak_100 = bal_100
            dd = (peak_100 - bal_100) / peak_100 * 100.0
            if dd > max_dd_100: max_dd_100 = dd

        # $500 Deca Compounding (10 sections)
        sec_deca = {i: 50.0 for i in range(1, 11)}
        sec_peaks = {i: 50.0 for i in range(1, 11)}
        sec_dds = {i: 0.0 for i in range(1, 11)}
        rr_ptr = 1

        for t in executed:
            s_id = rr_ptr
            rr_ptr = (rr_ptr % 10) + 1
            cur = sec_deca[s_id]
            pos_size = cur * 5.0
            fee = pos_size * 0.0010
            if t["outcome"] == "TP_HIT":
                pnl = pos_size * (t["risk_pct"] * 2.0 / 100.0) - fee
            else:
                pnl = -(pos_size * (t["risk_pct"] / 100.0)) - fee
            new_bal = round(max(5.0, cur + pnl), 2)
            sec_deca[s_id] = new_bal
            if new_bal > sec_peaks[s_id]: sec_peaks[s_id] = new_bal
            dd = (sec_peaks[s_id] - new_bal) / sec_peaks[s_id] * 100.0
            if dd > sec_dds[s_id]: sec_dds[s_id] = dd

        final_deca = sum(sec_deca.values())

        return {
            "mode": mode,
            "total_trades": tot,
            "missed": missed,
            "tp_wins": tp_wins,
            "sl_losses": sl_losses,
            "win_rate_pct": round(win_rate, 2),
            "net_r": round(net_r, 2),
            "profit_factor": round(pf, 2),
            "final_bal_100": round(bal_100, 2),
            "growth_100": round((bal_100 - 100.0) / 100.0 * 100.0, 2),
            "max_dd_100": round(max_dd_100, 2),
            "final_deca_500": round(final_deca, 2),
            "growth_deca": round((final_deca - 500.0) / 500.0 * 100.0, 2)
        }

    res_a = simulate_1to2(setups_vshape, mode="DIRECT_CLOSE")
    res_b = simulate_1to2(setups_vshape, mode="RETEST_50")
    res_c = simulate_1to2(setups_touch, mode="PURE_TOUCH")

    print("=" * 88)
    print("STRICT 1:2 RISK-TO-REWARD RATIO COMPREHENSIVE AUDIT (AUGUST 2026)")
    print("=" * 88)
    print(f"{'Execution Mode':<25} | {'Trades':<7} | {'Win Rate%':<10} | {'Profit Factor':<14} | {'Net R':<8} | {'$100 End':<10} | {'$500 Deca End':<14}")
    print("-" * 88)
    for r, name in [
        (res_a, "Var A: Direct Line Close"),
        (res_b, "Var B: 50% Retest Limit"),
        (res_c, "Var C: Pure Level Touch")
    ]:
        print(f"{name:<25} | {r['total_trades']:<7} | {r['win_rate_pct']}%{'':<4} | {r['profit_factor']:<14} | {r['net_r']:+6.1f}R | ${r['final_bal_100']:<9} | ${r['final_deca_500']:<13}")
    print("=" * 88)

    out_file = BASE_DIR / "vshape_1to2_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump({"var_a": res_a, "var_b": res_b, "var_c": res_c}, fp, indent=2)

if __name__ == "__main__":
    run_1to2_audit()
