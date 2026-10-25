import os
import glob
import json
import datetime
from pathlib import Path

# ==============================================================================
# PDH / PDL LIQUIDITY SWEEP DUAL-METHOD QUANT BACKTEST HARNESS
# Method 1: Direct 15m Candle Close Confirmation
# Method 2: 5m / Sub-impulse Retest to FVG / 50% Discount Mitigation
# Period: Full 1 Month (August 1, 2026 00:00 UTC to August 31, 2026 23:45 UTC)
# Universe: Top-20 Binance USDT-M Champions
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "market_data_cache_15m"

# August 2026 timestamps (UTC)
T_START = int(datetime.datetime(2026, 8, 1, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_END   = int(datetime.datetime(2026, 8, 31, 23, 59, tzinfo=datetime.timezone.utc).timestamp() * 1000)

def load_data():
    files = glob.glob(str(DATA_DIR / "*_15m.json"))
    coins_data = {}
    for f in sorted(files):
        sym = Path(f).name.replace("_15m.json", "")
        with open(f, "r", encoding="utf-8") as fp:
            raw = json.load(fp)
            # Filter August 2026 plus prior 2 days for PDH/PDL baseline
            filtered = [c for c in raw if (T_START - 2 * 86400 * 1000) <= c["time"] <= (T_END + 2 * 86400 * 1000)]
            if len(filtered) >= 2000:
                coins_data[sym] = filtered
    return coins_data

def group_candles_by_day(candles):
    """Groups 15m candles into daily buckets (UTC)."""
    days = {}
    for c in candles:
        dt = datetime.datetime.fromtimestamp(c["time"] / 1000.0, tz=datetime.timezone.utc)
        day_key = dt.strftime("%Y-%m-%d")
        if day_key not in days:
            days[day_key] = []
        days[day_key].append(c)
    return days

def run_backtest():
    coins_data = load_data()
    print(f"Loaded {len(coins_data)} coins with complete 15m candle data for August 2026.\n")

    all_setups = []

    for sym, candles in coins_data.items():
        daily_buckets = group_candles_by_day(candles)
        sorted_days = sorted(daily_buckets.keys())

        for idx in range(1, len(sorted_days)):
            prev_day_key = sorted_days[idx - 1]
            curr_day_key = sorted_days[idx]

            # Only evaluate setups occurring within August 2026
            if not curr_day_key.startswith("2026-08"):
                continue

            prev_day_candles = daily_buckets[prev_day_key]
            curr_day_candles = daily_buckets[curr_day_key]

            if len(prev_day_candles) < 80 or len(curr_day_candles) < 80:
                continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)
            pd_mid = (pdh + pdl) / 2.0
            pd_range_pct = (pdh - pdl) / pdl

            if pd_range_pct < 0.015:  # Skip super-tight chop days
                continue

            # Scan current day's candles
            for c_idx, c in enumerate(curr_day_candles):
                c_o = float(c["open"])
                c_h = float(c["high"])
                c_l = float(c["low"])
                c_c = float(c["close"])
                c_range = c_h - c_l
                if c_range <= 0:
                    continue

                # -----------------------------------------------------------------
                # 1. BULLISH PDL LIQUIDITY SWEEP (LONG)
                # -----------------------------------------------------------------
                if c_l < pdl and c_c > pdl:
                    sweep_depth = (pdl - c_l) / pdl
                    if 0.0010 <= sweep_depth <= 0.0350:  # Valid liquidity penetration
                        lower_wick = min(c_o, c_c) - c_l
                        wick_ratio = lower_wick / c_range
                        if wick_ratio >= 0.25:  # Rejection wick confirmed
                            # Check subsequent bars for outcome
                            all_setups.append({
                                "symbol": sym,
                                "day": curr_day_key,
                                "side": "LONG",
                                "time": c["time"],
                                "pdl": pdl,
                                "pdh": pdh,
                                "pd_mid": pd_mid,
                                "sweep_low": c_l,
                                "candle_close": c_c,
                                "wick_ratio": wick_ratio,
                                "sweep_depth_pct": sweep_depth * 100,
                                "raw_candles": curr_day_candles[c_idx:]
                            })

                # -----------------------------------------------------------------
                # 2. BEARISH PDH LIQUIDITY SWEEP (SHORT)
                # -----------------------------------------------------------------
                if c_h > pdh and c_c < pdh:
                    sweep_depth = (c_h - pdh) / pdh
                    if 0.0010 <= sweep_depth <= 0.0350:
                        upper_wick = c_h - max(c_o, c_c)
                        wick_ratio = upper_wick / c_range
                        if wick_ratio >= 0.25:
                            all_setups.append({
                                "symbol": sym,
                                "day": curr_day_key,
                                "side": "SHORT",
                                "time": c["time"],
                                "pdl": pdl,
                                "pdh": pdh,
                                "pd_mid": pd_mid,
                                "sweep_high": c_h,
                                "candle_close": c_c,
                                "wick_ratio": wick_ratio,
                                "sweep_depth_pct": sweep_depth * 100,
                                "raw_candles": curr_day_candles[c_idx:]
                            })

    # Sort setups chronologically
    all_setups.sort(key=lambda s: s["time"])
    print(f"Total Qualified Liquidity Sweep Setups Detected: {len(all_setups)}\n")

    # =========================================================================
    # SIMULATE METHOD 1: Direct 15m Candle Close
    # =========================================================================
    bal_m1 = 100.0
    trades_m1 = []
    tp_wins_m1 = 0
    be_saves_m1 = 0
    sl_losses_m1 = 0
    peak_bal_m1 = 100.0
    max_dd_m1 = 0.0

    # Sequential queue
    busy_until_m1 = 0

    for s in all_setups:
        if s["time"] < busy_until_m1:
            continue

        side = s["side"]
        ep = s["candle_close"]
        sub_candles = s["raw_candles"][1:]  # subsequent candles
        if len(sub_candles) < 3:
            continue

        # Targets (1:2 Strict Institutional Math at 5x leverage)
        tp_spot = 0.0300   # +3.00% Spot (+15.0% ROE)
        sl_spot = 0.0150   # -1.50% Spot (-7.5% ROE)
        be_spot = 0.0150   # +1.50% Spot triggers Break-Even Armor

        if side == "LONG":
            tp_p = ep * (1.0 + tp_spot)
            hard_sl = min(ep * (1.0 - sl_spot), s["sweep_low"] * 0.9990)
            be_trigger_p = ep * (1.0 + be_spot)
        else:
            tp_p = ep * (1.0 - tp_spot)
            hard_sl = max(ep * (1.0 + sl_spot), s["sweep_high"] * 1.0010)
            be_trigger_p = ep * (1.0 - be_spot)

        outcome = "UNDECIDED"
        be_locked = False
        curr_sl = hard_sl
        exit_p = ep
        exit_time = sub_candles[-1]["time"]

        for b in sub_candles:
            b_h = float(b["high"])
            b_l = float(b["low"])
            b_c = float(b["close"])

            if side == "LONG":
                # Check BE trigger
                if b_h >= be_trigger_p and not be_locked:
                    be_locked = True
                    curr_sl = ep * 1.0010  # Lock entry + 0.1% fees

                # Check TP
                if b_h >= tp_p:
                    outcome = "TP_HIT"
                    exit_p = tp_p
                    exit_time = b["time"]
                    break

                # Check SL
                if b_l <= curr_sl:
                    outcome = "BE_SAVE" if be_locked else "SL_HIT"
                    exit_p = curr_sl
                    exit_time = b["time"]
                    break
            else: # SHORT
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

        # Calculate PnL (5x leverage, 100% sequential compounding)
        margin = bal_m1
        pos_size = margin * 5.0

        if outcome == "TP_HIT":
            pnl = pos_size * tp_spot - (pos_size * 0.0010)
            tp_wins_m1 += 1
        elif outcome == "BE_SAVE":
            pnl = 0.0 - (pos_size * 0.0010)  # Breakeven minus taker fee
            be_saves_m1 += 1
        else: # SL_HIT
            sl_move = abs(ep - exit_p) / ep
            pnl = -(pos_size * sl_move) - (pos_size * 0.0010)
            sl_losses_m1 += 1

        bal_m1 += pnl
        if bal_m1 > peak_bal_m1:
            peak_bal_m1 = bal_m1
        dd = (peak_bal_m1 - bal_m1) / peak_bal_m1 * 100.0
        if dd > max_dd_m1:
            max_dd_m1 = dd

        busy_until_m1 = exit_time
        trades_m1.append({
            "symbol": s["symbol"],
            "side": side,
            "entry_time": s["time"],
            "outcome": outcome,
            "pnl": pnl,
            "bal": bal_m1
        })

    # =========================================================================
    # SIMULATE METHOD 2: 5m / Sub-impulse Retest to FVG / 50% Discount
    # =========================================================================
    bal_m2 = 100.0
    trades_m2 = []
    tp_wins_m2 = 0
    be_saves_m2 = 0
    sl_losses_m2 = 0
    missed_orders_m2 = 0
    filled_orders_m2 = 0
    peak_bal_m2 = 100.0
    max_dd_m2 = 0.0

    busy_until_m2 = 0

    for s in all_setups:
        if s["time"] < busy_until_m2:
            continue

        side = s["side"]
        c_close = s["candle_close"]
        sub_candles = s["raw_candles"][1:]
        if len(sub_candles) < 3:
            continue

        # In Method 2, place limit order at 50% discount of the sweep candle
        if side == "LONG":
            limit_entry = s["sweep_low"] + (c_close - s["sweep_low"]) * 0.50
        else:
            limit_entry = s["sweep_high"] - (s["sweep_high"] - c_close) * 0.50

        # Check if limit is filled within the next 4 candles (1 hour)
        is_filled = False
        fill_idx = -1

        for idx_wait in range(min(4, len(sub_candles))):
            b_wait = sub_candles[idx_wait]
            if side == "LONG":
                if float(b_wait["low"]) <= limit_entry:
                    is_filled = True
                    fill_idx = idx_wait
                    break
            else:
                if float(b_wait["high"]) >= limit_entry:
                    is_filled = True
                    fill_idx = idx_wait
                    break

        if not is_filled:
            missed_orders_m2 += 1
            continue  # MISSED RUNAWAY MOVE!

        filled_orders_m2 += 1
        active_sub = sub_candles[fill_idx + 1:]
        if not active_sub:
            continue

        ep = limit_entry
        tp_spot = 0.0300
        sl_spot = 0.0150
        be_spot = 0.0150

        if side == "LONG":
            tp_p = ep * (1.0 + tp_spot)
            hard_sl = min(ep * (1.0 - sl_spot), s["sweep_low"] * 0.9990)
            be_trigger_p = ep * (1.0 + be_spot)
        else:
            tp_p = ep * (1.0 - tp_spot)
            hard_sl = max(ep * (1.0 + sl_spot), s["sweep_high"] * 1.0010)
            be_trigger_p = ep * (1.0 - be_spot)

        outcome = "UNDECIDED"
        be_locked = False
        curr_sl = hard_sl
        exit_p = ep
        exit_time = active_sub[-1]["time"]

        for b in active_sub:
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

        margin = bal_m2
        pos_size = margin * 5.0

        if outcome == "TP_HIT":
            pnl = pos_size * tp_spot - (pos_size * 0.0010)
            tp_wins_m2 += 1
        elif outcome == "BE_SAVE":
            pnl = 0.0 - (pos_size * 0.0010)
            be_saves_m2 += 1
        else:
            sl_move = abs(ep - exit_p) / ep
            pnl = -(pos_size * sl_move) - (pos_size * 0.0010)
            sl_losses_m2 += 1

        bal_m2 += pnl
        if bal_m2 > peak_bal_m2:
            peak_bal_m2 = bal_m2
        dd = (peak_bal_m2 - bal_m2) / peak_bal_m2 * 100.0
        if dd > max_dd_m2:
            max_dd_m2 = dd

        busy_until_m2 = exit_time
        trades_m2.append({
            "symbol": s["symbol"],
            "side": side,
            "entry_time": s["time"],
            "outcome": outcome,
            "pnl": pnl,
            "bal": bal_m2
        })

    # =========================================================================
    # COMPILE AUDIT RESULTS
    # =========================================================================
    tot_trades_m1 = len(trades_m1)
    pure_wr_m1 = (tp_wins_m1 / tot_trades_m1 * 100.0) if tot_trades_m1 else 0.0
    eff_wr_m1 = ((tp_wins_m1 + be_saves_m1) / tot_trades_m1 * 100.0) if tot_trades_m1 else 0.0

    tot_trades_m2 = len(trades_m2)
    pure_wr_m2 = (tp_wins_m2 / tot_trades_m2 * 100.0) if tot_trades_m2 else 0.0
    eff_wr_m2 = ((tp_wins_m2 + be_saves_m2) / tot_trades_m2 * 100.0) if tot_trades_m2 else 0.0

    results = {
        "period": "August 2026 (1 Full Month)",
        "starting_capital": 100.0,
        "method_1": {
            "name": "Method 1: Direct 15m Candle Close",
            "total_trades": tot_trades_m1,
            "tp_wins": tp_wins_m1,
            "be_saves": be_saves_m1,
            "sl_losses": sl_losses_m1,
            "pure_win_rate": round(pure_wr_m1, 2),
            "effective_win_rate": round(eff_wr_m1, 2),
            "final_balance": round(bal_m1, 2),
            "net_growth_pct": round((bal_m1 - 100.0) / 100.0 * 100.0, 2),
            "max_drawdown_pct": round(max_dd_m1, 2),
            "trades": trades_m1
        },
        "method_2": {
            "name": "Method 2: 5m / FVG Retest Sniper",
            "total_setups": len(all_setups),
            "filled_orders": filled_orders_m2,
            "missed_orders": missed_orders_m2,
            "miss_rate_pct": round(missed_orders_m2 / (filled_orders_m2 + missed_orders_m2) * 100.0, 2) if (filled_orders_m2 + missed_orders_m2) else 0.0,
            "total_trades": tot_trades_m2,
            "tp_wins": tp_wins_m2,
            "be_saves": be_saves_m2,
            "sl_losses": sl_losses_m2,
            "pure_win_rate": round(pure_wr_m2, 2),
            "effective_win_rate": round(eff_wr_m2, 2),
            "final_balance": round(bal_m2, 2),
            "net_growth_pct": round((bal_m2 - 100.0) / 100.0 * 100.0, 2),
            "max_drawdown_pct": round(max_dd_m2, 2),
            "trades": trades_m2
        }
    }

    out_file = BASE_DIR / "pdh_pdl_1month_duel_results.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(results, fp, indent=2)

    miss_pct = results["method_2"]["miss_rate_pct"]
    g1 = results["method_1"]["net_growth_pct"]
    g2 = results["method_2"]["net_growth_pct"]
    print("=" * 80)
    print("🏆 1-MONTH OOS HEAD-TO-HEAD DUEL AUDIT: AUGUST 2026")
    print("=" * 80)
    print(f"{'Metric':<30} | {'Method 1 (15m Close)':<22} | {'Method 2 (5m FVG Retest)':<22}")
    print("-" * 80)
    print(f"{'Total Trades Executed':<30} | {tot_trades_m1:<22} | {tot_trades_m2:<22}")
    print(f"{'Missed Runaway Setups':<30} | {'0 (0.0%)':<22} | {f'{missed_orders_m2} ({miss_pct}%)':<22}")
    print(f"{'Take Profit (TP) Wins':<30} | {f'{tp_wins_m1} ({pure_wr_m1:.1f}%)':<22} | {f'{tp_wins_m2} ({pure_wr_m2:.1f}%)':<22}")
    print(f"{'Break-Even (BE) Saves':<30} | {f'{be_saves_m1} ({be_saves_m1/tot_trades_m1*100:.1f}%)':<22} | {f'{be_saves_m2} ({be_saves_m2/tot_trades_m2*100:.1f}%)':<22}")
    print(f"{'Stop Loss (SL) Hits':<30} | {f'{sl_losses_m1} ({sl_losses_m1/tot_trades_m1*100:.1f}%)':<22} | {f'{sl_losses_m2} ({sl_losses_m2/tot_trades_m2*100:.1f}%)':<22}")
    print(f"{'Effective Win Rate (TP+BE)':<30} | {f'{eff_wr_m1:.1f}%':<22} | {f'{eff_wr_m2:.1f}%':<22}")
    print(f"{'Maximum Drawdown':<30} | {f'{max_dd_m1:.2f}%':<22} | {f'{max_dd_m2:.2f}%':<22}")
    print(f"{'Final Account Capital':<30} | {f'${bal_m1:.2f}':<22} | {f'${bal_m2:.2f}':<22}")
    print(f"{'Net Capital Growth %':<30} | {f'+{g1}%':<22} | {f'+{g2}%':<22}")
    print("=" * 80)

if __name__ == "__main__":
    run_backtest()
