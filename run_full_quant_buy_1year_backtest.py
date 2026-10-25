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

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_data_with_quant_features(sym, interval):
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
    btc_4h = load_data_with_quant_features("BTCUSDT", "4h")
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
    hit_1k = None
    hit_2k = None
    wins = 0
    losses = 0
    gp = 0.0
    gl = 0.0
    
    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - fee_rate
        pos_size = cap * 5.0
        pnl = pos_size * net_move
        
        if trade["res"] == "WIN":
            wins += 1
            gp += pnl
            cap += (pnl * 0.85)
            vault += (pnl * 0.15)
        else:
            losses += 1
            gl += abs(pnl)
            cap += pnl
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
        if tot >= target and hit_2k is None:
            hit_2k = idx + 1
            
    tot_trades = wins + losses
    wr = (wins / tot_trades * 100.0) if tot_trades > 0 else 0.0
    pf = (gp / gl) if gl > 0 else 99.0
    
    return {
        "executed_trades": executed,
        "total_trades": tot_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "profit_factor": round(pf, 2),
        "max_drawdown": round(max_dd, 2),
        "hit_1k": hit_1k,
        "hit_2k": hit_2k,
        "final_capital": round(cap, 2),
        "final_vault": round(vault, 2),
        "total_equity": round(cap + vault, 2)
    }

