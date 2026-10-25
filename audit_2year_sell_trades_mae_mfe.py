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

def run_sell_backtest_with_mae_mfe():
    print("================================================================================")
    print("   HERMES 2.5 APEX HYBRID: 2-YEAR SELL TRADES (SHORTS) QUANT AUDIT             ")
    print("   Metrics: Win Rate, MAE (Max Adverse Excursion), MFE (Max Favorable Excursion)")
    print("   Time Window: 27 September 2024 — 27 September 2026 (24 Continuous Months)   ")
    print("   Engine: HERMES 3.0-C DYNAMIC PROFIT ARMOR (SELL SIDE)                       ")
    print("   Universe: Top-22 Champions (1H and 4H Timeframes)                           ")
    print("================================================================================\n")

    btc_map_4h = build_btc_map()
    sell_trades = []

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
                # SELL / SHORT (HERMES 3.0-C DYNAMIC PROFIT ARMOR)
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
                                            # Filter strictly within 2-year window
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
                                                exit_idx = min(t + max_hold, n - 1)
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
                                                        exit_idx = m
                                                        exit_reason_short = "TP_HIT"
                                                        break

                                                    # 2. Hard Stop Loss breach
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res_short = "LOSS"
                                                        exit_p_short = max(hard_sl_p, candles[m]["open"])
                                                        exit_t_short = candles[m]["time"]
                                                        exit_idx = m
                                                        exit_reason_short = "HARD_SL"
                                                        break

                                                    # 3. Soft SL / Dynamic Armor Tightened SL Hit
                                                    if candles[m]["close"] >= curr_effective_sl:
                                                        res_short = "WIN" if curr_effective_sl < entry else "LOSS"
                                                        exit_p_short = candles[m]["close"]
                                                        exit_t_short = candles[m]["time"]
                                                        exit_idx = m
                                                        exit_reason_short = f"ARMOR_STAGE_{armor_stage}" if armor_stage > 0 else "SOFT_SL"
                                                        break

                                                if not res_short:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res_short = "WIN" if fc <= entry else "LOSS"
                                                    exit_p_short = fc
                                                    exit_idx = min(t + max_hold, n - 1)
                                                    exit_t_short = candles[exit_idx]["time"]

                                                # Exact MAE and MFE calculation during trade lifetime (from candle t to exit_idx)
                                                trade_window = candles[t:exit_idx + 1]
                                                highest_during_trade = max(c["high"] for c in trade_window)
                                                lowest_during_trade = min(c["low"] for c in trade_window)

                                                # For SHORT: Adverse move is price rising above entry; Favorable is price dropping below entry
                                                mae_pct = max(0.0, (highest_during_trade - entry) / entry * 100.0)
                                                mfe_pct = max(0.0, (entry - lowest_during_trade) / entry * 100.0)
                                                gross_move = (entry - exit_p_short) / entry

                                                duration_hrs = (exit_t_short - tap_c["time"]) / (3600 * 1000.0)
                                                month_key = datetime.fromtimestamp(tap_c["time"] / 1000.0).strftime("%Y-%m")

                                                sell_trades.append({
                                                    "sym": sym,
                                                    "side": "SHORT",
                                                    "tf": tf,
                                                    "time": tap_c["time"],
                                                    "exit_time": exit_t_short,
                                                    "entry": entry,
                                                    "exit": exit_p_short,
                                                    "gross": gross_move,
                                                    "res": res_short,
                                                    "exit_reason": exit_reason_short,
                                                    "mae_pct": mae_pct,
                                                    "mfe_pct": mfe_pct,
                                                    "duration_hrs": duration_hrs,
                                                    "month": month_key
                                                })
                                            break

    # Sort sequentially by entry time
    sell_trades.sort(key=lambda x: x["time"])

    # Separate by TF
    trades_1h = [t for t in sell_trades if t["tf"] == "1h"]
    trades_4h = [t for t in sell_trades if t["tf"] == "4h"]

    def compute_stats(trades, label):
        total = len(trades)
        if total == 0:
            return {}
        wins = [t for t in trades if t["res"] == "WIN"]
        losses = [t for t in trades if t["res"] == "LOSS"]
        win_count = len(wins)
        loss_count = len(losses)
        wr = (win_count / total) * 100.0

        # MAE metrics
        all_mae = [t["mae_pct"] for t in trades]
        win_mae = [t["mae_pct"] for t in wins]
        loss_mae = [t["mae_pct"] for t in losses]

        avg_mae = sum(all_mae) / total
        avg_win_mae = sum(win_mae) / len(wins) if wins else 0.0
        avg_loss_mae = sum(loss_mae) / len(losses) if losses else 0.0

        # MFE metrics
        all_mfe = [t["mfe_pct"] for t in trades]
        win_mfe = [t["mfe_pct"] for t in wins]
        loss_mfe = [t["mfe_pct"] for t in losses]

        avg_mfe = sum(all_mfe) / total
        avg_win_mfe = sum(win_mfe) / len(wins) if wins else 0.0
        avg_loss_mfe = sum(loss_mfe) / len(losses) if losses else 0.0

        # Profit Factor
        gross_wins = sum(t["gross"] for t in wins)
        gross_losses = sum(abs(t["gross"]) for t in losses)
        pf = (gross_wins / gross_losses) if gross_losses > 0 else 999.0

        # Duration
        avg_dur = sum(t["duration_hrs"] for t in trades) / total

        # Streaks
        max_win_streak = 0
        cur_win_streak = 0
        max_loss_streak = 0
        cur_loss_streak = 0
        for t in trades:
            if t["res"] == "WIN":
                cur_win_streak += 1
                cur_loss_streak = 0
                max_win_streak = max(max_win_streak, cur_win_streak)
            else:
                cur_loss_streak += 1
                cur_win_streak = 0
                max_loss_streak = max(max_loss_streak, cur_loss_streak)

        return {
            "label": label,
            "total": total,
            "wins": win_count,
            "losses": loss_count,
            "win_rate": wr,
            "avg_mae": avg_mae,
            "avg_win_mae": avg_win_mae,
            "avg_loss_mae": avg_loss_mae,
            "avg_mfe": avg_mfe,
            "avg_win_mfe": avg_win_mfe,
            "avg_loss_mfe": avg_loss_mfe,
            "profit_factor": pf,
            "avg_dur_hrs": avg_dur,
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak
        }

    s_1h = compute_stats(trades_1h, "1H Queue (Sell Only)")
    s_4h = compute_stats(trades_4h, "4H Queue (Sell Only)")
    s_comb = compute_stats(sell_trades, "Combined (1H + 4H Sell Only)")

    print(f"--- 1H SELL TRADES SUMMARY ---")
    print(f"Total Trades: {s_1h['total']}")
    print(f"Wins / Losses: {s_1h['wins']}W / {s_1h['losses']}L")
    print(f"Win Rate: {s_1h['win_rate']:.2f}%")
    print(f"Average MAE (Adverse): {s_1h['avg_mae']:.2f}% (Wins: {s_1h['avg_win_mae']:.2f}%, Losses: {s_1h['avg_loss_mae']:.2f}%)")
    print(f"Average MFE (Favorable): {s_1h['avg_mfe']:.2f}% (Wins: {s_1h['avg_win_mfe']:.2f}%, Losses: {s_1h['avg_loss_mfe']:.2f}%)")
    print(f"Profit Factor: {s_1h['profit_factor']:.2f}")
    print(f"Max Consecutive Win Streak: {s_1h['max_win_streak']} trades")
    print(f"Max Consecutive Loss Streak: {s_1h['max_loss_streak']} trades\n")

    print(f"--- 4H SELL TRADES SUMMARY ---")
    print(f"Total Trades: {s_4h['total']}")
    print(f"Wins / Losses: {s_4h['wins']}W / {s_4h['losses']}L")
    print(f"Win Rate: {s_4h['win_rate']:.2f}%")
    print(f"Average MAE (Adverse): {s_4h['avg_mae']:.2f}% (Wins: {s_4h['avg_win_mae']:.2f}%, Losses: {s_4h['avg_loss_mae']:.2f}%)")
    print(f"Average MFE (Favorable): {s_4h['avg_mfe']:.2f}% (Wins: {s_4h['avg_win_mfe']:.2f}%, Losses: {s_4h['avg_loss_mfe']:.2f}%)")
    print(f"Profit Factor: {s_4h['profit_factor']:.2f}")
    print(f"Max Consecutive Win Streak: {s_4h['max_win_streak']} trades")
    print(f"Max Consecutive Loss Streak: {s_4h['max_loss_streak']} trades\n")

    print(f"--- COMBINED SELL TRADES SUMMARY ---")
    print(f"Total Trades: {s_comb['total']}")
    print(f"Wins / Losses: {s_comb['wins']}W / {s_comb['losses']}L")
    print(f"Win Rate: {s_comb['win_rate']:.2f}%")
    print(f"Average MAE (Adverse): {s_comb['avg_mae']:.2f}%")
    print(f"Average MFE (Favorable): {s_comb['avg_mfe']:.2f}%")
    print(f"Profit Factor: {s_comb['profit_factor']:.2f}")
    print(f"Average Duration: {s_comb['avg_dur_hrs']:.1f} hours\n")

    # Monthly breakdown for Sell Trades
    months = sorted(list(set(t["month"] for t in sell_trades)))
    monthly_data = {}
    for m in months:
        m_trades = [t for t in sell_trades if t["month"] == m]
        m_1h = [t for t in m_trades if t["tf"] == "1h"]
        m_4h = [t for t in m_trades if t["tf"] == "4h"]

        w_all = len([t for t in m_trades if t["res"] == "WIN"])
        l_all = len([t for t in m_trades if t["res"] == "LOSS"])
        wr_all = (w_all / len(m_trades) * 100.0) if m_trades else 0.0

        w_1h = len([t for t in m_1h if t["res"] == "WIN"])
        l_1h = len([t for t in m_1h if t["res"] == "LOSS"])
        wr_1h = (w_1h / len(m_1h) * 100.0) if m_1h else 0.0

        w_4h = len([t for t in m_4h if t["res"] == "WIN"])
        l_4h = len([t for t in m_4h if t["res"] == "LOSS"])
        wr_4h = (w_4h / len(m_4h) * 100.0) if m_4h else 0.0

        avg_mae_m = sum(t["mae_pct"] for t in m_trades) / len(m_trades) if m_trades else 0.0
        avg_mfe_m = sum(t["mfe_pct"] for t in m_trades) / len(m_trades) if m_trades else 0.0

        monthly_data[m] = {
            "month": m,
            "total_trades": len(m_trades),
            "wins": w_all,
            "losses": l_all,
            "win_rate": wr_all,
            "trades_1h": len(m_1h),
            "wr_1h": wr_1h,
            "trades_4h": len(m_4h),
            "wr_4h": wr_4h,
            "avg_mae": avg_mae_m,
            "avg_mfe": avg_mfe_m
        }

    # Per-Coin breakdown for Sell Trades
    coin_data = {}
    for sym in TOP_22_CHAMPIONS:
        c_trades = [t for t in sell_trades if t["sym"] == sym]
        if not c_trades:
            continue
        c_wins = [t for t in c_trades if t["res"] == "WIN"]
        c_losses = [t for t in c_trades if t["res"] == "LOSS"]
        c_wr = (len(c_wins) / len(c_trades)) * 100.0
        c_mae = sum(t["mae_pct"] for t in c_trades) / len(c_trades)
        c_mfe = sum(t["mfe_pct"] for t in c_trades) / len(c_trades)
        coin_data[sym] = {
            "sym": sym,
            "total": len(c_trades),
            "wins": len(c_wins),
            "losses": len(c_losses),
            "win_rate": c_wr,
            "avg_mae": c_mae,
            "avg_mfe": c_mfe
        }

    results = {
        "stats_1h": s_1h,
        "stats_4h": s_4h,
        "stats_combined": s_comb,
        "monthly_data": monthly_data,
        "coin_data": coin_data,
        "trades_sample": sell_trades[:20]
    }

    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hermes25_2year_sell_trades_mae_mfe.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[OK] Audit complete! Saved to {out_file}")

if __name__ == "__main__":
    run_sell_backtest_with_mae_mfe()
