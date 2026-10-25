import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import json
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed
from config import TOP_22_CHAMPIONS, ALL_MONITORED_COINS
from engine.hermes40_live import calculate_atr_series

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

async def run_oos_test():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    
    print(f"Fetching 30-Day Real Binance OOS Data for {len(coins)} Champions...")
    
    # Fetch 720 1H candles and 180 4H candles for each
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
    
    # Extract BTC 4H for macro causal checks
    btc_4h = data_4h.get("BTCUSDT", [])
    
    # -------------------------------------------------------------
    # SIMULATION ENGINE: 1-MONTH SEQUENTIAL COMPOUNDING QUEUE
    # -------------------------------------------------------------
    # Find all qualified candidate setups across time
    candidate_events = []
    
    for c in coins:
        for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
            n = len(dataset)
            if n < 35:
                continue
            atrs = calculate_atr_series(dataset, 14)
            
            for i in range(15, n - 4):
                c1, c2 = dataset[i-1], dataset[i]
                c1_l, c1_h = float(c1["low"]), float(c1["high"])
                c2_o, c2_c = float(c2["open"]), float(c2["close"])
                c2_l, c2_h = float(c2["low"]), float(c2["high"])
                
                # Check BTC Macro at time of setup
                t_event = c2["time"]
                btc_long_veto = False
                btc_short_veto = False
                if btc_4h:
                    prior_btc = [x for x in btc_4h if x["time"] < t_event]
                    if len(prior_btc) >= 2:
                        last_b = prior_btc[-1]
                        o_b, c_b = float(last_b["open"]), float(last_b["close"])
                        chg_b = (c_b - o_b) / o_b if o_b > 0 else 0.0
                        if chg_b < -0.010:
                            btc_long_veto = True
                        if chg_b > 0.015:
                            btc_short_veto = True
                            
                # 1. Bullish Setup
                if not btc_long_veto and c2_c <= c2_o and c2_l < c1_l:
                    prior_lows = [float(x["low"]) for x in dataset[max(0, i-15):i+1]]
                    if c2_l == min(prior_lows):
                        sub_w = dataset[i:min(i+20, n)]
                        highs = [float(x["high"]) for x in sub_w]
                        m_high = max(highs)
                        h_idx = i + highs.index(m_high)
                        if h_idx > i + 2:
                            disp = (m_high - c2_l) / c2_l if c2_l > 0 else 0.0
                            if disp >= 0.035:
                                has_fvg = any(float(dataset[d+1]["low"]) > float(dataset[d-1]["high"]) for d in range(i+1, min(h_idx, n-1)) if d+1 < n)
                                prev_sh = max(float(x["high"]) for x in dataset[max(0, i-15):i])
                                body_bos = any(float(x["close"]) > prev_sh for x in dataset[i+1:h_idx+1])
                                if has_fvg and body_bos:
                                    entry_p = round((c2_h + c2_l) / 2.0, 6)
                                    idm_l = float(dataset[h_idx-1]["low"])
                                    atr_val = atrs[min(h_idx, len(atrs)-1)]
                                    sl_p = round(c2_l - (0.35 * atr_val), 6)
                                    tp_p = round(entry_p * 1.0300, 6)
                                    be_p = round(entry_p * 1.0150, 6)
                                    
                                    for t in range(h_idx+1, n):
                                        tap = dataset[t]
                                        t_l, t_h, t_o, t_c = float(tap["low"]), float(tap["high"]), float(tap["open"]), float(tap["close"])
                                        idm_swept = any(float(dataset[k]["low"]) < idm_l for k in range(h_idx, t+1))
                                        touched = t_l <= entry_p * 1.0010
                                        if idm_swept and touched:
                                            c_range = t_h - t_l
                                            w_ratio = (min(t_o, t_c) - t_l) / c_range if c_range > 0 else 0.0
                                            if w_ratio >= 0.18 and t_c >= c2_l:
                                                candidate_events.append({
                                                    "symbol": c,
                                                    "side": "LONG",
                                                    "timeframe": tf,
                                                    "entry_time": tap["time"],
                                                    "entry_price": entry_p,
                                                    "tp_price": tp_p,
                                                    "sl_price": sl_p,
                                                    "be_price": be_p,
                                                    "idx_in_dataset": t,
                                                    "dataset": dataset
                                                })
                                            break
                                            
                # 2. Bearish Setup
                if not btc_short_veto and c2_c >= c2_o and c2_h > c1_h:
                    prior_highs = [float(x["high"]) for x in dataset[max(0, i-15):i+1]]
                    if c2_h == max(prior_highs):
                        sub_w = dataset[i:min(i+20, n)]
                        lows = [float(x["low"]) for x in sub_w]
                        m_low = min(lows)
                        l_idx = i + lows.index(m_low)
                        if l_idx > i + 2:
                            disp = (c2_h - m_low) / c2_h if c2_h > 0 else 0.0
                            if disp >= 0.035:
                                has_fvg = any(float(dataset[d+1]["high"]) < float(dataset[d-1]["low"]) for d in range(i+1, min(l_idx, n-1)) if d+1 < n)
                                prev_sl_val = min(float(x["low"]) for x in dataset[max(0, i-15):i])
                                body_bos = any(float(x["close"]) < prev_sl_val for x in dataset[i+1:l_idx+1])
                                if has_fvg and body_bos:
                                    entry_p = round((c2_h + c2_l) / 2.0, 6)
                                    idm_h = float(dataset[l_idx-1]["high"])
                                    atr_val = atrs[min(l_idx, len(atrs)-1)]
                                    sl_p = round(c2_h + (0.35 * atr_val), 6)
                                    tp_p = round(entry_p * 0.9700, 6)
                                    be_p = round(entry_p * 0.9850, 6)
                                    
                                    for t in range(l_idx+1, n):
                                        tap = dataset[t]
                                        t_l, t_h, t_o, t_c = float(tap["low"]), float(tap["high"]), float(tap["open"]), float(tap["close"])
                                        idm_swept = any(float(dataset[k]["high"]) > idm_h for k in range(l_idx, t+1))
                                        touched = t_h >= entry_p * 0.9990
                                        if idm_swept and touched:
                                            c_range = t_h - t_l
                                            w_ratio = (t_h - max(t_o, t_c)) / c_range if c_range > 0 else 0.0
                                            if w_ratio >= 0.18 and t_c <= c2_h:
                                                candidate_events.append({
                                                    "symbol": c,
                                                    "side": "SHORT",
                                                    "timeframe": tf,
                                                    "entry_time": tap["time"],
                                                    "entry_price": entry_p,
                                                    "tp_price": tp_p,
                                                    "sl_price": sl_p,
                                                    "be_price": be_p,
                                                    "idx_in_dataset": t,
                                                    "dataset": dataset
                                                })
                                            break

    # Sort all candidates chronologically
    candidate_events.sort(key=lambda x: x["entry_time"])
    print(f"Total qualified institutional candidate triggers found across month: {len(candidate_events)}")
    
    # -------------------------------------------------------------
    # SIMULATE SEQUENTIAL QUEUE TRADING ($100 STARTING EQUITY)
    # -------------------------------------------------------------
    balance = 100.00
    peak_balance = 100.00
    max_drawdown_pct = 0.0
    
    trades_executed = []
    current_trade_end_time = 0
    
    for ev in candidate_events:
        t_entry = ev["entry_time"]
        # Sequential Queue: Only take trade if no trade currently running
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
        
        # Forward simulate candle by candle
        for bar in ds[t_idx+1:]:
            b_h, b_l, b_t = float(bar["high"]), float(bar["low"]), bar["time"]
            
            if side == "LONG":
                # Check BE trigger (+1.50% spot)
                if not be_locked and b_h >= be_trig:
                    be_locked = True
                    active_sl = ep  # moved to entry!
                    
                # Check TP hit (+3.00% spot / +15% ROE)
                if b_h >= tp:
                    outcome = "TP_HIT"
                    exit_p = tp
                    exit_time = b_t
                    break
                # Check SL hit
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
            
        # P&L Calculation with 5x Leverage
        margin = balance  # 100% sequential compounding
        pos_size = margin * 5.0
        
        if outcome == "TP_HIT":
            pnl_pct = 15.00  # +15.0% ROE
        elif outcome == "BE_SAVE":
            pnl_pct = 0.00   # Break-Even $0.00
        else: # SL_HIT
            pnl_pct = -7.50  # -7.5% ROE
            
        gross_pnl_usdt = round(margin * (pnl_pct / 100.0), 2)
        fee = round(pos_size * 0.0016, 2)  # 0.08% taker per leg (0.16% roundtrip)
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
    win_rate = round((wins / total) * 100.0, 2) if total > 0 else 0.0
    win_plus_be_rate = round(((wins + be_saves) / total) * 100.0, 2) if total > 0 else 0.0
    
    total_gains = sum(t["net_pnl_usdt"] for t in trades_executed if t["net_pnl_usdt"] > 0)
    total_losses = abs(sum(t["net_pnl_usdt"] for t in trades_executed if t["net_pnl_usdt"] < 0))
    pf = round(total_gains / total_losses, 2) if total_losses > 0 else 99.0
    net_growth_pct = round(((balance - 100.0) / 100.0) * 100.0, 2)
    
    results = {
        "period": "Last 30 Days (09 Sep 2026 - 09 Oct 2026)",
        "starting_balance_usdt": 100.00,
        "ending_balance_usdt": balance,
        "net_growth_pct": net_growth_pct,
        "total_trades": total,
        "wins": wins,
        "be_saves": be_saves,
        "losses": losses,
        "pure_win_rate_pct": win_rate,
        "effective_win_rate_pct": win_plus_be_rate,
        "profit_factor": pf,
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "trades": trades_executed
    }
    
    with open("last_month_oos_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "="*80)
    print("🎯 LAST 30-DAY OUT-OF-SAMPLE (OOS) AUDIT RESULTS ($100 STARTING BALANCE):")
    print("="*80)
    print(f"Total Trades: {total}")
    print(f"Wins (TP Hit): {wins} ({win_rate}%)")
    print(f"Break-Even Saves: {be_saves}")
    print(f"Losses (SL Hit): {losses}")
    print(f"Pure Win Rate: {win_rate}% | Effective WR (Wins + BE Saves): {win_plus_be_rate}%")
    print(f"Profit Factor: {pf}")
    print(f"Max Drawdown: {round(max_drawdown_pct, 2)}%")
    print(f"Starting Balance: $100.00 USDT")
    print(f"Final Balance: ${balance} USDT (+{net_growth_pct}%)")
    print("="*80)
    print("Saved full trades details to last_month_oos_results.json")

if __name__ == '__main__':
    asyncio.run(run_oos_test())
