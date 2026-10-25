import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import json
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed

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

async def run_experiment():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    
    print(f"Fetching 30-day historical klines for {len(coins)} Champions...")
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
            
    print(f"Candles loaded: 1H={len(data_1h)}, 4H={len(data_4h)}")
    
    # -------------------------------------------------------------------------
    # SCANNER FOR MODEL 1: Pine Script Parity (5% Boundary Limit Entry)
    # -------------------------------------------------------------------------
    pine_candidates = []
    
    for c in coins:
        for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
            n = len(dataset)
            if n < 40:
                continue
            effective_min_bars = 18 if tf == "1h" else 8
            effective_max_bars = 720 if tf == "1h" else 360
            
            for i in range(5, n - 3):
                c3 = dataset[i]
                c2 = dataset[i+1]
                c1 = dataset[i+2]
                
                impulse_h = max(c1["high"], c2["high"])
                impulse_l = min(c1["low"], c2["low"])
                
                # Bullish OB
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
                        
                        if bars_alive > effective_max_bars:
                            break
                        if bar["close"] < ob_low:
                            break
                            
                        # Reach boundary
                        if bar["low"] <= entry_p and bar["low"] >= sl_p:
                            if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                pine_candidates.append({
                                    "symbol": c,
                                    "side": "LONG",
                                    "timeframe": tf,
                                    "entry_time": bar["time"],
                                    "entry_price": entry_p,
                                    "tp_price": tp_p,
                                    "sl_price": sl_p,
                                    "be_price": be_p,
                                    "idx_in_dataset": t,
                                    "dataset": dataset
                                })
                            break
                            
                # Bearish OB
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
                        
                        if bars_alive > effective_max_bars:
                            break
                        if bar["close"] > ob_high:
                            break
                            
                        if bar["high"] >= entry_p and bar["high"] <= sl_p:
                            if runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                pine_candidates.append({
                                    "symbol": c,
                                    "side": "SHORT",
                                    "timeframe": tf,
                                    "entry_time": bar["time"],
                                    "entry_price": entry_p,
                                    "tp_price": tp_p,
                                    "sl_price": sl_p,
                                    "be_price": be_p,
                                    "idx_in_dataset": t,
                                    "dataset": dataset
                                })
                            break

    # De-duplicate pine candidates
    seen = set()
    uniq_pine = []
    for ev in pine_candidates:
        k = (ev["symbol"], ev["entry_time"])
        if k not in seen:
            seen.add(k)
            uniq_pine.append(ev)
    uniq_pine.sort(key=lambda x: x["entry_time"])
    print(f"Total Pine Script Parity candidate triggers: {len(uniq_pine)}")

    def simulate_trades(events, model_name):
        balance = 100.00
        peak = 100.00
        max_dd = 0.0
        trades = []
        busy_until = 0
        
        for ev in events:
            t_entry = ev["entry_time"]
            if t_entry < busy_until:
                continue
                
            ds = ev["dataset"]
            t_idx = ev["idx_in_dataset"]
            ep = ev["entry_price"]
            tp = ev["tp_price"]
            sl = ev["sl_price"]
            be = ev["be_price"]
            side = ev["side"]
            
            be_active = False
            curr_sl = sl
            outcome = None
            exit_p = ep
            exit_time = t_entry
            
            for bar in ds[t_idx+1:]:
                b_h = float(bar["high"])
                b_l = float(bar["low"])
                b_t = bar["time"]
                
                if side == "LONG":
                    if not be_active and b_h >= be:
                        be_active = True
                        curr_sl = ep
                    if b_h >= tp:
                        outcome = "TP_HIT"
                        exit_p = tp
                        exit_time = b_t
                        break
                    elif b_l <= curr_sl:
                        outcome = "BE_SAVE" if be_active else "SL_HIT"
                        exit_p = curr_sl
                        exit_time = b_t
                        break
                else: # SHORT
                    if not be_active and b_l <= be:
                        be_active = True
                        curr_sl = ep
                    if b_l <= tp:
                        outcome = "TP_HIT"
                        exit_p = tp
                        exit_time = b_t
                        break
                    elif b_h >= curr_sl:
                        outcome = "BE_SAVE" if be_active else "SL_HIT"
                        exit_p = curr_sl
                        exit_time = b_t
                        break
                        
            if not outcome:
                continue
                
            margin = balance
            pos_size = margin * 5.0
            
            if outcome == "TP_HIT":
                roe = 15.00
            elif outcome == "BE_SAVE":
                roe = 0.00
            else:
                roe = -7.50
                
            gross = round(margin * (roe / 100.0), 2)
            fee = round(pos_size * 0.0016, 2)
            net = round(gross - fee, 2)
            
            prev_b = balance
            balance = round(max(5.0, balance + net), 2)
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak * 100.0 if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
                
            busy_until = exit_time
            
            trades.append({
                "trade_id": len(trades) + 1,
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
                "roe_pct": roe,
                "net_pnl_usdt": net,
                "balance_before": prev_b,
                "balance_after": balance
            })
            
        wins = len([t for t in trades if t["outcome"] == "TP_HIT"])
        be_saves = len([t for t in trades if t["outcome"] == "BE_SAVE"])
        losses = len([t for t in trades if t["outcome"] == "SL_HIT"])
        tot = len(trades)
        wr = (wins / tot * 100.0) if tot > 0 else 0.0
        eff_wr = ((wins + be_saves) / tot * 100.0) if tot > 0 else 0.0
        
        gains = sum(t["net_pnl_usdt"] for t in trades if t["net_pnl_usdt"] > 0)
        loss_val = abs(sum(t["net_pnl_usdt"] for t in trades if t["net_pnl_usdt"] < 0))
        pf = (gains / loss_val) if loss_val > 0 else 99.0
        
        return {
            "model_name": model_name,
            "initial_balance": 100.00,
            "final_balance": balance,
            "net_growth_pct": round((balance - 100.0) / 100.0 * 100.0, 2),
            "total_trades": tot,
            "tp_wins": wins,
            "be_saves": be_saves,
            "sl_losses": losses,
            "pure_win_rate_pct": round(wr, 2),
            "effective_win_rate_pct": round(eff_wr, 2),
            "profit_factor": round(pf, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "trades": trades
        }

    res_pine = simulate_trades(uniq_pine, "Hermes 3.5 Single Tier (Pine Limit Parity)")
    
    print("\n------------------------------------------------------------")
    print(f"MODEL 1: {res_pine['model_name']}")
    print(f"Final Balance: ${res_pine['final_balance']} ({res_pine['net_growth_pct']:+.2f}%)")
    print(f"Trades: {res_pine['total_trades']} | TP: {res_pine['tp_wins']} | BE: {res_pine['be_saves']} | SL: {res_pine['sl_losses']}")
    print(f"Effective Win Rate: {res_pine['effective_win_rate_pct']}% | Profit Factor: {res_pine['profit_factor']}")
    print(f"Max DD: {res_pine['max_drawdown_pct']}%")
    print("------------------------------------------------------------\n")
    
    out_file = os.path.join(os.path.dirname(__file__), "..", "hermes35_deep_oos_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res_pine, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_experiment())
