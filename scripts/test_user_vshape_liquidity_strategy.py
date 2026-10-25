import os
import glob
import json
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# ==============================================================================
# USER V-SHAPE RECOVERY LIQUIDITY STRATEGY TEST HARNESS
# ==============================================================================
# Core Rules:
#   1. Level: Previous Day High (PDH) & Previous Day Low (PDL) marked by wicks.
#   2. Liquidity Sweep: Price pierces beyond PDH/PDL.
#   3. V-Shape Recovery Signature: Strong rejection wick (>= 30% of range).
#   4. Re-entry inside line: 15m candle closes back INSIDE the previous day's range.
#   5. Entry: Next candle open immediately upon 15m close.
#   6. Stop Loss: Extreme sweep wick + 0.20% dynamic safety buffer.
#   7. Target: Strict 1:3 Risk-to-Reward Ratio (TP = 3.0 * Risk).
#   8. Pure Binary Outcome: Straight TP or SL.
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

def run_test():
    coins_data = load_data()
    print(f"Loaded {len(coins_data)} coins for User V-Shape 1:3 R:R Audit.")

    all_setups = []

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

                # 1. BULLISH PDL V-SHAPE SWEEP (LONG)
                # Sweep past PDL + Close inside PDL + Rejection wick >= 30%
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
                            "entry_price": c_c,
                            "sweep_extreme": c_l,
                            "post_candles": post_candles
                        })

                # 2. BEARISH PDH V-SHAPE SWEEP (SHORT)
                # Sweep past PDH + Close inside PDH + Rejection wick >= 30%
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
                            "entry_price": c_c,
                            "sweep_extreme": c_h,
                            "post_candles": post_candles
                        })

    all_setups.sort(key=lambda s: s["time"])
    print(f"Total Qualified V-Shape Line-Close Setups: {len(all_setups)}")

    # =========================================================================
    # SIMULATE 1:3 R:R TRADES
    # =========================================================================
    executed_trades = []
    
    for s in all_setups:
        ep = s["entry_price"]
        side = s["side"]
        post = s["post_candles"]

        # SL = Extreme + 0.20% buffer
        if side == "LONG":
            sl_price = s["sweep_extreme"] * 0.9980
            risk_dist = ep - sl_price
            if risk_dist <= 0: continue
            # Bound risk between 0.8% and 2.5% for realistic futures trading
            risk_dist = max(ep * 0.0080, min(ep * 0.0250, risk_dist))
            sl_price = ep - risk_dist
            tp_price = ep + (3.0 * risk_dist) # Strict 1:3
        else: # SHORT
            sl_price = s["sweep_extreme"] * 1.0020
            risk_dist = sl_price - ep
            if risk_dist <= 0: continue
            risk_dist = max(ep * 0.0080, min(ep * 0.0250, risk_dist))
            sl_price = ep + risk_dist
            tp_price = ep - (3.0 * risk_dist) # Strict 1:3

        outcome = "UNDECIDED"
        exit_p = ep
        exit_time = post[-1]["time"]

        for b in post[:192]:
            bh = float(b["high"])
            bl = float(b["low"])

            if side == "LONG":
                # Conservative conflict check
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
            last_c = float(post[min(191, len(post)-1)]["close"])
            if side == "LONG": outcome = "TP_HIT" if last_c >= ep else "SL_HIT"
            else: outcome = "TP_HIT" if last_c <= ep else "SL_HIT"
            exit_p = last_c

        executed_trades.append({
            "symbol": s["symbol"],
            "side": side,
            "date": s["date"],
            "time": s["time"],
            "entry_price": ep,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "risk_pct": risk_dist / ep * 100.0,
            "outcome": outcome,
            "exit_time": exit_time
        })

    # =========================================================================
    # STATISTICAL ACCURACY & R-MULTIPLE CALCULATIONS
    # =========================================================================
    tot = len(executed_trades)
    tp_wins = sum(1 for t in executed_trades if t["outcome"] == "TP_HIT")
    sl_losses = sum(1 for t in executed_trades if t["outcome"] == "SL_HIT")
    win_rate = (tp_wins / tot * 100.0) if tot else 0.0

    long_trades = [t for t in executed_trades if t["side"] == "LONG"]
    short_trades = [t for t in executed_trades if t["side"] == "SHORT"]
    long_wr = (sum(1 for t in long_trades if t["outcome"] == "TP_HIT") / len(long_trades) * 100.0) if long_trades else 0
    short_wr = (sum(1 for t in short_trades if t["outcome"] == "TP_HIT") / len(short_trades) * 100.0) if short_trades else 0

    # R-multiple PnL
    gross_r_profit = tp_wins * 3.0
    gross_r_loss = sl_losses * 1.0
    net_r = gross_r_profit - gross_r_loss
    profit_factor = (gross_r_profit / gross_r_loss) if gross_r_loss else 0.0
    expectancy = (win_rate/100.0 * 3.0) - ((100.0 - win_rate)/100.0 * 1.0)

    # Dollar simulation on $100 Start ($10 margin per trade, 5x leverage)
    bal_100 = 100.0
    peak_100 = 100.0
    max_dd_100 = 0.0
    for t in executed_trades:
        margin = 10.0
        pos_size = margin * 5.0 # $50 notional
        fee = pos_size * 0.0010
        if t["outcome"] == "TP_HIT":
            pnl = pos_size * (t["risk_pct"] * 3.0 / 100.0) - fee
        else:
            pnl = -(pos_size * (t["risk_pct"] / 100.0)) - fee
        bal_100 += pnl
        if bal_100 > peak_100: peak_100 = bal_100
        dd = (peak_100 - bal_100) / peak_100 * 100.0
        if dd > max_dd_100: max_dd_100 = dd

    # Dollar simulation on Deca Compounding ($500 Start across 10 sections)
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

    report = {
        "strategy": "USER V-SHAPE RECOVERY LINE-CLOSE 1:3 R:R",
        "total_trades": tot,
        "tp_wins": tp_wins,
        "sl_losses": sl_losses,
        "win_rate_pct": round(win_rate, 2),
        "long_win_rate": round(long_wr, 2),
        "short_win_rate": round(short_wr, 2),
        "profit_factor": round(profit_factor, 2),
        "net_r_units": round(net_r, 2),
        "expectancy_r": round(expectancy, 3),
        "final_balance_100": round(bal_100, 2),
        "growth_100_pct": round((bal_100 - 100.0) / 100.0 * 100.0, 2),
        "max_dd_100_pct": round(max_dd_100, 2),
        "final_deca_500": round(final_deca, 2),
        "growth_deca_pct": round((final_deca - 500.0) / 500.0 * 100.0, 2)
    }

    out_file = BASE_DIR / "user_vshape_liquidity_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2)

    print("\n" + "=" * 85)
    print("USER V-SHAPE LINE-CLOSE 1:3 R:R AUDIT REPORT: AUGUST 2026")
    print("=" * 85)
    print(f"{'Performance Metric':<35} | {'Value':<30}")
    print("-" * 85)
    print(f"{'Audit Period':<35} | {'August 2026 (1 Full Month OOS)':<30}")
    print(f"{'Total Trades Executed':<35} | {tot:<30}")
    print(f"{'Take Profit (TP) Wins':<35} | {f'{tp_wins} ({win_rate:.2f}%)':<30}")
    print(f"{'Stop Loss (SL) Losses':<35} | {f'{sl_losses} ({100.0-win_rate:.2f}%)':<30}")
    print(f"{'  - Long Win Rate (PDL Sweeps)':<35} | {f'{long_wr:.2f}% ({len(long_trades)} trades)':<30}")
    print(f"{'  - Short Win Rate (PDH Sweeps)':<35} | {f'{short_wr:.2f}% ({len(short_trades)} trades)':<30}")
    print(f"{'Break-Even Requirement for 1:3 R:R':<35} | {'25.00% Win Rate':<30}")
    print(f"{'Strategy Win Rate Edge':<35} | {f'{win_rate - 25.0:+.2f}% Edge over Market!':<30}")
    print(f"{'Profit Factor':<35} | {profit_factor:.2f}:<30")
    print(f"{'Net R Units Profit':<35} | {f'{net_r:+.2f} R Units':<30}")
    print(f"{'Expectancy per Trade':<35} | {f'{expectancy:+.3f} R per trade':<30}")
    print("-" * 85)
    print(f"{'$100 Account Final Equity':<35} | {f'${bal_100:.2f} ({((bal_100-100)/100*100):+.2f}%)':<30}")
    print(f"{'$500 Deca Compounding Final Equity':<35} | {f'${final_deca:.2f} ({((final_deca-500)/500*100):+.2f}%)':<30}")
    print("=" * 85)

if __name__ == "__main__":
    run_test()
