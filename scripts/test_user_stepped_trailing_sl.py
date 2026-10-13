import sys
import os
import json
from datetime import datetime, timezone, timedelta

def run_stepped_trailing_sl_duel():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    
    # 3-Month Range: July 1 to Sept 30, 2026
    START_MS = int(datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    END_MS = int(datetime(2026, 9, 30, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
    
    WINDOW_START_MS = int(datetime(2026, 6, 20, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    WINDOW_END_MS = int(datetime(2026, 10, 10, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
    
    data_1h = {}
    data_4h = {}
    
    for c in coins:
        f1 = os.path.join(hist_dir, f"{c}_1h.json")
        f4 = os.path.join(hist_dir, f"{c}_4h.json")
        if os.path.exists(f1):
            with open(f1, "r", encoding="utf-8") as f:
                all_1h = json.load(f)
                data_1h[c] = [x for x in all_1h if WINDOW_START_MS <= x["time"] <= WINDOW_END_MS]
        if os.path.exists(f4):
            with open(f4, "r", encoding="utf-8") as f:
                all_4h = json.load(f)
                data_4h[c] = [x for x in all_4h if WINDOW_START_MS <= x["time"] <= WINDOW_END_MS]
                
    btc_4h = data_4h.get("BTCUSDT", [])
    max_tap_window = 28
    
    candidate_events = []
    
    for c in coins:
        for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
            n = len(dataset)
            if n < 40:
                continue
                
            for i in range(20, n - 2):
                # 1. LONG SETUP
                prior_lows = [float(x["low"]) for x in dataset[max(0, i-15):i+1]]
                if float(dataset[i]["low"]) == min(prior_lows):
                    sub_w = dataset[i:min(i+16, n)]
                    highs = [float(x["high"]) for x in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    
                    if high_idx > i + 2:
                        origin_l = float(dataset[i]["low"])
                        gain = (max_high - origin_l) / origin_l if origin_l > 0 else 0.0
                        if gain >= 0.050:
                            idm_low = float(dataset[high_idx - 1]["low"])
                            best_mid = -1
                            max_bg = 0.0
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
                                        t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                        if tap_c["time"] < START_MS:
                                            continue
                                        if tap_c["time"] > END_MS:
                                            break
                                            
                                        if t_l <= mt and t_c >= mt:
                                            c_range = t_h - t_l
                                            swept = any(float(dataset[k]["low"]) < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(t_o, t_c) - t_l
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                            
                                            btc_clean = True
                                            if btc_4h:
                                                prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                if len(prior_btc) >= 2:
                                                    last_b = prior_btc[-1]
                                                    o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                    if (o_b - c_b) / o_b >= 0.020:
                                                        btc_clean = False
                                                        
                                            if btc_clean and swept and w_ratio >= 0.18:
                                                candidate_events.append({
                                                    "symbol": c, "side": "LONG", "timeframe": tf,
                                                    "entry_time": tap_c["time"], "entry_price": mt,
                                                    "idx_in_dataset": t, "dataset": dataset
                                                })
                                            break
                                            
                # 2. SHORT SETUP
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
                                        t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                        if tap_c["time"] < START_MS:
                                            continue
                                        if tap_c["time"] > END_MS:
                                            break
                                            
                                        if t_h >= mt and t_c <= mt:
                                            c_range = t_h - t_l
                                            swept = any(float(dataset[k]["high"]) > idm_high for k in range(low_idx, t + 1))
                                            u_wick = t_h - max(t_o, t_c)
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                            
                                            btc_clean = True
                                            if btc_4h:
                                                prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                if len(prior_btc) >= 2:
                                                    last_b = prior_btc[-1]
                                                    o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                    if (c_b - o_b) / o_b >= 0.020:
                                                        btc_clean = False
                                                        
                                            if btc_clean and swept and w_ratio >= 0.18:
                                                candidate_events.append({
                                                    "symbol": c, "side": "SHORT", "timeframe": tf,
                                                    "entry_time": tap_c["time"], "entry_price": mt,
                                                    "idx_in_dataset": t, "dataset": dataset
                                                })
                                            break

    # De-duplicate
    seen = set()
    uniq = []
    for ev in candidate_events:
        k = (ev["symbol"], ev["entry_time"])
        if k not in seen:
            seen.add(k)
            uniq.append(ev)
    uniq.sort(key=lambda x: x["entry_time"])
    print(f"Total Qualified Candidate Triggers (July-Sept 2026): {len(uniq)}")
    
    # =========================================================================
    # SIMULATION FUNCTION
    # =========================================================================
    def run_sim(mode="BASELINE"):
        # mode: 'BASELINE' (Fixed +3% TP, +1.5% BE, -1.5% SL)
        #       'STEPPED_TRAILING' (User's rule: 5% ROI -> 1%, 10% -> 5%, 15% -> 10%, etc.)
        balance = 100.0
        peak = 100.0
        max_dd = 0.0
        trades = []
        cur_end = 0
        
        # Track counts
        tp_wins = 0
        trailing_wins = 0
        sl_losses = 0
        be_saves = 0
        total_pnl = 0.0
        
        leverage = 5.0
        
        for ev in uniq:
            t_entry = ev["entry_time"]
            if t_entry < cur_end:
                continue
                
            ds = ev["dataset"]
            t_idx = ev["idx_in_dataset"]
            ep = ev["entry_price"]
            side = ev["side"]
            
            # Initial Hard SL (-1.50% spot move = -7.5% ROI, with -3% emergency)
            initial_sl_dist = ep * 0.0150
            hard_sl_price = ep - initial_sl_dist if side == "LONG" else ep + initial_sl_dist
            
            outcome = None
            exit_p = ep
            exit_t = t_entry
            realized_roi = 0.0
            
            if mode == "BASELINE":
                tp_price = ep * 1.030 if side == "LONG" else ep * 0.970
                be_price = ep * 1.015 if side == "LONG" else ep * 0.985
                active_sl = hard_sl_price
                be_active = False
                
                for bar in ds[t_idx+1:]:
                    bh, bl, bt = float(bar["high"]), float(bar["low"]), bar["time"]
                    if side == "LONG":
                        if not be_active and bh >= be_price:
                            be_active = True
                            active_sl = ep
                        if bh >= tp_price:
                            outcome = "TP_HIT"
                            exit_p = tp_price
                            exit_t = bt
                            realized_roi = 15.0 # +15% ROE
                            break
                        elif bl <= active_sl:
                            outcome = "BE_SAVE" if be_active else "SL_HIT"
                            exit_p = active_sl
                            exit_t = bt
                            realized_roi = 0.0 if be_active else -7.5
                            break
                    else: # SHORT
                        if not be_active and bl <= be_price:
                            be_active = True
                            active_sl = ep
                        if bl <= tp_price:
                            outcome = "TP_HIT"
                            exit_p = tp_price
                            exit_t = bt
                            realized_roi = 15.0
                            break
                        elif bh >= active_sl:
                            outcome = "BE_SAVE" if be_active else "SL_HIT"
                            exit_p = active_sl
                            exit_t = bt
                            realized_roi = 0.0 if be_active else -7.5
                            break
                            
            elif mode == "STEPPED_TRAILING":
                # User Rule:
                # 5% ROI -> SL to 1% ROI (+0.2% spot)
                # 10% ROI -> SL to 5% ROI (+1.0% spot)
                # 15% ROI -> SL to 10% ROI (+2.0% spot)
                # 20% ROI -> SL to 15% ROI (+3.0% spot)
                # 25% ROI -> SL to 20% ROI (+4.0% spot)
                # No upper TP limit - rides the trend!
                
                max_roi_achieved = 0.0
                active_sl = hard_sl_price
                current_locked_roi = -7.5 # initial hard SL
                
                for bar in ds[t_idx+1:]:
                    bh, bl, bt = float(bar["high"]), float(bar["low"]), bar["time"]
                    
                    # Update peak ROI
                    if side == "LONG":
                        bar_peak_roi = ((bh - ep) / ep) * 100.0 * leverage
                        bar_trough_roi = ((bl - ep) / ep) * 100.0 * leverage
                    else:
                        bar_peak_roi = ((ep - bl) / ep) * 100.0 * leverage
                        bar_trough_roi = ((ep - bh) / ep) * 100.0 * leverage
                        
                    if bar_peak_roi > max_roi_achieved:
                        max_roi_achieved = bar_peak_roi
                        
                    # Calculate new target locked ROI based on user ladder
                    target_locked_roi = current_locked_roi
                    if max_roi_achieved >= 5.0 and target_locked_roi < 1.0:
                        target_locked_roi = 1.0
                    if max_roi_achieved >= 10.0 and target_locked_roi < 5.0:
                        target_locked_roi = 5.0
                    if max_roi_achieved >= 15.0 and target_locked_roi < 10.0:
                        target_locked_roi = 10.0
                    if max_roi_achieved >= 20.0 and target_locked_roi < 15.0:
                        target_locked_roi = 15.0
                    if max_roi_achieved >= 25.0 and target_locked_roi < 20.0:
                        target_locked_roi = 20.0
                    if max_roi_achieved >= 30.0 and target_locked_roi < 25.0:
                        target_locked_roi = 25.0
                    if max_roi_achieved >= 35.0 and target_locked_roi < 30.0:
                        target_locked_roi = 30.0
                    if max_roi_achieved >= 40.0 and target_locked_roi < 35.0:
                        target_locked_roi = 35.0
                    if max_roi_achieved >= 50.0 and target_locked_roi < 45.0:
                        target_locked_roi = 45.0
                        
                    if target_locked_roi > current_locked_roi:
                        current_locked_roi = target_locked_roi
                        # calculate exact SL price
                        spot_move_pct = (current_locked_roi / 100.0) / leverage
                        if side == "LONG":
                            active_sl = ep * (1.0 + spot_move_pct)
                        else:
                            active_sl = ep * (1.0 - spot_move_pct)
                            
                    # Check if bar triggered active SL
                    hit_sl = False
                    if side == "LONG" and bl <= active_sl:
                        hit_sl = True
                    elif side == "SHORT" and bh >= active_sl:
                        hit_sl = True
                        
                    if hit_sl:
                        exit_p = active_sl
                        exit_t = bt
                        realized_roi = current_locked_roi
                        if current_locked_roi >= 5.0:
                            outcome = "TRAILING_WIN"
                        elif current_locked_roi == 1.0:
                            outcome = "BE_FEE_SAVE"
                        else:
                            outcome = "INITIAL_SL"
                        break
                        
            if outcome is None:
                continue
                
            cur_end = exit_t
            
            # PnL accounting (5x leverage, 1 trade sequential queue, $50 margin or full compounding)
            # Standard $100 starting equity risk
            pos_size = balance * leverage
            gain_fraction = realized_roi / 100.0 # e.g. +15% ROE = +0.15 * margin
            margin_used = balance # 1 sequential trade uses current balance
            trade_pnl = margin_used * gain_fraction
            balance += trade_pnl
            
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak * 100.0 if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
                
            if realized_roi >= 5.0:
                trailing_wins += 1
            elif realized_roi >= 1.0:
                be_saves += 1
            else:
                sl_losses += 1
                
            trades.append({
                "symbol": ev["symbol"], "side": side, "entry_p": ep, "exit_p": exit_p,
                "roi": realized_roi, "outcome": outcome, "bal_after": balance
            })
            
        tot = len(trades)
        effective_wr = (trailing_wins + be_saves) / tot * 100.0 if tot else 0.0
        pure_tp_wr = trailing_wins / tot * 100.0 if tot else 0.0
        
        return {
            "mode": mode, "total_trades": tot, "wins": trailing_wins, "be_saves": be_saves,
            "losses": sl_losses, "effective_wr": effective_wr, "pure_tp_wr": pure_tp_wr,
            "final_bal": balance, "growth_pct": (balance - 100.0), "max_dd": max_dd,
            "trades": trades
        }

    res_base = run_sim("BASELINE")
    res_trail = run_sim("STEPPED_TRAILING")
    
    print("\n==========================================================================================")
    print("3-MONTH BATTLE AUDIT: HERMES 3.0 BASELINE vs USER'S STEPPED TRAILING SL (JULY - SEPT 2026)")
    print("==========================================================================================")
    print(f"BASELINE MODEL: Fixed +15% ROE TP, +7.5% ROE BE Lock (0.0%), -7.5% ROE SL")
    print(f"Total Trades: {res_base['total_trades']}")
    print(f"TP Wins: {res_base['wins']} | BE Saves: {res_base['be_saves']} | Losses: {res_base['losses']}")
    print(f"Effective Win Rate (Non-Losing): {res_base['effective_wr']:.2f}% | Pure Win Rate: {res_base['pure_tp_wr']:.2f}%")
    print(f"Final Balance ($100 Start): ${res_base['final_bal']:.2f} ({res_base['growth_pct']:+.2f}%) | Max DD: {res_base['max_dd']:.2f}%\n")
    
    print(f"------------------------------------------------------------------------------------------")
    print(f"USER'S STEPPED TRAILING SL MODEL: 5% ROI->1%, 10%->5%, 15%->10%, 20%->15%... Infinite Trail")
    print(f"Total Trades: {res_trail['total_trades']}")
    print(f"Trailing Wins (>=5% ROI): {res_trail['wins']} | Tier 1 Saves (+1% ROI): {res_trail['be_saves']} | Losses: {res_trail['losses']}")
    print(f"Effective Win Rate (In Profit): {res_trail['effective_wr']:.2f}% | Pure Big Win Rate: {res_trail['pure_tp_wr']:.2f}%")
    print(f"Final Balance ($100 Start): ${res_trail['final_bal']:.2f} ({res_trail['growth_pct']:+.2f}%) | Max DD: {res_trail['max_dd']:.2f}%")
    print("==========================================================================================\n")
    
    # Save results
    with open("stepped_trailing_sl_duel_results.json", "w") as f:
        json.dump({"baseline": res_base, "stepped_trailing": res_trail}, f, indent=2, default=str)
    print("Audit results saved to stepped_trailing_sl_duel_results.json")

if __name__ == "__main__":
    run_stepped_trailing_sl_duel()
