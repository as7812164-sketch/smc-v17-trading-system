import os
import sys
import glob
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# PDH / PDL LIQUIDITY SWEEP AUDIT WITH 7% MOVE REQUIREMENT
# Evaluates:
#   Filter 1: Previous Day Candle Move >= 7% ((PDH - PDL) / PDL >= 0.070)
#   Filter 2: Sweep Leg / Wave Move >= 7% (Impulse leading into sweep >= 7%)
# Across:
#   Option A: Trend-Aligned (Long PDL in Bull, Short PDH in Bear)
#   Option B: Both Sides (Trade both PDH & PDL)
# Across:
#   Method 1: Direct 15m Candle Close
#   Method 2: 5m / 50% Discount Mitigation Retest
# Targets:
#   1:2 Risk-to-Reward Ratio (and 1:3 comparison)
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

def simulate_trade(setup, mode="METHOD_1", rr_ratio=2.0, max_hold=96):
    """
    mode == 'METHOD_1': Enter on next bar open at candle close
    mode == 'METHOD_2': Limit order at 50% retracement of sweep candle
    rr_ratio: 2.0 (1:2) or 3.0 (1:3)
    """
    candles = setup["candles"]
    sweep_idx = setup["sweep_idx"]
    side = setup["side"]
    c = candles[sweep_idx]
    n = len(candles)

    c_h = c["high"]
    c_l = c["low"]
    c_c = c["close"]

    # Stop loss placement
    buffer_pct = 0.0015 # 0.15% round buffer beyond wick
    if side == "LONG":
        sl_price = c_l * (1.0 - buffer_pct)
    else:
        sl_price = c_h * (1.0 + buffer_pct)

    if mode == "METHOD_1":
        entry_price = c_c
        entry_idx = sweep_idx + 1
        risk = abs(entry_price - sl_price)
        if risk <= 0:
            return None
        tp_price = entry_price + (risk * rr_ratio) if side == "LONG" else entry_price - (risk * rr_ratio)
        be_price = entry_price + risk if side == "LONG" else entry_price - risk
    elif mode == "METHOD_2":
        # 50% discount limit order
        if side == "LONG":
            entry_price = c_l + (c_c - c_l) * 0.50
        else:
            entry_price = c_h - (c_h - c_c) * 0.50

        risk = abs(entry_price - sl_price)
        if risk <= 0:
            return None
        tp_price = entry_price + (risk * rr_ratio) if side == "LONG" else entry_price - (risk * rr_ratio)
        be_price = entry_price + risk if side == "LONG" else entry_price - risk

        # Look for fill in subsequent 8 bars (2 hours)
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
            return {"outcome": "MISSED", "pnl_pct": 0.0, "pnl_r": 0.0}

    # Evaluate outcome
    be_active = False
    outcome = "TIMEOUT"
    pnl_r = 0.0

    for idx in range(entry_idx, min(entry_idx + max_hold, n)):
        b = candles[idx]
        b_h = b["high"]
        b_l = b["low"]
        b_c = b["close"]

        if side == "LONG":
            # Check BE trigger (1:1 move)
            if not be_active and b_h >= be_price:
                be_active = True

            # Check SL
            if b_l <= sl_price:
                outcome = "SL_HIT"
                pnl_r = -1.0
                break

            # Check TP
            if b_h >= tp_price:
                outcome = "TP_HIT"
                pnl_r = rr_ratio
                break

            # Check BE exit
            if be_active and b_l <= entry_price:
                outcome = "BE_SAVE"
                pnl_r = 0.0
                break
        else: # SHORT
            if not be_active and b_l <= be_price:
                be_active = True

            if b_h >= sl_price:
                outcome = "SL_HIT"
                pnl_r = -1.0
                break

            if b_l <= tp_price:
                outcome = "TP_HIT"
                pnl_r = rr_ratio
                break

            if be_active and b_h >= entry_price:
                outcome = "BE_SAVE"
                pnl_r = 0.0
                break

    if outcome == "TIMEOUT":
        # Closed at timeout bar
        exit_c = candles[min(entry_idx + max_hold - 1, n - 1)]["close"]
        if side == "LONG":
            pnl_r = (exit_c - entry_price) / risk
        else:
            pnl_r = (entry_price - exit_c) / risk
        outcome = "TP_HIT" if pnl_r > 0.5 else ("SL_HIT" if pnl_r < -0.5 else "BE_SAVE")

    return {
        "symbol": setup["symbol"],
        "side": side,
        "entry_price": entry_price,
        "sl_price": sl_price,
        "tp_price": tp_price,
        "outcome": outcome,
        "pnl_r": pnl_r,
        "time": candles[entry_idx]["time"]
    }

