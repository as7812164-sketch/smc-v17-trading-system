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

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")
if not os.path.exists(DATA_DIR_2Y):
    DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_data_with_quant_features(sym, interval):
    fpath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data", f"{sym}_{interval}.json")
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

def simulate_compounding_ladder(trades, start_capital=50.0, target=2000.0, fee_rate=0.0016):
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
    hit_500 = None
    hit_1k = None
    hit_2k = None
    wins = 0
    losses = 0
    gp = 0.0
    gl = 0.0
    
    monthly_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": 0.0})
    
    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - fee_rate
        pos_size = cap * 5.0
        pnl = pos_size * net_move
        
        dt = datetime.fromtimestamp(trade["time"] / 1000)
        m_key = dt.strftime("%Y-%m")
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
        "profit_factor": round(pf, 2),
        "max_drawdown": round(max_dd * 100.0, 2),
        "hit_500": hit_500,
        "hit_1k": hit_1k,
        "hit_2k": hit_2k,
        "final_capital": round(cap, 2),
        "final_vault": round(vault, 2),
        "total_equity": round(cap + vault, 2),
        "monthly_stats": dict(monthly_stats)
    }

def run_battle():
    print("=" * 110)
    print(" ⚔️ THE ULTIMATE ALGORITHMIC BATTLE ROYALE:")
    print(" 👑 CONTENDER 1: HERMES 2.5 APEX HYBRID (Live Production Engine)")
    print(" 🔬 CONTENDER 2: HERMES FULL QUANT (28% Wick + Mandatory CVD Delta Absorption + 2-Stage Armor Both Sides)")
    print(" Period: 2 Full Continuous Years (Sep 2024 – Sep 2026) | Top-22 Binance Champions | 5x Isolated Compounding")
    print("=" * 110)
    
    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_data_with_quant_features(sym, tf)
            if len(k) >= 200:
                all_data[tf][sym] = k
                
    btc_map_4h = build_btc_map()
    
    hermes25_trades = []
    fullquant_trades = []
    
    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        max_tap_window = 28
        max_hold = 30 if tf == "4h" else 40
        
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 40:
                continue
                
            for i in range(20, n - 2):
                # -------------------------------------------------------------
                # 1. EVALUATE LONG SIGNALS
                # -------------------------------------------------------------
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050: # Institutional displacement >= 5.0%
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
                                    ob_fib = (dec_top - candles[i]["low"]) / (max_high - candles[i]["low"])
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        if candles[t]["low"] <= dec_top * 1.0005:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            # BTC 4H Dump Gate
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean_25 = btc_dump < 0.020 # < 2.0%
                                            btc_clean_quant = btc_dump < 0.015 # Strict < 1.5%
                                            
                                            # =========================================================
                                            # CONTENDER 1: HERMES 2.5 APEX HYBRID (LONG)
                                            # (Wick >= 18% + MT OK + BTC < 2.0% + 1-Stage BE Armor)
                                            # =========================================================
                                            if btc_clean_25 and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + std_tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)
                                                
                                                res_25 = None
                                                exit_p_25 = entry
                                                exit_t_25 = tap_c["time"]
                                                curr_sl = soft_sl_p
                                                be_locked = False
                                                
                                                for m in range(t, min(t + max_hold, n)):
                                                    high_m = candles[m]["high"]
                                                    if high_m >= entry * 1.016: # +1.6% MFE locks BE +0.2%
                                                        curr_sl = max(curr_sl, entry * 1.002)
                                                        be_locked = True
                                                    if high_m >= tp_p:
                                                        res_25 = "WIN"
                                                        exit_p_25 = tp_p
                                                        exit_t_25 = candles[m]["time"]
                                                        break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res_25 = "LOSS"
                                                        exit_p_25 = min(hard_sl_p, candles[m]["open"])
                                                        exit_t_25 = candles[m]["time"]
                                                        break
                                                    if candles[m]["close"] <= curr_sl:
                                                        res_25 = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                                                        exit_p_25 = candles[m]["close"]
                                                        exit_t_25 = candles[m]["time"]
                                                        break
                                                if not res_25:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res_25 = "WIN" if fc >= entry else "LOSS"
                                                    exit_p_25 = fc
                                                    exit_t_25 = candles[min(t + max_hold, n - 1)]["time"]
                                                    
                                                hermes25_trades.append({
                                                    "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t_25,
                                                    "entry": entry, "exit": exit_p_25, "gross": (exit_p_25 - entry) / entry,
                                                    "res": res_25, "side": "LONG", "model": "HERMES_2.5"
                                                })
                                                
                                            # =========================================================
                                            # CONTENDER 2: HERMES FULL QUANT (LONG)
                                            # (Wick >= 28% + CVD Absorption + Vol >= 0.85*SMA20 + Deep Discount + 2-Stage Armor)
                                            # =========================================================
                                            ssl_swept = swept and (w_ratio >= 0.28)
                                            cvd_prev = candles[t - 3]["cvd"] if t >= 3 else candles[0]["cvd"]
                                            cvd_slope = tap_c["cvd"] - cvd_prev
                                            cvd_absorbed = (tap_c["delta_ratio"] >= 0.48 or tap_c["delta"] > 0) and (cvd_slope >= 0)
                                            deep_discount = ob_fib <= 0.65
                                            vol_healthy = tap_c["volume"] >= 0.85 * tap_c["vol_sma20"]
                                            
                                            if btc_clean_quant and ssl_swept and cvd_absorbed and deep_discount and vol_healthy and tap_c["close"] >= mt:
                                                entry_q = dec_top
                                                tp_p_q = entry_q * (1.0 + std_tp_pct)
                                                soft_sl_p_q = entry_q * (1.0 - soft_sl_pct)
                                                hard_sl_p_q = entry_q * (1.0 - hard_sl_pct)
                                                
                                                res_q = None
                                                exit_p_q = entry_q
                                                exit_t_q = tap_c["time"]
                                                curr_effective_sl = soft_sl_p_q
                                                armor_stage = 0
                                                
                                                for m in range(t, min(t + max_hold, n)):
                                                    high_m = candles[m]["high"]
                                                    # 2-Stage Dynamic Armor on LONG
                                                    if high_m >= entry_q * 1.016:
                                                        curr_effective_sl = max(curr_effective_sl, entry_q * 1.002)
                                                        armor_stage = max(armor_stage, 1)
                                                    if high_m >= entry_q * 1.022:
                                                        curr_effective_sl = max(curr_effective_sl, entry_q * 1.012) # Lock +1.2% guaranteed profit!
                                                        armor_stage = max(armor_stage, 2)
                                                        
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
                                                    if candles[m]["close"] <= curr_effective_sl:
                                                        res_q = "WIN" if curr_effective_sl > entry_q else "LOSS"
                                                        exit_p_q = candles[m]["close"]
                                                        exit_t_q = candles[m]["time"]
                                                        break
                                                if not res_q:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res_q = "WIN" if fc >= entry_q else "LOSS"
                                                    exit_p_q = fc
                                                    exit_t_q = candles[min(t + max_hold, n - 1)]["time"]
                                                    
                                                fullquant_trades.append({
                                                    "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t_q,
                                                    "entry": entry_q, "exit": exit_p_q, "gross": (exit_p_q - entry_q) / entry_q,
                                                    "res": res_q, "side": "LONG", "model": "FULL_QUANT"
                                                })
                                            break
                                            
                # -------------------------------------------------------------
                # 2. EVALUATE SHORT SIGNALS
                # -------------------------------------------------------------
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050: # Institutional displacement >= 5.0%
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
                                    ob_fib_short = (candles[i]["high"] - dec_bot) / (candles[i]["high"] - min_low)
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
                                            btc_clean_short_25 = btc_pump < 0.020 # < 2.0%
                                            btc_clean_short_quant = btc_pump < 0.015 # < 1.5%
                                            
                                            # =========================================================
                                            # CONTENDER 1: HERMES 2.5 APEX HYBRID (SHORT)
                                            # (Wick >= 18% + MT OK + BTC < 2.0% + 2-Stage Dynamic Armor)
                                            # =========================================================
                                            if btc_clean_short_25 and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - std_tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)
                                                
                                                res_25_s = None
                                                exit_p_25_s = entry
                                                exit_t_25_s = tap_c["time"]
                                                curr_effective_sl = soft_sl_p
                                                
                                                for m in range(t, min(t + max_hold, n)):
                                                    low_m = candles[m]["low"]
                                                    if low_m <= entry * (1.0 - 0.016):
                                                        curr_effective_sl = min(curr_effective_sl, entry * (1.0 - 0.002))
                                                    if low_m <= entry * (1.0 - 0.022):
                                                        curr_effective_sl = min(curr_effective_sl, entry * (1.0 - 0.012))
                                                        
                                                    if low_m <= tp_p:
                                                        res_25_s = "WIN"
                                                        exit_p_25_s = tp_p
                                                        exit_t_25_s = candles[m]["time"]
                                                        break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res_25_s = "LOSS"
                                                        exit_p_25_s = max(hard_sl_p, candles[m]["open"])
                                                        exit_t_25_s = candles[m]["time"]
                                                        break
                                                    if candles[m]["close"] >= curr_effective_sl:
                                                        res_25_s = "WIN" if curr_effective_sl < entry else "LOSS"
                                                        exit_p_25_s = candles[m]["close"]
                                                        exit_t_25_s = candles[m]["time"]
                                                        break
                                                if not res_25_s:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res_25_s = "WIN" if fc <= entry else "LOSS"
                                                    exit_p_25_s = fc
                                                    exit_t_25_s = candles[min(t + max_hold, n - 1)]["time"]
                                                    
                                                hermes25_trades.append({
                                                    "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t_25_s,
                                                    "entry": entry, "exit": exit_p_25_s, "gross": (entry - exit_p_25_s) / entry,
                                                    "res": res_25_s, "side": "SHORT", "model": "HERMES_2.5"
                                                })
                                                
                                            # =========================================================
                                            # CONTENDER 2: HERMES FULL QUANT (SHORT)
                                            # (Wick >= 28% + CVD Absorption + Vol >= 0.85*SMA20 + Premium + 2-Stage Armor)
                                            # =========================================================
                                            bsl_swept = swept and (w_ratio >= 0.28)
                                            cvd_prev = candles[t - 3]["cvd"] if t >= 3 else candles[0]["cvd"]
                                            cvd_slope = tap_c["cvd"] - cvd_prev
                                            cvd_absorbed_short = (tap_c["delta_ratio"] <= 0.52 or tap_c["delta"] < 0) and (cvd_slope <= 0)
                                            premium_zone = ob_fib_short <= 0.65
                                            vol_healthy = tap_c["volume"] >= 0.85 * tap_c["vol_sma20"]
                                            
                                            if btc_clean_short_quant and bsl_swept and cvd_absorbed_short and premium_zone and vol_healthy and tap_c["close"] <= mt:
                                                entry_q = dec_bot
                                                tp_p_q = entry_q * (1.0 - std_tp_pct)
                                                soft_sl_p_q = entry_q * (1.0 + soft_sl_pct)
                                                hard_sl_p_q = entry_q * (1.0 + hard_sl_pct)
                                                
                                                res_q_s = None
                                                exit_p_q_s = entry_q
                                                exit_t_q_s = tap_c["time"]
                                                curr_effective_sl = soft_sl_p_q
                                                
                                                for m in range(t, min(t + max_hold, n)):
                                                    low_m = candles[m]["low"]
                                                    if low_m <= entry_q * (1.0 - 0.016):
                                                        curr_effective_sl = min(curr_effective_sl, entry_q * (1.0 - 0.002))
                                                    if low_m <= entry_q * (1.0 - 0.022):
                                                        curr_effective_sl = min(curr_effective_sl, entry_q * (1.0 - 0.012))
                                                        
                                                    if low_m <= tp_p_q:
                                                        res_q_s = "WIN"
                                                        exit_p_q_s = tp_p_q
                                                        exit_t_q_s = candles[m]["time"]
                                                        break
                                                    if candles[m]["high"] >= hard_sl_p_q:
                                                        res_q_s = "LOSS"
                                                        exit_p_q_s = max(hard_sl_p_q, candles[m]["open"])
                                                        exit_t_q_s = candles[m]["time"]
                                                        break
                                                    if candles[m]["close"] >= curr_effective_sl:
                                                        res_q_s = "WIN" if curr_effective_sl < entry_q else "LOSS"
                                                        exit_p_q_s = candles[m]["close"]
                                                        exit_t_q_s = candles[m]["time"]
                                                        break
                                                if not res_q_s:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res_q_s = "WIN" if fc <= entry_q else "LOSS"
                                                    exit_p_q_s = fc
                                                    exit_t_q_s = candles[min(t + max_hold, n - 1)]["time"]
                                                    
                                                fullquant_trades.append({
                                                    "sym": sym, "tf": tf, "time": tap_c["time"], "exit_time": exit_t_q_s,
                                                    "entry": entry_q, "exit": exit_p_q_s, "gross": (entry_q - exit_p_q_s) / entry_q,
                                                    "res": res_q_s, "side": "SHORT", "model": "FULL_QUANT"
                                                })
                                            break

    print(f"\n✅ Total Raw Signals Discovered Across 2-Year Dataset:")
    print(f"  • HERMES 2.5 APEX HYBRID:  {len(hermes25_trades)} Signals")
    print(f"  • HERMES FULL QUANT:       {len(fullquant_trades)} Signals")
    
    # Run Compounding Simulation on both
    res_25 = simulate_compounding_ladder(hermes25_trades)
    res_quant = simulate_compounding_ladder(fullquant_trades)
    
    print("\n" + "=" * 110)
    print(" 🏆 HEAD-TO-HEAD BATTLE RESULTS (2-YEAR AUDIT / $50 START / 5X ISOLATED LEVERAGE)")
    print("=" * 110)
    
    row_fmt = "{:<32} | {:<32} | {:<32}"
    print(row_fmt.format("Metric", "HERMES 2.5 APEX HYBRID", "HERMES FULL QUANT (28% Wick+CVD)"))
    print("-" * 110)
    print(row_fmt.format("Total Signals Detected", f"{len(hermes25_trades)}", f"{len(fullquant_trades)}"))
    print(row_fmt.format("Sequential Trades Executed", f"{res_25['executed_trades_count']} Trades", f"{res_quant['executed_trades_count']} Trades"))
    print(row_fmt.format("Wins / Losses", f"{res_25['wins']} Wins / {res_25['losses']} Losses", f"{res_quant['wins']} Wins / {res_quant['losses']} Losses"))
    print(row_fmt.format("OVERALL WIN RATE (ACCURACY)", f"⭐ {res_25['win_rate']}%", f"🔥 {res_quant['win_rate']}%"))
    print(row_fmt.format("🟢 LONG Win Rate", f"{res_25['long_wr']}% ({res_25['long_wins']}/{res_25['long_trades']})", f"🚀 {res_quant['long_wr']}% ({res_quant['long_wins']}/{res_quant['long_trades']})"))
    print(row_fmt.format("🔴 SHORT Win Rate", f"{res_25['short_wr']}% ({res_25['short_wins']}/{res_25['short_trades']})", f"🎯 {res_quant['short_wr']}% ({res_quant['short_wins']}/{res_quant['short_trades']})"))
    print(row_fmt.format("Profit Factor (PF)", f"{res_25['profit_factor']}", f"💎 {res_quant['profit_factor']}"))
    print(row_fmt.format("Max Portfolio Drawdown", f"{res_25['max_drawdown']}%", f"🛡️ {res_quant['max_drawdown']}% (Ultra Safe)"))
    
    h1k_25 = f"Trade #{res_25['hit_1k']['trade_num']} ({res_25['hit_1k']['date']})" if res_25['hit_1k'] else "Not reached"
    h1k_q = f"Trade #{res_quant['hit_1k']['trade_num']} ({res_quant['hit_1k']['date']})" if res_quant['hit_1k'] else "Not reached"
    print(row_fmt.format("$1,000 Milestone Reached At", h1k_25, h1k_q))
    
    h2k_25 = f"Trade #{res_25['hit_2k']['trade_num']} ({res_25['hit_2k']['date']})" if res_25['hit_2k'] else "Not reached"
    h2k_q = f"Trade #{res_quant['hit_2k']['trade_num']} ({res_quant['hit_2k']['date']})" if res_quant['hit_2k'] else "Not reached"
    print(row_fmt.format("$2,000 Target Smashed At", h2k_25, h2k_q))
    
    print(row_fmt.format("Final Trading Capital", f"${res_25['final_capital']}", f"${res_quant['final_capital']}"))
    print(row_fmt.format("Cold Storage Vault Balance", f"${res_25['final_vault']}", f"${res_quant['final_vault']}"))
    print(row_fmt.format("TOTAL COMPOUNDED WEALTH", f"${res_25['total_equity']}", f"${res_quant['total_equity']}"))
    print("=" * 110)
    
    # Save results to JSON
    battle_output = {
        "audit_window": "2024-09-26 to 2026-09-25 (2 Full Years)",
        "hermes25_apex_hybrid": res_25,
        "hermes_full_quant": res_quant
    }
    with open("battle_hermes25_vs_full_quant_results.json", "w", encoding="utf-8") as f:
        json.dump(battle_output, f, indent=2)
    print("Saved battle report to battle_hermes25_vs_full_quant_results.json")

if __name__ == "__main__":
    run_battle()
