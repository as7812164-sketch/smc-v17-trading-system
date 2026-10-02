import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config import TOP_28_CHAMPIONS
from engine.hermes3_5_apex import hermes35_engine

IST = timezone(timedelta(hours=5, minutes=30))
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_data_with_quant_features(sym, interval):
    fpath = os.path.join(CACHE_DIR, f"{sym}_{interval}.json")
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

def build_btc_map(data_4h):
    btc_4h = data_4h.get("BTCUSDT", [])
    return {c["time"]: c for c in btc_4h}

def harvest_1year_top28_setups(all_data):
    btc_map_4h = build_btc_map(all_data["4h"])
    raw_setups = []
    
    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        max_tap_window = 28
        max_hold = 30 if tf == "4h" else 40
        
        for sym in TOP_28_CHAMPIONS:
            if sym == "BTCUSDT":
                continue
            candles = all_data[tf].get(sym, [])
            n = len(candles)
            if n < 40:
                continue
                
            atr = [0.0] * n
            for k in range(1, n):
                tr = max(candles[k]["high"] - candles[k]["low"],
                         abs(candles[k]["high"] - candles[k-1]["close"]),
                         abs(candles[k]["low"] - candles[k-1]["close"]))
                atr[k] = tr if k < 14 else (atr[k-1] * 13 + tr) / 14
                
            for i in range(15, n - 2):
                # -------------------------------------------------------------
                # LONG SETUPS
                # -------------------------------------------------------------
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-14):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 1:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.045: # Institutional displacement >= 4.5%
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.25 <= fib <= 0.75 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        if tap_c["low"] <= dec_top * 1.0005:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean = btc_dump < 0.020 # BTC Causal Brake (< 2.0% dump)
                                            
                                            if btc_clean and swept and w_ratio >= 0.15 and tap_c["close"] >= mt:
                                                sniper_pass, sniper_reason = hermes35_engine.evaluate_15m_micro_sniper_gate(tap_c, "LONG")
                                                tier_info = hermes35_engine.classify_dual_tier_setup(candles, t, "LONG")
                                                cvd_pass = tier_info.get("cvd_confirmed", False)
                                                
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold,
                                                    "sniper_pass": sniper_pass, "cvd_pass": cvd_pass,
                                                    "sniper_reason": sniper_reason
                                                })
                                                break
                
                # -------------------------------------------------------------
                # SHORT SETUPS
                # -------------------------------------------------------------
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-14):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 1:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.045: # Institutional displacement >= 4.5%
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.25 <= fib <= 0.75 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        if tap_c["high"] >= dec_bot * 0.9995:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean_short = btc_pump < 0.020 # BTC Causal Brake (< 2.0% pump)
                                            
                                            if btc_clean_short and swept and w_ratio >= 0.15 and tap_c["close"] <= mt:
                                                sniper_pass, sniper_reason = hermes35_engine.evaluate_15m_micro_sniper_gate(tap_c, "SHORT")
                                                tier_info = hermes35_engine.classify_dual_tier_setup(candles, t, "SHORT")
                                                cvd_pass = tier_info.get("cvd_confirmed", False)
                                                
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold,
                                                    "sniper_pass": sniper_pass, "cvd_pass": cvd_pass,
                                                    "sniper_reason": sniper_reason
                                                })
                                                break
                                                
    raw_setups.sort(key=lambda x: x["time"])
    return raw_setups

