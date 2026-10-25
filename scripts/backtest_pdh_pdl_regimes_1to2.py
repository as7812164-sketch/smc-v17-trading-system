import os
import sys
import glob
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# STRATEGY AUDIT: PREVIOUS DAY SUPPORT/RESISTANCE LIQUIDITY SWEEP (1:2 R:R)
# Rules Defined by User:
# 1. Levels: Previous Day High = RESISTANCE, Previous Day Low = SUPPORT
# 2. Sweep Logic:
#    - LONG: Price reaches Day Support (PDL), sweeps below for liquidity,
#            then closes back ABOVE the Support line.
#    - SHORT: Price reaches Day Resistance (PDH), sweeps above for liquidity,
#             then closes back BELOW the Resistance line.
# 3. Execution: Instant entry on candle close.
# 4. Stop Loss: Last liquidity sweep extreme wick (Sweep Low for Long, Sweep High for Short).
# 5. Take Profit: Strict 1:2 Risk-to-Reward.
# 6. Regimes Evaluated:
#    - UPTREND (EMA50 > EMA200 and Price > EMA50)
#    - DOWNTREND (EMA50 < EMA200 and Price < EMA50)
#    - SIDEWAYS (EMA50 and EMA200 within 0.5% or oscillating)
# 7. Universe: Top-20 Binance USDT-M Champions (March 2026 to September 2026, 15m dataset)
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "market_data_cache_15m"

def load_all_data():
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

