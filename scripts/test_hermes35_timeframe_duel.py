import os
import sys
import json

REPO_ROOT = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

CACHE_DIR = os.path.join(REPO_ROOT, "market_data_cache_15m")

CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "NEARUSDT", "OPUSDT",
    "RENDERUSDT", "SUIUSDT", "TIAUSDT", "UNIUSDT", "APTUSDT",
    "ARBUSDT", "FETUSDT", "DOTUSDT", "LTCUSDT", "1000PEPEUSDT"
]

PAIR_MAPPING = {
    "BTCUSDT": 1, "ETHUSDT": 1,
    "SOLUSDT": 2, "BNBUSDT": 2,
    "AVAXUSDT": 3, "DOGEUSDT": 3,
    "DOTUSDT": 4, "LINKUSDT": 4,
    "LTCUSDT": 5, "NEARUSDT": 5,
    "OPUSDT": 6, "RENDERUSDT": 6,
    "SUIUSDT": 7, "TIAUSDT": 7,
    "UNIUSDT": 8, "XRPUSDT": 8,
    "1000PEPEUSDT": 9, "APTUSDT": 9,
    "ARBUSDT": 10, "FETUSDT": 10
}

def resample_candles(candles, factor):
    res = []
    for i in range(0, len(candles), factor):
        chunk = candles[i:i+factor]
        if len(chunk) < factor:
            continue
        res.append({
            'time': chunk[0]['time'],
            'open': chunk[0]['open'],
            'high': max(b['high'] for b in chunk),
            'low': min(b['low'] for b in chunk),
            'close': chunk[-1]['close'],
            'volume': sum(b.get('volume', 0) for b in chunk)
        })
    return res

