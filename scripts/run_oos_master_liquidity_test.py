import os
import sys
import glob
import json
import datetime
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# MASTER LIQUIDITY SWEEP: OUT-OF-SAMPLE (OOS) RIGOROUS QUANT AUDIT
# Evaluates:
#   - IN-SAMPLE (IS): March 20, 2026 to July 31, 2026
#   - OUT-OF-SAMPLE (OOS - Primary): August 1, 2026 to September 23, 2026
#   - Dedicated Last Month OOS: September 2026 (Sep 1 to Sep 23, 2026)
#   - Dedicated Prior Month OOS: August 2026 (Aug 1 to Aug 31, 2026)
# Sizing: $500 Starting Capital with:
#   - Model 1: 2% Risk ($10 per trade initial)
#   - Model 2: 10% Margin Compounding (5x leverage)
# Universe: Top-20 Binance USDT-M Champions
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

def simulate_trade(setup, max_hold=120):
    candles = setup["candles"]
    sweep_idx = setup["sweep_idx"]
    side = setup["side"]
    c = candles[sweep_idx]
    n = len(candles)

    c_h = c["high"]
    c_l = c["low"]
    c_c = c["close"]

    # 0.15% Anti-Hunt Buffer beyond extreme wick
    buffer_pct = 0.0015
    if side == "LONG":
        initial_sl = c_l * (1.0 - buffer_pct)
        entry_price = c_l + (c_c - c_l) * 0.50
    else:
        initial_sl = c_h * (1.0 + buffer_pct)
        entry_price = c_h - (c_h - c_c) * 0.50

    # Look for 50% FVG mitigation fill in next 8 bars
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
            max_fav_r = (b_h - entry_price) / risk
            # Stepped Trailing SL Ladder
            if max_fav_r >= 1.0:
                tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
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
            max_fav_r = (entry_price - b_l) / risk
            if max_fav_r >= 1.0:
                tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
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

    trade_dt = datetime.datetime.fromtimestamp(candles[entry_idx]["time"] / 1000.0, tz=datetime.timezone.utc)
    month_str = trade_dt.strftime("%B %Y")

    return {
        "symbol": setup["symbol"],
        "side": side,
        "regime": setup["regime"],
        "entry_price": entry_price,
        "initial_sl": initial_sl,
        "outcome": outcome,
        "pnl_r": realized_r,
        "trailing_tier": current_tier,
        "time": candles[entry_idx]["time"],
        "month": month_str,
        "date_str": trade_dt.strftime("%Y-%m-%d %H:%M")
    }