def run_backtest():
    coins_data = load_all_data()
    print("=" * 95)
    print("🏛️ PREVIOUS DAY SUPPORT/RESISTANCE LIQUIDITY SWEEP AUDIT (1:2 R:R)")
    print("=" * 95)
    print(f"Dataset Scope: Top-20 Champions across 6 Months (March to September 2026)")
    print(f"Target: 1:2 R:R | Stop Loss: Sweep Extreme Wick | Both Sides: LONG & SHORT\n")

    trades = []

    for sym, candles in coins_data.items():
        n = len(candles)
        closes = [c["close"] for c in candles]
        ema50 = compute_ema(closes, 50)
        ema200 = compute_ema(closes, 200)

        daily = group_by_day(candles)
        sorted_days = sorted(daily.keys())

        busy_until = 0

        for d_i in range(1, len(sorted_days)):
            p_day = sorted_days[d_i - 1]
            c_day = sorted_days[d_i]

            p_list = daily[p_day]
            c_list = daily[c_day]

            if len(p_list) < 80 or len(c_list) < 80:
                continue

            pdh = max(c[1]["high"] for c in p_list) # Resistance
            pdl = min(c[1]["low"] for c in p_list)  # Support

            for idx_in_day, (g_idx, c) in enumerate(c_list):
                if c["time"] < busy_until:
                    continue

                c_o = c["open"]
                c_h = c["high"]
                c_l = c["low"]
                c_c = c["close"]
                c_rng = c_h - c_l
                if c_rng <= 0:
                    continue

                regime = classify_market_regime(c_c, ema50[g_idx], ema200[g_idx])

                # -------------------------------------------------------------
                # 1. LONG SETUP: Support (PDL) Sweep & Close Above Support
                # -------------------------------------------------------------
                if c_l < pdl and c_c > pdl:
                    sweep_depth_pct = (pdl - c_l) / pdl * 100.0
                    # Penetration filter: between 0.05% and 4.0%
                    if 0.05 <= sweep_depth_pct <= 4.0:
                        entry_price = c_c
                        sl_price = c_l # Exactly at the lowest liquidity sweep wick
                        risk = entry_price - sl_price
                        if risk > 0:
                            tp_price = entry_price + (risk * 2.0) # 1:2 R:R Target

                            # Simulate outcome forward
                            outcome = None
                            exit_price = entry_price
                            exit_time = c["time"]
                            max_hold = 96 # 24 hours max hold

                            for f_i in range(g_idx + 1, min(g_idx + 1 + max_hold, n)):
                                b = candles[f_i]
                                b_h = b["high"]
                                b_l = b["low"]
                                b_t = b["time"]

                                # Pessimistic SL first
                                if b_l <= sl_price:
                                    outcome = "SL_HIT"
                                    exit_price = sl_price
                                    exit_time = b_t
                                    break
                                elif b_h >= tp_price:
                                    outcome = "TP_HIT"
                                    exit_price = tp_price
                                    exit_time = b_t
                                    break

                            if not outcome:
                                last_c = candles[min(g_idx + max_hold, n - 1)]
                                exit_price = last_c["close"]
                                exit_time = last_c["time"]
                                pnl = (exit_price - entry_price) / risk
                                outcome = "TP_HIT" if pnl >= 1.0 else ("SL_HIT" if pnl <= -0.5 else "TIMEOUT")

                            busy_until = exit_time
                            pnl_r = 2.0 if outcome == "TP_HIT" else (-1.0 if outcome == "SL_HIT" else 0.0)

                            trades.append({
                                "symbol": sym,
                                "side": "LONG",
                                "regime": regime,
                                "entry_time": c["time"],
                                "exit_time": exit_time,
                                "entry_price": entry_price,
                                "sl_price": sl_price,
                                "tp_price": tp_price,
                                "outcome": outcome,
                                "pnl_r": pnl_r
                            })
                            continue

                # -------------------------------------------------------------
                # 2. SHORT SETUP: Resistance (PDH) Sweep & Close Below Resistance
                # -------------------------------------------------------------
                if c_h > pdh and c_c < pdh:
                    sweep_depth_pct = (c_h - pdh) / pdh * 100.0
                    if 0.05 <= sweep_depth_pct <= 4.0:
                        entry_price = c_c
                        sl_price = c_h # Exactly at the highest liquidity sweep wick
                        risk = sl_price - entry_price
                        if risk > 0:
                            tp_price = entry_price - (risk * 2.0) # 1:2 R:R Target

                            outcome = None
                            exit_price = entry_price
                            exit_time = c["time"]
                            max_hold = 96

                            for f_i in range(g_idx + 1, min(g_idx + 1 + max_hold, n)):
                                b = candles[f_i]
                                b_h = b["high"]
                                b_l = b["low"]
                                b_t = b["time"]

                                if b_h >= sl_price:
                                    outcome = "SL_HIT"
                                    exit_price = sl_price
                                    exit_time = b_t
                                    break
                                elif b_l <= tp_price:
                                    outcome = "TP_HIT"
                                    exit_price = tp_price
                                    exit_time = b_t
                                    break

                            if not outcome:
                                last_c = candles[min(g_idx + max_hold, n - 1)]
                                exit_price = last_c["close"]
                                exit_time = last_c["time"]
                                pnl = (entry_price - exit_price) / risk
                                outcome = "TP_HIT" if pnl >= 1.0 else ("SL_HIT" if pnl <= -0.5 else "TIMEOUT")

                            busy_until = exit_time
                            pnl_r = 2.0 if outcome == "TP_HIT" else (-1.0 if outcome == "SL_HIT" else 0.0)

                            trades.append({
                                "symbol": sym,
                                "side": "SHORT",
                                "regime": regime,
                                "entry_time": c["time"],
                                "exit_time": exit_time,
                                "entry_price": entry_price,
                                "sl_price": sl_price,
                                "tp_price": tp_price,
                                "outcome": outcome,
                                "pnl_r": pnl_r
                            })
                            continue

    print(f"Total Trades Harvested Across All Regimes: {len(trades)}\n")

    # -------------------------------------------------------------------------
    # ANALYSIS: BY REGIME & BY SIDE
    # -------------------------------------------------------------------------
    def report_table(t_list, title):
        total = len(t_list)
        if total == 0:
            print(f"{title}: No trades found.")
            return {}
        tp = sum(1 for x in t_list if x["outcome"] == "TP_HIT")
        sl = sum(1 for x in t_list if x["outcome"] == "SL_HIT")
        to = sum(1 for x in t_list if x["outcome"] == "TIMEOUT")
        wr = (tp / (tp + sl) * 100.0) if (tp + sl) > 0 else 0.0
        pure_acc = (tp / total * 100.0)
        net_r = sum(x["pnl_r"] for x in t_list)

        print(f"{title:<35} | Trades: {total:<5} | TP (1:2): {tp:<4} | SL: {sl:<4} | Acc (Win%): {wr:5.1f}% | Net (R): {net_r:+7.1f} R")
        return {"total": total, "tp": tp, "sl": sl, "win_rate": wr, "net_r": net_r}

    print("=" * 95)
    print("📊 1. PERFORMANCE BY MARKET REGIME (UPTREND vs DOWNTREND vs SIDEWAYS)")
    print("=" * 95)
    print(f"{'MARKET REGIME':<35} | {'TRADES':<12} | {'TP (1:2)':<10} | {'SL':<6} | {'ACCURACY':<11} | {'NET PROFIT'}")
    print("-" * 95)
    res_uptrend = report_table([t for t in trades if t["regime"] == "UPTREND"], "UPTREND (Bullish Market)")
    res_downtrend = report_table([t for t in trades if t["regime"] == "DOWNTREND"], "DOWNTREND (Bearish Market)")
    res_sideways = report_table([t for t in trades if t["regime"] == "SIDEWAYS"], "SIDEWAYS (Ranging Market)")
    print("-" * 95)
    res_all = report_table(trades, "TOTAL OVERALL (ALL REGIMES)")
    print("=" * 95 + "\n")

    print("=" * 95)
    print("🎯 2. PERFORMANCE BY TRADE SIDE (LONG vs SHORT)")
    print("=" * 95)
    print(f"{'TRADE SIDE & REGIME':<35} | {'TRADES':<12} | {'TP (1:2)':<10} | {'SL':<6} | {'ACCURACY':<11} | {'NET PROFIT'}")
    print("-" * 95)
    report_table([t for t in trades if t["side"] == "LONG"], "ALL LONGS (PDL Support Sweeps)")
    report_table([t for t in trades if t["side"] == "LONG" and t["regime"] == "UPTREND"], "  • LONGS in UPTREND")
    report_table([t for t in trades if t["side"] == "LONG" and t["regime"] == "SIDEWAYS"], "  • LONGS in SIDEWAYS")
    report_table([t for t in trades if t["side"] == "LONG" and t["regime"] == "DOWNTREND"], "  • LONGS in DOWNTREND")
    print("-" * 95)
    report_table([t for t in trades if t["side"] == "SHORT"], "ALL SHORTS (PDH Resistance Sweeps)")
    report_table([t for t in trades if t["side"] == "SHORT" and t["regime"] == "DOWNTREND"], "  • SHORTS in DOWNTREND")
    report_table([t for t in trades if t["side"] == "SHORT" and t["regime"] == "SIDEWAYS"], "  • SHORTS in SIDEWAYS")
    report_table([t for t in trades if t["side"] == "SHORT" and t["regime"] == "UPTREND"], "  • SHORTS in UPTREND")
    print("=" * 95 + "\n")

    # Save to json report
    out = {
        "strategy": "PREVIOUS_DAY_SUPPORT_RESISTANCE_SWEEP_1TO2",
        "total_trades": len(trades),
        "uptrend": res_uptrend,
        "downtrend": res_downtrend,
        "sideways": res_sideways,
        "overall": res_all
    }
    with open("pdh_pdl_regimes_1to2_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    run_backtest()
