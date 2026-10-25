import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import json
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed
from config import TOP_22_CHAMPIONS, ALL_MONITORED_COINS

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

async def run_hermes35_1to2_oos():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    
    print(f"Fetching 30-Day Real Binance OOS Data for {len(coins)} Champions...")
    
    data_1h = {}
    data_4h = {}
    
    for c in coins:
        try:
            k1 = await binance_feed.fetch_klines(c, interval="1h", limit=720)
            if len(k1) >= 200:
                data_1h[c] = k1
            k4 = await binance_feed.fetch_klines(c, interval="4h", limit=200)
            if len(k4) >= 50:
                data_4h[c] = k4
        except Exception as e:
            print(f"Error fetching {c}: {e}")
            
    print(f"Data ready: {len(data_1h)} coins on 1H, {len(data_4h)} coins on 4H.")
    
    btc_4h = data_4h.get("BTCUSDT", [])
    
    # -------------------------------------------------------------
    # HERMES 3.5 SINGLE TIER SETUP SCANNER
    # -------------------------------------------------------------
    candidate_events = []
    
    min_displacement = 0.050 # >= 5.0% Displacement wave
    min_runway_pct = 5.0     # Airspace Void >= 5.0%
    
    for c in coins:
        for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
            n = len(dataset)
            if n < 40:
                continue
            
            min_maturation_bars = 18 if tf == "1h" else 8
            max_maturation_bars = 720 if tf == "1h" else 360
            
            search_start = max(5, n - max_maturation_bars)
            for i in range(search_start, n - 3):
                c3 = dataset[i]
                c2 = dataset[i+1]
                c1 = dataset[i+2]
                
                impulse_h = max(c1["high"], c2["high"])
                impulse_l = min(c1["low"], c2["low"])
                
                t_event = c1["time"]
                
                # BTC Macro Sentry
                btc_long_veto = False
                btc_short_veto = False
                if btc_4h:
                    prior_btc = [x for x in btc_4h if x["time"] < t_event]
                    if len(prior_btc) >= 2:
                        last_b = prior_btc[-1]
                        o_b, c_b = float(last_b["open"]), float(last_b["close"])
                        chg_b = (c_b - o_b) / o_b if o_b > 0 else 0.0
                        if chg_b < -0.015:
                            btc_long_veto = True
                        if chg_b > 0.020:
                            btc_short_veto = True
                            
                # 1. BULLISH SETUP (Origin Red OB + Bull FVG + >= 5.0% Disp)
                if not btc_long_veto:
                    is_strict_red = (c3["close"] < c3["open"])
                    has_bull_fvg = (c1["low"] > c3["high"])
                    bull_gain = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                    
                    if is_strict_red and has_bull_fvg and bull_gain >= min_displacement:
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_range = ob_high - ob_low
                        mt = round((ob_high + ob_low) / 2.0, 8)
                        
                        # 5% Boundary entry for Hermes 3.5
                        eff_entry = round(ob_high - (ob_range * 0.05), 8)
                        
                        # Origin Bedrock Check: lowest of prior 25 bars
                        is_origin = (c3["low"] <= min(dataset[k]["low"] for k in range(max(0, i - 25), i + 1)))
                        
                        # Runway Check
                        peak_runway = max(dataset[k]["high"] for k in range(i + 1, min(i + 25, n)))
                        runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0
                        if runway_pct < min_runway_pct:
                            continue
                            
                        # Scan forward for maturation and first virgin tap
                        broken = False
                        idm_low = min(dataset[k]["low"] for k in range(max(0, i - 3), min(i + 4, n)))
                        for t in range(i + 3, n):
                            curr_c = dataset[t]
                            if curr_c["close"] < ob_low:
                                broken = True
                                break
                                
                            if curr_c["low"] <= eff_entry * 1.0005:
                                bars_alive = t - (i + 2)
                                if bars_alive < min_maturation_bars:
                                    broken = True
                                    break
                                    
                                idm_swept = any(dataset[k]["low"] < idm_low for k in range(i + 3, t + 1)) or (curr_c["low"] < idm_low)
                                c_range = curr_c["high"] - curr_c["low"]
                                l_wick = min(curr_c["open"], curr_c["close"]) - curr_c["low"]
                                w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                
                                # Hermes 3.5 Gate: >= 18% wick, close defends MT, IDM swept
                                if w_ratio >= 0.18 and curr_c["close"] >= mt and idm_swept:
                                    # 1:2 Risk:Reward calibration:
                                    # Spot TP = +3.00% (+15.0% ROE)
                                    # Spot SL = -1.50% (-7.5% ROE)
                                    # Stepped BE = +1.50% (+7.5% ROE -> lock SL to Entry)
                                    tp_p = round(eff_entry * 1.0300, 8)
                                    sl_p = round(eff_entry * 0.9850, 8)
                                    be_p = round(eff_entry * 1.0150, 8)
                                    
                                    candidate_events.append({
                                        "symbol": c,
                                        "side": "LONG",
                                        "timeframe": tf,
                                        "entry_time": curr_c["time"],
                                        "entry_price": eff_entry,
                                        "tp_price": tp_p,
                                        "sl_price": sl_p,
                                        "be_price": be_p,
                                        "idx_in_dataset": t,
                                        "dataset": dataset,
                                        "is_origin": is_origin,
                                        "displacement_pct": round(bull_gain * 100, 2),
                                        "wick_ratio_pct": round(w_ratio * 100, 1)
                                    })
                                else:
                                    broken = True
                                break
                                
                # 2. BEARISH SETUP (Origin Green OB + Bear FVG + >= 5.0% Disp)
                if not btc_short_veto:
                    is_strict_green = (c3["close"] > c3["open"])
                    has_bear_fvg = (c1["high"] < c3["low"])
                    bear_drop = (c3["high"] - impulse_l) / c3["high"] if c3["high"] > 0 else 0.0
                    
                    if is_strict_green and has_bear_fvg and bear_drop >= min_displacement:
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_range = ob_high - ob_low
                        mt = round((ob_high + ob_low) / 2.0, 8)
                        
                        eff_entry = round(ob_low + (ob_range * 0.05), 8)
                        is_origin = (c3["high"] >= max(dataset[k]["high"] for k in range(max(0, i - 25), i + 1)))
                        
                        peak_runway = min(dataset[k]["low"] for k in range(i + 1, min(i + 25, n)))
                        runway_pct = ((ob_low - peak_runway) / ob_low * 100.0) if ob_low > 0 else 0.0
                        if runway_pct < min_runway_pct:
                            continue
                            
                        broken = False
                        idm_high = max(dataset[k]["high"] for k in range(max(0, i - 3), min(i + 4, n)))
                        for t in range(i + 3, n):
                            curr_c = dataset[t]
                            if curr_c["close"] > ob_high:
                                broken = True
                                break
                                
                            if curr_c["high"] >= eff_entry * 0.9995:
                                bars_alive = t - (i + 2)
                                if bars_alive < min_maturation_bars:
                                    broken = True
                                    break
                                    
                                idm_swept = any(dataset[k]["high"] > idm_high for k in range(i + 3, t + 1)) or (curr_c["high"] > idm_high)
                                c_range = curr_c["high"] - curr_c["low"]
                                u_wick = curr_c["high"] - max(curr_c["open"], curr_c["close"])
                                w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                
                                if w_ratio >= 0.18 and curr_c["close"] <= mt and idm_swept:
                                    tp_p = round(eff_entry * 0.9700, 8)
                                    sl_p = round(eff_entry * 1.0150, 8)
                                    be_p = round(eff_entry * 0.9850, 8)
                                    
                                    candidate_events.append({
                                        "symbol": c,
                                        "side": "SHORT",
                                        "timeframe": tf,
                                        "entry_time": curr_c["time"],
                                        "entry_price": eff_entry,
                                        "tp_price": tp_p,
                                        "sl_price": sl_p,
                                        "be_price": be_p,
                                        "idx_in_dataset": t,
                                        "dataset": dataset,
                                        "is_origin": is_origin,
                                        "displacement_pct": round(bear_drop * 100, 2),
                                        "wick_ratio_pct": round(w_ratio * 100, 1)
                                    })
                                else:
                                    broken = True
                                break

    # Remove duplicates on same symbol/time
    seen = set()
    unique_candidates = []
    for ev in candidate_events:
        key = (ev["symbol"], ev["entry_time"])
        if key not in seen:
            seen.add(key)
            unique_candidates.append(ev)
            
    unique_candidates.sort(key=lambda x: x["entry_time"])
    print(f"Total Hermes 3.5 Single Tier candidate triggers found: {len(unique_candidates)}")
    
    # -------------------------------------------------------------
    # SIMULATE SEQUENTIAL QUEUE TRADING ($100 STARTING BALANCE)
    # -------------------------------------------------------------
    balance = 100.00
    peak_balance = 100.00
    max_drawdown_pct = 0.0
    
    trades_executed = []
    current_trade_end_time = 0
    
    for ev in unique_candidates:
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
                    
                # Take Profit hit (+3.00% spot move / +15.0% ROE)
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
        "period": "09 Sep 2026 - 09 Oct 2026 (Last 30 Days)",
        "strategy": "HERMES_3.5_SINGLE_TIER",
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
    
    output_path = os.path.join(os.path.dirname(__file__), "..", "hermes35_1to2_oos_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)
        
    print(f"\n=======================================================")
    print(f"HERMES 3.5 SINGLE TIER (1:2 R:R) 30-DAY OOS TEST RESULTS")
    print(f"=======================================================")
    print(f"Initial Balance:     $100.00 USDT")
    print(f"Final Balance:       ${balance:.2f} USDT ({result_data['net_growth_pct']:+.2f}%)")
    print(f"Total Trades:        {total}")
    print(f"Take Profit Wins:    {wins} ({wins/total*100:.1f}%)" if total else "0")
    print(f"Break-Even Saves:    {be_saves} ({be_saves/total*100:.1f}%)" if total else "0")
    print(f"Stop Losses:         {losses} ({losses/total*100:.1f}%)" if total else "0")
    print(f"Effective Win Rate:  {effective_wr:.2f}%")
    print(f"Profit Factor:       {pf:.2f}")
    print(f"Max Drawdown:        {max_drawdown_pct:.2f}%")
    print(f"=======================================================\n")

if __name__ == "__main__":
    asyncio.run(run_hermes35_1to2_oos())
