import os
import sys
import json

REPO_ROOT = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
CACHE_DIR = os.path.join(REPO_ROOT, "market_data_cache_15m")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 20 Altcoins (BTC and ETH REPLACED by ADA and AAVE)
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

def simulate_hybrid_oos(c1h, c4h, symbol, leverage=4.0):
    trades = []
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
    
    def get_4h_macro_trend(t_ms):
        valid = [t for t in sorted_4h_times if t <= t_ms]
        if not valid: return "NEUTRAL"
        last_t = valid[-1]
        ema_val, close_val = ema20_4h[last_t]
        return "BULLISH" if close_val >= ema_val else "BEARISH"

    used_obs = set()
    disp_threshold = 0.020 # 2% displacement
    
    for i in range(5, n_1h - 20):
        c = c1h[i]
        c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
        c_disp = c1h[i+1]
        c_curr = c1h[i+2]
        
        macro_bias = get_4h_macro_trend(c["time"])
        
        # LONG
        if macro_bias == "BULLISH":
            disp_gain = (c_disp["high"] - c_l) / c_l
            has_fvg = c_curr["low"] > c_h
            if disp_gain >= disp_threshold and has_fvg:
                ob_high = c_h
                ob_low = c_l
                entry_price = (ob_high + ob_low) / 2.0
                sl_price = ob_low * (1.0 - 0.0015)
                
                # Check 1st Tap within 24 hours
                for tap_idx in range(i + 3, min(i + 3 + 24, n_1h)):
                    b_tap = c1h[tap_idx]
                    if b_tap["low"] <= sl_price and b_tap["open"] > entry_price:
                        break
                    if b_tap["low"] <= entry_price and b_tap["high"] >= entry_price:
                        if i in used_obs:
                            break
                        # Wick Gate (>=12% lower rejection wick)
                        bar_range = b_tap["high"] - b_tap["low"]
                        lower_wick = min(b_tap["open"], b_tap["close"]) - b_tap["low"]
                        wick_ratio = (lower_wick / bar_range) if bar_range > 0 else 0
                        if wick_ratio < 0.12:
                            continue # Skip falling knife
                            
                        used_obs.add(i)
                        active_sl = sl_price
                        current_tier = -1
                        outcome = None
                        final_roi = 0.0
                        
                        for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 48, n_1h)):
                            hb = c1h[h_idx]
                            
                            high_gain = (hb["high"] - entry_price) / entry_price
                            high_roi = high_gain * leverage
                            
                            # Check ladder progression
                            for step_idx, (trig_roi, lock_roi) in enumerate(LADDER):
                                if high_roi >= trig_roi and step_idx > current_tier:
                                    current_tier = step_idx
                                    locked_price_gain = lock_roi / leverage
                                    active_sl = entry_price * (1.0 + locked_price_gain)
                                    
                            # Check SL hit
                            if hb["low"] <= active_sl:
                                if current_tier >= 0:
                                    lock_roi = LADDER[current_tier][1]
                                    final_roi = lock_roi
                                    outcome = f"LADDER_TIER_{current_tier+1}_LOCK (+{lock_roi*100:.1f}%)"
                                else:
                                    sl_drop = (entry_price - active_sl) / entry_price
                                    final_roi = -(sl_drop * leverage)
                                    outcome = f"FULL_SL_LOSS ({final_roi*100:.1f}%)"
                                break
                                
                        if not outcome:
                            last_c = c1h[min(tap_idx + 48, n_1h - 1)]["close"]
                            final_roi = ((last_c - entry_price) / entry_price) * leverage
                            outcome = f"TIMEOUT ({final_roi*100:.1f}%)"
                            
                        trades.append({
                            "symbol": symbol,
                            "time": b_tap.get("time", 0),
                            "side": "LONG",
                            "entry": entry_price,
                            "final_roi": round(final_roi, 4),
                            "outcome": outcome,
                            "tier_reached": current_tier + 1
                        })
                        break

        # SHORT
        elif macro_bias == "BEARISH":
            disp_drop = (c_h - c_disp["low"]) / c_h
            has_fvg = c_curr["high"] < c_l
            if disp_drop >= disp_threshold and has_fvg:
                ob_high = c_h
                ob_low = c_l
                entry_price = (ob_high + ob_low) / 2.0
                sl_price = ob_high * (1.0 + 0.0015)
                
                for tap_idx in range(i + 3, min(i + 3 + 24, n_1h)):
                    b_tap = c1h[tap_idx]
                    if b_tap["high"] >= sl_price and b_tap["open"] < entry_price:
                        break
                    if b_tap["high"] >= entry_price and b_tap["low"] <= entry_price:
                        if i in used_obs:
                            break
                        # Wick Gate (>=12% upper rejection wick)
                        bar_range = b_tap["high"] - b_tap["low"]
                        upper_wick = b_tap["high"] - max(b_tap["open"], b_tap["close"])
                        wick_ratio = (upper_wick / bar_range) if bar_range > 0 else 0
                        if wick_ratio < 0.12:
                            continue
                            
                        used_obs.add(i)
                        active_sl = sl_price
                        current_tier = -1
                        outcome = None
                        final_roi = 0.0
                        
                        for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 48, n_1h)):
                            hb = c1h[h_idx]
                            
                            drop_gain = (entry_price - hb["low"]) / entry_price
                            drop_roi = drop_gain * leverage
                            
                            for step_idx, (trig_roi, lock_roi) in enumerate(LADDER):
                                if drop_roi >= trig_roi and step_idx > current_tier:
                                    current_tier = step_idx
                                    locked_price_gain = lock_roi / leverage
                                    active_sl = entry_price * (1.0 - locked_price_gain)
                                    
                            if hb["high"] >= active_sl:
                                if current_tier >= 0:
                                    lock_roi = LADDER[current_tier][1]
                                    final_roi = lock_roi
                                    outcome = f"LADDER_TIER_{current_tier+1}_LOCK (+{lock_roi*100:.1f}%)"
                                else:
                                    sl_rise = (active_sl - entry_price) / entry_price
                                    final_roi = -(sl_rise * leverage)
                                    outcome = f"FULL_SL_LOSS ({final_roi*100:.1f}%)"
                                break
                                
                        if not outcome:
                            last_c = c1h[min(tap_idx + 48, n_1h - 1)]["close"]
                            final_roi = ((entry_price - last_c) / entry_price) * leverage
                            outcome = f"TIMEOUT ({final_roi*100:.1f}%)"
                            
                        trades.append({
                            "symbol": symbol,
                            "time": b_tap.get("time", 0),
                            "side": "SHORT",
                            "entry": entry_price,
                            "final_roi": round(final_roi, 4),
                            "outcome": outcome,
                            "tier_reached": current_tier + 1
                        })
                        break
                        
    return trades

