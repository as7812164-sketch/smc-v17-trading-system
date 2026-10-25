import os
import sys
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "historical_data_2year")
CANDLE_CACHE = {}

def load_candles(sym, interval):
    key = f"{sym}_{interval}"
    if key in CANDLE_CACHE:
        return CANDLE_CACHE[key]
    fpath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        c["volume"] = float(c.get("volume", 0.0))
    CANDLE_CACHE[key] = data
    return data

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_1h = load_candles("BTCUSDT", "1h")
    return {c["time"]: c for c in btc_4h}, {c["time"]: c for c in btc_1h}

def harvest_real_trades():
    """Extracts all sequential executed trades from real candle data using Hermes 3.0 Model 2A rules."""
    btc_map_4h, _ = build_btc_map()
    raw_setups = []

    for tf in ["4h", "1h"]:
        max_tap_window = 28
        max_hold = 36 if tf == "4h" else 48

        for sym in TOP_22_CHAMPIONS:
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < 40:
                continue

            for i in range(20, n - 2):
                # LONG
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    mt = (dec_top + dec_bot) / 2.0
                                    tp = mt * 1.030
                                    soft_sl = mt * (1.0 - 0.015)
                                    hard_sl = mt * (1.0 - 0.030)
                                    be_trigger = mt * (1.0 + 0.015)

                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        t_l, t_h, t_o, t_c = tap_c["low"], tap_c["high"], tap_c["open"], tap_c["close"]
                                        if t_l <= mt * 1.002 and t_c >= mt * 0.995:
                                            c_range = t_h - t_l
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(t_o, t_c) - t_l
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                            if swept and w_ratio >= 0.18:
                                                btc_c = btc_map_4h.get(tap_c["time"])
                                                btc_ok = True
                                                if btc_c and btc_c["open"] > 0:
                                                    drop = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                                                    if drop < -0.040:
                                                        btc_ok = False
                                                if btc_ok:
                                                    raw_setups.append({
                                                        "sym": sym, "tf": tf, "side": "LONG", "time": tap_c["time"],
                                                        "tap_idx": t, "mt": mt, "tp": tp, "soft_sl": soft_sl,
                                                        "hard_sl": hard_sl, "be_trigger": be_trigger, "max_hold": max_hold
                                                    })
                                            break

                # SHORT
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    mt = (dec_top + dec_bot) / 2.0
                                    tp = mt * (1.0 - 0.030)
                                    soft_sl = mt * (1.0 + 0.015)
                                    hard_sl = mt * (1.0 + 0.030)
                                    be_trigger = mt * (1.0 - 0.015)

                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        t_l, t_h, t_o, t_c = tap_c["low"], tap_c["high"], tap_c["open"], tap_c["close"]
                                        if t_h >= mt * 0.998 and t_c <= mt * 1.005:
                                            c_range = t_h - t_l
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = t_h - max(t_o, t_c)
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                            if swept and w_ratio >= 0.18:
                                                btc_c = btc_map_4h.get(tap_c["time"])
                                                btc_ok = True
                                                if btc_c and btc_c["open"] > 0:
                                                    drop_b = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                                                    if drop_b < -0.040:
                                                        btc_ok = False
                                                if btc_ok:
                                                    raw_setups.append({
                                                        "sym": sym, "tf": tf, "side": "SHORT", "time": tap_c["time"],
                                                        "tap_idx": t, "mt": mt, "tp": tp, "soft_sl": soft_sl,
                                                        "hard_sl": hard_sl, "be_trigger": be_trigger, "max_hold": max_hold
                                                    })
                                            break

    raw_setups.sort(key=lambda s: s["time"])
    print(f"Total raw setups found across 2 years: {len(raw_setups)}")

    # Sequential trade resolution
    executed_trades = []
    busy_until = 0
    fee_rate = 0.0010  # 0.10% taker fee round-trip

    for s in raw_setups:
        if s["time"] < busy_until:
            continue

        sym = s["sym"]
        tf = s["tf"]
        side = s["side"]
        candles = load_candles(sym, tf)
        n = len(candles)
        t = s["tap_idx"]

        entry_price = s["mt"]
        tp_price = s["tp"]
        soft_sl_price = s["soft_sl"]
        hard_sl_price = s["hard_sl"]
        be_trigger_price = s["be_trigger"]

        be_activated = False
        outcome = None
        exit_price = entry_price
        exit_time = s["time"]

        for bar_idx in range(t + 1, min(t + s["max_hold"] + 1, n)):
            c = candles[bar_idx]
            bar_time = c["time"]

            if side == "LONG":
                if not be_activated and c["high"] >= be_trigger_price:
                    be_activated = True
                if c["low"] <= hard_sl_price:
                    outcome = "HARD_SL"; exit_price = hard_sl_price; exit_time = bar_time; break
                if c["high"] >= tp_price:
                    outcome = "TP_HIT"; exit_price = tp_price; exit_time = bar_time; break
                if be_activated and c["low"] <= entry_price:
                    outcome = "BE_SAVE"; exit_price = entry_price; exit_time = bar_time; break
                if not be_activated and c["low"] <= soft_sl_price:
                    if c["close"] <= soft_sl_price:
                        outcome = "SOFT_SL"; exit_price = c["close"]; exit_time = bar_time; break
            else:
                if not be_activated and c["low"] <= be_trigger_price:
                    be_activated = True
                if c["high"] >= hard_sl_price:
                    outcome = "HARD_SL"; exit_price = hard_sl_price; exit_time = bar_time; break
                if c["low"] <= tp_price:
                    outcome = "TP_HIT"; exit_price = tp_price; exit_time = bar_time; break
                if be_activated and c["high"] >= entry_price:
                    outcome = "BE_SAVE"; exit_price = entry_price; exit_time = bar_time; break
                if not be_activated and c["high"] >= soft_sl_price:
                    if c["close"] >= soft_sl_price:
                        outcome = "SOFT_SL"; exit_price = c["close"]; exit_time = bar_time; break

        if not outcome:
            last_c = candles[min(t + s["max_hold"], n - 1)]
            exit_price = last_c["close"]
            exit_time = last_c["time"]
            if side == "LONG":
                outcome = "TP_HIT" if exit_price > entry_price else ("BE_SAVE" if be_activated else "SOFT_SL")
            else:
                outcome = "TP_HIT" if exit_price < entry_price else ("BE_SAVE" if be_activated else "SOFT_SL")

        busy_until = exit_time

        if side == "LONG":
            raw_move = (exit_price - entry_price) / entry_price
        else:
            raw_move = (entry_price - exit_price) / entry_price

        net_move = raw_move - fee_rate
        roe_pct = net_move * 500.0  # 5x leverage * 100%

        trade_dt = datetime.fromtimestamp(s["time"] / 1000, tz=IST)
        executed_trades.append({
            "num": len(executed_trades) + 1,
            "sym": sym, "tf": tf, "side": side, "time": s["time"],
            "date_str": trade_dt.strftime("%Y-%m-%d %H:%M"),
            "entry": round(entry_price, 5), "exit": round(exit_price, 5),
            "outcome": outcome, "roe_pct": round(roe_pct, 2), "duration_hours": (exit_time - s["time"]) / 3600000.0
        })

    print(f"Total sequentially executed trades: {len(executed_trades)}")
    return executed_trades

