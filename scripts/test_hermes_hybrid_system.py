import os
import sys
import json

REPO_ROOT = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
CACHE_DIR = os.path.join(REPO_ROOT, "market_data_cache_15m")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')


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

def simulate_hybrid_engine(c1h, c4h, symbol, leverage=4.0):
    trades = []
    n_1h = len(c1h)
    n_4h = len(c4h)
    
    # 4H EMA20 dictionary mapping 4H candle time to EMA20
    ema20_4h = {}
    if n_4h >= 10:
        k = 2.0 / (20 + 1)
        ema = float(c4h[0]["close"])
        for b in c4h:
            cp = float(b["close"])
            ema = (cp * k) + (ema * (1.0 - k))
            ema20_4h[b["time"]] = (ema, cp)
            
    # Sorted 4H timestamps
    sorted_4h_times = sorted(ema20_4h.keys())
    
    def get_4h_macro_trend(t_ms):
        # binary search or last prior timestamp
        valid = [t for t in sorted_4h_times if t <= t_ms]
        if not valid:
            return "NEUTRAL"
        last_t = valid[-1]
        ema_val, close_val = ema20_4h[last_t]
        if close_val >= ema_val:
            return "BULLISH"
        else:
            return "BEARISH"

    used_obs = set()
    disp_threshold = 0.020 # 2% displacement on 1H
    
    for i in range(5, n_1h - 20):
        c = c1h[i]
        c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
        c_disp = c1h[i+1]
        c_curr = c1h[i+2]
        
        macro_bias = get_4h_macro_trend(c["time"])
        
        # LONG: Only when 4H Macro is Bullish
        if macro_bias == "BULLISH":
            disp_gain = (c_disp["high"] - c_l) / c_l
            has_fvg = c_curr["low"] > c_h
            if disp_gain >= disp_threshold and has_fvg:
                ob_high = c_h
                ob_low = c_l
                entry_price = (ob_high + ob_low) / 2.0
                sl_price = ob_low * (1.0 - 0.0015)
                risk = entry_price - sl_price
                if risk > 0:
                    tp_price = entry_price + (2.0 * risk)
                    
                    for tap_idx in range(i + 3, min(i + 3 + 24, n_1h)):
                        b_tap = c1h[tap_idx]
                        if b_tap["low"] <= sl_price and b_tap["open"] > entry_price:
                            break
                        if b_tap["low"] <= entry_price and b_tap["high"] >= entry_price:
                            if i in used_obs:
                                break
                            # Wick Gate: >= 12% lower rejection wick
                            bar_range = b_tap["high"] - b_tap["low"]
                            lower_wick = min(b_tap["open"], b_tap["close"]) - b_tap["low"]
                            wick_ratio = (lower_wick / bar_range) if bar_range > 0 else 0
                            if wick_ratio < 0.12:
                                continue # Filter out falling knife
                                
                            used_obs.add(i)
                            active_sl = sl_price
                            current_tier = 0
                            outcome = None
                            pnl_r = 0.0
                            
                            t1_price = entry_price + (1.0 * risk)
                            t2_price = entry_price + (1.5 * risk)
                            
                            for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 48, n_1h)):
                                hb = c1h[h_idx]
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
                                last_c = c1h[min(tap_idx + 48, n_1h - 1)]["close"]
                                pnl_r = (last_c - entry_price) / risk
                                
                            risk_pct = risk / entry_price
                            roe_pct = pnl_r * risk_pct * leverage * 100.0
                            
                            trades.append({
                                "symbol": symbol,
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

        # SHORT: Only when 4H Macro is Bearish
        elif macro_bias == "BEARISH":
            disp_drop = (c_h - c_disp["low"]) / c_h
            has_fvg = c_curr["high"] < c_l
            if disp_drop >= disp_threshold and has_fvg:
                ob_high = c_h
                ob_low = c_l
                entry_price = (ob_high + ob_low) / 2.0
                sl_price = ob_high * (1.0 + 0.0015)
                risk = sl_price - entry_price
                if risk > 0:
                    tp_price = entry_price - (2.0 * risk)
                    
                    for tap_idx in range(i + 3, min(i + 3 + 24, n_1h)):
                        b_tap = c1h[tap_idx]
                        if b_tap["high"] >= sl_price and b_tap["open"] < entry_price:
                            break
                        if b_tap["high"] >= entry_price and b_tap["low"] <= entry_price:
                            if i in used_obs:
                                break
                            # Wick Gate: >= 12% upper rejection wick
                            bar_range = b_tap["high"] - b_tap["low"]
                            upper_wick = b_tap["high"] - max(b_tap["open"], b_tap["close"])
                            wick_ratio = (upper_wick / bar_range) if bar_range > 0 else 0
                            if wick_ratio < 0.12:
                                continue # Filter out momentum blowout
                                
                            used_obs.add(i)
                            active_sl = sl_price
                            current_tier = 0
                            outcome = None
                            pnl_r = 0.0
                            
                            t1_price = entry_price - (1.0 * risk)
                            t2_price = entry_price - (1.5 * risk)
                            
                            for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 48, n_1h)):
                                hb = c1h[h_idx]
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
                                last_c = c1h[min(tap_idx + 48, n_1h - 1)]["close"]
                                pnl_r = (entry_price - last_c) / risk
                                
                            risk_pct = risk / entry_price
                            roe_pct = pnl_r * risk_pct * leverage * 100.0
                            
                            trades.append({
                                "symbol": symbol,
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

def evaluate_portfolio(trades):
    trades.sort(key=lambda x: x.get("time", 0))
    total = len(trades)
    if total == 0:
        return {}
        
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
    
    sections = {str(i): {"balance": 50.0, "trades": 0, "wins": 0, "losses": 0} for i in range(1, 11)}
    peak_eq = 500.0
    max_dd = 0.0
    
    for t in trades:
        sym = t["symbol"]
        sec_id = str(PAIR_MAPPING.get(sym, 1))
        sec = sections[sec_id]
        
        bal = sec["balance"]
        risk_usd = bal * 0.05
        trade_usd = t["pnl_r"] * risk_usd
        sec["balance"] = max(1.0, bal + trade_usd)
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
    roi_pct = ((final_eq - 500.0) / 500.0) * 100.0
    
    return {
        "total_trades": total,
        "full_tp_wins": len(full_tp),
        "trailing_lock_wins": len(trail_wins),
        "be_fee_shield_saves": len(be_saves),
        "losses": len(losses),
        "pure_win_rate_pct": round(pure_wr, 2),
        "quality_win_rate_pct": round(quality_wr, 2),
        "total_r_accumulated": round(total_r, 2),
        "avg_r_per_trade": round(avg_r, 2),
        "profit_factor": round(profit_factor, 2),
        "initial_capital_usd": 500.0,
        "final_capital_usd": round(final_eq, 2),
        "net_profit_usd": round(final_eq - 500.0, 2),
        "portfolio_roi_pct": round(roi_pct, 2),
        "max_drawdown_pct": round(max_dd, 2)
    }

def main():
    all_trades = []
    for sym in CHAMPIONS:
        fpath = os.path.join(CACHE_DIR, f"{sym}_15m.json")
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            raw_candles = json.load(f)
            
        c_15m = raw_candles[-2880:]
        c_1h = resample_candles(c_15m, 4)
        c_4h = resample_candles(c_15m, 16)
        
        t = simulate_hybrid_engine(c_1h, c_4h, sym, leverage=4.0)
        all_trades.extend(t)
        
    res = evaluate_portfolio(all_trades)
    print("=" * 70)
    print("💎 HYBRID ARCHITECTURE (4H MACRO + 1H PRECISION + HARVEST ARMOR)")
    print("=" * 70)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