def run_backtest():
    print("=" * 100)
    print(" 🚀 1-YEAR (365 DAYS) FULL QUANT BUY / LONG STRATEGY BACKTEST")
    print(" Top-22 Champions | Binance Futures Dataset | Period: Sep 2025 - Sep 2026")
    print(" Features: CVD Absorption + SSL Sweeps + Deep Discount FVG + King BTC Gate + Dynamic Armor")
    print("=" * 100)
    
    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_data_with_quant_features(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k
                
    btc_map_4h = build_btc_map()
    
    baseline_trades_4h = []
    baseline_trades_all = []
    
    full_quant_trades_4h = []
    full_quant_trades_all = []
    
    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        max_tap_window = 28
        max_hold = 30 if tf == "4h" else 40
        
        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                # Origin of impulse: 15-bar local swing low
                if candles[i]["low"] != min(c["low"] for c in candles[i-15:i+1]):
                    continue
                    
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx <= i + 3:
                    continue
                    
                gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                if gain < 0.050: # Institutional displacement >= 5%
                    continue
                    
                idm_low = candles[high_idx - 1]["low"]
                
                # Scan for OB / FVG
                best_mid = -1
                max_bg = 0.0
                for mid in range(i+1, high_idx):
                    bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                    fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                        max_bg = bg
                        best_mid = mid
                        
                if best_mid == -1:
                    continue
                    
                dec_c = candles[best_mid - 1]
                dec_top = max(dec_c["open"], dec_c["close"])
                dec_bot = dec_c["low"]
                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                
                if not has_fvg:
                    continue
                    
                # Fib level of OB
                ob_fib = (dec_top - candles[i]["low"]) / (max_high - candles[i]["low"])
                
                for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                    if candles[t]["low"] <= dec_top * 1.0005:
                        tap_c = candles[t]
                        
                        # BTC Macro Gate
                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                        btc_c = btc_map_4h.get(prev_4h_ts)
                        btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                        btc_clean_baseline = btc_dump < 0.020 # < 2.0%
                        btc_clean_quant = btc_dump < 0.015   # < 1.5% strict quant gate
                        
                        # Candle wick & sweep
                        c_range = tap_c["high"] - tap_c["low"]
                        swept_idm = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                        mt = (dec_top + dec_bot) / 2.0
                        
                        # ---------------------------------------------
                        # BASELINE HERMES 2.0 APEX EVALUATION
                        # ---------------------------------------------
                        if btc_clean_baseline and swept_idm and w_ratio >= 0.18 and tap_c["close"] >= mt:
                            entry = dec_top
                            tp_p = entry * (1.0 + std_tp_pct)
                            soft_sl_p = entry * (1.0 - soft_sl_pct)
                            hard_sl_p = entry * (1.0 - hard_sl_pct)
                            
                            res_base = None
                            exit_p_base = entry
                            exit_t_base = tap_c["time"]
                            for m in range(t, min(t + max_hold, n)):
                                if candles[m]["high"] >= tp_p:
                                    res_base = "WIN"
                                    exit_p_base = tp_p
                                    exit_t_base = candles[m]["time"]
                                    break
                                if candles[m]["low"] <= hard_sl_p:
                                    res_base = "LOSS"
                                    exit_p_base = min(hard_sl_p, candles[m]["open"])
                                    exit_t_base = candles[m]["time"]
                                    break
                                if candles[m]["close"] <= soft_sl_p:
                                    res_base = "LOSS"
                                    exit_p_base = candles[m]["close"]
                                    exit_t_base = candles[m]["time"]
                                    break
                            if not res_base:
                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                res_base = "WIN" if fc >= entry else "LOSS"
                                exit_p_base = fc
                                exit_t_base = candles[min(t + max_hold, n - 1)]["time"]
                                
                            t_base = {
                                "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t_base,
                                "entry": entry, "exit": exit_p_base, "gross": (exit_p_base - entry) / entry,
                                "res": res_base, "side": "LONG"
                            }
                            baseline_trades_all.append(t_base)
                            if tf == "4h":
                                baseline_trades_4h.append(t_base)
                                
                        # ---------------------------------------------
                        # FULL QUANT BUY EVALUATION (CVD + SSL + LIQ)
                        # ---------------------------------------------
                        # 1. SSL Sweep: Prior local swing low swept with lower wick >= 28%
                        ssl_swept = swept_idm and (w_ratio >= 0.28)
                        
                        # 2. CVD Absorption / Delta:
                        # Buyers absorbing at the sweep: delta_ratio >= 0.50 or positive delta
                        # and CVD curling up over 3 bars
                        cvd_prev = candles[t - 3]["cvd"] if t >= 3 else candles[0]["cvd"]
                        cvd_slope = tap_c["cvd"] - cvd_prev
                        cvd_absorbed = (tap_c["delta_ratio"] >= 0.48 or tap_c["delta"] > 0) and (cvd_slope >= 0)
                        
                        # 3. Deep Discount Zone check (fib <= 0.65 of impulse)
                        deep_discount = ob_fib <= 0.65
                        
                        # 4. Volume participation (Volume >= 0.85x SMA20)
                        vol_healthy = tap_c["volume"] >= 0.85 * tap_c["vol_sma20"]
                        
                        if btc_clean_quant and ssl_swept and cvd_absorbed and deep_discount and vol_healthy and tap_c["close"] >= mt:
                            entry_q = dec_top
                            tp_p_q = entry_q * (1.0 + std_tp_pct)
                            soft_sl_p_q = entry_q * (1.0 - soft_sl_pct)
                            hard_sl_p_q = entry_q * (1.0 - hard_sl_pct)
                            
                            # Dynamic Armor Execution (BE Lock at +1.6% MFE)
                            res_q = None
                            exit_p_q = entry_q
                            exit_t_q = tap_c["time"]
                            curr_sl = soft_sl_p_q
                            be_locked = False
                            
                            for m in range(t, min(t + max_hold, n)):
                                high_m = candles[m]["high"]
                                # BE Lock trigger at +1.6% move (+8% ROE)
                                if high_m >= entry_q * 1.016:
                                    curr_sl = max(curr_sl, entry_q * 1.002) # Protect entry + fees
                                    be_locked = True
                                    
                                if high_m >= tp_p_q:
                                    res_q = "WIN"
                                    exit_p_q = tp_p_q
                                    exit_t_q = candles[m]["time"]
                                    break
                                if candles[m]["low"] <= hard_sl_p_q:
                                    res_q = "LOSS"
                                    exit_p_q = min(hard_sl_p_q, candles[m]["open"])
                                    exit_t_q = candles[m]["time"]
                                    break
                                if candles[m]["close"] <= curr_sl:
                                    res_q = "WIN" if (be_locked and curr_sl > entry_q) else "LOSS"
                                    exit_p_q = candles[m]["close"]
                                    exit_t_q = candles[m]["time"]
                                    break
                                    
                            if not res_q:
                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                res_q = "WIN" if fc >= entry_q else "LOSS"
                                exit_p_q = fc
                                exit_t_q = candles[min(t + max_hold, n - 1)]["time"]
                                
                            t_quant = {
                                "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t_q,
                                "entry": entry_q, "exit": exit_p_q, "gross": (exit_p_q - entry_q) / entry_q,
                                "res": res_q, "side": "LONG", "be_locked": be_locked
                            }
                            full_quant_trades_all.append(t_quant)
                            if tf == "4h":
                                full_quant_trades_4h.append(t_quant)
                                
                        break

    return (
        baseline_trades_4h,
        baseline_trades_all,
        full_quant_trades_4h,
        full_quant_trades_all
    )

if __name__ == "__main__":
    b_4h, b_all, q_4h, q_all = run_backtest()
    
    print("\n" + "=" * 100)
    print(" 📊 RAW SIGNAL POOL COMPARISON (BEFORE SEQUENTIAL FILTER)")
    print("=" * 100)
    
    b_4h_w = sum(1 for x in b_4h if x["res"] == "WIN")
    b_4h_l = len(b_4h) - b_4h_w
    b_4h_wr = (b_4h_w / len(b_4h) * 100.0) if b_4h else 0.0
    
    q_4h_w = sum(1 for x in q_4h if x["res"] == "WIN")
    q_4h_l = len(q_4h) - q_4h_w
    q_4h_wr = (q_4h_w / len(q_4h) * 100.0) if q_4h else 0.0
    
    print(f"Baseline 4H BUY:    Total = {len(b_4h):3d} | Wins = {b_4h_w:3d} | Losses = {b_4h_l:3d} | Win Rate = {b_4h_wr:5.2f}%")
    print(f"Full Quant 4H BUY:  Total = {len(q_4h):3d} | Wins = {q_4h_w:3d} | Losses = {q_4h_l:3d} | Win Rate = {q_4h_wr:5.2f}%")
    
    b_all_w = sum(1 for x in b_all if x["res"] == "WIN")
    b_all_l = len(b_all) - b_all_w
    b_all_wr = (b_all_w / len(b_all) * 100.0) if b_all else 0.0
    
    q_all_w = sum(1 for x in q_all if x["res"] == "WIN")
    q_all_l = len(q_all) - q_all_w
    q_all_wr = (q_all_w / len(q_all) * 100.0) if q_all else 0.0
    
    print(f"Baseline 1H+4H BUY: Total = {len(b_all):3d} | Wins = {b_all_w:3d} | Losses = {b_all_l:3d} | Win Rate = {b_all_wr:5.2f}%")
    print(f"Full Quant 1H+4H:   Total = {len(q_all):3d} | Wins = {q_all_w:3d} | Losses = {q_all_l:3d} | Win Rate = {q_all_wr:5.2f}%")
    
    # Run Sequential Compounding ($50 -> $2,000 Milestone Ladder)
    print("\n" + "=" * 100)
    print(" 💰 SEQUENTIAL COMPOUNDING AUDIT ($50 START | 5x LEVERAGE | 85/15 VAULT SPLIT)")
    print("=" * 100)
    
    sim_b_4h = simulate_compounding(b_4h)
    sim_q_4h = simulate_compounding(q_4h)
    sim_b_all = simulate_compounding(b_all)
    sim_q_all = simulate_compounding(q_all)
    
    print(f"--- 4H Timeframe Only ---")
    print(f"Baseline 4H:   Trades={sim_b_4h['total_trades']} | WR={sim_b_4h['win_rate']}% | PF={sim_b_4h['profit_factor']} | MaxDD={sim_b_4h['max_drawdown']}% | Equity=${sim_b_4h['total_equity']:,.2f} | Hit $1k: {sim_b_4h['hit_1k']} | Hit $2k: {sim_b_4h['hit_2k']}")
    print(f"Full Quant 4H: Trades={sim_q_4h['total_trades']} | WR={sim_q_4h['win_rate']}% | PF={sim_q_4h['profit_factor']} | MaxDD={sim_q_4h['max_drawdown']}% | Equity=${sim_q_4h['total_equity']:,.2f} | Hit $1k: {sim_q_4h['hit_1k']} | Hit $2k: {sim_q_4h['hit_2k']}")
    
    print(f"\n--- 1H + 4H Combined ---")
    print(f"Baseline 1H+4H:   Trades={sim_b_all['total_trades']} | WR={sim_b_all['win_rate']}% | PF={sim_b_all['profit_factor']} | MaxDD={sim_b_all['max_drawdown']}% | Equity=${sim_b_all['total_equity']:,.2f} | Hit $1k: {sim_b_all['hit_1k']} | Hit $2k: {sim_b_all['hit_2k']}")
    print(f"Full Quant 1H+4H: Trades={sim_q_all['total_trades']} | WR={sim_q_all['win_rate']}% | PF={sim_q_all['profit_factor']} | MaxDD={sim_q_all['max_drawdown']}% | Equity=${sim_q_all['total_equity']:,.2f} | Hit $1k: {sim_q_all['hit_1k']} | Hit $2k: {sim_q_all['hit_2k']}")
    
    # Save results to json for detailed month-by-month and trade inspection
    output_res = {
        "baseline_4h": sim_b_4h,
        "full_quant_4h": sim_q_4h,
        "baseline_all": sim_b_all,
        "full_quant_all": sim_q_all
    }
    with open("full_quant_buy_1year_results.json", "w", encoding="utf-8") as f:
        # Avoid serializing executed_trades object directly if too large, just count & metrics
        summary_clean = {k: {m: v for m, v in val.items() if m != "executed_trades"} for k, val in output_res.items()}
        json.dump(summary_clean, f, indent=2)
    print("\nResults saved to full_quant_buy_1year_results.json")
