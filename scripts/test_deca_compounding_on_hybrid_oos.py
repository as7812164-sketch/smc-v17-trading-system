import os
import sys
import json

REPO_ROOT = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
CACHE_DIR = os.path.join(REPO_ROOT, "market_data_cache_15m")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CHAMPIONS_NO_BTC_ETH = [
    "ADAUSDT", "AAVEUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", "DOGEUSDT",
    "DOTUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT", "OPUSDT", "RENDERUSDT",
    "SUIUSDT", "TIAUSDT", "UNIUSDT", "XRPUSDT", "1000PEPEUSDT", "APTUSDT",
    "ARBUSDT", "FETUSDT"
]

PAIR_MAPPING = {
    "ADAUSDT": 1, "AAVEUSDT": 1,
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

LADDER = [
    (0.049, 0.005),  # Step 1: Trigger +4.90% ROI -> Lock +0.50%
    (0.098, 0.051),  # Step 2: Trigger +9.80% ROI -> Lock +5.10%
    (0.148, 0.101),  # Step 3: Trigger +14.80% ROI -> Lock +10.10%
    (0.198, 0.151),  # Step 4: Trigger +19.80% ROI -> Lock +15.10%
    (0.240, 0.201),  # Step 5: Trigger +24.00% ROI -> Lock +20.10%
    (0.290, 0.250)   # Step 6: Trigger +29.00% ROI -> Lock +25.00%
]

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

def extract_oos_trades():
    trades = []
    for sym in CHAMPIONS_NO_BTC_ETH:
        fpath = os.path.join(CACHE_DIR, f"{sym}_15m.json")
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            raw = json.load(f)
            
        c_15m = raw[-5760:-2880] if len(raw) >= 5760 else raw[-2880:]
        c1h = resample_candles(c_15m, 4)
        c4h = resample_candles(c_15m, 16)
        
        n_1h = len(c1h)
        n_4h = len(c4h)
        
        ema20_4h = {}
        if n_4h >= 10:
            k = 2.0 / (20 + 1)
            ema = float(c4h[0]["close"])
            for b in c4h:
                cp = float(b["close"])
                ema = (cp * k) + (ema * (1.0 - k))
                ema20_4h[b["time"]] = (ema, cp)
                
        sorted_4h_times = sorted(ema20_4h.keys())
        
        def get_4h_bias(t_ms):
            valid = [t for t in sorted_4h_times if t <= t_ms]
            if not valid: return "NEUTRAL"
            last_t = valid[-1]
            ema_val, close_val = ema20_4h[last_t]
            return "BULLISH" if close_val >= ema_val else "BEARISH"
            
        used_obs = set()
        disp_threshold = 0.020
        
        for i in range(5, n_1h - 20):
            c = c1h[i]
            c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
            c_disp = c1h[i+1]
            c_curr = c1h[i+2]
            
            macro_bias = get_4h_bias(c["time"])
            
            # LONG
            if macro_bias == "BULLISH":
                disp_gain = (c_disp["high"] - c_l) / c_l
                has_fvg = c_curr["low"] > c_h
                if disp_gain >= disp_threshold and has_fvg:
                    ob_high, ob_low = c_h, c_l
                    entry_price = (ob_high + ob_low) / 2.0
                    sl_price = ob_low * 0.9985
                    
                    for tap_idx in range(i + 3, min(i + 3 + 24, n_1h)):
                        b_tap = c1h[tap_idx]
                        if b_tap["low"] <= sl_price and b_tap["open"] > entry_price:
                            break
                        if b_tap["low"] <= entry_price and b_tap["high"] >= entry_price:
                            if i in used_obs:
                                break
                            bar_range = b_tap["high"] - b_tap["low"]
                            lower_wick = min(b_tap["open"], b_tap["close"]) - b_tap["low"]
                            wick_ratio = (lower_wick / bar_range) if bar_range > 0 else 0
                            if wick_ratio < 0.12:
                                continue
                                
                            used_obs.add(i)
                            active_sl = sl_price
                            current_tier = -1
                            final_roi = 0.0
                            exit_time = b_tap["time"]
                            
                            for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 48, n_1h)):
                                hb = c1h[h_idx]
                                high_gain = (hb["high"] - entry_price) / entry_price
                                high_roi = high_gain * 4.0
                                
                                for step_idx, (trig_roi, lock_roi) in enumerate(LADDER):
                                    if high_roi >= trig_roi and step_idx > current_tier:
                                        current_tier = step_idx
                                        active_sl = entry_price * (1.0 + (lock_roi / 4.0))
                                        
                                if hb["low"] <= active_sl:
                                    exit_time = hb["time"]
                                    if current_tier >= 0:
                                        final_roi = LADDER[current_tier][1]
                                    else:
                                        final_roi = -((entry_price - active_sl) / entry_price * 4.0)
                                    break
                                    
                            trades.append({
                                "symbol": sym,
                                "side": "LONG",
                                "entry_time": b_tap["time"],
                                "exit_time": exit_time,
                                "final_roi": final_roi,
                                "tier": current_tier + 1
                            })
                            break
                            
            # SHORT
            elif macro_bias == "BEARISH":
                disp_drop = (c_h - c_disp["low"]) / c_h
                has_fvg = c_curr["high"] < c_l
                if disp_drop >= disp_threshold and has_fvg:
                    ob_high, ob_low = c_h, c_l
                    entry_price = (ob_high + ob_low) / 2.0
                    sl_price = ob_high * 1.0015
                    
                    for tap_idx in range(i + 3, min(i + 3 + 24, n_1h)):
                        b_tap = c1h[tap_idx]
                        if b_tap["high"] >= sl_price and b_tap["open"] < entry_price:
                            break
                        if b_tap["high"] >= entry_price and b_tap["low"] <= entry_price:
                            if i in used_obs:
                                break
                            bar_range = b_tap["high"] - b_tap["low"]
                            upper_wick = b_tap["high"] - max(b_tap["open"], b_tap["close"])
                            wick_ratio = (upper_wick / bar_range) if bar_range > 0 else 0
                            if wick_ratio < 0.12:
                                continue
                                
                            used_obs.add(i)
                            active_sl = sl_price
                            current_tier = -1
                            final_roi = 0.0
                            exit_time = b_tap["time"]
                            
                            for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 48, n_1h)):
                                hb = c1h[h_idx]
                                drop_gain = (entry_price - hb["low"]) / entry_price
                                drop_roi = drop_gain * 4.0
                                
                                for step_idx, (trig_roi, lock_roi) in enumerate(LADDER):
                                    if drop_roi >= trig_roi and step_idx > current_tier:
                                        current_tier = step_idx
                                        active_sl = entry_price * (1.0 - (lock_roi / 4.0))
                                        
                                if hb["high"] >= active_sl:
                                    exit_time = hb["time"]
                                    if current_tier >= 0:
                                        final_roi = LADDER[current_tier][1]
                                    else:
                                        final_roi = -((active_sl - entry_price) / entry_price * 4.0)
                                    break
                                    
                            trades.append({
                                "symbol": sym,
                                "side": "SHORT",
                                "entry_time": b_tap["time"],
                                "exit_time": exit_time,
                                "final_roi": final_roi,
                                "tier": current_tier + 1
                            })
                            break
                            
    trades.sort(key=lambda x: x["entry_time"])
    return trades