def run_simulation():
    trades = harvest_real_trades()
    if not trades:
        print("No trades harvested!")
        return

    TARGET_1CR_INR_USDT = 115000.0  # ₹1 Crore INR ≈ $115,000 USDT (@ ₹87-89/USDT)
    TARGET_1CR_USDT = 10000000.0   # 1 Crore USDT ($10M)

    # =========================================================================
    # MODEL 1: USER'S "10% STEP-DOUBLE MILESTONE" COMPOUNDING
    # Start: $500. Margin = 10% of $500 ($50) until 2x ($1,000).
    # Then margin = 10% of $1,000 ($100) until 2x ($2,000).
    # Then margin = 10% of $2,000 ($200) until 2x ($4,000), etc.
    # =========================================================================
    print("\n" + "=" * 90)
    print("🚀 RUNNING SIMULATION: USER'S 10% STEP-DOUBLE MILESTONE MODEL vs RAPID COMPOUNDING")
    print("=" * 90)

    def simulate_model_1(step_down_on_dd=False):
        capital = 500.0
        peak = capital
        max_dd = 0.0
        tier_base = 500.0
        tier_margin = 50.0  # 10% of base
        tier_target = 1000.0

        milestones_reached = []
        trade_log = []
        target_hit_trade = None
        target_hit_time_days = None

        # Repeat trade sequence to simulate multi-year journey until 1 Crore
        loop_count = 0
        current_trade_idx = 0
        total_executed = 0
        start_time_ms = trades[0]["time"]

        while capital < TARGET_1CR_INR_USDT and loop_count < 15:
            for t in trades:
                total_executed += 1
                margin = tier_margin
                # PnL on margin at 5x leverage
                pnl = margin * (t["roe_pct"] / 100.0)
                capital += pnl

                if capital < 10.0:
                    capital = 10.0 # Floor guard

                if capital > peak:
                    peak = capital
                dd = (peak - capital) / peak * 100.0
                if dd > max_dd:
                    max_dd = dd

                # Check if Milestone Doubled!
                if capital >= tier_target:
                    old_base = tier_base
                    old_margin = tier_margin
                    milestone_trade_num = total_executed
                    milestone_days = round((t["time"] - start_time_ms) / (86400 * 1000) + (loop_count * 365), 1)

                    milestones_reached.append({
                        "stage": len(milestones_reached) + 1,
                        "from_cap": old_base,
                        "to_cap": tier_target,
                        "capital_reached": round(capital, 2),
                        "margin_used": old_margin,
                        "trade_num": milestone_trade_num,
                        "days_elapsed": milestone_days
                    })

                    tier_base = tier_target
                    tier_margin = tier_base * 0.10 # 10% of new doubled base
                    tier_target = tier_base * 2.0

                elif step_down_on_dd and capital < tier_base:
                    # Drop back to previous tier if drawdown breaches base
                    if tier_base > 500.0:
                        tier_target = tier_base
                        tier_base = tier_base / 2.0
                        tier_margin = tier_base * 0.10

                if capital >= TARGET_1CR_INR_USDT and target_hit_trade is None:
                    target_hit_trade = total_executed
                    target_hit_time_days = round((t["time"] - start_time_ms) / (86400 * 1000) + (loop_count * 365), 1)
                    break

            loop_count += 1

        return {
            "name": f"Model 1: Step-Double 10% ({'Dynamic Step-Down' if step_down_on_dd else 'Ratchet Lock'})",
            "final_capital": capital,
            "max_dd_pct": round(max_dd, 2),
            "trades_to_1cr": target_hit_trade,
            "days_to_1cr": target_hit_time_days,
            "years_to_1cr": round(target_hit_time_days / 365.25, 2) if target_hit_time_days else None,
            "milestones": milestones_reached
        }

    # =========================================================================
    # MODEL 2: RAPID CONTINUOUS 10% COMPOUNDING (Every Trade Compounds)
    # Start: $500. Every trade uses margin = 10% of LIVE capital.
    # =========================================================================
    def simulate_model_2():
        capital = 500.0
        peak = capital
        max_dd = 0.0

        loop_count = 0
        total_executed = 0
        start_time_ms = trades[0]["time"]
        target_hit_trade = None
        target_hit_time_days = None
        milestones = []
        next_double = 1000.0

        while capital < TARGET_1CR_INR_USDT and loop_count < 15:
            for t in trades:
                total_executed += 1
                margin = capital * 0.10 # Exact 10% of live equity
                pnl = margin * (t["roe_pct"] / 100.0)
                capital += pnl

                if capital < 10.0:
                    capital = 10.0

                if capital > peak:
                    peak = capital
                dd = (peak - capital) / peak * 100.0
                if dd > max_dd:
                    max_dd = dd

                if capital >= next_double and next_double <= TARGET_1CR_INR_USDT:
                    milestones.append({
                        "stage": len(milestones) + 1,
                        "milestone": next_double,
                        "capital_reached": round(capital, 2),
                        "trade_num": total_executed,
                        "days_elapsed": round((t["time"] - start_time_ms) / (86400 * 1000) + (loop_count * 365), 1)
                    })
                    next_double *= 2.0

                if capital >= TARGET_1CR_INR_USDT and target_hit_trade is None:
                    target_hit_trade = total_executed
                    target_hit_time_days = round((t["time"] - start_time_ms) / (86400 * 1000) + (loop_count * 365), 1)
                    break
            loop_count += 1

        return {
            "name": "Model 2: Rapid Continuous 10% Compounding",
            "final_capital": capital,
            "max_dd_pct": round(max_dd, 2),
            "trades_to_1cr": target_hit_trade,
            "days_to_1cr": target_hit_time_days,
            "years_to_1cr": round(target_hit_time_days / 365.25, 2) if target_hit_time_days else None,
            "milestones": milestones
        }

    # =========================================================================
    # MODEL 3: DECA COMPOUNDING MATRIX (10 Isolated Sections @ $50 each)
    # Start: $500 ($50 x 10). Each section compounds independently.
    # =========================================================================
    def simulate_model_3():
        sections = [50.0] * 10
        max_dd = 0.0
        peak = 500.0

        loop_count = 0
        total_executed = 0
        start_time_ms = trades[0]["time"]
        target_hit_trade = None
        target_hit_time_days = None

        while sum(sections) < TARGET_1CR_INR_USDT and loop_count < 15:
            for t in trades:
                total_executed += 1
                sec_idx = total_executed % 10
                sec_bal = sections[sec_idx]

                # Full section compounding at 5x leverage
                pnl = sec_bal * (t["roe_pct"] / 100.0)
                sections[sec_idx] += pnl
                if sections[sec_idx] < 2.0:
                    sections[sec_idx] = 2.0

                tot_equity = sum(sections)
                if tot_equity > peak:
                    peak = tot_equity
                dd = (peak - tot_equity) / peak * 100.0
                if dd > max_dd:
                    max_dd = dd

                if tot_equity >= TARGET_1CR_INR_USDT and target_hit_trade is None:
                    target_hit_trade = total_executed
                    target_hit_time_days = round((t["time"] - start_time_ms) / (86400 * 1000) + (loop_count * 365), 1)
                    break
            loop_count += 1

        return {
            "name": "Model 3: Deca Compounding Matrix (10 Isolated Slots)",
            "final_capital": sum(sections),
            "max_dd_pct": round(max_dd, 2),
            "trades_to_1cr": target_hit_trade,
            "days_to_1cr": target_hit_time_days,
            "years_to_1cr": round(target_hit_time_days / 365.25, 2) if target_hit_time_days else None
        }

    res_user_ratchet = simulate_model_1(step_down_on_dd=False)
    res_user_dynamic = simulate_model_1(step_down_on_dd=True)
    res_continuous = simulate_model_2()
    res_deca = simulate_model_3()

    print("\n--- RESULTS SUMMARY ---")
    print(f"Goal: ₹1 Crore INR = ${TARGET_1CR_INR_USDT:,.2f} USDT starting from $500.00 USDT\n")

    for r in [res_user_ratchet, res_user_dynamic, res_continuous, res_deca]:
        print(f"▶ {r['name']}")
        print(f"   Trades to ₹1 Crore : {r['trades_to_1cr']} trades")
        print(f"   Time to ₹1 Crore   : {r['days_to_1cr']} days ({r['years_to_1cr']} years)")
        print(f"   Max Drawdown %     : {r['max_dd_pct']}%")
        print()

    # Save detailed comparison JSON
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compounding_duel_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "target_inr_usdt": TARGET_1CR_INR_USDT,
            "user_model_ratchet": res_user_ratchet,
            "user_model_dynamic": res_user_dynamic,
            "continuous_compounding": res_continuous,
            "deca_compounding": res_deca
        }, f, indent=2)
    print(f"Detailed output saved to: {out_file}")

if __name__ == "__main__":
    run_simulation()
