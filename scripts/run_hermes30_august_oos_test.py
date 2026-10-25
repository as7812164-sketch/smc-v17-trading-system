import sys
import os
import json
from datetime import datetime, timezone, timedelta

def format_ist(ts_ms):
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) + timedelta(hours=5, minutes=30)
    return dt.strftime("%d %b %Y %I:%M %p IST")

def format_duration(ms):
    secs = int(ms / 1000)
    hrs = secs // 3600
    mins = (secs % 3600) // 60
    if hrs > 0:
        return f"{hrs}h {mins}m"
    return f"{mins}m"

def run_hermes30_august_oos():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    
    AUG_START_MS = int(datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    AUG_END_MS = int(datetime(2026, 8, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
    
    # Load dataset with buffer before August (from July 20) and after August (to Sept 10)
    WINDOW_START_MS = int(datetime(2026, 7, 20, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    WINDOW_END_MS = int(datetime(2026, 9, 10, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
    
    print(f"Loading August 2026 Historical Data across {len(coins)} Champions from {hist_dir}...")
    
    data_1h = {}
    data_4h = {}
    
    for c in coins:
        f1 = os.path.join(hist_dir, f"{c}_1h.json")
        f4 = os.path.join(hist_dir, f"{c}_4h.json")
        
        if os.path.exists(f1):
            with open(f1, "r", encoding="utf-8") as f:
                all_1h = json.load(f)
                filtered_1h = [x for x in all_1h if WINDOW_START_MS <= x["time"] <= WINDOW_END_MS]
                data_1h[c] = filtered_1h
        if os.path.exists(f4):
            with open(f4, "r", encoding="utf-8") as f:
                all_4h = json.load(f)
                filtered_4h = [x for x in all_4h if WINDOW_START_MS <= x["time"] <= WINDOW_END_MS]
                data_4h[c] = filtered_4h
                
    print(f"Data ready: 1H loaded={len(data_1h)}, 4H loaded={len(data_4h)}")
    
    btc_4h = data_4h.get("BTCUSDT", [])
    max_tap_window = 28 # Retest tap strictly <= 28 bars
    
    candidate_events = []
    
    for c in coins:
        for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
            n = len(dataset)
            if n < 40:
                continue
                
            for i in range(20, n - 2):
                # -----------------------------------------------------
                # 1. HERMES 3.0 BULLISH SETUP (LONG)
                # -----------------------------------------------------
                prior_lows = [float(x["low"]) for x in dataset[max(0, i-15):i+1]]
                if float(dataset[i]["low"]) == min(prior_lows):
                    sub_w = dataset[i:min(i+16, n)]
                    highs = [float(x["high"]) for x in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    
                    if high_idx > i + 2:
                        origin_l = float(dataset[i]["low"])
                        gain = (max_high - origin_l) / origin_l if origin_l > 0 else 0.0
                        if gain >= 0.050: # >= 5.0% Displacement wave
                            idm_low = float(dataset[high_idx - 1]["low"])
                            best_mid = -1
                            max_bg = 0.0
                            
                            # Find Decisional Order Block (Fib 0.30 - 0.70)
                            for mid in range(i + 1, high_idx):
                                m_h = float(dataset[mid]["high"])
                                m_l = float(dataset[mid]["low"])
                                bg = (m_h - m_l) / m_l if m_l > 0 else 0.0
                                fib = (m_l - origin_l) / (max_high - origin_l) if max_high > origin_l else 0.0
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                                    
                            if best_mid != -1:
                                dec_c = dataset[best_mid - 1]
                                dec_top = max(float(dec_c["open"]), float(dec_c["close"]))
                                dec_bot = float(dec_c["low"])
                                has_fvg = (float(dataset[best_mid + 1]["low"]) > float(dataset[best_mid - 1]["high"])) if best_mid + 1 < n else False
                                
                                if has_fvg:
                                    mt = round((dec_top + dec_bot) / 2.0, 8)
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        tap_c = dataset[t]
                                        t_l = float(tap_c["low"])
                                        t_h = float(tap_c["high"])
                                        t_o = float(tap_c["open"])
                                        t_c = float(tap_c["close"])
                                        
                                        # Only consider trades entered strictly within August 2026
                                        if tap_c["time"] < AUG_START_MS:
                                            continue
                                        if tap_c["time"] > AUG_END_MS:
                                            break
                                            
                                        # Strict Physical Execution: tap candle low MUST reach mt, and close above mt
                                        if t_l <= mt and t_c >= mt:
                                            c_range = t_h - t_l
                                            swept = any(float(dataset[k]["low"]) < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(t_o, t_c) - t_l
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                            
                                            # BTC Causal Brake for Hermes 3.0 (< 2.0% dump)
                                            btc_clean = True
                                            if btc_4h:
                                                prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                if len(prior_btc) >= 2:
                                                    last_b = prior_btc[-1]
                                                    o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                    btc_dump = (o_b - c_b) / o_b if o_b > 0 else 0.0
                                                    if btc_dump >= 0.020:
                                                        btc_clean = False
                                                        
                                            if btc_clean and swept and w_ratio >= 0.18:
                                                entry_p = mt
                                                
                                                # 1:2 Risk:Reward Calibration
                                                tp_p = round(entry_p * 1.0300, 8)
                                                sl_p = round(entry_p * 0.9850, 8)
                                                be_p = round(entry_p * 1.0150, 8)
                                                
                                                candidate_events.append({
                                                    "symbol": c,
                                                    "side": "LONG",
                                                    "timeframe": tf,
                                                    "entry_time": tap_c["time"],
                                                    "entry_price": entry_p,
                                                    "tp_price": tp_p,
                                                    "sl_price": sl_p,
                                                    "be_price": be_p,
                                                    "idx_in_dataset": t,
                                                    "dataset": dataset,
                                                    "displacement_pct": round(gain * 100, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100, 1)
                                                })
                                            break
                                            
                # -----------------------------------------------------
                # 2. HERMES 3.0 BEARISH SETUP (SHORT)
                # -----------------------------------------------------
                prior_highs = [float(x["high"]) for x in dataset[max(0, i-15):i+1]]
                if float(dataset[i]["high"]) == max(prior_highs):
                    sub_w = dataset[i:min(i+16, n)]
                    lows = [float(x["low"]) for x in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    
                    if low_idx > i + 2:
                        origin_h = float(dataset[i]["high"])
                        drop = (origin_h - min_low) / origin_h if origin_h > 0 else 0.0
                        if drop >= 0.050:
                            idm_high = float(dataset[low_idx - 1]["high"])
                            best_mid = -1
                            max_bg = 0.0
                            
                            for mid in range(i + 1, low_idx):
                                m_h = float(dataset[mid]["high"])
                                m_l = float(dataset[mid]["low"])
                                bg = (m_h - m_l) / m_h if m_h > 0 else 0.0
                                fib = (origin_h - m_h) / (origin_h - min_low) if origin_h > min_low else 0.0
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                                    
                            if best_mid != -1:
                                dec_c = dataset[best_mid - 1]
                                dec_top = float(dec_c["high"])
                                dec_bot = min(float(dec_c["open"]), float(dec_c["close"]))
                                has_bear_fvg = (float(dataset[best_mid + 1]["high"]) < float(dataset[best_mid - 1]["low"])) if best_mid + 1 < n else False
                                
                                if has_bear_fvg:
                                    mt = round((dec_top + dec_bot) / 2.0, 8)
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        tap_c = dataset[t]
                                        t_l = float(tap_c["low"])
                                        t_h = float(tap_c["high"])
                                        t_o = float(tap_c["open"])
                                        t_c = float(tap_c["close"])
                                        
                                        if tap_c["time"] < AUG_START_MS:
                                            continue
                                        if tap_c["time"] > AUG_END_MS:
                                            break
                                            
                                        # Strict Physical Execution: tap candle high MUST reach mt, and close below mt
                                        if t_h >= mt and t_c <= mt:
                                            c_range = t_h - t_l
                                            swept = any(float(dataset[k]["high"]) > idm_high for k in range(low_idx, t + 1))
                                            u_wick = t_h - max(t_o, t_c)
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                            
                                            btc_clean_short = True
                                            if btc_4h:
                                                prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                if len(prior_btc) >= 2:
                                                    last_b = prior_btc[-1]
                                                    o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                    btc_pump = (c_b - o_b) / o_b if o_b > 0 else 0.0
                                                    if btc_pump >= 0.020:
                                                        btc_clean_short = False
                                                        
                                            if btc_clean_short and swept and w_ratio >= 0.18:
                                                entry_p = mt
                                                
                                                tp_p = round(entry_p * 0.9700, 8)
                                                sl_p = round(entry_p * 1.0150, 8)
                                                be_p = round(entry_p * 0.9850, 8)
                                                
                                                candidate_events.append({
                                                    "symbol": c,
                                                    "side": "SHORT",
                                                    "timeframe": tf,
                                                    "entry_time": tap_c["time"],
                                                    "entry_price": entry_p,
                                                    "tp_price": tp_p,
                                                    "sl_price": sl_p,
                                                    "be_price": be_p,
                                                    "idx_in_dataset": t,
                                                    "dataset": dataset,
                                                    "displacement_pct": round(drop * 100, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100, 1)
                                                })
                                            break

    # De-duplicate
    seen = set()
    uniq_candidates = []
    for ev in candidate_events:
        k = (ev["symbol"], ev["entry_time"])
        if k not in seen:
            seen.add(k)
            uniq_candidates.append(ev)
            
    uniq_candidates.sort(key=lambda x: x["entry_time"])
    print(f"Total August 2026 Hermes 3.0 Quantum qualified candidate triggers: {len(uniq_candidates)}")
    
    # -------------------------------------------------------------
    # SIMULATE SEQUENTIAL QUEUE TRADING ($100 STARTING EQUITY)
    # -------------------------------------------------------------
    balance = 100.00
    peak_balance = 100.00
    max_drawdown_pct = 0.0
    
    trades_executed = []
    current_trade_end_time = 0
    
    for ev in uniq_candidates:
        t_entry = ev["entry_time"]
        if t_entry < current_trade_end_time:
            continue
            
        ds = ev["dataset"]
        t_idx = ev["idx_in_dataset"]
        ep = ev["entry_price"]
        tp = ev["tp_price"]
        sl = ev["sl_price"]
        be_trig = ev["be_price"]
        side = ev["side"]
        
        active_sl = sl
        be_locked = False
        outcome = None
        exit_p = ep
        exit_time = t_entry
        
        for bar in ds[t_idx+1:]:
            b_h, b_l, b_t = float(bar["high"]), float(bar["low"]), bar["time"]
            
            if side == "LONG":
                # Stepped Break-Even trigger (+1.50% spot move / +7.5% ROE)
                if not be_locked and b_h >= be_trig:
                    be_locked = True
                    active_sl = ep
                    
                # Take profit hit (+3.00% spot move / +15.0% ROE)
                if b_h >= tp:
                    outcome = "TP_HIT"
                    exit_p = tp
                    exit_time = b_t
                    break
                elif b_l <= active_sl:
                    outcome = "BE_SAVE" if be_locked else "SL_HIT"
                    exit_p = active_sl
                    exit_time = b_t
                    break
            else: # SHORT
                if not be_locked and b_l <= be_trig:
                    be_locked = True
                    active_sl = ep
                    
                if b_l <= tp:
                    outcome = "TP_HIT"
                    exit_p = tp
                    exit_time = b_t
                    break
                elif b_h >= active_sl:
                    outcome = "BE_SAVE" if be_locked else "SL_HIT"
                    exit_p = active_sl
                    exit_time = b_t
                    break
                    
        if not outcome:
            continue
            
        margin = balance
        pos_size = margin * 5.0
        
        if outcome == "TP_HIT":
            pnl_pct = 15.00
        elif outcome == "BE_SAVE":
            pnl_pct = 0.00
        else:
            pnl_pct = -7.50
            
        gross_pnl_usdt = round(margin * (pnl_pct / 100.0), 2)
        fee = round(pos_size * 0.0016, 2)
        net_pnl_usdt = round(gross_pnl_usdt - fee, 2)
        
        prev_balance = balance
        balance = round(max(5.0, balance + net_pnl_usdt), 2)
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance * 100.0 if peak_balance > 0 else 0.0
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd
            
        current_trade_end_time = exit_time
        
        trade_record = {
            "trade_id": len(trades_executed) + 1,
            "symbol": ev["symbol"],
            "side": side,
            "timeframe": ev["timeframe"].upper(),
            "entry_time_str": format_ist(t_entry),
            "exit_time_str": format_ist(exit_time),
            "duration": format_duration(exit_time - t_entry),
            "entry_price": ep,
            "tp_price": tp,
            "sl_price": sl,
            "exit_price": exit_p,
            "outcome": outcome,
            "roe_pct": pnl_pct,
            "net_pnl_usdt": net_pnl_usdt,
            "balance_before": prev_balance,
            "balance_after": balance
        }
        trades_executed.append(trade_record)
        
    wins = len([t for t in trades_executed if t["outcome"] == "TP_HIT"])
    be_saves = len([t for t in trades_executed if t["outcome"] == "BE_SAVE"])
    losses = len([t for t in trades_executed if t["outcome"] == "SL_HIT"])
    total = len(trades_executed)
    
    win_rate = (wins / total * 100.0) if total > 0 else 0.0
    effective_wr = ((wins + be_saves) / total * 100.0) if total > 0 else 0.0
    
    total_gains = sum(t["net_pnl_usdt"] for t in trades_executed if t["net_pnl_usdt"] > 0)
    total_losses = abs(sum(t["net_pnl_usdt"] for t in trades_executed if t["net_pnl_usdt"] < 0))
    pf = (total_gains / total_losses) if total_losses > 0 else 99.0
    
    result_data = {
        "period": "01 Aug 2026 - 31 Aug 2026 (August Month)",
        "strategy": "HERMES_3.0_QUANTUM",
        "risk_reward_ratio": "1:2 (15% ROE TP / 7.5% ROE SL)",
        "initial_balance": 100.00,
        "final_balance": balance,
        "net_growth_pct": round((balance - 100.0) / 100.0 * 100.0, 2),
        "total_trades": total,
        "tp_wins": wins,
        "be_saves": be_saves,
        "sl_losses": losses,
        "pure_win_rate_pct": round(win_rate, 2),
        "effective_win_rate_pct": round(effective_wr, 2),
        "profit_factor": round(pf, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "trades": trades_executed
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "..", "hermes30_august_oos_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)
        
    print(f"\n=======================================================")
    print(f"HERMES 3.0 QUANTUM (1:2 R:R) AUGUST 2026 OOS TEST RESULTS")
    print(f"=======================================================")
    print(f"Period:              01 Aug 2026 - 31 Aug 2026")
    print(f"Initial Balance:     $100.00 USDT")
    print(f"Final Balance:       ${balance:.2f} USDT ({result_data['net_growth_pct']:+.2f}%)")
    print(f"Total Trades:        {total}")
    print(f"Take Profit Wins:    {wins} ({wins/total*100:.1f}%)" if total else "0")
    print(f"Break-Even Saves:    {be_saves} ({be_saves/total*100:.1f}%)" if total else "0")
    print(f"Stop Losses:         {losses} ({losses/total*100:.1f}%)" if total else "0")
    print(f"Pure Win Rate:       {win_rate:.2f}%")
    print(f"Effective Win Rate:  {effective_wr:.2f}%")
    print(f"Profit Factor:       {pf:.2f}")
    print(f"Max Drawdown:        {max_drawdown_pct:.2f}%")
    print(f"=======================================================\n")

if __name__ == "__main__":
    run_hermes30_august_oos()
