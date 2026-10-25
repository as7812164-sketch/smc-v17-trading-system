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

def run_hermes35_oos():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    
    months = [
        {"name": "July 2026", "start_ms": 1782864000000, "end_ms": 1785542399000},
        {"name": "August 2026", "start_ms": 1785542400000, "end_ms": 1788220799000},
        {"name": "September 2026", "start_ms": 1788220800000, "end_ms": 1790294400000}
    ]
    
    # Preload all 1h and 4h data
    data_1h = {}
    data_4h = {}
    for c in coins:
        f1 = os.path.join(hist_dir, f"{c}_1h.json")
        f4 = os.path.join(hist_dir, f"{c}_4h.json")
        if os.path.exists(f1):
            with open(f1, "r", encoding="utf-8") as f:
                data_1h[c] = json.load(f)
        if os.path.exists(f4):
            with open(f4, "r", encoding="utf-8") as f:
                data_4h[c] = json.load(f)
                
    all_month_results = {}
    total_trades_all = []
    
    for m in months:
        m_start = m["start_ms"]
        m_end = m["end_ms"]
        candidates = []
        
        for c in coins:
            for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
                n = len(dataset)
                if n < 40: continue
                effective_min_bars = 18 if tf == "1h" else 8
                effective_max_bars = 720 if tf == "1h" else 360
                
                for i in range(5, n - 3):
                    c3 = dataset[i]
                    c2 = dataset[i+1]
                    c1 = dataset[i+2]
                    
                    impulse_h = max(c1["high"], c2["high"])
                    impulse_l = min(c1["low"], c2["low"])
                    
                    # 1. Bullish OB
                    bull_fvg = (c1["low"] > c3["high"])
                    bull_disp = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                    if (c3["close"] < c3["open"]) and bull_fvg and (bull_disp >= 0.050):
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_rng = ob_high - ob_low
                        entry_p = round(ob_high - (ob_rng * 0.05), 8)
                        tp_p = round(entry_p * 1.0300, 8)
                        sl_p = round(entry_p * 0.9850, 8)
                        be_p = round(entry_p * 1.0150, 8)
                        
                        peak_runway = impulse_h
                        for t in range(i + 3, n):
                            bar = dataset[t]
                            peak_runway = max(peak_runway, bar["high"])
                            runway_pct = ((peak_runway - ob_high) / ob_high) * 100.0
                            bars_alive = t - i
                            
                            if bars_alive > effective_max_bars: break
                            if bar["close"] < ob_low: break
                            
                            if bar["time"] < m_start: continue
                            if bar["time"] > m_end: break
                            
                            # Strict physical fill
                            if bar["low"] <= entry_p and bar["high"] >= entry_p:
                                if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                    candidates.append({
                                        "month": m["name"], "symbol": c, "side": "LONG", "tf": tf,
                                        "entry_time": bar["time"], "idx": t, "dataset": dataset,
                                        "ep": entry_p, "tp": tp_p, "sl": sl_p, "be": be_p
                                    })
                                break
                                
                    # 2. Bearish OB
                    bear_fvg = (c1["high"] < c3["low"])
                    bear_disp = (c3["high"] - impulse_l) / c3["high"] if c3["high"] > 0 else 0.0
                    if (c3["close"] > c3["open"]) and bear_fvg and (bear_disp >= 0.050):
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_rng = ob_high - ob_low
                        entry_p = round(ob_low + (ob_rng * 0.05), 8)
                        tp_p = round(entry_p * 0.9700, 8)
                        sl_p = round(entry_p * 1.0150, 8)
                        be_p = round(entry_p * 0.9850, 8)
                        
                        peak_runway = impulse_l
                        for t in range(i + 3, n):
                            bar = dataset[t]
                            peak_runway = min(peak_runway, bar["low"])
                            runway_pct = ((ob_low - peak_runway) / ob_low) * 100.0
                            bars_alive = t - i
                            
                            if bars_alive > effective_max_bars: break
                            if bar["close"] > ob_high: break
                            
                            if bar["time"] < m_start: continue
                            if bar["time"] > m_end: break
                            
                            if bar["high"] >= entry_p and bar["low"] <= entry_p:
                                if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                    candidates.append({
                                        "month": m["name"], "symbol": c, "side": "SHORT", "tf": tf,
                                        "entry_time": bar["time"], "idx": t, "dataset": dataset,
                                        "ep": entry_p, "tp": tp_p, "sl": sl_p, "be": be_p
                                    })
                                break

        # Deduplicate
        seen = set()
        uniq = []
        for ev in candidates:
            k = (ev["symbol"], ev["entry_time"])
            if k not in seen:
                seen.add(k)
                uniq.append(ev)
        uniq.sort(key=lambda x: x["entry_time"])
        
        # Simulate Sequential Compounding from $100
        balance = 100.00
        peak_balance = 100.00
        max_drawdown = 0.0
        busy_until = 0
        month_trades = []
        
        for ev in uniq:
            if ev["entry_time"] < busy_until: continue
            ds = ev["dataset"]
            idx = ev["idx"]
            ep, tp, sl, be_trig = ev["ep"], ev["tp"], ev["sl"], ev["be"]
            side = ev["side"]
            
            active_sl = sl
            be_locked = False
            outcome = None
            exit_time = ev["entry_time"]
            be_exit_bar_idx = -1
            
            for b_i, bar in enumerate(ds[idx+1:], start=idx+1):
                b_h, b_l, b_t = float(bar["high"]), float(bar["low"]), bar["time"]
                if side == "LONG":
                    if not be_locked and b_h >= be_trig:
                        be_locked = True
                        active_sl = ep
                    if b_h >= tp:
                        outcome = "TP_HIT"
                        exit_time = b_t
                        break
                    elif b_l <= active_sl:
                        outcome = "BE_SAVE" if be_locked else "SL_HIT"
                        exit_time = b_t
                        be_exit_bar_idx = b_i
                        break
                else:
                    if not be_locked and b_l <= be_trig:
                        be_locked = True
                        active_sl = ep
                    if b_l <= tp:
                        outcome = "TP_HIT"
                        exit_time = b_t
                        break
                    elif b_h >= active_sl:
                        outcome = "BE_SAVE" if be_locked else "SL_HIT"
                        exit_time = b_t
                        be_exit_bar_idx = b_i
                        break
                        
            if not outcome: continue
            
            # Post-BE Autopsy
            post_be_result = "N/A"
            if outcome == "BE_SAVE":
                for bar in ds[be_exit_bar_idx:]:
                    b_h, b_l = float(bar["high"]), float(bar["low"])
                    if side == "LONG":
                        if b_h >= tp:
                            post_be_result = "EVENTUAL_TP"
                            break
                        elif b_l <= sl:
                            post_be_result = "EVENTUAL_SL"
                            break
                    else:
                        if b_l <= tp:
                            post_be_result = "EVENTUAL_TP"
                            break
                        elif b_h >= sl:
                            post_be_result = "EVENTUAL_SL"
                            break
                if post_be_result == "N/A":
                    post_be_result = "UNDECIDED_CHOP"
                    
            margin = balance
            pos_size = margin * 5.0
            roe = 15.0 if outcome == "TP_HIT" else (0.0 if outcome == "BE_SAVE" else -7.5)
            gross = round(margin * (roe / 100.0), 2)
            fee = round(pos_size * 0.0016, 2)
            net = round(gross - fee, 2)
            
            prev_bal = balance
            balance = round(max(5.0, balance + net), 2)
            if balance > peak_balance: peak_balance = balance
            dd = (peak_balance - balance) / peak_balance * 100.0 if peak_balance > 0 else 0.0
            if dd > max_drawdown: max_drawdown = dd
            
            busy_until = exit_time
            trade_obj = {
                "month": ev["month"], "trade_id": len(month_trades) + 1,
                "symbol": ev["symbol"], "side": side, "tf": ev["tf"].upper(),
                "entry_time_str": format_ist(ev["entry_time"]),
                "exit_time_str": format_ist(exit_time),
                "duration": format_duration(exit_time - ev["entry_time"]),
                "ep": ep, "tp": tp, "sl": sl, "outcome": outcome,
                "roe_pct": roe, "net_pnl": net, "balance": balance,
                "post_be_result": post_be_result
            }
            month_trades.append(trade_obj)
            total_trades_all.append(trade_obj)
            
        wins = len([t for t in month_trades if t["outcome"] == "TP_HIT"])
        bes = len([t for t in month_trades if t["outcome"] == "BE_SAVE"])
        losses = len([t for t in month_trades if t["outcome"] == "SL_HIT"])
        tot = len(month_trades)
        
        all_month_results[m["name"]] = {
            "initial_balance": 100.00,
            "final_balance": balance,
            "growth_pct": round((balance - 100.0) / 100.0 * 100.0, 2),
            "total_trades": tot,
            "tp_wins": wins,
            "be_saves": bes,
            "sl_losses": losses,
            "win_rate": round(wins / tot * 100.0, 2) if tot else 0.0,
            "effective_wr": round((wins + bes) / tot * 100.0, 2) if tot else 0.0,
            "max_drawdown": round(max_drawdown, 2),
            "trades": month_trades
        }

    # Summary
    print("\n=================================================================")
    print("HERMES 3.5 SINGLE-TIER (1:2 R:R) 3-MONTH OUT-OF-SAMPLE AUDIT")
    print("=================================================================\n")
    for m_name, res in all_month_results.items():
        print(f"[{m_name}]")
        print(f"  Starting Balance:  $100.00 USDT -> Final: ${res['final_balance']:.2f} USDT ({res['growth_pct']:+.2f}%)")
        print(f"  Total Trades:      {res['total_trades']} | TP Wins: {res['tp_wins']} ({res['win_rate']}%) | BE Saves: {res['be_saves']} | SL: {res['sl_losses']}")
        print(f"  Effective Win Rate: {res['effective_wr']}% | Max DD: {res['max_drawdown']}%\n")
        
    tot_all = len(total_trades_all)
    all_sl = len([t for t in total_trades_all if t["outcome"] == "SL_HIT"])
    all_be = len([t for t in total_trades_all if t["outcome"] == "BE_SAVE"])
    all_tp = len([t for t in total_trades_all if t["outcome"] == "TP_HIT"])
    be_sl = len([t for t in total_trades_all if t["post_be_result"] == "EVENTUAL_SL"])
    be_tp = len([t for t in total_trades_all if t["post_be_result"] == "EVENTUAL_TP"])
    
    print("-----------------------------------------------------------------")
    print(f"HERMES 3.5 3-MONTH AGGREGATE POST-MORTEM (Total {tot_all} Trades):")
    print(f"  * Real Stop Losses:   {all_sl} ({all_sl/tot_all*100:.2f}%)")
    print(f"  * Pure Take Profits:  {all_tp} ({all_tp/tot_all*100:.2f}%)")
    print(f"  * Break-Even Closures:{all_be} ({all_be/tot_all*100:.2f}%)")
    print(f"  * BE -> Saved from SL: {be_sl} ({be_sl/all_be*100:.1f}% of BE closures)")
    print(f"  * BE -> Missed TP:     {be_tp} ({be_tp/all_be*100:.1f}% of BE closures)")
    print("=================================================================\n")
    
    with open(os.path.join(os.path.dirname(__file__), "..", "hermes35_3month_oos_results.json"), "w", encoding="utf-8") as f:
        json.dump({"months": all_month_results, "all_trades": total_trades_all}, f, indent=2)

if __name__ == "__main__":
    run_hermes35_oos()