def simulate_hermes35_engine(candles, symbol, tf_name, leverage=4.0, max_tap_bars=48, max_hold_bars=96):
    trades = []
    n = len(candles)
    used_obs = set()
    
    # Adjust displacement threshold slightly per timeframe:
    # 15m: 1.5% displacement
    # 1H: 2.0% displacement
    # 4H: 3.0% displacement
    disp_threshold = 0.015 if tf_name == "15m" else (0.020 if tf_name == "1H" else 0.030)
    
    for i in range(5, n - 20):
        c = candles[i]
        c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
        c_disp = candles[i+1]
        c_curr = candles[i+2]
        
        # Bullish OB
        if c_c < c_o or (c_h - c_l) > 0:
            disp_gain = (c_disp["high"] - c_l) / c_l
            has_fvg = c_curr["low"] > c_h
            if disp_gain >= disp_threshold and has_fvg:
                ob_high = c_h
                ob_low = c_l
                entry_price = (ob_high + ob_low) / 2.0 # 50% MT
                sl_price = ob_low * (1.0 - 0.0015)
                risk = entry_price - sl_price
                
                if risk <= 0:
                    continue
                tp_price = entry_price + (2.0 * risk) # 2:4 RRR (1:2 R:R)
                
                # Scan for 1st Tap
                for tap_idx in range(i + 3, min(i + 3 + max_tap_bars, n)):
                    b_tap = candles[tap_idx]
                    
                    if b_tap["low"] <= sl_price and b_tap["open"] > entry_price:
                        break
                        
                    if b_tap["low"] <= entry_price and b_tap["high"] >= entry_price:
                        if i in used_obs:
                            break
                        used_obs.add(i)
                        
                        active_sl = sl_price
                        current_tier = 0
                        outcome = None
                        pnl_r = 0.0
                        
                        t1_price = entry_price + (1.0 * risk)
                        t2_price = entry_price + (1.5 * risk)
                        
                        for h_idx in range(tap_idx + 1, min(tap_idx + 1 + max_hold_bars, n)):
                            hb = candles[h_idx]
                            
                            if current_tier < 2 and hb["high"] >= t2_price:
                                current_tier = 2
                                active_sl = entry_price + (1.0 * risk)
                            elif current_tier < 1 and hb["high"] >= t1_price:
                                current_tier = 1
                                active_sl = entry_price + (0.2 * risk)
                                
                            if hb["high"] >= tp_price:
                                outcome = "FULL_TP_WIN (+2.0R)"
                                pnl_r = 2.0
                                break
                                
                            if hb["low"] <= active_sl:
                                if current_tier == 2:
                                    outcome = "TRAILING_LOCK_WIN (+1.0R)"
                                    pnl_r = 1.0
                                elif current_tier == 1:
                                    outcome = "BE_FEE_SHIELD (+0.2R)"
                                    pnl_r = 0.2
                                else:
                                    outcome = "LOSS (-1.0R)"
                                    pnl_r = -1.0
                                break
                                
                        if not outcome:
                            outcome = "TIMEOUT"
                            last_c = candles[min(tap_idx + max_hold_bars, n - 1)]["close"]
                            pnl_r = (last_c - entry_price) / risk
                            
                        risk_pct = risk / entry_price
                        roe_pct = pnl_r * risk_pct * leverage * 100.0
                        
                        trades.append({
                            "symbol": symbol,
                            "timeframe": tf_name,
                            "time": b_tap.get("time", 0),
                            "side": "LONG",
                            "entry": entry_price,
                            "sl": sl_price,
                            "tp": tp_price,
                            "pnl_r": round(pnl_r, 2),
                            "roe_pct": round(roe_pct, 2),
                            "outcome": outcome
                        })
                        break
                        
        # Bearish OB
        elif c_c > c_o or (c_h - c_l) > 0:
            disp_drop = (c_h - c_disp["low"]) / c_h
            has_fvg = c_curr["high"] < c_l
            if disp_drop >= disp_threshold and has_fvg:
                ob_high = c_h
                ob_low = c_l
                entry_price = (ob_high + ob_low) / 2.0
                sl_price = ob_high * (1.0 + 0.0015)
                risk = sl_price - entry_price
                
                if risk <= 0:
                    continue
                tp_price = entry_price - (2.0 * risk)
                
                for tap_idx in range(i + 3, min(i + 3 + max_tap_bars, n)):
                    b_tap = candles[tap_idx]
                    
                    if b_tap["high"] >= sl_price and b_tap["open"] < entry_price:
                        break
                        
                    if b_tap["high"] >= entry_price and b_tap["low"] <= entry_price:
                        if i in used_obs:
                            break
                        used_obs.add(i)
                        
                        active_sl = sl_price
                        current_tier = 0
                        outcome = None
                        pnl_r = 0.0
                        
                        t1_price = entry_price - (1.0 * risk)
                        t2_price = entry_price - (1.5 * risk)
                        
                        for h_idx in range(tap_idx + 1, min(tap_idx + 1 + max_hold_bars, n)):
                            hb = candles[h_idx]
                            
                            if current_tier < 2 and hb["low"] <= t2_price:
                                current_tier = 2
                                active_sl = entry_price - (1.0 * risk)
                            elif current_tier < 1 and hb["low"] <= t1_price:
                                current_tier = 1
                                active_sl = entry_price - (0.2 * risk)
                                
                            if hb["low"] <= tp_price:
                                outcome = "FULL_TP_WIN (+2.0R)"
                                pnl_r = 2.0
                                break
                                
                            if hb["high"] >= active_sl:
                                if current_tier == 2:
                                    outcome = "TRAILING_LOCK_WIN (+1.0R)"
                                    pnl_r = 1.0
                                elif current_tier == 1:
                                    outcome = "BE_FEE_SHIELD (+0.2R)"
                                    pnl_r = 0.2
                                else:
                                    outcome = "LOSS (-1.0R)"
                                    pnl_r = -1.0
                                break
                                
                        if not outcome:
                            outcome = "TIMEOUT"
                            last_c = candles[min(tap_idx + max_hold_bars, n - 1)]["close"]
                            pnl_r = (entry_price - last_c) / risk
                            
                        risk_pct = risk / entry_price
                        roe_pct = pnl_r * risk_pct * leverage * 100.0
                        
                        trades.append({
                            "symbol": symbol,
                            "timeframe": tf_name,
                            "time": b_tap.get("time", 0),
                            "side": "SHORT",
                            "entry": entry_price,
                            "sl": sl_price,
                            "tp": tp_price,
                            "pnl_r": round(pnl_r, 2),
                            "roe_pct": round(roe_pct, 2),
                            "outcome": outcome
                        })
                        break
                        
    return trades