def run_full_suite():
    print("==========================================================================================")
    print("📊 PDH / PDL LIQUIDITY SWEEP AUDIT WITH 7% MOVE REQUIREMENT")
    print("==========================================================================================")
    coins_data = load_data()
    print(f"Loaded {len(coins_data)} coins with complete 15m candle data.\n")

    setups_day_7pct = [] # Previous Day Range >= 7%
    setups_sweep_leg_7pct = [] # Pre-sweep wave move >= 7%
    setups_candle_7pct = [] # Sweep Candle Range >= 7%

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

            # Scan intraday candles
            for idx_in_day, (g_idx, c) in enumerate(c_list):
                c_o = c["open"]
                c_h = c["high"]
                c_l = c["low"]
                c_c = c["close"]
                c_rng = c_h - c_l
                if c_rng <= 0:
                    continue

                # Pre-sweep wave move (past 16 bars = 4 hours)
                lookback_bars = c_list[max(0, idx_in_day - 16):idx_in_day + 1]
                wave_high = max(x[1]["high"] for x in lookback_bars)
                wave_low = min(x[1]["low"] for x in lookback_bars)
                wave_move_pct = (wave_high - wave_low) / wave_low if wave_low > 0 else 0
                candle_range_pct = (c_h - c_l) / c_l if c_l > 0 else 0

                # Check Trend: EMA50 vs EMA200
                is_bullish = ema50[g_idx] > ema200[g_idx]
                is_bearish = ema50[g_idx] < ema200[g_idx]

                # -------------------------------------------------------------
                # 1. BULLISH PDL SWEEP (LONG)
                # -------------------------------------------------------------
                if c_l < pdl and c_c > pdl:
                    sweep_depth = (pdl - c_l) / pdl
                    if 0.0010 <= sweep_depth <= 0.040:
                        lower_wick = min(c_o, c_c) - c_l
                        wick_ratio = lower_wick / c_rng
                        if wick_ratio >= 0.25: # V-shape rejection wick >= 25%
                            s_data = {
                                "symbol": sym,
                                "side": "LONG",
                                "candles": candles,
                                "sweep_idx": g_idx,
                                "is_trend_aligned": is_bullish, # Bullish for Long
                                "pd_range_pct": pd_range_pct,
                                "wave_move_pct": wave_move_pct,
                                "candle_range_pct": candle_range_pct
                            }
                            if pd_range_pct >= 0.070:
                                setups_day_7pct.append(s_data)
                            if wave_move_pct >= 0.070:
                                setups_sweep_leg_7pct.append(s_data)
                            if candle_range_pct >= 0.070:
                                setups_candle_7pct.append(s_data)

                # -------------------------------------------------------------
                # 2. BEARISH PDH SWEEP (SHORT)
                # -------------------------------------------------------------
                if c_h > pdh and c_c < pdh:
                    sweep_depth = (c_h - pdh) / pdh
                    if 0.0010 <= sweep_depth <= 0.040:
                        upper_wick = c_h - max(c_o, c_c)
                        wick_ratio = upper_wick / c_rng
                        if wick_ratio >= 0.25: # Rejection wick >= 25%
                            s_data = {
                                "symbol": sym,
                                "side": "SHORT",
                                "candles": candles,
                                "sweep_idx": g_idx,
                                "is_trend_aligned": is_bearish, # Bearish for Short
                                "pd_range_pct": pd_range_pct,
                                "wave_move_pct": wave_move_pct,
                                "candle_range_pct": candle_range_pct
                            }
                            if pd_range_pct >= 0.070:
                                setups_day_7pct.append(s_data)
                            if wave_move_pct >= 0.070:
                                setups_sweep_leg_7pct.append(s_data)
                            if candle_range_pct >= 0.070:
                                setups_candle_7pct.append(s_data)

    print(f"Qualified Setups with Previous Day Range >= 7%: {len(setups_day_7pct)}")
    print(f"Qualified Setups with Pre-Sweep Wave Move >= 7%: {len(setups_sweep_leg_7pct)}")
    print(f"Qualified Setups with Sweep Candle Range >= 7%:   {len(setups_candle_7pct)}\n")

    # Helper function to run evaluation
    def evaluate(setups, name, rr=2.0):
        print(f"==========================================================================================")
        print(f"📌 {name} (TARGET 1:{int(rr)} R:R)")
        print(f"==========================================================================================")
        print(f"{'CONFIGURATION':<38} | {'TRADES':<6} | {'TP':<4} | {'BE':<4} | {'SL':<4} | {'WIN%':<7} | {'NON-LOSS%':<9} | {'EXP (R)'}")
        print("-" * 88)

        configs = [
            ("Option A (Trend-Aligned) - Method 1", [s for s in setups if s["is_trend_aligned"]], "METHOD_1"),
            ("Option A (Trend-Aligned) - Method 2", [s for s in setups if s["is_trend_aligned"]], "METHOD_2"),
            ("Option B (Both Sides)   - Method 1", setups, "METHOD_1"),
            ("Option B (Both Sides)   - Method 2", setups, "METHOD_2"),
        ]

        results = {}
        for cfg_name, s_list, mode in configs:
            executed = []
            busy_until = {}
            for s in sorted(s_list, key=lambda x: x["candles"][x["sweep_idx"]]["time"]):
                sym = s["symbol"]
                t = s["candles"][s["sweep_idx"]]["time"]
                if busy_until.get(sym, 0) > t:
                    continue
                res = simulate_trade(s, mode=mode, rr_ratio=rr)
                if res and res["outcome"] != "MISSED":
                    executed.append(res)
                    busy_until[sym] = res["time"] + (4 * 3600 * 1000)

            total = len(executed)
            tp = sum(1 for x in executed if x["outcome"] == "TP_HIT")
            be = sum(1 for x in executed if x["outcome"] == "BE_SAVE")
            sl = sum(1 for x in executed if x["outcome"] == "SL_HIT")
            pure_wr = (tp / (tp + sl) * 100.0) if (tp + sl) > 0 else 0.0
            non_loss = ((tp + be) / total * 100.0) if total > 0 else 0.0
            net_r = sum(x["pnl_r"] for x in executed)

            print(f"{cfg_name:<38} | {total:<6} | {tp:<4} | {be:<4} | {sl:<4} | {pure_wr:5.1f}% | {non_loss:6.1f}%    | {net_r:+6.1f}R")
            results[cfg_name] = {"total": total, "tp": tp, "be": be, "sl": sl, "win_rate": pure_wr, "non_loss": non_loss, "net_r": net_r}
        print("-" * 88 + "\n")
        return results

    # Evaluate Filter 1: Previous Day Move >= 7%
    res1_1to2 = evaluate(setups_day_7pct, "FILTER 1: PREVIOUS DAY CANDLE MOVE >= 7%", rr=2.0)
    res1_1to3 = evaluate(setups_day_7pct, "FILTER 1: PREVIOUS DAY CANDLE MOVE >= 7%", rr=3.0)

    # Evaluate Filter 2: Pre-Sweep Wave Move >= 7%
    res2_1to2 = evaluate(setups_sweep_leg_7pct, "FILTER 2: PRE-SWEEP IMPULSE WAVE MOVE >= 7%", rr=2.0)
    res2_1to3 = evaluate(setups_sweep_leg_7pct, "FILTER 2: PRE-SWEEP IMPULSE WAVE MOVE >= 7%", rr=3.0)

    # Save to report
    all_res = {
        "filter1_previous_day_7pct": {"1_to_2": res1_1to2, "1_to_3": res1_1to3},
        "filter2_wave_7pct": {"1_to_2": res2_1to2, "1_to_3": res2_1to3}
    }
    with open("pdh_pdl_7pct_move_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(all_res, f, indent=2)

if __name__ == "__main__":
    run_full_suite()
