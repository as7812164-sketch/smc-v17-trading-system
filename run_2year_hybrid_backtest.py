import json
import os
import sys
import time
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

# 2-Year Time Window: 2024-09-27 to 2026-09-27 (24 Continuous Months)
START_2Y_TS = int(datetime(2024, 9, 27, 0, 0, 0).timestamp() * 1000)

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
    btc_map = {}
    for c in btc_4h:
        btc_map[c["time"]] = c
    return btc_map

def run_2year_backtest():
    print("================================================================================")
    print("   HERMES 2.5 APEX HYBRID: 2-YEAR QUANTITATIVE AUDIT & ACCURACY REPORT          ")
    print("   Time Window: September 27, 2024 - September 27, 2026 (24 Months)             ")
    print("   Strategy: HERMES 2.0 APEX (BUY) + HERMES 3.0-C DYNAMIC PROFIT ARMOR (SELL)   ")
    print("   Asset Universe: Top-22 Binance USDT-M Perpetual Champions                    ")
    print("================================================================================\n")

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
                # 1. BUY / LONG (HERMES 2.0 APEX 4-SENTRIES)
                # -------------------------------------------------------------
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050: # Sentry 2: Institutional Floor >= 5.0%
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
                                            # Filter only within 2-year window
                                            if tap_c["time"] < START_2Y_TS:
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

                                            # Sentry 3: IDM Sweep + >=18% Wick + 50% MT
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
                # 2. SELL / SHORT (HERMES 3.0-C MULTI-STAGE DYNAMIC PROFIT ARMOR)
                # -------------------------------------------------------------
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050: # Sentry 2: Institutional Ceiling >= 5.0%
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
                                            # Filter only within 2-year window
                                            if tap_c["time"] < START_2Y_TS:
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

                                                    # 1. Full Take Profit Hit
                                                    if candles[m]["low"] <= tp_p:
                                                        res_short = "WIN"
                                                        exit_p_short = tp_p
                                                        exit_t_short = candles[m]["time"]
                                                        exit_reason_short = "TP_HIT"
                                                        break

                                                    # 2. Hard Stop Loss breach
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res_short = "LOSS"
                                                        exit_p_short = max(hard_sl_p, candles[m]["open"])
                                                        exit_t_short = candles[m]["time"]
                                                        exit_reason_short = "HARD_SL"
                                                        break

                                                    # 3. Soft SL / Dynamic Armor Tightened SL Hit
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

    results = {}

    for tf_filter in ["4h", "1h", "all"]:
        filtered = [s for s in all_signals if s["tf"] == tf_filter] if tf_filter != "all" else all_signals
        executed = []
        active_exit = 0
        for s in filtered:
            if s["time"] >= active_exit:
                executed.append(s)
                active_exit = s["exit_time"]

        cap = 50.0
        peak = 50.0
        max_dd = 0.0
        wins = sum(1 for t in executed if t["res"] == "WIN")
        losses = sum(1 for t in executed if t["res"] == "LOSS")
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0

        long_trades = [t for t in executed if t["side"] == "LONG"]
        short_trades = [t for t in executed if t["side"] == "SHORT"]

        long_wins = sum(1 for t in long_trades if t["res"] == "WIN")
        long_wr = (long_wins / len(long_trades) * 100.0) if long_trades else 0.0

        short_wins = sum(1 for t in short_trades if t["res"] == "WIN")
        short_wr = (short_wins / len(short_trades) * 100.0) if short_trades else 0.0

        gp = 0.0
        gl = 0.0
        hit_1k = None
        hit_2k = None
        hit_10k = None
        hit_40k = None

        monthly_perf = defaultdict(lambda: {"wins": 0, "losses": 0, "net_pnl": 0.0})

        for idx, t in enumerate(executed):
            pos_size = cap * 5.0
            fee = pos_size * 0.0016
            net_pnl = (pos_size * t["gross"]) - fee

            if t["res"] == "WIN":
                gp += net_pnl
            else:
                gl += abs(net_pnl)

            cap = max(1.0, cap + net_pnl)
            if cap > peak:
                peak = cap
            dd = (peak - cap) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

            if not hit_1k and cap >= 1000.0:
                hit_1k = idx + 1
            if not hit_2k and cap >= 2000.0:
                hit_2k = idx + 1
            if not hit_10k and cap >= 10000.0:
                hit_10k = idx + 1
            if not hit_40k and cap >= 40000.0:
                hit_40k = idx + 1

            m_key = datetime.fromtimestamp(t["time"] / 1000).strftime("%Y-%m")
            if t["res"] == "WIN":
                monthly_perf[m_key]["wins"] += 1
            else:
                monthly_perf[m_key]["losses"] += 1
            monthly_perf[m_key]["net_pnl"] += net_pnl

        pf = (gp / gl) if gl > 0 else 99.9

        results[tf_filter] = {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "long_trades": len(long_trades),
            "long_wins": long_wins,
            "long_wr": round(long_wr, 2),
            "short_trades": len(short_trades),
            "short_wins": short_wins,
            "short_wr": round(short_wr, 2),
            "profit_factor": round(pf, 2),
            "max_dd": round(max_dd, 2),
            "final_cap": round(cap, 2),
            "hit_1k": hit_1k,
            "hit_2k": hit_2k,
            "hit_10k": hit_10k,
            "hit_40k": hit_40k,
            "monthly": dict(monthly_perf)
        }

        print("--------------------------------------------------------------------------------")
        print(f"📊 2-YEAR ACCURACY: {tf_filter.upper()} QUEUE")
        print("--------------------------------------------------------------------------------")
        print(f"• Total Trades:            {total_trades}")
        print(f"• Overall Win Rate:        {win_rate:.2f}% ({wins} Wins / {losses} Losses)")
        print(f"• Long (Buy) Win Rate:     {long_wr:.2f}% ({long_wins}W / {len(long_trades) - long_wins}L) [Total: {len(long_trades)}]")
        print(f"• Short (Sell) Win Rate:    {short_wr:.2f}% ({short_wins}W / {len(short_trades) - short_wins}L) [Total: {len(short_trades)}]")
        print(f"• Profit Factor:           {pf:.2f}")
        print(f"• Max Drawdown:            {max_dd:.2f}%")
        print(f"• Starting Balance:        $50.00 USDT")
        print(f"• Final Compounded Equity: ${cap:,.2f} USDT")
        print(f"• $1,000 Milestone:        Trade #{hit_1k or 'N/A'}")
        print(f"• $2,000 Milestone:        Trade #{hit_2k or 'N/A'}")
        print(f"• $10,000 Milestone:       Trade #{hit_10k or 'N/A'}")
        print(f"• $40,000 Milestone:       Trade #{hit_40k or 'N/A'}\n")

    # Print monthly breakdown for combined
    print("================================================================================")
    print("                24-MONTH ACCURACY & PERFORMANCE BREAKDOWN                       ")
    print("================================================================================")
    all_months = sorted(results["all"]["monthly"].keys())
    for m in all_months:
        d = results["all"]["monthly"][m]
        tot = d["wins"] + d["losses"]
        wr = (d["wins"] / tot * 100.0) if tot > 0 else 0.0
        print(f"{m} | Trades: {tot:2d} | Wins: {d['wins']:2d} | Losses: {d['losses']:2d} | Win Rate: {wr:5.1f}% | Net PnL: ${d['net_pnl']:+,.2f}")

    with open("hermes25_2year_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_2year_backtest()
