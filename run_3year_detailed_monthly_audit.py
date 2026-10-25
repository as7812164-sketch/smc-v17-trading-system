"""
HERMES 2.5 APEX HYBRID: 3-Year Granular Month-by-Month Quant Audit
Period: September 2023 to September 2026 (36 Continuous Months)
Universe: Top-22 Champions (1H Fast Scalp & 4H Macro Swing)
Tracks:
- Month-by-month table: Total trades, Long trades, Short trades, Long WR%, Short WR%, Overall WR%
- Compounding Milestones: Starting with $50.00 USDT at 5x leverage:
  * Exactly how many trades & days to hit $2,000 USDT on 4H?
  * Exactly how many trades & days to hit $2,000 USDT on 1H?
"""

import json
import os
import sys
import time
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_4Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_4year")
START_3Y_TS = int(datetime(2023, 9, 27, 0, 0, 0).timestamp() * 1000)

def load_candles(sym, interval):
    fpath = os.path.join(DATA_DIR_4Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for c in data:
            c["high"] = float(c["high"])
            c["low"] = float(c["low"])
            c["open"] = float(c["open"])
            c["close"] = float(c["close"])
            c["volume"] = float(c.get("volume", 0.0))
        return data

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    return {c["time"]: c for c in btc_4h}

def generate_hermes25_signals():
    btc_map_4h = build_btc_map()
    all_signals = []

    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < 40:
                continue

            std_tp_pct = 0.022 if tf == "1h" else 0.028
            soft_sl_pct = 0.025 if tf == "1h" else 0.028
            hard_sl_pct = 0.036 if tf == "1h" else 0.038
            max_tap_window = 28
            max_hold = 40 if tf == "1h" else 30

            for i in range(20, n - 2):
                # -------------------------------------------------------------
                # 1. BUY / LONG (HERMES 2.0 APEX)
                # -------------------------------------------------------------
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050: # Sentry 2: Displacement >= 5%
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
                                            if tap_c["time"] < START_3Y_TS:
                                                break

                                            # Sentry 1: BTC Macro Dump check (< 2%)
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            sentry1_clean = btc_dump < 0.020

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt and sentry1_clean:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + std_tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                res = None
                                                exit_p = entry
                                                exit_t = tap_c["time"]
                                                exit_reason = "HOLD_EXPIRY"

                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"
                                                        exit_p = tp_p
                                                        exit_t = candles[m]["time"]
                                                        exit_reason = "TP_HIT"
                                                        break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res = "LOSS"
                                                        exit_p = min(hard_sl_p, candles[m]["open"])
                                                        exit_t = candles[m]["time"]
                                                        exit_reason = "HARD_SL"
                                                        break
                                                    if candles[m]["close"] <= soft_sl_p:
                                                        res = "LOSS"
                                                        exit_p = candles[m]["close"]
                                                        exit_t = candles[m]["time"]
                                                        exit_reason = "SOFT_SL"
                                                        break

                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                gross_move = (exit_p - entry) / entry
                                                all_signals.append({
                                                    "sym": sym,
                                                    "side": "LONG",
                                                    "tf": tf,
                                                    "time": tap_c["time"],
                                                    "exit_time": exit_t,
                                                    "entry": entry,
                                                    "exit": exit_p,
                                                    "gross": gross_move,
                                                    "res": res,
                                                    "exit_reason": exit_reason
                                                })
                                            break

                # -------------------------------------------------------------
                # 2. SELL / SHORT (HERMES 3.0-C DYNAMIC PROFIT ARMOR)
                # -------------------------------------------------------------
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050: # Sentry 2: Institutional Ceiling >= 5%
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
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False

                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            if tap_c["time"] < START_3Y_TS:
                                                break

                                            # Sentry 1: BTC Macro Pump check (< 2%)
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            sentry1_clean = btc_pump < 0.020

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt and sentry1_clean:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - std_tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                res_short = None
                                                exit_p_short = entry
                                                exit_t_short = tap_c["time"]
                                                exit_reason_short = "HOLD_EXPIRY"
                                                curr_effective_sl = soft_sl_p
                                                armor_stage = 0

                                                for m in range(t, min(t + max_hold, n)):
                                                    low_so_far = candles[m]["low"]

                                                    # Stage 1: lowest drops >= +1.60% -> Lock BE +0.20% Profit
                                                    if low_so_far <= entry * (1.0 - 0.016):
                                                        curr_effective_sl = min(curr_effective_sl, entry * (1.0 - 0.002))
                                                        armor_stage = max(armor_stage, 1)

                                                    # Stage 2: lowest drops >= +2.20% -> Lock +1.20% Guaranteed Profit
                                                    if low_so_far <= entry * (1.0 - 0.022):
                                                        curr_effective_sl = min(curr_effective_sl, entry * (1.0 - 0.012))
                                                        armor_stage = max(armor_stage, 2)

                                                    if candles[m]["low"] <= tp_p:
                                                        res_short = "WIN"
                                                        exit_p_short = tp_p
                                                        exit_t_short = candles[m]["time"]
                                                        exit_reason_short = "TP_HIT"
                                                        break

                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res_short = "LOSS"
                                                        exit_p_short = max(hard_sl_p, candles[m]["open"])
                                                        exit_t_short = candles[m]["time"]
                                                        exit_reason_short = "HARD_SL"
                                                        break

                                                    if candles[m]["close"] >= curr_effective_sl:
                                                        res_short = "WIN" if curr_effective_sl < entry else "LOSS"
                                                        exit_p_short = candles[m]["close"]
                                                        exit_t_short = candles[m]["time"]
                                                        exit_reason_short = f"ARMOR_STAGE_{armor_stage}" if armor_stage > 0 else "SOFT_SL"
                                                        break

                                                if not res_short:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res_short = "WIN" if fc <= entry else "LOSS"
                                                    exit_p_short = fc
                                                    exit_t_short = candles[min(t + max_hold, n - 1)]["time"]

                                                gross_move = (entry - exit_p_short) / entry
                                                all_signals.append({
                                                    "sym": sym,
                                                    "side": "SHORT",
                                                    "tf": tf,
                                                    "time": tap_c["time"],
                                                    "exit_time": exit_t_short,
                                                    "entry": entry,
                                                    "exit": exit_p_short,
                                                    "gross": gross_move,
                                                    "res": res_short,
                                                    "exit_reason": exit_reason_short
                                                })
                                            break
    all_signals.sort(key=lambda x: x["time"])
    return all_signals

def simulate_sequential_queue(signals: List[Dict[str, Any]], tf_name: str) -> Dict[str, Any]:
    executed = []
    active_exit = 0
    for s in signals:
        if s["time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    cap = 50.0
    peak = 50.0
    max_dd = 0.0
    start_time = executed[0]["time"] if executed else 0

    hit_2k_trade = None
    hit_2k_days = None
    hit_2k_winrate = None
    hit_2k_date = None

    wins_so_far = 0
    losses_so_far = 0

    # Monthly tracking
    monthly_data = defaultdict(lambda: {
        "total": 0, "wins": 0, "losses": 0,
        "long_total": 0, "long_wins": 0, "long_losses": 0,
        "short_total": 0, "short_wins": 0, "short_losses": 0,
        "net_pnl": 0.0
    })

    for idx, t in enumerate(executed):
        is_win = t["res"] == "WIN"
        if is_win:
            wins_so_far += 1
        else:
            losses_so_far += 1

        pos_size = cap * 5.0
        fee = pos_size * 0.0016
        net_pnl = (pos_size * t["gross"]) - fee

        cap = max(1.0, cap + net_pnl)
        if cap > peak:
            peak = cap
        dd = (peak - cap) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

        # Check $2,000 Milestone
        if not hit_2k_trade and cap >= 2000.0:
            hit_2k_trade = idx + 1
            hit_2k_days = round((t["exit_time"] - start_time) / (1000 * 86400), 1)
            hit_2k_winrate = round(wins_so_far / (wins_so_far + losses_so_far) * 100.0, 1)
            hit_2k_date = datetime.fromtimestamp(t["exit_time"] / 1000).strftime("%Y-%m-%d")

        # Record monthly
        m_str = datetime.fromtimestamp(t["time"] / 1000).strftime("%Y-%m")
        m_dict = monthly_data[m_str]
        m_dict["total"] += 1
        m_dict["net_pnl"] += net_pnl
        if is_win:
            m_dict["wins"] += 1
        else:
            m_dict["losses"] += 1

        if t["side"] == "LONG":
            m_dict["long_total"] += 1
            if is_win:
                m_dict["long_wins"] += 1
            else:
                m_dict["long_losses"] += 1
        else:
            m_dict["short_total"] += 1
            if is_win:
                m_dict["short_wins"] += 1
            else:
                m_dict["short_losses"] += 1

    total_t = len(executed)
    tot_wins = sum(1 for t in executed if t["res"] == "WIN")
    tot_losses = total_t - tot_wins
    overall_wr = round(tot_wins / total_t * 100.0, 1) if total_t > 0 else 0.0

    longs = [t for t in executed if t["side"] == "LONG"]
    shorts = [t for t in executed if t["side"] == "SHORT"]
    long_w = sum(1 for t in longs if t["res"] == "WIN")
    short_w = sum(1 for t in shorts if t["res"] == "WIN")
    long_wr = round(long_w / len(longs) * 100.0, 1) if longs else 0.0
    short_wr = round(short_w / len(shorts) * 100.0, 1) if shorts else 0.0

    return {
        "tf": tf_name,
        "total_trades": total_t,
        "wins": tot_wins,
        "losses": tot_losses,
        "win_rate": overall_wr,
        "long_total": len(longs),
        "long_wins": long_w,
        "long_losses": len(longs) - long_w,
        "long_win_rate": long_wr,
        "short_total": len(shorts),
        "short_wins": short_w,
        "short_losses": len(shorts) - short_w,
        "short_win_rate": short_wr,
        "final_capital": round(cap, 2),
        "max_drawdown": round(max_dd, 1),
        "milestone_2k": {
            "trade_number": hit_2k_trade,
            "days_taken": hit_2k_days,
            "date_reached": hit_2k_date,
            "win_rate_at_2k": hit_2k_winrate
        },
        "monthly": dict(monthly_data)
    }

def main():
    print("[*] Generating HERMES 2.5 APEX HYBRID 3-Year signals across Top-22 Champions...")
    all_signals = generate_hermes25_signals()
    print(f"[*] Generated {len(all_signals)} raw qualified signals across 36 months.")

    signals_4h = [s for s in all_signals if s["tf"] == "4h"]
    signals_1h = [s for s in all_signals if s["tf"] == "1h"]

    print("\n[*] Simulating 4H Macro Swing Queue ($50 start)...")
    res_4h = simulate_sequential_queue(signals_4h, "4h")

    print("[*] Simulating 1H Fast Scalp Queue ($50 start)...")
    res_1h = simulate_sequential_queue(signals_1h, "1h")

    output = {
        "queue_4h": res_4h,
        "queue_1h": res_1h
    }

    with open("hermes25_3year_detailed_monthly.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 80)
    print("🏆 3-YEAR COMPREHENSIVE AUDIT RESULTS (HERMES 2.5 APEX HYBRID)")
    print("=" * 80)
    print(f"🏛️ 4H MACRO SWING QUEUE:")
    print(f"   • Total Trades: {res_4h['total_trades']} | Wins: {res_4h['wins']} | Losses: {res_4h['losses']}")
    print(f"   • Overall Win Rate: {res_4h['win_rate']}%")
    print(f"   • Longs:  {res_4h['long_total']} trades | Win Rate: {res_4h['long_win_rate']}% ({res_4h['long_wins']}W / {res_4h['long_losses']}L)")
    print(f"   • Shorts: {res_4h['short_total']} trades | Win Rate: {res_4h['short_win_rate']}% ({res_4h['short_wins']}W / {res_4h['short_losses']}L)")
    print(f"   • $50 -> $2,000 Milestone: Trade #{res_4h['milestone_2k']['trade_number']} reached on {res_4h['milestone_2k']['date_reached']} ({res_4h['milestone_2k']['days_taken']} days) with {res_4h['milestone_2k']['win_rate_at_2k']}% WR!")

    print(f"\n⚡ 1H FAST SCALP QUEUE:")
    print(f"   • Total Trades: {res_1h['total_trades']} | Wins: {res_1h['wins']} | Losses: {res_1h['losses']}")
    print(f"   • Overall Win Rate: {res_1h['win_rate']}%")
    print(f"   • Longs:  {res_1h['long_total']} trades | Win Rate: {res_1h['long_win_rate']}% ({res_1h['long_wins']}W / {res_1h['long_losses']}L)")
    print(f"   • Shorts: {res_1h['short_total']} trades | Win Rate: {res_1h['short_win_rate']}% ({res_1h['short_wins']}W / {res_1h['short_losses']}L)")
    print(f"   • $50 -> $2,000 Milestone: Trade #{res_1h['milestone_2k']['trade_number']} reached on {res_1h['milestone_2k']['date_reached']} ({res_1h['milestone_2k']['days_taken']} days) with {res_1h['milestone_2k']['win_rate_at_2k']}% WR!")

if __name__ == "__main__":
    main()
