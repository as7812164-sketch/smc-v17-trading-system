import json
import time
import os
import sys
import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")

def load_data(sym, interval):
    fpath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def run_hermes2_2year_monthly():
    btc_4h = load_data("BTCUSDT", "4h")
    btc_map_4h = {c["time"]: c for c in btc_4h}

    candles_map = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_data(sym, tf)
            if len(k) >= 500:
                candles_map[tf][sym] = k

    all_signals = []

    for tf in ["1h", "4h"]:
        tp_pct = 0.022 if tf == "1h" else 0.028
        soft_sl_pct = 0.025 if tf == "1h" else 0.028
        hard_sl_pct = 0.036 if tf == "1h" else 0.038
        max_hold = 24
        min_displacement = 0.050
        max_tap_window = 28

        for sym, candles in candles_map[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                # BULLISH SETUP
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= min_displacement:
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
                                            
                                            # Sentry 1: Macro BTC Check
                                            if btc_dump >= 0.020:
                                                break

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            # Sentry 3: IDM Sweep + >=18% Wick + 50% MT
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] <= soft_sl_p:
                                                        res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                all_signals.append({
                                                    "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (exit_p - entry) / entry, "res": res
                                                })
                                            break

                # BEARISH SETUP
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= min_displacement:
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
                                            
                                            # Sentry 1: Macro BTC Check
                                            if btc_pump >= 0.020:
                                                break

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] >= soft_sl_p:
                                                        res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                all_signals.append({
                                                    "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (entry - exit_p) / entry, "res": res
                                                })
                                            break

    # Sequential Compounding Simulation
    all_signals.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for s in all_signals:
        if s["time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    # Monthly Grouping
    monthly_data = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "gp": 0.0, "gl": 0.0, "start_cap": 0.0, "end_cap": 0.0, "coins": defaultdict(int)})

    fee_rate = 0.0016
    cap = 50.0
    vault = 0.0
    peak = 50.0
    max_dd = 0.0

    hit_1k = None
    hit_2k = None

    for idx, t in enumerate(executed):
        dt = datetime.datetime.fromtimestamp(t["time"]/1000, datetime.timezone.utc)
        m_key = dt.strftime("%Y-%m")
        
        if monthly_data[m_key]["trades"] == 0:
            monthly_data[m_key]["start_cap"] = cap + vault

        net_move = t["gross"] - fee_rate
        pos_size = cap * 5.0
        pnl = pos_size * net_move

        monthly_data[m_key]["trades"] += 1
        monthly_data[m_key]["coins"][t["sym"]] += 1

        if t["res"] == "WIN":
            monthly_data[m_key]["wins"] += 1
            monthly_data[m_key]["gp"] += pnl
            cap += (pnl * 0.85)
            vault += (pnl * 0.15)
        else:
            monthly_data[m_key]["losses"] += 1
            monthly_data[m_key]["gl"] += abs(pnl)
            cap += pnl
            if cap < 2.0:
                cap = 0.0

        monthly_data[m_key]["end_cap"] = cap + vault
        tot = cap + vault
        if tot > peak: peak = tot
        dd = (peak - tot) / peak * 100.0 if peak > 0 else 0.0
        if dd > max_dd: max_dd = dd

        if tot >= 1000.0 and hit_1k is None: hit_1k = idx + 1
        if tot >= 2000.0 and hit_2k is None: hit_2k = idx + 1

    # Output detailed report
    results = {
        "total_trades": len(executed),
        "total_wins": sum(m["wins"] for m in monthly_data.values()),
        "total_losses": sum(m["losses"] for m in monthly_data.values()),
        "hit_1k": hit_1k,
        "hit_2k": hit_2k,
        "final_capital": cap,
        "final_vault": vault,
        "total_equity": cap + vault,
        "max_drawdown": max_dd,
        "months": []
    }

    print("=" * 115)
    print(" 👑 HERMES 2.0 APEX: 2-YEAR MONTH-BY-MONTH FORENSIC AUDIT (24 MONTHS)")
    print(" Universe: Top-22 Champions | $50 Start | 5x Isolated Leverage | 85/15 Compounding Split")
    print("=" * 115)
    print(f"{'Month':<10} | {'Trades':<7} | {'Wins':<5} | {'Losses':<6} | {'Win Rate':<9} | {'Profit Factor':<13} | {'End Equity ($)':<16} | {'Status'}")
    print("-" * 115)

    for m_key in sorted(monthly_data.keys()):
        m = monthly_data[m_key]
        wr = (m["wins"] / m["trades"] * 100.0) if m["trades"] > 0 else 0.0
        pf = (m["gp"] / m["gl"]) if m["gl"] > 0 else (99.0 if m["gp"] > 0 else 1.0)
        status = "🟢 Profitable" if m["wins"] >= m["losses"] else "🔴 Loss"
        print(f"{m_key:<10} | {m['trades']:<7} | {m['wins']:<5} | {m['losses']:<6} | {wr:>6.1f}%   | {pf:>10.2f}    | ${m['end_cap']:>15,.2f} | {status}")
        results["months"].append({
            "month": m_key, "trades": m["trades"], "wins": m["wins"], "losses": m["losses"],
            "win_rate": round(wr, 2), "profit_factor": round(pf, 2), "end_equity": round(m["end_cap"], 2)
        })

    print("=" * 115)
    print(f"2-YEAR TOTAL TRADES: {results['total_trades']}")
    print(f"TOTAL WINS: {results['total_wins']} | TOTAL LOSSES: {results['total_losses']}")
    overall_wr = (results['total_wins'] / results['total_trades'] * 100.0) if results['total_trades'] > 0 else 0.0
    print(f"OVERALL 2-YEAR WIN RATE: {overall_wr:.2f}%")
    print(f"MILESTONE $1,000 HIT AT: Trade #{results['hit_1k']}")
    print(f"MILESTONE $2,000 HIT AT: Trade #{results['hit_2k']}")
    print(f"MAX DRAWDOWN: {results['max_drawdown']:.2f}%")
    print(f"FINAL TERMINAL EQUITY: ${results['total_equity']:,.2f} USDT")

    with open("hermes2_2year_monthly_audit.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_hermes2_2year_monthly()