def resolve_setup_outcome(s, model_name, all_data):
    """Calculates outcome for a single setup under model rules."""
    sym = s["sym"]
    tf = s["tf"]
    candles = all_data[tf][sym]
    n = len(candles)
    t = s["t_idx"]
    side = s["side"]
    s_time = s["time"]
    
    mt = s["mt"]
    if side == "LONG":
        entry = mt if s["tap_low"] <= mt else (s["dec_top"] + mt) / 2.0
        tp_p = entry * (1.0 + s["std_tp_pct"])
        struct_sl = min(s["dec_bot"], s["tap_low"]) - 0.20 * s["atr"]
        hard_sl_p = min(struct_sl, entry * (1.0 - s["hard_sl_pct"]))
        hard_sl_p = max(hard_sl_p, entry * 0.962)
        soft_sl_p = (entry + hard_sl_p) / 2.0
    else:
        entry = mt if s["tap_high"] >= mt else (s["dec_bot"] + mt) / 2.0
        tp_p = entry * (1.0 - s["std_tp_pct"])
        struct_sl = max(s["dec_top"], s["tap_high"]) + 0.20 * s["atr"]
        hard_sl_p = max(struct_sl, entry * (1.0 + s["hard_sl_pct"]))
        hard_sl_p = min(hard_sl_p, entry * 1.038)
        soft_sl_p = (entry + hard_sl_p) / 2.0
        
    res = None
    exit_price = entry
    exit_time = s_time
    curr_sl = soft_sl_p
    be_locked = False
    
    be_threshold = 0.016
    trail_threshold = 0.022
    trail_lock_p = 0.012
    
    if model_name == "HERMES_3.5_DUAL_SNIPER" and not s["cvd_pass"]:
        # Tier-2 Fast BE Armor (Insulates capital earlier at +1.0% move)
        be_threshold = 0.010
        trail_threshold = 0.018
        trail_lock_p = 0.008
        
    for m in range(t, min(t + s["max_hold"], n)):
        c_m = candles[m]
        m_time = c_m["time"]
        
        if side == "LONG":
            if c_m["high"] >= entry * (1.0 + trail_threshold):
                curr_sl = max(curr_sl, entry * (1.0 + trail_lock_p))
                be_locked = True
            elif c_m["high"] >= entry * (1.0 + be_threshold):
                curr_sl = max(curr_sl, entry * 1.002)
                be_locked = True
                
            if c_m["high"] >= tp_p:
                res = "WIN"; exit_price = tp_p; exit_time = m_time; break
            if c_m["low"] <= hard_sl_p:
                res = "LOSS"; exit_price = hard_sl_p; exit_time = m_time; break
            if c_m["close"] <= curr_sl:
                res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                exit_price = c_m["close"]; exit_time = m_time; break
        else: # SHORT
            if c_m["low"] <= entry * (1.0 - trail_threshold):
                curr_sl = min(curr_sl, entry * (1.0 - trail_lock_p))
                be_locked = True
            elif c_m["low"] <= entry * (1.0 - be_threshold):
                curr_sl = min(curr_sl, entry * 0.998)
                be_locked = True
                
            if c_m["low"] <= tp_p:
                res = "WIN"; exit_price = tp_p; exit_time = m_time; break
            if c_m["high"] >= hard_sl_p:
                res = "LOSS"; exit_price = hard_sl_p; exit_time = m_time; break
            if c_m["close"] >= curr_sl:
                res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                exit_price = c_m["close"]; exit_time = m_time; break
                
    if not res:
        fc = candles[min(t + s["max_hold"], n - 1)]["close"]
        res = "WIN" if (fc > entry if side == "LONG" else fc < entry) else "LOSS"
        exit_price = fc
        exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]
        
    gross_pct = ((exit_price - entry) / entry) if side == "LONG" else ((entry - exit_price) / entry)
    
    return {
        "sym": sym,
        "tf": tf,
        "side": side,
        "time": s_time,
        "exit_time": exit_time,
        "entry": entry,
        "exit": exit_price,
        "gross_pct": gross_pct,
        "res": res,
        "cvd_pass": s["cvd_pass"]
    }

