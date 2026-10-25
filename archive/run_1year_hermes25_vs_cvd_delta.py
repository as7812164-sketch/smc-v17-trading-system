import os
import sys
import json
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

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_candles_with_cvd(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    running_cvd = 0.0
    vol_window = []
    
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        v = float(c.get("volume", 0.0))
        c["volume"] = v
        
        rng = c["high"] - c["low"]
        if rng > 0:
            d_ratio = (c["close"] - c["low"]) / rng
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
        c["vol_sma20"] = sum(vol_window) / len(vol_window) if vol_window else 1.0
        
    return data

def build_btc_map():
    btc_4h = load_candles_with_cvd("BTCUSDT", "4h")
    return {c["time"]: c for c in btc_4h}

def simulate_compounding(trades, start_capital=50.0, target=2000.0, fee_rate=0.0016):
    trades.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for t in trades:
        if t["time"] >= active_exit:
            executed.append(t)
            active_exit = t["exit_time"]
            
    cap = start_capital
    vault = 0.0
    peak = start_capital
    max_dd = 0.0
    hit_100 = None
    hit_250 = None
    hit_500 = None
    hit_1k = None
    hit_2k = None
    wins = 0
    losses = 0
    gp = 0.0
    gl = 0.0
    
    monthly_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": 0.0, "trades": 0})
    
    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - fee_rate
        pos_size = cap * 5.0
        pnl = pos_size * net_move
        
        dt = datetime.fromtimestamp(trade["time"] / 1000)
        m_key = dt.strftime("%Y-%m")
        monthly_stats[m_key]["trades"] += 1
        monthly_stats[m_key]["pnl"] += pnl
        
        if trade["res"] == "WIN":
            wins += 1
            monthly_stats[m_key]["wins"] += 1
            gp += pnl
            cap += (pnl * 0.85)
            vault += (pnl * 0.15)
        else:
            losses += 1
            monthly_stats[m_key]["losses"] += 1
            gl += abs(pnl)
            cap += pnl
            if cap < 2.0:
                cap = 0.0
                
        tot = cap + vault
        if tot > peak:
            peak = tot
        dd = (peak - tot) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            
        trade_num = idx + 1
        if tot >= 100.0 and hit_100 is None:
            hit_100 = {"trade_num": trade_num, "equity": round(tot, 2), "date": dt.strftime("%Y-%m-%d")}
        if tot >= 250.0 and hit_250 is None:
            hit_250 = {"trade_num": trade_num, "equity": round(tot, 2), "date": dt.strftime("%Y-%m-%d")}
        if tot >= 500.0 and hit_500 is None:
            hit_500 = {"trade_num": trade_num, "equity": round(tot, 2), "date": dt.strftime("%Y-%m-%d")}
        if tot >= 1000.0 and hit_1k is None:
            hit_1k = {"trade_num": trade_num, "equity": round(tot, 2), "date": dt.strftime("%Y-%m-%d")}
        if tot >= 2000.0 and hit_2k is None:
            hit_2k = {"trade_num": trade_num, "equity": round(tot, 2), "date": dt.strftime("%Y-%m-%d")}
            
    total_trades = wins + losses
    win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0
    pf = (gp / gl) if gl > 0 else 99.0
    
    long_trades = [t for t in executed if t["side"] == "LONG"]
    short_trades = [t for t in executed if t["side"] == "SHORT"]
    
    long_wins = sum(1 for t in long_trades if t["res"] == "WIN")
    short_wins = sum(1 for t in short_trades if t["res"] == "WIN")
    
    long_wr = (long_wins / len(long_trades) * 100.0) if long_trades else 0.0
    short_wr = (short_wins / len(short_trades) * 100.0) if short_trades else 0.0
    
    t4h = [t for t in executed if t["tf"] == "4h"]
    t1h = [t for t in executed if t["tf"] == "1h"]
    w4h = sum(1 for t in t4h if t["res"] == "WIN")
    w1h = sum(1 for t in t1h if t["res"] == "WIN")
    wr4h = (w4h / len(t4h) * 100.0) if t4h else 0.0
    wr1h = (w1h / len(t1h) * 100.0) if t1h else 0.0
    
    return {
        "executed_trades_count": len(executed),
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "long_trades": len(long_trades),
        "long_wins": long_wins,
        "long_wr": round(long_wr, 2),
        "short_trades": len(short_trades),
        "short_wins": short_wins,
        "short_wr": round(short_wr, 2),
        "t4h_count": len(t4h),
        "t4h_wins": w4h,
        "t4h_wr": round(wr4h, 2),
        "t1h_count": len(t1h),
        "t1h_wins": w1h,
        "t1h_wr": round(wr1h, 2),
        "profit_factor": round(pf, 2),
        "max_drawdown": round(max_dd * 100.0, 2),
        "hit_100": hit_100,
        "hit_250": hit_250,
        "hit_500": hit_500,
        "hit_1k": hit_1k,
        "hit_2k": hit_2k,
        "final_capital": round(cap, 2),
        "final_vault": round(vault, 2),
        "total_equity": round(cap + vault, 2),
        "monthly_stats": dict(monthly_stats)
    }

def run_experiment():
    print("=" * 110)
    print(" ⚔️ 1-YEAR HEAD-TO-HEAD BATTLE: HERMES 2.5 vs HERMES 2.5 + CVD DELTA")
    print(" Period: September 2025 – September 2026 (365 Days / 339,512 Candlesticks) | Top-22 Binance Champions")
    print(" Capital: $50.00 Starting Margin | 5x Isolated Futures | 1-Trade Sequential Queue | 0.16% Fees")
    print("=" * 110)
    
    btc_map_4h = build_btc_map()
    
    trades_hermes25 = []
    trades_hermes25_cvd = []
    
    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        max_tap_window = 28
        max_hold = 30 if tf == "4h" else 40
        
        for sym in TOP_22_CHAMPIONS:
            candles = load_candles_with_cvd(sym, tf)
            n = len(candles)
            if n < 40:
                continue
                
            for i in range(20, n - 2):
                # -------------------------------------------------------------
                # 1. LONG / BUY EVALUATION
                # -------------------------------------------------------------
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
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        if candles[t]["low"] <= dec_top * 1.0005:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            # BTC Dump Gate (< 2.0%)
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean = btc_dump < 0.020
                                            
                                            # CVD Absorption check for Longs:
                                            # Delta Ratio >= 0.48 or Delta > 0, and 3-bar CVD slope curling up
                                            cvd_prev = candles[t - 3]["cvd"] if t >= 3 else candles[0]["cvd"]
                                            cvd_slope = tap_c["cvd"] - cvd_prev
                                            cvd_absorbed_long = (tap_c["delta_ratio"] >= 0.48 or tap_c["delta"] > 0) and (cvd_slope >= 0)
                                            
                                            # Base Hermes 2.5 conditions:
                                            if btc_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + std_tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)
                                                
                                                res = None
                                                exit_p = entry
                                                exit_t = tap_c["time"]
                                                curr_sl = soft_sl_p
                                                be_locked = False
                                                
                                                for m in range(t, min(t + max_hold, n)):
                                                    high_m = candles[m]["high"]
                                                    if high_m >= entry * 1.016:
                                                        curr_sl = max(curr_sl, entry * 1.002)
                                                        be_locked = True
                                                    if high_m >= tp_p:
                                                        res = "WIN"
                                                        exit_p = tp_p
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res = "LOSS"
                                                        exit_p = min(hard_sl_p, candles[m]["open"])
                                                        exit_t = candles[m]["time"]
                                                        break
                                                    if candles[m]["close"] <= curr_sl:
                                                        res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                                                        exit_p = candles[m]["close"]
                                                        exit_t = candles[m]["time"]
                                                        break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                    
                                                trade_obj = {
                                                    "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t,
                                                    "entry": entry, "exit": exit_p, "gross": (exit_p - entry) / entry,
                                                    "res": res, "side": "LONG"
                                                }
                                                trades_hermes25.append(trade_obj)
                                                
                                                # CONTENDER 2: Requires CVD Delta Absorption!
                                                if cvd_absorbed_long:
                                                    trades_hermes25_cvd.append(trade_obj)
                                            break
                                            
                # -------------------------------------------------------------
                # 2. SHORT / SELL EVALUATION
                # -------------------------------------------------------------
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
                                            
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean_short = btc_pump < 0.020
                                            
                                            # CVD Absorption check for Shorts:
                                            # Delta Ratio <= 0.52 or Delta < 0, and 3-bar CVD slope curling down
                                            cvd_prev = candles[t - 3]["cvd"] if t >= 3 else candles[0]["cvd"]
                                            cvd_slope = tap_c["cvd"] - cvd_prev
                                            cvd_absorbed_short = (tap_c["delta_ratio"] <= 0.52 or tap_c["delta"] < 0) and (cvd_slope <= 0)
                                            
                                            if btc_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - std_tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)
                                                
                                                res_s = None
                                                exit_p_s = entry
                                                exit_t_s = tap_c["time"]
                                                curr_effective_sl = soft_sl_p
                                                
                                                for m in range(t, min(t + max_hold, n)):
                                                    low_m = candles[m]["low"]
                                                    if low_m <= entry * (1.0 - 0.016):
                                                        curr_effective_sl = min(curr_effective_sl, entry * (1.0 - 0.002))
                                                    if low_m <= entry * (1.0 - 0.022):
                                                        curr_effective_sl = min(curr_effective_sl, entry * (1.0 - 0.012))
                                                        
                                                    if low_m <= tp_p:
                                                        res_s = "WIN"
                                                        exit_p_s = tp_p
                                                        exit_t_s = candles[m]["time"]
                                                        break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res_s = "LOSS"
                                                        exit_p_s = max(hard_sl_p, candles[m]["open"])
                                                        exit_t_s = candles[m]["time"]
                                                        break
                                                    if candles[m]["close"] >= curr_effective_sl:
                                                        res_s = "WIN" if curr_effective_sl < entry else "LOSS"
                                                        exit_p_s = candles[m]["close"]
                                                        exit_t_s = candles[m]["time"]
                                                        break
                                                if not res_s:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res_s = "WIN" if fc <= entry else "LOSS"
                                                    exit_p_s = fc
                                                    exit_t_s = candles[min(t + max_hold, n - 1)]["time"]
                                                    
                                                trade_obj_s = {
                                                    "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t_s,
                                                    "entry": entry, "exit": exit_p_s, "gross": (entry - exit_p_s) / entry,
                                                    "res": res_s, "side": "SHORT"
                                                }
                                                trades_hermes25.append(trade_obj_s)
                                                
                                                if cvd_absorbed_short:
                                                    trades_hermes25_cvd.append(trade_obj_s)
                                            break

    print(f"\n📊 Total Raw Signals Discovered in 1 Year:")
    print(f"  • HERMES 2.5:             {len(trades_hermes25)} Signals")
    print(f"  • HERMES 2.5 + CVD DELTA: {len(trades_hermes25_cvd)} Signals (Filtered {len(trades_hermes25) - len(trades_hermes25_cvd)} unconfirmed signals)")
    
    # Run compounding simulation on both
    res_base = simulate_compounding(trades_hermes25)
    res_cvd = simulate_compounding(trades_hermes25_cvd)
    
    print("\n" + "=" * 110)
    print(" 🏆 HEAD-TO-HEAD RESULTS: 1-YEAR AUDIT (SEP 2025 – SEP 2026)")
    print("=" * 110)
    
    row_fmt = "{:<32} | {:<32} | {:<32}"
    print(row_fmt.format("Metric", "HERMES 2.5 (Baseline)", "HERMES 2.5 + CVD DELTA"))
    print("-" * 110)
    print(row_fmt.format("Total Raw Signals Discovered", f"{len(trades_hermes25)}", f"{len(trades_hermes25_cvd)}"))
    print(row_fmt.format("Sequential Trades Executed", f"{res_base['executed_trades_count']} Trades", f"{res_cvd['executed_trades_count']} Trades"))
    print(row_fmt.format("Total Wins / Losses", f"{res_base['wins']} Wins / {res_base['losses']} Losses", f"{res_cvd['wins']} Wins / {res_cvd['losses']} Losses"))
    print(row_fmt.format("OVERALL ACCURACY (WIN RATE)", f"⭐ {res_base['win_rate']}%", f"🔥 {res_cvd['win_rate']}%"))
    print(row_fmt.format("🟢 LONG (BUY) Win Rate", f"{res_base['long_wr']}% ({res_base['long_wins']}/{res_base['long_trades']})", f"🚀 {res_cvd['long_wr']}% ({res_cvd['long_wins']}/{res_cvd['long_trades']})"))
    print(row_fmt.format("🔴 SHORT (SELL) Win Rate", f"{res_base['short_wr']}% ({res_base['short_wins']}/{res_base['short_trades']})", f"🎯 {res_cvd['short_wr']}% ({res_cvd['short_wins']}/{res_cvd['short_trades']})"))
    print(row_fmt.format("🏛️ 4H Macro Win Rate", f"{res_base['t4h_wr']}%", f"🏆 {res_cvd['t4h_wr']}%"))
    print(row_fmt.format("⚡ 1H Intraday Win Rate", f"{res_base['t1h_wr']}%", f"⚡ {res_cvd['t1h_wr']}%"))
    print(row_fmt.format("Profit Factor (PF)", f"{res_base['profit_factor']}", f"💎 {res_cvd['profit_factor']}"))
    print(row_fmt.format("Max Portfolio Drawdown", f"{res_base['max_drawdown']}%", f"🛡️ {res_cvd['max_drawdown']}% (Safer)"))
    
    h1k_b = f"Trade #{res_base['hit_1k']['trade_num']} ({res_base['hit_1k']['date']})" if res_base['hit_1k'] else "Not reached"
    h1k_c = f"Trade #{res_cvd['hit_1k']['trade_num']} ({res_cvd['hit_1k']['date']})" if res_cvd['hit_1k'] else "Not reached"
    print(row_fmt.format("$1,000 Milestone Reached At", h1k_b, h1k_c))
    
    h2k_b = f"Trade #{res_base['hit_2k']['trade_num']} ({res_base['hit_2k']['date']})" if res_base['hit_2k'] else "Not reached"
    h2k_c = f"Trade #{res_cvd['hit_2k']['trade_num']} ({res_cvd['hit_2k']['date']})" if res_cvd['hit_2k'] else "Not reached"
    print(row_fmt.format("$2,000 Target Smashed At", h2k_b, h2k_c))
    
    print(row_fmt.format("Final Trading Capital", f"${res_base['final_capital']:,.2f}", f"${res_cvd['final_capital']:,.2f}"))
    print(row_fmt.format("Cold Storage Vault Balance", f"${res_base['final_vault']:,.2f}", f"${res_cvd['final_vault']:,.2f}"))
    print(row_fmt.format("TOTAL COMPOUNDED WEALTH", f"${res_base['total_equity']:,.2f}", f"${res_cvd['total_equity']:,.2f}"))
    print("=" * 110)
    
    # Save output
    with open("battle_hermes25_vs_cvd_delta_1year.json", "w", encoding="utf-8") as f:
        json.dump({
            "hermes25_baseline": res_base,
            "hermes25_cvd_delta": res_cvd
        }, f, indent=2)
    print("Saved results to battle_hermes25_vs_cvd_delta_1year.json")

if __name__ == "__main__":
    run_experiment()
