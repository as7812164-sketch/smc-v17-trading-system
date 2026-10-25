import json
import time
import os
import sys
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_4Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_4year")

def load_data(sym, interval):
    fpath = os.path.join(DATA_DIR_4Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        running_cvd = 0.0
        vol_window = []
        for c in data:
            v = float(c.get("volume", 0.0))
            h = float(c["high"])
            l = float(c["low"])
            cl = float(c["close"])
            op = float(c["open"])
            
            rng = h - l
            if rng > 0:
                d_ratio = (cl - l) / rng
                delta = v * (2.0 * d_ratio - 1.0)
            else:
                d_ratio = 0.5
                delta = 0.0
            
            running_cvd += delta
            c["delta"] = delta
            c["delta_ratio"] = d_ratio
            c["cvd"] = running_cvd
            
            vol_window.append(v)
            if len(vol_window) > 20:
                vol_window.pop(0)
            c["vol_sma20"] = sum(vol_window) / len(vol_window)
            c["oi_expansion"] = (v / c["vol_sma20"]) * max(0.0, (cl - op) / rng) if (c["vol_sma20"] > 0 and rng > 0) else 0.0
        return data

def run_compounding_sim(signals, start_cap=50.0, fee_rate=0.0016):
    signals.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for s in signals:
        if s["time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    cap = start_cap
    vault = 0.0
    peak = start_cap
    max_dd = 0.0
    hit_1k = None
    hit_2k = None
    wins = 0
    losses = 0
    buy_wins = 0
    buy_losses = 0
    sell_wins = 0
    sell_losses = 0
    gp = 0.0
    gl = 0.0

    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - fee_rate
        pos_size = cap * 5.0
        pnl = pos_size * net_move

        is_buy = trade["side"] == "LONG"

        if trade["res"] == "WIN":
            wins += 1
            gp += pnl
            cap += (pnl * 0.85)
            vault += (pnl * 0.15)
            if is_buy: buy_wins += 1
            else: sell_wins += 1
        else:
            losses += 1
            gl += abs(pnl)
            cap += pnl
            if is_buy: buy_losses += 1
            else: sell_losses += 1
            if cap < 2.0:
                cap = 0.0

        tot = cap + vault
        if tot > peak:
            peak = tot
        dd = (peak - tot) / peak * 100.0 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

        if tot >= 1000.0 and hit_1k is None:
            hit_1k = idx + 1
        if tot >= 2000.0 and hit_2k is None:
            hit_2k = idx + 1

    tot_trades = wins + losses
    wr = (wins / tot_trades * 100.0) if tot_trades > 0 else 0.0
    tot_buys = buy_wins + buy_losses
    buy_wr = (buy_wins / tot_buys * 100.0) if tot_buys > 0 else 0.0
    tot_sells = sell_wins + sell_losses
    sell_wr = (sell_wins / tot_sells * 100.0) if tot_sells > 0 else 0.0
    pf = (gp / gl) if gl > 0 else 99.0

    return {
        "executed_trades": executed,
        "total_trades": tot_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "total_buys": tot_buys,
        "buy_wins": buy_wins,
        "buy_losses": buy_losses,
        "buy_win_rate": round(buy_wr, 2),
        "total_sells": tot_sells,
        "sell_wins": sell_wins,
        "sell_losses": sell_losses,
        "sell_win_rate": round(sell_wr, 2),
        "profit_factor": round(pf, 2),
        "max_drawdown": round(max_dd, 2),
        "hit_1k": hit_1k or "N/A",
        "hit_2k": hit_2k or "N/A",
        "final_capital": round(cap, 2),
        "final_vault": round(vault, 2),
        "total_equity": round(cap + vault, 2)
    }

def main():
    print("=" * 110)
    print(" 👑 HERMES 3.0-C (CVD DELTA + OI FILTER + DYNAMIC PROFIT ARMOR)")
    print(" 4-YEAR COMPLETE MARKET AUDIT & BACKTEST (2022 - 2026)")
    print(" Compounding: $50 Start | 5x Isolated Leverage | 1-Trade Sequential Queue | 85/15 Compounding")
    print("=" * 110)

    # Load 4-year data
    candles_map = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_data(sym, tf)
            if len(k) >= 500:
                candles_map[tf][sym] = k

    btc_4h = load_data("BTCUSDT", "4h")
    btc_map_4h = {c["time"]: c for c in btc_4h}

    signals_hermes2 = []
    signals_hermes3c = []

    max_hold = 24

    for tf in ["1h", "4h"]:
        std_tp_pct = 0.022 if tf == "1h" else 0.028
        soft_sl_pct = 0.025 if tf == "1h" else 0.028
        hard_sl_pct = 0.036 if tf == "1h" else 0.038
        max_tap_window = 28

        for sym, candles in candles_map[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                # ----------------- 1. BUY EVALUATION -----------------
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1; max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid

                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False

                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        if candles[t]["low"] <= dec_top * 0.9995:
                                            tap_c = candles[t]

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

                                            if sentry1_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + std_tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                # Baseline outcome
                                                res2 = None; exit_p2 = entry; exit_t2 = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res2 = "WIN"; exit_p2 = tp_p; exit_t2 = candles[m]["time"]; break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res2 = "LOSS"; exit_p2 = min(hard_sl_p, candles[m]["open"]); exit_t2 = candles[m]["time"]; break
                                                    if candles[m]["close"] <= soft_sl_p:
                                                        res2 = "LOSS"; exit_p2 = candles[m]["close"]; exit_t2 = candles[m]["time"]; break
                                                if not res2:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res2 = "WIN" if fc >= entry else "LOSS"
                                                    exit_p2 = fc
                                                    exit_t2 = candles[min(t + max_hold, n - 1)]["time"]

                                                trade_h2 = {
                                                    "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t2, "entry": entry, "exit": exit_p2,
                                                    "gross": (exit_p2 - entry) / entry, "res": res2
                                                }
                                                signals_hermes2.append(trade_h2)

                                                # Hermes 3.0-C Evaluation (CVD + OI + Dynamic Profit Armor)
                                                cvd_prev = candles[t - 3]["cvd"] if t >= 3 else candles[0]["cvd"]
                                                cvd_slope = tap_c["cvd"] - cvd_prev
                                                cvd_pass = (tap_c["delta_ratio"] >= 0.50 or tap_c["delta"] > 0) and (cvd_slope > 0)
                                                oi_pass = (tap_c["volume"] >= 0.90 * tap_c["vol_sma20"]) and (tap_c["oi_expansion"] >= 0.08)

                                                if cvd_pass and oi_pass:
                                                    curr_soft_sl = soft_sl_p
                                                    res_q = None; exit_pq = entry; exit_tq = tap_c["time"]
                                                    for m in range(t, min(t + max_hold, n)):
                                                        high_so_far = candles[m]["high"]
                                                        if high_so_far >= entry * 1.016:
                                                            curr_soft_sl = max(curr_soft_sl, entry * 1.002) # BE Lock
                                                        if high_so_far >= entry * 1.022:
                                                            curr_soft_sl = max(curr_soft_sl, entry * 1.012) # Profit Lock

                                                        if candles[m]["high"] >= tp_p:
                                                            res_q = "WIN"; exit_pq = tp_p; exit_tq = candles[m]["time"]; break
                                                        if candles[m]["low"] <= hard_sl_p:
                                                            res_q = "LOSS"; exit_pq = min(hard_sl_p, candles[m]["open"]); exit_tq = candles[m]["time"]; break
                                                        if candles[m]["close"] <= curr_soft_sl:
                                                            res_q = "WIN" if curr_soft_sl > entry else "LOSS"
                                                            exit_pq = candles[m]["close"]
                                                            exit_tq = candles[m]["time"]
                                                            break
                                                    if not res_q:
                                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                                        res_q = "WIN" if fc >= entry else "LOSS"
                                                        exit_pq = fc
                                                        exit_tq = candles[min(t + max_hold, n - 1)]["time"]

                                                    signals_hermes3c.append({
                                                        "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                        "exit_time": exit_tq, "entry": entry, "exit": exit_pq,
                                                        "gross": (exit_pq - entry) / entry, "res": res_q
                                                    })
                                                break

                # ----------------- 2. SELL EVALUATION -----------------
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1; max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid

                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False

                                if has_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]

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

                                            if sentry1_clean and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - std_tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                # Baseline outcome
                                                res2 = None; exit_p2 = entry; exit_t2 = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["low"] <= tp_p:
                                                        res2 = "WIN"; exit_p2 = tp_p; exit_t2 = candles[m]["time"]; break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res2 = "LOSS"; exit_p2 = max(hard_sl_p, candles[m]["open"]); exit_t2 = candles[m]["time"]; break
                                                    if candles[m]["close"] >= soft_sl_p:
                                                        res2 = "LOSS"; exit_p2 = candles[m]["close"]; exit_t2 = candles[m]["time"]; break
                                                if not res2:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res2 = "WIN" if fc <= entry else "LOSS"
                                                    exit_p2 = fc
                                                    exit_t2 = candles[min(t + max_hold, n - 1)]["time"]

                                                trade_h2 = {
                                                    "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t2, "entry": entry, "exit": exit_p2,
                                                    "gross": (entry - exit_p2) / entry, "res": res2
                                                }
                                                signals_hermes2.append(trade_h2)

                                                # Quantum Armor outcome for SHORT
                                                curr_soft_sl = soft_sl_p
                                                res_q = None; exit_pq = entry; exit_tq = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    low_so_far = candles[m]["low"]
                                                    if low_so_far <= entry * 0.984:
                                                        curr_soft_sl = min(curr_soft_sl, entry * 0.998)
                                                    if low_so_far <= entry * 0.978:
                                                        curr_soft_sl = min(curr_soft_sl, entry * 0.988)

                                                    if candles[m]["low"] <= tp_p:
                                                        res_q = "WIN"; exit_pq = tp_p; exit_tq = candles[m]["time"]; break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res_q = "LOSS"; exit_pq = max(hard_sl_p, candles[m]["open"]); exit_tq = candles[m]["time"]; break
                                                    if candles[m]["close"] >= curr_soft_sl:
                                                        res_q = "WIN" if curr_soft_sl < entry else "LOSS"
                                                        exit_pq = candles[m]["close"]
                                                        exit_tq = candles[m]["time"]
                                                        break
                                                if not res_q:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res_q = "WIN" if fc <= entry else "LOSS"
                                                    exit_pq = fc
                                                    exit_tq = candles[min(t + max_hold, n - 1)]["time"]

                                                signals_hermes3c.append({
                                                    "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_tq, "entry": entry, "exit": exit_pq,
                                                    "gross": (entry - exit_pq) / entry, "res": res_q
                                                })
                                                break

    # 1. Full 4-Year Compounding Run
    res_4y_h2 = run_compounding_sim(signals_hermes2)
    res_4y_h3c = run_compounding_sim(signals_hermes3c)

    print("\n" + "=" * 120)
    print("🏆 4-YEAR CONTINUOUS FULL COMPOUNDING COMPARISON ($50.00 START)")
    print("=" * 120)
    wl_h2 = f"{res_4y_h2['wins']}W / {res_4y_h2['losses']}L"
    wl_h3 = f"{res_4y_h3c['wins']}W / {res_4y_h3c['losses']}L"
    buy_h2 = f"{res_4y_h2['buy_win_rate']}% ({res_4y_h2['buy_wins']}W/{res_4y_h2['buy_losses']}L)"
    buy_h3 = f"{res_4y_h3c['buy_win_rate']}% ({res_4y_h3c['buy_wins']}W/{res_4y_h3c['buy_losses']}L)"
    sell_h2 = f"{res_4y_h2['sell_win_rate']}% ({res_4y_h2['sell_wins']}W/{res_4y_h2['sell_losses']}L)"
    sell_h3 = f"{res_4y_h3c['sell_win_rate']}% ({res_4y_h3c['sell_wins']}W/{res_4y_h3c['sell_losses']}L)"
    hit1k_h2 = f"Trade #{res_4y_h2['hit_1k']}"
    hit1k_h3 = f"Trade #{res_4y_h3c['hit_1k']}"
    hit2k_h2 = f"Trade #{res_4y_h2['hit_2k']}"
    hit2k_h3 = f"Trade #{res_4y_h3c['hit_2k']}"
    eq_h2 = f"${res_4y_h2['total_equity']:,.2f}"
    eq_h3 = f"${res_4y_h3c['total_equity']:,.2f}"

    print(f"{'METRIC':<35} | {'HERMES 2.0 APEX (BASELINE)':<38} | {'HERMES 3.0-C (CVD+OI+ARMOR)'}")
    print("-" * 120)
    print(f"{'Total Trades Executed':<35} | {res_4y_h2['total_trades']:<38} | {res_4y_h3c['total_trades']}")
    print(f"{'Win / Loss Record':<35} | {wl_h2:<38} | {wl_h3}")
    print(f"{'Overall Win Rate':<35} | {str(res_4y_h2['win_rate']) + '%':<38} | {str(res_4y_h3c['win_rate']) + '%'}")
    print(f"{'BUY (LONG) Win Rate':<35} | {buy_h2:<38} | {buy_h3}")
    print(f"{'SELL (SHORT) Win Rate':<35} | {sell_h2:<38} | {sell_h3}")
    print(f"{'Profit Factor':<35} | {str(res_4y_h2['profit_factor']):<38} | {res_4y_h3c['profit_factor']}")
    print(f"{'Max Drawdown':<35} | {str(res_4y_h2['max_drawdown']) + '%':<38} | {str(res_4y_h3c['max_drawdown']) + '%'}")
    print(f"{'$1,000 Milestone Reached':<35} | {hit1k_h2:<38} | {hit1k_h3}")
    print(f"{'$2,000 Milestone Reached':<35} | {hit2k_h2:<38} | {hit2k_h3}")
    print(f"{'Final Compounded Equity':<35} | {eq_h2:<38} | {eq_h3}")
    print("=" * 120)

    # 2. Year-by-Year Segregated Breakdown
    # Split executed trades by year
    # Year 1: 2022-09-26 to 2023-09-26
    # Year 2: 2023-09-26 to 2024-09-26
    # Year 3: 2024-09-26 to 2025-09-26
    # Year 4: 2025-09-26 to 2026-09-26
    
    # We will analyze:
    # A) All signals falling within each year (Standalone $50 reset per year)
    now_ms = int(time.time() * 1000)
    ms_in_year = 365 * 24 * 3600 * 1000
    y4_start = now_ms - ms_in_year
    y3_start = now_ms - (2 * ms_in_year)
    y2_start = now_ms - (3 * ms_in_year)
    y1_start = now_ms - (4 * ms_in_year)

    year_ranges = [
        ("Year 1 (2022-2023: Bear Market & FTX Crash)", y1_start, y2_start),
        ("Year 2 (2023-2024: Accumulation & Recovery)", y2_start, y3_start),
        ("Year 3 (2024-2025: ETF Launch & Super Bull)", y3_start, y4_start),
        ("Year 4 (2025-2026: Institutional Market)", y4_start, now_ms)
    ]

    print("\n" + "=" * 120)
    print("📅 HERMES 3.0-C YEAR-BY-YEAR STANDALONE AUDIT ($50 STARTING CAPITAL EACH YEAR)")
    print("=" * 120)
    print(f"{'YEAR / MARKET REGIME':<45} | {'TRADES':<6} | {'W/L':<9} | {'WIN RATE':<9} | {'BUY WR':<8} | {'SELL WR':<8} | {'PF':<5} | {'MAX DD':<7} | {'FINAL PROFIT'}")
    print("-" * 120)

    for y_name, start_t, end_t in year_ranges:
        y_sigs_h3 = [s for s in signals_hermes3c if start_t <= s["time"] < end_t]
        res_y = run_compounding_sim(y_sigs_h3, start_cap=50.0)
        wl_str = f"{res_y['wins']}/{res_y['losses']}"
        print(f"{y_name:<45} | {res_y['total_trades']:<6} | {wl_str:<9} | {res_y['win_rate']:<8}% | {res_y['buy_win_rate']:<7}% | {res_y['sell_win_rate']:<7}% | {res_y['profit_factor']:<5} | {res_y['max_drawdown']:<6}% | ${res_y['total_equity']:,.2f}")
    print("=" * 120)

    # Save results as json for artifact creation
    audit_data = {
        "full_4y_hermes2": res_4y_h2,
        "full_4y_hermes3c": res_4y_h3c,
        "year_by_year": []
    }
    for y_name, start_t, end_t in year_ranges:
        y_sigs_h3 = [s for s in signals_hermes3c if start_t <= s["time"] < end_t]
        y_sigs_h2 = [s for s in signals_hermes2 if start_t <= s["time"] < end_t]
        r3 = run_compounding_sim(y_sigs_h3, start_cap=50.0)
        r2 = run_compounding_sim(y_sigs_h2, start_cap=50.0)
        # remove executed trades list to keep json clean
        r3.pop("executed_trades", None)
        r2.pop("executed_trades", None)
        audit_data["year_by_year"].append({
            "period": y_name,
            "hermes3c": r3,
            "hermes2": r2
        })
    res_4y_h2.pop("executed_trades", None)
    res_4y_h3c.pop("executed_trades", None)

    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hermes3c_4year_audit_summary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"\nAudit results exported to {out_file}")

if __name__ == "__main__":
    main()