def simulate_engine_1year(model_name, setups, all_data):
    """
    Simulates 1-Year performance:
    1. Global Setups (all valid signals evaluated)
    2. Compounding Ladder ($50 start, 100% full compounding sequential queue, fee deduction 0.16%)
    """
    fee_rate = 0.0016
    candidate_trades = []
    
    for s in setups:
        if model_name == "HERMES_3.5_DUAL_SNIPER":
            if not s["sniper_pass"]:
                continue
        tr = resolve_setup_outcome(s, model_name, all_data)
        candidate_trades.append(tr)
        
    candidate_trades.sort(key=lambda x: x["time"])
    
    # 1. Global Setup Metrics (across all 28 coins)
    tot_global = len(candidate_trades)
    wins_global = sum(1 for t in candidate_trades if t["res"] == "WIN")
    losses_global = tot_global - wins_global
    wr_global = (wins_global / tot_global * 100.0) if tot_global > 0 else 0.0
    
    global_long = [t for t in candidate_trades if t["side"] == "LONG"]
    global_short = [t for t in candidate_trades if t["side"] == "SHORT"]
    
    long_w = sum(1 for t in global_long if t["res"] == "WIN")
    long_l = len(global_long) - long_w
    long_wr = (long_w / len(global_long) * 100.0) if global_long else 0.0
    
    short_w = sum(1 for t in global_short if t["res"] == "WIN")
    short_l = len(global_short) - short_w
    short_wr = (short_w / len(global_short) * 100.0) if global_short else 0.0
    
    # Coin-by-coin analysis
    coin_stats = {}
    for sym in TOP_28_CHAMPIONS:
        if sym == "BTCUSDT": continue
        c_trades = [t for t in candidate_trades if t["sym"] == sym]
        if not c_trades:
            continue
        c_wins = sum(1 for t in c_trades if t["res"] == "WIN")
        c_losses = len(c_trades) - c_wins
        c_wr = (c_wins / len(c_trades) * 100.0) if c_trades else 0.0
        
        c_long = [t for t in c_trades if t["side"] == "LONG"]
        c_lw = sum(1 for t in c_long if t["res"] == "WIN")
        c_ll = len(c_long) - c_lw
        c_lwr = (c_lw / len(c_long) * 100.0) if c_long else 0.0
        
        c_short = [t for t in c_trades if t["side"] == "SHORT"]
        c_sw = sum(1 for t in c_short if t["res"] == "WIN")
        c_sl = len(c_short) - c_sw
        c_swr = (c_sw / len(c_short) * 100.0) if c_short else 0.0
        
        coin_stats[sym] = {
            "total": len(c_trades),
            "wins": c_wins,
            "losses": c_losses,
            "win_rate": round(c_wr, 2),
            "long_trades": len(c_long),
            "long_wins": c_lw,
            "long_losses": c_ll,
            "long_wr": round(c_lwr, 2),
            "short_trades": len(c_short),
            "short_wins": c_sw,
            "short_losses": c_sl,
            "short_wr": round(c_swr, 2)
        }
        
    # 2. Sequential Compounding Ladder Simulation ($50 starting capital, 100% full compounding per user)
    # Using 4 concurrent execution slots: 2 for 4H and 2 for 1H
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
    executed_trades = []
    
    balance = 50.0
    vault = 0.0
    peak = 50.0
    max_dd = 0.0
    gross_profits = 0.0
    gross_losses = 0.0
    
    hit_500 = None
    hit_1k = None
    hit_2k = None
    
    monthly_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": 0.0, "trades": 0})
    
    for t in candidate_trades:
        tf = t["tf"]
        s_time = t["time"]
        
        target_slot = None
        if tf == "4h":
            if s_time >= slot_busy["4h_1"]: target_slot = "4h_1"
            elif s_time >= slot_busy["4h_2"]: target_slot = "4h_2"
        else:
            if s_time >= slot_busy["1h_1"]: target_slot = "1h_1"
            elif s_time >= slot_busy["1h_2"]: target_slot = "1h_2"
            
        if not target_slot:
            continue
            
        slot_busy[target_slot] = t["exit_time"]
        
        net_pct = t["gross_pct"] - fee_rate
        pos_size = balance * 5.0
        pnl = pos_size * net_pct
        
        dt_in = datetime.fromtimestamp(s_time/1000.0, tz=IST)
        m_key = dt_in.strftime("%Y-%m")
        monthly_stats[m_key]["trades"] += 1
        monthly_stats[m_key]["pnl"] += pnl
        
        if t["res"] == "WIN":
            balance += (pnl * 0.85)
            vault += (pnl * 0.15)
            gross_profits += pnl
            monthly_stats[m_key]["wins"] += 1
        else:
            balance += pnl
            gross_losses += abs(pnl)
            monthly_stats[m_key]["losses"] += 1
            if balance < 5.0: balance = 5.0
            
        tot_eq = balance + vault
        if tot_eq > peak: peak = tot_eq
        dd = (peak - tot_eq) / peak if peak > 0 else 0
        if dd > max_dd: max_dd = dd
        
        trade_num = len(executed_trades) + 1
        if tot_eq >= 500.0 and hit_500 is None:
            hit_500 = {"trade": trade_num, "equity": round(tot_eq, 2), "date": dt_in.strftime("%Y-%m-%d")}
        if tot_eq >= 1000.0 and hit_1k is None:
            hit_1k = {"trade": trade_num, "equity": round(tot_eq, 2), "date": dt_in.strftime("%Y-%m-%d")}
        if tot_eq >= 2000.0 and hit_2k is None:
            hit_2k = {"trade": trade_num, "equity": round(tot_eq, 2), "date": dt_in.strftime("%Y-%m-%d")}
            
        dt_out = datetime.fromtimestamp(t["exit_time"]/1000.0, tz=IST)
        executed_trades.append({
            "num": trade_num,
            "sym": t["sym"],
            "tf": t["tf"],
            "side": t["side"],
            "time_in": dt_in.strftime("%Y-%m-%d %H:%M"),
            "time_out": dt_out.strftime("%Y-%m-%d %H:%M"),
            "entry": round(t["entry"], 4),
            "exit": round(t["exit"], 4),
            "net_pct": round(net_pct * 100.0, 2),
            "roe_pct": round(net_pct * 5.0 * 100.0, 2),
            "pnl": round(pnl, 2),
            "res": t["res"],
            "tot_eq": round(tot_eq, 2)
        })
        
    ladder_wins = sum(1 for e in executed_trades if e["res"] == "WIN")
    ladder_tot = len(executed_trades)
    ladder_wr = (ladder_wins / ladder_tot * 100.0) if ladder_tot > 0 else 0.0
    
    ladder_long = [e for e in executed_trades if e["side"] == "LONG"]
    ladder_short = [e for e in executed_trades if e["side"] == "SHORT"]
    
    ladder_lw = sum(1 for e in ladder_long if e["res"] == "WIN")
    ladder_ll = len(ladder_long) - ladder_lw
    ladder_lwr = (ladder_lw / len(ladder_long) * 100.0) if ladder_long else 0.0
    
    ladder_sw = sum(1 for e in ladder_short if e["res"] == "WIN")
    ladder_sl = len(ladder_short) - ladder_sw
    ladder_swr = (ladder_sw / len(ladder_short) * 100.0) if ladder_short else 0.0
    
    pf = (gross_profits / gross_losses) if gross_losses > 0 else 99.0
    
    return {
        "model": model_name,
        "global_metrics": {
            "total_setups": tot_global,
            "wins": wins_global,
            "losses": losses_global,
            "win_rate": round(wr_global, 2),
            "long_setups": len(global_long),
            "long_wins": long_w,
            "long_losses": long_l,
            "long_wr": round(long_wr, 2),
            "short_setups": len(global_short),
            "short_wins": short_w,
            "short_losses": short_l,
            "short_wr": round(short_wr, 2)
        },
        "compounding_ladder": {
            "total_trades": ladder_tot,
            "wins": ladder_wins,
            "losses": ladder_tot - ladder_wins,
            "win_rate": round(ladder_wr, 2),
            "long_trades": len(ladder_long),
            "long_wins": ladder_lw,
            "long_losses": ladder_ll,
            "long_wr": round(ladder_lwr, 2),
            "short_trades": len(ladder_short),
            "short_wins": ladder_sw,
            "short_losses": ladder_sl,
            "short_wr": round(ladder_swr, 2),
            "starting_balance": 50.0,
            "final_balance": round(balance, 2),
            "final_vault": round(vault, 2),
            "final_equity": round(balance + vault, 2),
            "growth_pct": round(((balance + vault - 50.0) / 50.0) * 100.0, 2),
            "max_drawdown": round(max_dd * 100.0, 2),
            "profit_factor": round(pf, 2),
            "hit_500": hit_500,
            "hit_1k": hit_1k,
            "hit_2k": hit_2k,
            "monthly_stats": dict(monthly_stats)
        },
        "coin_stats": coin_stats,
        "executed_trades": executed_trades
    }