def evaluate_oos_portfolio(trades, period_label):
    trades.sort(key=lambda x: x.get("time", 0))
    total = len(trades)
    if total == 0:
        return {"period": period_label, "total_trades": 0}
        
    wins = [t for t in trades if t["final_roi"] > 0]
    fee_shield = [t for t in trades if 0.004 <= t["final_roi"] <= 0.007]
    pure_profit_wins = [t for t in trades if t["final_roi"] >= 0.05]
    losses = [t for t in trades if t["final_roi"] < 0]
    
    pure_wr = (len(pure_profit_wins) / total) * 100.0
    quality_wr = (len(wins) / total) * 100.0
    
    # Portfolio Deca simulation: $500 initial ($50 per section, 10 sections)
    sections = {str(i): {"balance": 50.0, "trades": 0, "wins": 0, "losses": 0} for i in range(1, 11)}
    peak_eq = 500.0
    max_dd = 0.0
    
    gross_win_usd = 0.0
    gross_loss_usd = 0.0
    
    for t in trades:
        sym = t["symbol"]
        sec_id = str(PAIR_MAPPING.get(sym, 1))
        sec = sections[sec_id]
        
        bal = sec["balance"]
        margin_usd = bal * 0.10 # 10% section margin
        trade_usd = margin_usd * t["final_roi"]
        
        sec["balance"] = max(1.0, bal + trade_usd)
        sec["trades"] += 1
        
        if trade_usd > 0:
            sec["wins"] += 1
            gross_win_usd += trade_usd
        elif trade_usd < 0:
            sec["losses"] += 1
            gross_loss_usd += abs(trade_usd)
            
        cur_eq = sum(s["balance"] for s in sections.values())
        if cur_eq > peak_eq:
            peak_eq = cur_eq
        dd = ((peak_eq - cur_eq) / peak_eq) * 100.0
        if dd > max_dd:
            max_dd = dd
            
    final_eq = sum(s["balance"] for s in sections.values())
    roi_pct = ((final_eq - 500.0) / 500.0) * 100.0
    profit_factor = (gross_win_usd / gross_loss_usd) if gross_loss_usd > 0 else 999.0
    
    tier_distribution = {
        "Tier_0_Initial_SL_Loss": sum(1 for t in trades if t["tier_reached"] == 0),
        "Tier_1_Fee_Shield_Lock (+0.5% ROI)": sum(1 for t in trades if t["tier_reached"] == 1),
        "Tier_2_Profit_Lock (+5.1% ROI)": sum(1 for t in trades if t["tier_reached"] == 2),
        "Tier_3_Profit_Lock (+10.1% ROI)": sum(1 for t in trades if t["tier_reached"] == 3),
        "Tier_4_Profit_Lock (+15.1% ROI)": sum(1 for t in trades if t["tier_reached"] == 4),
        "Tier_5_Profit_Lock (+20.1% ROI)": sum(1 for t in trades if t["tier_reached"] == 5),
        "Tier_6_Profit_Lock (+25.0% ROI)": sum(1 for t in trades if t["tier_reached"] == 6)
    }
    
    return {
        "period": period_label,
        "universe": "20 Altcoins (NO BTC/ETH — ADA & AAVE Added)",
        "leverage": "4x",
        "total_trades": total,
        "pure_profit_wins (>= +5.1% ROI)": len(pure_profit_wins),
        "fee_shield_saves (+0.5% ROI)": len(fee_shield),
        "total_losses": len(losses),
        "pure_win_rate_pct": round(pure_wr, 2),
        "quality_win_rate_pct": round(quality_wr, 2),
        "profit_factor": round(profit_factor, 2),
        "initial_capital_usd": 500.0,
        "final_capital_usd": round(final_eq, 2),
        "net_profit_usd": round(final_eq - 500.0, 2),
        "portfolio_roi_pct": round(roi_pct, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "tier_distribution": tier_distribution
    }

def main():
    oos_trades = []
    
    for sym in CHAMPIONS_NO_BTC_ETH:
        fpath = os.path.join(CACHE_DIR, f"{sym}_15m.json")
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            raw = json.load(f)
            
        # OOS period: bars [-5760 : -2880] (30 full days unseen prior month)
        if len(raw) < 5760:
            c_15m_oos = raw[-2880:] # fallback if less bars
        else:
            c_15m_oos = raw[-5760:-2880]
            
        c_1h_oos = resample_candles(c_15m_oos, 4)
        c_4h_oos = resample_candles(c_15m_oos, 16)
        
        t = simulate_hybrid_oos(c_1h_oos, c_4h_oos, sym, leverage=4.0)
        oos_trades.extend(t)
        
    res = evaluate_oos_portfolio(oos_trades, "1-Month OUT-OF-SAMPLE (OOS) Test (Prior Unseen 30 Days)")
    print(json.dumps(res, indent=2))
    
    with open(os.path.join(REPO_ROOT, "scratch", "oos_1month_test_results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

if __name__ == "__main__":
    main()