def evaluate_portfolio(trades, tf_label):
    trades.sort(key=lambda x: x.get("time", 0))
    total = len(trades)
    if total == 0:
        return {"timeframe": tf_label, "total_trades": 0}
        
    full_tp = [t for t in trades if "+2.0R" in t["outcome"]]
    trail_wins = [t for t in trades if "+1.0R" in t["outcome"]]
    be_saves = [t for t in trades if "+0.2R" in t["outcome"]]
    losses = [t for t in trades if "-1.0R" in t["outcome"]]
    
    pure_wins = len(full_tp) + len(trail_wins)
    pure_wr = (pure_wins / total) * 100.0
    quality_wr = ((pure_wins + len(be_saves)) / total) * 100.0
    
    total_r = sum(t["pnl_r"] for t in trades)
    avg_r = total_r / total
    
    gross_win_r = sum(t["pnl_r"] for t in trades if t["pnl_r"] > 0)
    gross_loss_r = abs(sum(t["pnl_r"] for t in trades if t["pnl_r"] < 0))
    profit_factor = (gross_win_r / gross_loss_r) if gross_loss_r > 0 else 999.0
    
    # Deca Compounding Simulation: $500 starting ($50 per section, 5% risk = $2.50 per trade unit)
    sections = {str(i): {"balance": 50.0, "trades": 0, "wins": 0, "losses": 0} for i in range(1, 11)}
    peak_eq = 500.0
    max_dd = 0.0
    
    for t in trades:
        sec_id = str(PAIR_MAPPING.get(t["symbol"], 1))
        sec = sections[sec_id]
        risk_usd = sec["balance"] * 0.05
        dollar_pnl = t["pnl_r"] * risk_usd
        
        sec["balance"] += dollar_pnl
        sec["trades"] += 1
        if t["pnl_r"] > 0:
            sec["wins"] += 1
        elif t["pnl_r"] < 0:
            sec["losses"] += 1
            
        cur_eq = sum(s["balance"] for s in sections.values())
        if cur_eq > peak_eq:
            peak_eq = cur_eq
        dd = ((peak_eq - cur_eq) / peak_eq) * 100.0
        if dd > max_dd:
            max_dd = dd
            
    final_eq = sum(s["balance"] for s in sections.values())
    net_profit = final_eq - 500.0
    roi_pct = (net_profit / 500.0) * 100.0
    
    return {
        "timeframe": tf_label,
        "total_trades": total,
        "full_tp_wins_2r": len(full_tp),
        "trailing_lock_wins_1r": len(trail_wins),
        "be_fee_shield_saves_02r": len(be_saves),
        "losses_neg_1r": len(losses),
        "pure_win_rate_pct": round(pure_wr, 2),
        "quality_win_rate_pct": round(quality_wr, 2),
        "total_net_r": round(total_r, 2),
        "avg_r_per_trade": round(avg_r, 2),
        "profit_factor": round(profit_factor, 2),
        "starting_capital_usd": 500.0,
        "final_capital_usd": round(final_eq, 2),
        "net_profit_usd": round(net_profit, 2),
        "portfolio_roi_pct": round(roi_pct, 2),
        "max_drawdown_pct": round(max_dd, 2)
    }

def run_timeframe_duel():
    trades_15m = []
    trades_1h = []
    trades_4h = []
    
    for sym in CHAMPIONS:
        fpath = os.path.join(CACHE_DIR, f"{sym}_15m.json")
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            raw_candles = json.load(f)
            
        # 1 Month = last 2880 bars of 15m
        c_15m = raw_candles[-2880:]
        c_1h = resample_candles(c_15m, 4)   # 720 bars
        c_4h = resample_candles(c_15m, 16)  # 180 bars
        
        # 1. 15m Simulation
        t_15m = simulate_hermes35_engine(c_15m, sym, "15m", leverage=4.0, max_tap_bars=48, max_hold_bars=96)
        trades_15m.extend(t_15m)
        
        # 2. 1H Simulation (max_tap_bars = 24 bars = 24 hours, max_hold = 48 bars = 2 days)
        t_1h = simulate_hermes35_engine(c_1h, sym, "1H", leverage=4.0, max_tap_bars=24, max_hold_bars=48)
        trades_1h.extend(t_1h)
        
        # 3. 4H Simulation (max_tap_bars = 12 bars = 48 hours, max_hold = 24 bars = 4 days)
        t_4h = simulate_hermes35_engine(c_4h, sym, "4H", leverage=4.0, max_tap_bars=12, max_hold_bars=24)
        trades_4h.extend(t_4h)
        
    res_15m = evaluate_portfolio(trades_15m, "15m Intraday (High Velocity)")
    res_1h = evaluate_portfolio(trades_1h, "1H Swing (Optimal Balance)")
    res_4h = evaluate_portfolio(trades_4h, "4H Macro (Institutional Core)")
    
    final_comparison = {
        "15m_Intraday": res_15m,
        "1H_Swing": res_1h,
        "4H_Macro": res_4h
    }
    
    print("=" * 80)
    print("⚔️ HERMES 3.5 RADAR HARVEST — TIMEFRAME DUEL (15M vs 1H vs 4H)")
    print("Rules: 4x Leverage | 50% MT 1st Tap | 2:4 RRR | Stepped Trailing SL")
    print("Period: 1 Full Month (30 Days) | Universe: Top-20 Champions | Seed: $500.00")
    print("=" * 80)
    print(json.dumps(final_comparison, indent=2))
    
    with open(os.path.join(REPO_ROOT, "scratch", "hermes35_timeframe_duel_1month.json"), "w", encoding="utf-8") as f:
        json.dump(final_comparison, f, indent=2)

if __name__ == "__main__":
    run_timeframe_duel()