def simulate_compounding_mode(trades, margin_fraction, label):
    # 10 isolated sections, $50 starting each
    sections = {str(i): {"balance": 50.0, "trades": 0, "wins": 0, "saves": 0, "losses": 0} for i in range(1, 11)}
    peak_portfolio = 500.0
    max_dd = 0.0
    
    for t in trades:
        sym = t["symbol"]
        sec_id = str(PAIR_MAPPING.get(sym, 1))
        sec = sections[sec_id]
        
        # Compounding Margin = fraction of CURRENT dynamic section balance!
        margin = sec["balance"] * margin_fraction
        pnl_usd = margin * t["final_roi"]
        
        sec["balance"] = max(1.0, sec["balance"] + pnl_usd)
        sec["trades"] += 1
        
        if t["final_roi"] > 0.007:
            sec["wins"] += 1
        elif 0.003 <= t["final_roi"] <= 0.007:
            sec["saves"] += 1
        else:
            sec["losses"] += 1
            
        cur_tot = sum(s["balance"] for s in sections.values())
        if cur_tot > peak_portfolio:
            peak_portfolio = cur_tot
        dd = ((peak_portfolio - cur_tot) / peak_portfolio) * 100.0
        if dd > max_dd:
            max_dd = dd
            
    final_tot = sum(s["balance"] for s in sections.values())
    roi_pct = ((final_tot - 500.0) / 500.0) * 100.0
    
    sec_details = {}
    for sid, s in sections.items():
        sec_details[f"Sec_{sid}"] = {
            "final_balance": round(s["balance"], 2),
            "trades": s["trades"],
            "wins": s["wins"],
            "saves": s["saves"],
            "losses": s["losses"]
        }
        
    return {
        "mode": label,
        "margin_allocated_pct": f"{margin_fraction*100:.0f}% of dynamic section balance",
        "initial_capital_usd": 500.0,
        "final_capital_usd": round(final_tot, 2),
        "net_profit_usd": round(final_tot - 500.0, 2),
        "portfolio_roi_pct": round(roi_pct, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "section_breakdown": sec_details
    }

def main():
    trades = extract_oos_trades()
    print(f"Extracted {len(trades)} chronological OOS trades across 20 Altcoins.")
    
    # Run 3 Compounding Tiers:
    res_10 = simulate_compounding_mode(trades, 0.10, "Conservative Deca Compounding (10% Dynamic Margin)")
    res_25 = simulate_compounding_mode(trades, 0.25, "Balanced Deca Compounding (25% Dynamic Margin)")
    res_50 = simulate_compounding_mode(trades, 0.50, "Aggressive Deca Compounding (50% Dynamic Margin)")
    
    summary = {
        "Conservative_10pct": res_10,
        "Balanced_25pct": res_25,
        "Aggressive_50pct": res_50
    }
    
    print(json.dumps(summary, indent=2))
    
    with open(os.path.join(REPO_ROOT, "scratch", "deca_compounding_oos_comparison.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