def main():
    print("=" * 95)
    print(" ⚔️ 1-YEAR HEAD-TO-HEAD BATTLE ROYALE (365 DAYS / 8,760 CANDLES)")
    print(" UNIVERSE: TOP-28 CHAMPIONS (22 CORE + 6 GOLDEN ADDITIONS)")
    print(" CONTENDER 1: HERMES 3.0 QUANTUM (MT Limit + Multi-Stage Profit Armor)")
    print(" CONTENDER 2: HERMES 3.5 DUAL-TIER SNIPER (15m Micro-Sniper Gate + Tier-1 CVD / Tier-2 Fast BE)")
    print(" CAPITAL: $50.00 | 5x LEVERAGE | 100% COMPOUNDING SIZING | ISOLATED MARGIN")
    print("=" * 95)
    
    print("\n📥 Loading 1-Year historical datasets for all 28 coins...")
    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_28_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_data_with_quant_features(sym, tf)
            if len(k) >= 200:
                all_data[tf][sym] = k
    print(f"✅ Loaded {len(all_data['1h'])} coins (1h) and {len(all_data['4h'])} coins (4h)")
    
    print("\n🔍 Harvesting qualified SMC setups across 365 days...")
    raw_setups = harvest_1year_top28_setups(all_data)
    print(f"✅ Harvested {len(raw_setups)} total institutional setups across Top-28 Champions!")
    
    print("\n⚙️ Running 1-Year Simulation for HERMES 3.0 QUANTUM...")
    res_h30 = simulate_engine_1year("HERMES_3.0_QUANTUM", raw_setups, all_data)
    
    print("⚙️ Running 1-Year Simulation for HERMES 3.5 DUAL-TIER SNIPER...")
    res_h35 = simulate_engine_1year("HERMES_3.5_DUAL_SNIPER", raw_setups, all_data)
    
    # Save complete JSON results
    out_file = "battle_1year_top28_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"hermes_30": res_h30, "hermes_35": res_h35}, f, indent=2)
    print(f"\n💾 Full audit data successfully saved to {out_file}!")
    
    # Print Executive Scorecard
    g30 = res_h30["global_metrics"]
    g35 = res_h35["global_metrics"]
    c30 = res_h30["compounding_ladder"]
    c35 = res_h35["compounding_ladder"]
    
    print("\n" + "=" * 95)
    print(f" 🏆 1-YEAR MASTER SCORECARD: TOP-28 CHAMPIONS")
    print("=" * 95)
    print(f"{'Metric':<34} | {'HERMES 3.0 QUANTUM':<26} | {'HERMES 3.5 DUAL SNIPER':<26}")
    print("-" * 95)
    print(f"{'1. Global Setups Detected':<34} | {g30['total_setups']:<26} | {g35['total_setups']:<26}")
    print(f"{'   - Global Win Rate %':<34} | {g30['win_rate']}% ({g30['wins']}W / {g30['losses']}L){'':<7} | {g35['win_rate']}% ({g35['wins']}W / {g35['losses']}L){'':<7}")
    print(f"{'   - Long Accuracy %':<34} | {g30['long_wr']}% ({g30['long_wins']}W / {g30['long_losses']}L){'':<7} | {g35['long_wr']}% ({g35['long_wins']}W / {g35['long_losses']}L){'':<7}")
    print(f"{'   - Short Accuracy %':<34} | {g30['short_wr']}% ({g30['short_wins']}W / {g30['short_losses']}L){'':<7} | {g35['short_wr']}% ({g35['short_wins']}W / {g35['short_losses']}L){'':<7}")
    print("-" * 95)
    print(f"{'2. Compounding Executed Trades':<34} | {c30['total_trades']:<26} | {c35['total_trades']:<26}")
    print(f"{'   - Executed Win Rate %':<34} | {c30['win_rate']}% ({c30['wins']}W / {c30['losses']}L){'':<7} | {c35['win_rate']}% ({c35['wins']}W / {c35['losses']}L){'':<7}")
    print(f"{'   - Executed Long Trades':<34} | {c30['long_trades']} ({c30['long_wr']}%, {c30['long_wins']}W/{c30['long_losses']}L){'':<5} | {c35['long_trades']} ({c35['long_wr']}%, {c35['long_wins']}W/{c35['long_losses']}L){'':<5}")
    print(f"{'   - Executed Short Trades':<34} | {c30['short_trades']} ({c30['short_wr']}%, {c30['short_wins']}W/{c30['short_losses']}L){'':<5} | {c35['short_trades']} ({c35['short_wr']}%, {c35['short_wins']}W/{c35['short_losses']}L){'':<5}")
    print(f"{'   - Profit Factor':<34} | {c30['profit_factor']:<26} | {c35['profit_factor']:<26}")
    print(f"{'   - Max Drawdown %':<34} | {c30['max_drawdown']}%{'':<20} | {c35['max_drawdown']}%{'':<20}")
    print("-" * 95)
    print(f"{'3. Financial Compounding':<34} | {'$50.00 Starting':<26} | {'$50.00 Starting':<26}")
    print(f"{'   - Final Total Equity':<34} | ${c30['final_equity']:,.2f}{'':<13} | ${c35['final_equity']:,.2f}{'':<13}")
    print(f"{'   - Net Capital Growth %':<34} | +{c30['growth_pct']:,.1f}%{'':<13} | +{c35['growth_pct']:,.1f}%{'':<13}")
    print(f"{'   - Hit $500 Milestone':<34} | {c30['hit_500']['date'] if c30['hit_500'] else 'N/A'} (Trade #{c30['hit_500']['trade'] if c30['hit_500'] else '-'}){'':<5} | {c35['hit_500']['date'] if c35['hit_500'] else 'N/A'} (Trade #{c35['hit_500']['trade'] if c35['hit_500'] else '-'}){'':<5}")
    print(f"{'   - Hit $1,000 Milestone':<34} | {c30['hit_1k']['date'] if c30['hit_1k'] else 'N/A'} (Trade #{c30['hit_1k']['trade'] if c30['hit_1k'] else '-'}){'':<4} | {c35['hit_1k']['date'] if c35['hit_1k'] else 'N/A'} (Trade #{c35['hit_1k']['trade'] if c35['hit_1k'] else '-'}){'':<4}")
    print(f"{'   - Hit $2,000 Milestone':<34} | {c30['hit_2k']['date'] if c30['hit_2k'] else 'N/A'} (Trade #{c30['hit_2k']['trade'] if c30['hit_2k'] else '-'}){'':<4} | {c35['hit_2k']['date'] if c35['hit_2k'] else 'N/A'} (Trade #{c35['hit_2k']['trade'] if c35['hit_2k'] else '-'}){'':<4}")
    print("=" * 95)
    
    # Print Coin-by-Coin Scorecard
    print("\n" + "=" * 95)
    print(" 📊 TOP-28 CHAMPIONS: COIN-BY-COIN ACCURACY & BREAKDOWN (HERMES 3.5)")
    print("=" * 95)
    print(f"{'Coin':<12} | {'Trades':<8} | {'Wins':<6} | {'Loss':<6} | {'Accuracy %':<12} | {'Long WR% (W/L)':<18} | {'Short WR% (W/L)':<18}")
    print("-" * 95)
    
    sorted_coins = sorted(res_h35["coin_stats"].items(), key=lambda x: (x[1]["win_rate"], x[1]["total"]), reverse=True)
    for sym, st in sorted_coins:
        l_info = f"{st['long_wr']}% ({st['long_wins']}/{st['long_losses']})"
        s_info = f"{st['short_wr']}% ({st['short_wins']}/{st['short_losses']})"
        badge = "🔥" if st['win_rate'] >= 80.0 else ("✅" if st['win_rate'] >= 70.0 else "⚠️")
        print(f"{badge} {sym:<9} | {st['total']:<8} | {st['wins']:<6} | {st['losses']:<6} | {st['win_rate']}%{'':<6} | {l_info:<18} | {s_info:<18}")
    print("=" * 95)

if __name__ == "__main__":
    main()
