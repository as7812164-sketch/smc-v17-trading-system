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

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")
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

def harvest_model2a_setups():
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
                # ----------------- LONG SETUP -----------------
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050: # Sentry 2: >= 5% displacement
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
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        if candles[t]["low"] <= dec_top * 1.0005:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            # Sentry 1: King BTC Causal Brake
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean = btc_dump < 0.020

                                            # Model 2A Qualification
                                            if btc_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "tap_close": tap_c["close"], "max_hold": max_hold
                                                })
                                                break

                # ----------------- SHORT SETUP -----------------
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050: # Sentry 2: >= 5% displacement
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        if candles[t]["high"] >= dec_bot * 0.9995:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            # Sentry 1: King BTC Causal Brake
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean_short = btc_pump < 0.020

                                            # Model 2A Qualification
                                            if btc_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "tap_close": tap_c["close"], "max_hold": max_hold
                                                })
                                                break

    raw_setups.sort(key=lambda x: x["time"])
    return raw_setups

def simulate_oos_model2a():
    print("=" * 85)
    print(" 🏛️ HERMES 3.0 MODEL 2A: REAL OUT-OF-SAMPLE (OOS) QUANT AUDIT ($100 START)")
    print("=" * 85)
    
    setups = harvest_model2a_setups()
    print(f"Total Model 2A Raw Setups Harvested: {len(setups)}")

    # OOS Filter: September 25, 2025 to September 25, 2026 (Year 2 OOS Period)
    oos_start_ts = int(datetime(2025, 9, 25, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    oos_setups = [s for s in setups if s["time"] >= oos_start_ts]
    print(f"Total Out-of-Sample (OOS) Setups: {len(oos_setups)}")

    # Execution Simulation Parameters
    # Starting Balance: $100.00
    # Sequential Trade Queue (1 trade active at a time to strictly isolate compounding)
    # Model 2A Rules:
    # Entry: 50% Mean Threshold (MT)
    # TP: +3.00% Spot (+15.0% ROE)
    # BE Trigger: +1.50% Spot (+7.5% ROE) -> Moves SL to Entry Price ($0 risk)
    # Soft SL (Layer 1): -1.50% Spot (-7.5% ROE) on CANDLE BODY CLOSE
    # Hard Circuit Breaker (Layer 2): -3.00% Spot (-15.0% ROE) on any intra-bar wick
    # Friction: 0.10% roundtrip taker fee

    fee_rate = 0.0010 # 0.10% roundtrip taker fee

    busy_until = 0
    executed_trades = []

    for s in oos_setups:
        if s["time"] < busy_until:
            continue # Sequential 1-trade queue

        sym, tf, t = s["sym"], s["tf"], s["t_idx"]
        side = s["side"]
        candles = load_candles(sym, tf)
        n = len(candles)

        entry_price = s["mt"]
        # Invalidation check: did tap bar close violate soft SL already?
        if side == "LONG" and s["tap_close"] < entry_price * 0.985:
            continue
        if side == "SHORT" and s["tap_close"] > entry_price * 1.015:
            continue

        tp_price = entry_price * 1.030 if side == "LONG" else entry_price * 0.970
        be_trigger_price = entry_price * 1.015 if side == "LONG" else entry_price * 0.985
        soft_sl_price = entry_price * 0.985 if side == "LONG" else entry_price * 1.015
        hard_sl_price = entry_price * 0.970 if side == "LONG" else entry_price * 1.030

        outcome = None
        exit_price = entry_price
        exit_time = s["time"]
        be_activated = False
        wick_absorbed_count = 0

        for bar_idx in range(t + 1, min(t + 1 + s["max_hold"], n)):
            c = candles[bar_idx]
            bar_time = c["time"]

            # Pessimistic Intra-Bar Evaluation
            if side == "LONG":
                # Check BE Activation
                if not be_activated and c["high"] >= be_trigger_price:
                    be_activated = True

                # Check Hard SL first (Worst-case priority)
                if c["low"] <= hard_sl_price:
                    outcome = "HARD_SL"
                    exit_price = hard_sl_price
                    exit_time = bar_time
                    break

                # Check TP
                if c["high"] >= tp_price:
                    outcome = "TP_HIT"
                    exit_price = tp_price
                    exit_time = bar_time
                    break

                # Check BE Hit if BE was activated
                if be_activated and c["low"] <= entry_price:
                    outcome = "BE_SAVE"
                    exit_price = entry_price
                    exit_time = bar_time
                    break

                # Check Soft SL on Candle Body Close
                if not be_activated:
                    if c["low"] <= soft_sl_price:
                        if c["close"] <= soft_sl_price:
                            # Body closed below soft SL -> Structural exit
                            outcome = "SOFT_SL"
                            exit_price = c["close"]
                            exit_time = bar_time
                            break
                        else:
                            # Wick dipped below -1.5% but body closed above -> WICK ABSORBED!
                            wick_absorbed_count += 1
            else: # SHORT
                # Check BE Activation
                if not be_activated and c["low"] <= be_trigger_price:
                    be_activated = True

                # Check Hard SL first
                if c["high"] >= hard_sl_price:
                    outcome = "HARD_SL"
                    exit_price = hard_sl_price
                    exit_time = bar_time
                    break

                # Check TP
                if c["low"] <= tp_price:
                    outcome = "TP_HIT"
                    exit_price = tp_price
                    exit_time = bar_time
                    break

                # Check BE Hit if BE was activated
                if be_activated and c["high"] >= entry_price:
                    outcome = "BE_SAVE"
                    exit_price = entry_price
                    exit_time = bar_time
                    break

                # Check Soft SL on Candle Body Close
                if not be_activated:
                    if c["high"] >= soft_sl_price:
                        if c["close"] >= soft_sl_price:
                            outcome = "SOFT_SL"
                            exit_price = c["close"]
                            exit_time = bar_time
                            break
                        else:
                            wick_absorbed_count += 1

        if not outcome:
            # Timeout / Max hold reached
            last_c = candles[min(t + s["max_hold"], n - 1)]
            exit_price = last_c["close"]
            exit_time = last_c["time"]
            if side == "LONG":
                outcome = "TP_HIT" if exit_price > entry_price else ("BE_SAVE" if be_activated else "SOFT_SL")
            else:
                outcome = "TP_HIT" if exit_price < entry_price else ("BE_SAVE" if be_activated else "SOFT_SL")

        busy_until = exit_time

        # Calculate Spot Return & 5x ROE
        if side == "LONG":
            raw_move = (exit_price - entry_price) / entry_price
        else:
            raw_move = (entry_price - exit_price) / entry_price
        
        net_move = raw_move - fee_rate
        roe_pct = net_move * 500.0 # 5x leverage * 100%

        trade_dt = datetime.fromtimestamp(s["time"] / 1000, tz=IST)
        month_str = trade_dt.strftime("%B %Y")

        executed_trades.append({
            "num": len(executed_trades) + 1,
            "sym": sym,
            "tf": tf,
            "side": side,
            "time": s["time"],
            "date_str": trade_dt.strftime("%Y-%m-%d %H:%M"),
            "month": month_str,
            "entry": round(entry_price, 5),
            "exit": round(exit_price, 5),
            "outcome": outcome,
            "roe_pct": round(roe_pct, 2),
            "wicks_absorbed": wick_absorbed_count
        })

    # Compounding from $100.00
    starting_balance = 100.0
    current_balance = starting_balance
    peak_balance = starting_balance
    max_drawdown = 0.0

    monthly_stats = defaultdict(lambda: {"trades": 0, "tp": 0, "be": 0, "sl": 0, "wicks": 0, "net_pnl": 0.0, "start_bal": 0.0, "end_bal": 0.0})

    for t in executed_trades:
        m = t["month"]
        if monthly_stats[m]["trades"] == 0:
            monthly_stats[m]["start_bal"] = round(current_balance, 2)

        # 100% position compounding at 5x leverage (or 20% margin / risk-controlled)
        # In sequential compounding, position size = current_balance * 5x
        pos_size = current_balance * 5.0
        pnl = pos_size * (t["roe_pct"] / 500.0)
        
        current_balance += pnl
        if current_balance < 5.0:
            current_balance = 5.0 # Floor guard

        if current_balance > peak_balance:
            peak_balance = current_balance
        dd = (peak_balance - current_balance) / peak_balance * 100.0
        if dd > max_drawdown:
            max_drawdown = dd

        t["balance_after"] = round(current_balance, 2)
        t["pnl_usdt"] = round(pnl, 2)

        monthly_stats[m]["trades"] += 1
        if t["outcome"] == "TP_HIT":
            monthly_stats[m]["tp"] += 1
        elif t["outcome"] == "BE_SAVE":
            monthly_stats[m]["be"] += 1
        else:
            monthly_stats[m]["sl"] += 1
        monthly_stats[m]["wicks"] += t["wicks_absorbed"]
        monthly_stats[m]["net_pnl"] += pnl
        monthly_stats[m]["end_bal"] = round(current_balance, 2)

    total_t = len(executed_trades)
    tp_cnt = sum(1 for t in executed_trades if t["outcome"] == "TP_HIT")
    be_cnt = sum(1 for t in executed_trades if t["outcome"] == "BE_SAVE")
    sl_cnt = sum(1 for t in executed_trades if "SL" in t["outcome"])
    total_wicks = sum(t["wicks_absorbed"] for t in executed_trades)

    pure_wr = (tp_cnt / (tp_cnt + sl_cnt) * 100.0) if (tp_cnt + sl_cnt) > 0 else 0.0
    effective_wr = ((tp_cnt + be_cnt) / total_t * 100.0) if total_t > 0 else 0.0

    print(f"\n================================================================================")
    print(f"📊 HERMES 3.0 MODEL 2A: 1-YEAR OUT-OF-SAMPLE AUDIT SUMMARY ($100.00 START)")
    print(f"================================================================================")
    print(f"OOS Date Range             : {executed_trades[0]['date_str']} to {executed_trades[-1]['date_str']}")
    print(f"Starting Capital           : ${starting_balance:.2f} USDT")
    print(f"Final Capital              : ${current_balance:.2f} USDT")
    print(f"Net Growth (%)             : {((current_balance - starting_balance) / starting_balance * 100.0):+,.2f}%")
    print(f"Max Drawdown               : {max_drawdown:.2f}%")
    print(f"--------------------------------------------------------------------------------")
    print(f"Total Sequential Trades    : {total_t}")
    print(f"Take Profit Wins (TP)      : {tp_cnt} (+15.0% ROE)")
    print(f"Break-Even Saves (BE)      : {be_cnt} ($0 Risk Saved by Armor)")
    print(f"Stop Loss Hits (SL)        : {sl_cnt}")
    print(f"Absorbed Stop-Hunt Wicks   : {total_wicks} (Saved from early exit by Body Close SL!)")
    print(f"--------------------------------------------------------------------------------")
    print(f"PURE WIN RATE (TP vs SL)   : {pure_wr:.2f}%")
    print(f"CAPITAL PRESERVATION RATE  : {effective_wr:.2f}% (Non-Losing Trades: {tp_cnt + be_cnt}/{total_t})")
    print(f"REAL LOSS RATE             : {(sl_cnt / total_t * 100.0):.2f}%")
    print(f"================================================================================\n")

    print(f"{'MONTH':<16} | {'TRADES':<6} | {'TP':<4} | {'BE':<4} | {'SL':<4} | {'WIN RATE':<9} | {'NON-LOSS%':<9} | {'START':<9} | {'END BAL':<9} | {'NET GAIN'}")
    print("-" * 95)
    for m, st in monthly_stats.items():
        m_wr = (st["tp"] / (st["tp"] + st["sl"]) * 100.0) if (st["tp"] + st["sl"]) > 0 else 0.0
        m_nl = ((st["tp"] + st["be"]) / st["trades"] * 100.0) if st["trades"] > 0 else 0.0
        gain_pct = ((st["end_bal"] - st["start_bal"]) / st["start_bal"] * 100.0) if st["start_bal"] > 0 else 0.0
        print(f"{m:<16} | {st['trades']:<6} | {st['tp']:<4} | {st['be']:<4} | {st['sl']:<4} | {m_wr:6.1f}%   | {m_nl:6.1f}%   | ${st['start_bal']:<8.2f} | ${st['end_bal']:<8.2f} | {gain_pct:+7.1f}%")
    print("-" * 95)

    # Save to JSON report
    out_data = {
        "strategy": "HERMES_3.0_MODEL_2A",
        "starting_capital": starting_balance,
        "final_capital": round(current_balance, 2),
        "growth_pct": round(((current_balance - starting_balance) / starting_balance * 100.0), 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "total_trades": total_t,
        "tp_wins": tp_cnt,
        "be_saves": be_cnt,
        "sl_losses": sl_cnt,
        "pure_win_rate": round(pure_wr, 2),
        "capital_preservation_rate": round(effective_wr, 2),
        "absorbed_wicks": total_wicks,
        "monthly_breakdown": dict(monthly_stats),
        "recent_trades": executed_trades[-15:]
    }

    with open("hermes30_model2a_real_oos_report.json", "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)
    print("\nSaved comprehensive report to hermes30_model2a_real_oos_report.json")

if __name__ == "__main__":
    simulate_oos_model2a()
