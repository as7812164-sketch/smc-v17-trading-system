import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
import json
from datetime import datetime, timezone, timedelta

def run_deca_oos_test():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    
    month_arg = sys.argv[1].lower() if len(sys.argv) > 1 else "september"
    if "aug" in month_arg:
        month_name = "August 2026"
        SEP_START_MS = int(datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
        SEP_END_MS = int(datetime(2026, 8, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
        WINDOW_START_MS = int(datetime(2026, 7, 20, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
        WINDOW_END_MS = int(datetime(2026, 9, 10, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
    else:
        month_name = "September 2026"
        SEP_START_MS = int(datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
        SEP_END_MS = int(datetime(2026, 9, 25, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
        WINDOW_START_MS = int(datetime(2026, 8, 15, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
        WINDOW_END_MS = int(datetime(2026, 9, 25, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)

    print(f"Loading Historical Data for {month_name} OOS across {len(coins)} Champions...")
    
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
                        if gain >= 0.050: # >= 5.0% Displacement
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
                                        if tap_c["time"] < SEP_START_MS:
                                            continue
                                        if tap_c["time"] > SEP_END_MS:
                                            break
                                            
                                        # 0.20% Limit Proximity & Tap Check
                                        if t_l <= mt * 1.0020 and t_c >= mt * 0.995:
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
                                                    "idx_in_dataset": t, "dataset": dataset,
                                                    "wick_ratio_pct": round(w_ratio * 100, 1)
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
                                        if tap_c["time"] < SEP_START_MS:
                                            continue
                                        if tap_c["time"] > SEP_END_MS:
                                            break
                                            
                                        if t_h >= mt * 0.9980 and t_c <= mt * 1.005:
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
                                                    "idx_in_dataset": t, "dataset": dataset,
                                                    "wick_ratio_pct": round(w_ratio * 100, 1)
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
    print(f"Total Qualified Candidate Setups for September 2026: {len(uniq)}")
    
    # =========================================================================
    # DECA COMPOUNDING SIMULATION ($500 STARTING CAPITAL across 10 SECTIONS)
    # =========================================================================
    # Sections 1 to 5: 4H Macro Swing ($50 start each)
    # Sections 6 to 10: 1H Intraday Scalp ($50 start each)
    sections = {}
    for sid in range(1, 11):
        tf_name = "4h" if sid <= 5 else "1h"
        sections[sid] = {
            "id": sid,
            "name": f"Section {sid} ({'4H Macro' if sid <= 5 else '1H Intraday'})",
            "timeframe": tf_name,
            "balance": 50.00,
            "peak_balance": 50.00,
            "max_dd_pct": 0.0,
            "wins": 0,
            "losses": 0,
            "fee_saves": 0,
            "trades": [],
            "busy_until": 0
        }
        
    leverage = 5.0
    active_coins = set() # Coin collision guard across all sections
    
    # Store all trade executions
    executed_trades = []
    
    for ev in uniq:
        entry_t = ev["entry_time"]
        sym = ev["symbol"]
        tf = ev["timeframe"]
        
        # Free up any sections or coins whose trades finished before entry_t
        for sid, sec in sections.items():
            if sec["busy_until"] <= entry_t:
                sec["busy_until"] = 0
                
        # Check active coin exclusivity
        # (re-check busy coins among trades currently running)
        running_coins = set()
        for sid, sec in sections.items():
            if sec["busy_until"] > entry_t:
                if sec["trades"]:
                    running_coins.add(sec["trades"][-1]["symbol"])
                    
        if sym in running_coins:
            continue # Zero coin duplicate collision!
            
        # Select available section
        target_sids = list(range(1, 6)) if tf == "4h" else list(range(6, 11))
        available_sid = next((sid for sid in target_sids if sections[sid]["busy_until"] <= entry_t), None)
        
        if available_sid is None:
            continue # Sequential queue full for this timeframe
            
        sec = sections[available_sid]
        
        # Simulate Trade Execution under Stepped Trailing SL Ladder
        ds = ev["dataset"]
        t_idx = ev["idx_in_dataset"]
        ep = ev["entry_price"]
        side = ev["side"]
        
        # Initial Hard SL (-1.50% Soft Body Close, -3.00% Disaster SL)
        initial_sl_dist = ep * 0.0150
        hard_sl_price = ep - initial_sl_dist if side == "LONG" else ep + initial_sl_dist
        
        max_roi_achieved = 0.0
        active_sl = hard_sl_price
        current_locked_roi = -7.5 # -1.5% spot = -7.5% ROI initial risk
        current_step = 0
        
        exit_p = ep
        exit_t = entry_t
        realized_roi = 0.0
        outcome = None
        
        for bar in ds[t_idx+1:]:
            bh, bl, bt = float(bar["high"]), float(bar["low"]), bar["time"]
            
            # Peak ROI
            if side == "LONG":
                bar_peak_roi = ((bh - ep) / ep) * 100.0 * leverage
            else:
                bar_peak_roi = ((ep - bl) / ep) * 100.0 * leverage
                
            if bar_peak_roi > max_roi_achieved:
                max_roi_achieved = bar_peak_roi
                
            # Stepped Trailing Ladder
            target_locked_roi = current_locked_roi
            target_step = current_step
            
            if max_roi_achieved >= 5.0 and target_locked_roi < 1.0:
                target_locked_roi = 1.0
                target_step = 1
            if max_roi_achieved >= 10.0 and target_locked_roi < 5.0:
                target_locked_roi = 5.0
                target_step = 2
            if max_roi_achieved >= 15.0 and target_locked_roi < 10.0:
                target_locked_roi = 10.0
                target_step = 3
            if max_roi_achieved >= 20.0 and target_locked_roi < 15.0:
                target_locked_roi = 15.0
                target_step = 4
            if max_roi_achieved >= 25.0:
                step_k = int(max_roi_achieved // 5) * 5
                target_k = float(step_k - 5)
                if target_k > target_locked_roi:
                    target_locked_roi = target_k
                    target_step = int((step_k - 5) // 5) + 1
                    
            if target_locked_roi > current_locked_roi:
                current_locked_roi = target_locked_roi
                current_step = target_step
                spot_move_pct = (current_locked_roi / 100.0) / leverage
                if side == "LONG":
                    active_sl = ep * (1.0 + spot_move_pct)
                else:
                    active_sl = ep * (1.0 - spot_move_pct)
                    
            # Check Exit
            hit_exit = False
            if side == "LONG" and bl <= active_sl:
                hit_exit = True
            elif side == "SHORT" and bh >= active_sl:
                hit_exit = True
                
            if hit_exit:
                exit_p = active_sl
                exit_t = bt
                realized_roi = current_locked_roi
                if current_locked_roi >= 5.0:
                    outcome = "TRAILING_WIN"
                elif current_locked_roi == 1.0:
                    outcome = "TIER_1_FEE_SAVE"
                else:
                    outcome = "INITIAL_SL"
                break
                
        if outcome is None:
            continue
            
        sec["busy_until"] = exit_t
        
        # Sizing: 100% Compounding of this section's capital
        curr_b = sec["balance"]
        margin_used = curr_b
        pnl_usdt = round(margin_used * (realized_roi / 100.0), 2)
        new_balance = round(curr_b + pnl_usdt, 2)
        sec["balance"] = new_balance
        
        if new_balance > sec["peak_balance"]:
            sec["peak_balance"] = new_balance
        dd = (sec["peak_balance"] - new_balance) / sec["peak_balance"] * 100.0 if sec["peak_balance"] > 0 else 0.0
        if dd > sec["max_dd_pct"]:
            sec["max_dd_pct"] = dd
            
        if realized_roi >= 5.0:
            sec["wins"] += 1
        elif realized_roi >= 1.0:
            sec["fee_saves"] += 1
        else:
            sec["losses"] += 1
            
        tr_record = {
            "section_id": available_sid,
            "section_name": sec["name"],
            "symbol": sym,
            "side": side,
            "timeframe": tf,
            "entry_time": entry_t,
            "entry_price": ep,
            "exit_time": exit_t,
            "exit_price": exit_p,
            "peak_roi": round(max_roi_achieved, 1),
            "trailing_step": current_step,
            "realized_roi": realized_roi,
            "outcome": outcome,
            "margin_usdt": margin_used,
            "pnl_usdt": pnl_usdt,
            "new_balance": new_balance
        }
        sec["trades"].append(tr_record)
        executed_trades.append(tr_record)
        
    # Aggregate Stats
    total_trades = len(executed_trades)
    total_wins = sum(s["wins"] for s in sections.values())
    total_saves = sum(s["fee_saves"] for s in sections.values())
    total_losses = sum(s["losses"] for s in sections.values())
    
    effective_wr = (total_wins + total_saves) / total_trades * 100.0 if total_trades else 0.0
    pure_win_wr = total_wins / total_trades * 100.0 if total_trades else 0.0
    
    total_starting_cap = 500.00
    total_final_cap = sum(s["balance"] for s in sections.values())
    total_net_pnl = total_final_cap - total_starting_cap
    total_growth_pct = (total_net_pnl / total_starting_cap) * 100.0
    avg_dd = sum(s["max_dd_pct"] for s in sections.values()) / 10.0
    max_single_sec_dd = max(s["max_dd_pct"] for s in sections.values())
    
    # Breakdown by ROI Tiers
    from collections import Counter
    roi_counts = Counter(t["realized_roi"] for t in executed_trades)
    
    print("\n" + "=" * 92)
    print("👑 HERMES 3.0 APEX TRAILING (LIMIT SNIPER) — LAST MONTH OOS AUDIT (SEPTEMBER 2026)")
    print("=" * 92)
    print(f"Dataset Scope: September 1, 2026 to September 25, 2026 | Top-20 Binance USDT-M Champions")
    print(f"Architecture: 10-Section Deca Compounding Matrix ($500 Starting Capital | $50/Section)")
    print("-" * 92)
    print(f"Total Trades Executed:        {total_trades}")
    print(f"Effective Win Rate (Green):   {effective_wr:.2f}% ({total_wins + total_saves} Profitable / {total_trades} Total)")
    print(f"Big Trending Wins (>=+5% ROI): {total_wins} Trades ({pure_win_wr:.2f}%)")
    print(f"Tier 1 Fee-Protection (+1%):  {total_saves} Trades")
    print(f"Stop Loss Losses (-7.5%):     {total_losses} Trades (Only {total_losses/total_trades*100:.1f}% loss rate!)")
    print("-" * 92)
    print(f"Starting Capital:             ${total_starting_cap:.2f} USDT")
    print(f"Final Deca Capital:           ${total_final_cap:.2f} USDT")
    print(f"Net Profit Realized:          +${total_net_pnl:.2f} USDT (+{total_growth_pct:.2f}% NET GROWTH)")
    print(f"Average Section Drawdown:     {avg_dd:.2f}% | Max Single Section Drawdown: {max_single_sec_dd:.2f}%")
    print("=" * 92)
    
    print("\n📊 10-SECTION DECA COMPOUNDING BREAKDOWN (SEPTEMBER 2026):")
    print("-" * 92)
    print("Section # | Timeframe   | Trades | Wins | Saves | Loss | Start Bal | Final Bal | Net PnL    | Max DD%")
    print("-" * 92)
    for sid in range(1, 11):
        s = sections[sid]
        pnl = s["balance"] - 50.0
        print(f"Sec {s['id']:02d}    | {s['timeframe'].upper():<11} | {len(s['trades']):<6} | {s['wins']:<4} | {s['fee_saves']:<5} | {s['losses']:<4} | $50.00     | ${s['balance']:<9.2f} | {pnl:+<10.2f} | {s['max_dd_pct']:.2f}%")
    print("-" * 92)
    print(f"TOTAL     | 10 SECTIONS | {total_trades:<6} | {total_wins:<4} | {total_saves:<5} | {total_losses:<4} | $500.00    | ${total_final_cap:<9.2f} | {total_net_pnl:+<10.2f} | {avg_dd:.2f}% avg")
    print("=" * 92)
    
    print("\n🎯 REALIZED ROI DISTRIBUTION:")
    for roi_val in sorted(roi_counts.keys()):
        print(f"  ROI {roi_val:+.1f}%: {roi_counts[roi_val]} trades")
    print("")

    # Save to JSON
    out_file = "august_deca_trailing_oos_results.json" if "aug" in month_arg else "september_deca_trailing_oos_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "scope": f"{month_name} OOS",
            "total_trades": total_trades,
            "wins": total_wins,
            "fee_saves": total_saves,
            "losses": total_losses,
            "effective_win_rate_pct": effective_wr,
            "starting_capital": total_starting_cap,
            "final_capital": total_final_cap,
            "net_profit_usdt": total_net_pnl,
            "net_growth_pct": total_growth_pct,
            "avg_section_dd": avg_dd,
            "sections": [
                {
                    "id": sid,
                    "name": s["name"],
                    "timeframe": s["timeframe"],
                    "trades_count": len(s["trades"]),
                    "wins": s["wins"],
                    "fee_saves": s["fee_saves"],
                    "losses": s["losses"],
                    "final_balance": s["balance"],
                    "net_pnl": s["balance"] - 50.0,
                    "max_dd_pct": s["max_dd_pct"]
                } for sid, s in sections.items()
            ],
            "trades": executed_trades
        }, f, indent=2, default=str)
    print(f"Detailed audit results saved to {out_file}\n")

if __name__ == "__main__":
    run_deca_oos_test()