def run_oos_audit():
    coins_data = load_data()
    print("=" * 100)
    print("🏛️ MASTER LIQUIDITY SWEEP: OUT-OF-SAMPLE (OOS) QUANT AUDIT")
    print("=" * 100)
    print("Universe: Top-20 Binance USDT-M Champions (15m high-resolution dataset)")
    print("Split Protocol: In-Sample (March-July 2026) vs Out-Of-Sample (August-September 2026)\n")

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

                if not is_killzone(c["time"]):
                    continue

                lookback_bars = c_list[max(0, idx_in_day - 16):idx_in_day + 1]
                wave_high = max(x[1]["high"] for x in lookback_bars)
                wave_low = min(x[1]["low"] for x in lookback_bars)
                wave_move_pct = (wave_high - wave_low) / wave_low if wave_low > 0 else 0

                is_vol_anchor = (pd_range_pct >= 0.070) or (wave_move_pct >= 0.070)
                if not is_vol_anchor:
                    continue

                regime = classify_market_regime(c_c, ema50[g_idx], ema200[g_idx])

                # LONG PDL Sweep
                if c_l < pdl and c_c > pdl:
                    sweep_depth = (pdl - c_l) / pdl
                    if 0.0010 <= sweep_depth <= 0.040:
                        lower_wick = min(c_o, c_c) - c_l
                        if (lower_wick / c_rng) >= 0.25:
                            setups.append({
                                "symbol": sym,
                                "side": "LONG",
                                "candles": candles,
                                "sweep_idx": g_idx,
                                "regime": regime,
                                "time": c["time"]
                            })

                # SHORT PDH Sweep
                if c_h > pdh and c_c < pdh:
                    sweep_depth = (c_h - pdh) / pdh
                    if 0.0010 <= sweep_depth <= 0.040:
                        upper_wick = c_h - max(c_o, c_c)
                        if (upper_wick / c_rng) >= 0.25:
                            setups.append({
                                "symbol": sym,
                                "side": "SHORT",
                                "candles": candles,
                                "sweep_idx": g_idx,
                                "regime": regime,
                                "time": c["time"]
                            })

    # Execute simulation chronologically
    executed_all = []
    busy_until = {}
    for s in sorted(setups, key=lambda x: x["time"]):
        sym = s["symbol"]
        t = s["time"]
        if busy_until.get(sym, 0) > t:
            continue
        res = simulate_trade(s)
        if res and res["outcome"] != "MISSED":
            executed_all.append(res)
            busy_until[sym] = res["time"] + (4 * 3600 * 1000)

    # Split into IS and OOS
    # In-Sample: March 20, 2026 to July 31, 2026
    # Out-Of-Sample: August 1, 2026 to September 23, 2026
    oos_start_ts = int(datetime.datetime(2026, 8, 1, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
    sep_start_ts = int(datetime.datetime(2026, 9, 1, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)

    trades_is = [t for t in executed_all if t["time"] < oos_start_ts]
    trades_oos = [t for t in executed_all if t["time"] >= oos_start_ts]
    trades_aug = [t for t in executed_all if oos_start_ts <= t["time"] < sep_start_ts]
    trades_sep = [t for t in executed_all if t["time"] >= sep_start_ts]

    # Helper function for metrics
    def calc_metrics(t_list, start_cap=500.0, risk_pct=0.02):
        total = len(t_list)
        if total == 0:
            return {}
        wins = sum(1 for x in t_list if x["pnl_r"] >= 0.5)
        saves = sum(1 for x in t_list if 0.0 <= x["pnl_r"] < 0.5)
        losses = sum(1 for x in t_list if x["pnl_r"] < 0.0)
        pure_wr = (wins / (wins + losses) * 100.0) if (wins + losses) > 0 else 0.0
        green_rate = ((wins + saves) / total * 100.0)
        net_r = sum(x["pnl_r"] for x in t_list)

        # Equity simulation from start_cap ($500)
        # Using 2% risk of initial equity ($10/R)
        bal = start_cap
        peak = start_cap
        max_dd_pct = 0.0
        for x in t_list:
            dollar_pnl = x["pnl_r"] * (start_cap * risk_pct)
            bal += dollar_pnl
            if bal > peak:
                peak = bal
            dd = (peak - bal) / peak * 100.0 if peak > 0 else 0.0
            if dd > max_dd_pct:
                max_dd_pct = dd

        return {
            "total": total,
            "wins": wins,
            "saves": saves,
            "losses": losses,
            "pure_wr": round(pure_wr, 1),
            "green_rate": round(green_rate, 1),
            "net_r": round(net_r, 1),
            "final_bal": round(bal, 2),
            "net_dollar_gain": round(bal - start_cap, 2),
            "growth_pct": round((bal - start_cap) / start_cap * 100.0, 1),
            "max_dd_pct": round(max_dd_pct, 1)
        }

    m_is = calc_metrics(trades_is)
    m_oos = calc_metrics(trades_oos)
    m_aug = calc_metrics(trades_aug)
    m_sep = calc_metrics(trades_sep)
    m_all = calc_metrics(executed_all)

    print("====================================================================================================")
    print("📊 1. IN-SAMPLE (IS) vs OUT-OF-SAMPLE (OOS) COMPARATIVE MATRIX ($500 START)")
    print("====================================================================================================")
    print(f"{'DATASET PERIOD':<30} | {'TRADES':<6} | {'WINS':<4} | {'SAVES':<5} | {'LOSS':<4} | {'WIN%':<6} | {'GREEN%':<7} | {'NET EXP':<9} | {'FINAL BAL':<10} | {'MAX DD'}")
    print("-" * 100)

    def print_row(label, m):
        if not m:
            return
        print(f"{label:<30} | {m['total']:<6} | {m['wins']:<4} | {m['saves']:<5} | {m['losses']:<4} | {m['pure_wr']:5.1f}% | {m['green_rate']:5.1f}%  | {m['net_r']:+6.1f} R   | ${m['final_bal']:<9.2f} | {m['max_dd_pct']:4.1f}%")

    print_row("IN-SAMPLE (Mar - Jul 2026)", m_is)
    print_row("OUT-OF-SAMPLE (Aug - Sep 2026) 🏆", m_oos)
    print_row("  • August 2026 OOS", m_aug)
    print_row("  • September 2026 OOS (Last Mo)", m_sep)
    print("-" * 100)
    print_row("FULL 6-MONTH LIFE CYCLE", m_all)
    print("====================================================================================================\n")

    # Granular Breakdown of Out-Of-Sample (August - September 2026)
    print("====================================================================================================")
    print("🎯 2. OUT-OF-SAMPLE (OOS) DEEP-DIVE: REGIMES & SIDES BREAKDOWN (AUG - SEP 2026)")
    print("====================================================================================================")
    print(f"{'CATEGORY':<35} | {'TRADES':<6} | {'WINS':<4} | {'SAVES':<5} | {'LOSS':<4} | {'WIN%':<6} | {'GREEN%':<7} | {'NET EXP':<9} | {'NET GAIN ($)'}")
    print("-" * 100)

    oos_side_long = [t for t in trades_oos if t["side"] == "LONG"]
    oos_side_short = [t for t in trades_oos if t["side"] == "SHORT"]
    oos_reg_sideways = [t for t in trades_oos if t["regime"] == "SIDEWAYS"]
    oos_reg_down = [t for t in trades_oos if t["regime"] == "DOWNTREND"]
    oos_reg_up = [t for t in trades_oos if t["regime"] == "UPTREND"]

    for lbl, subset in [
        ("OOS SIDEWAYS REGIME (Ranging)", oos_reg_sideways),
        ("OOS DOWNTREND REGIME (Bearish)", oos_reg_down),
        ("OOS UPTREND REGIME (Bullish)", oos_reg_up),
        ("OOS LONGS (Day Support Sweeps)", oos_side_long),
        ("OOS SHORTS (Day Resistance Sweeps)", oos_side_short),
    ]:
        m = calc_metrics(subset)
        if m:
            print(f"{lbl:<35} | {m['total']:<6} | {m['wins']:<4} | {m['saves']:<5} | {m['losses']:<4} | {m['pure_wr']:5.1f}% | {m['green_rate']:5.1f}%  | {m['net_r']:+6.1f} R   | +${m['net_dollar_gain']:.2f}")

    print("=" * 100 + "\n")

    # Monthly Progress in OOS
    monthly_dict = defaultdict(list)
    for t in executed_all:
        monthly_dict[t["month"]].append(t)

    print("====================================================================================================")
    print("📅 3. MONTH-BY-MONTH STABILITY AUDIT (IS & OOS)")
    print("====================================================================================================")
    print(f"{'MONTH':<18} | {'STATUS':<10} | {'TRADES':<6} | {'WINS':<4} | {'SAVES':<5} | {'LOSS':<4} | {'WIN%':<6} | {'GREEN%':<7} | {'NET (R)':<8} | {'PNL ($)'}")
    print("-" * 100)
    for m_str in ["March 2026", "April 2026", "May 2026", "June 2026", "July 2026", "August 2026", "September 2026"]:
        t_sub = monthly_dict.get(m_str, [])
        if not t_sub:
            continue
        status = "OOS 🏆" if ("August" in m_str or "September" in m_str) else "IN-SAMPLE"
        m = calc_metrics(t_sub)
        print(f"{m_str:<18} | {status:<10} | {m['total']:<6} | {m['wins']:<4} | {m['saves']:<5} | {m['losses']:<4} | {m['pure_wr']:5.1f}% | {m['green_rate']:5.1f}%  | {m['net_r']:+6.1f} R | +${m['net_dollar_gain']:.2f}")
    print("=" * 100 + "\n")

    # Save to JSON
    out_oos = {
        "strategy": "MASTER_LIQUIDITY_SWEEP_OOS_AUDIT",
        "in_sample": m_is,
        "out_of_sample": m_oos,
        "august_oos": m_aug,
        "september_oos": m_sep,
        "all_months": m_all
    }
    with open("master_liquidity_oos_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(out_oos, f, indent=2)
    print("Saved audit data to master_liquidity_oos_audit_results.json")

if __name__ == "__main__":
    run_oos_audit()
