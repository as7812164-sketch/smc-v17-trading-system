import os
import sys
import json
from datetime import datetime, timezone

# Add repo root to path
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

def load_1month_candles(symbol, bars=2880):
    """Loads 1 Full Month of 15m candles (2,880 bars = 30 days)."""
    fpath = os.path.join(CACHE_DIR, f"{symbol}_15m.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        candles = json.load(f)
    return candles[-bars:] if len(candles) >= bars else candles

def backtest_hermes35_new_rules(candles, symbol, leverage=4.0):
    """
    NEW USER SPECIFICATION:
    - Leverage: 4x Isolated
    - Entry Trigger: First Tap ONLY when price inserts 50% into OB (50% Mean Threshold)
    - Stop Loss: Extreme Wick of OB ± 0.15% buffer
    - Target: 2:4 R:R (1:2 Risk to Reward = 2.0R)
    - Trailing SL:
        * Milestone 1 (+1.0R): SL shifts to +0.2R (Breakeven Fee Shield)
        * Milestone 2 (+1.5R): SL shifts to +1.0R (Locked Profit)
        * Full Target (+2.0R): Full TP Exit
    """
    trades = []
    n = len(candles)
    
    # Track used/mitigated OBs to ensure strictly 1st TAP ONLY
    used_obs = set()
    
    for i in range(15, n - 40):
        c = candles[i]
        c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
        c_disp = candles[i+1]
        c_curr = candles[i+2]
        
        # ----------------------------------------------------------------------
        # 1. BULLISH ORDER BLOCK (Demand Base + Displacement + FVG)
        # ----------------------------------------------------------------------
        if c_c < c_o or (c_h - c_l) > 0:
            disp_gain = (c_disp["high"] - c_l) / c_l
            has_fvg = c_curr["low"] > c_h
            if disp_gain >= 0.015 and has_fvg:
                ob_high = c_h
                ob_low = c_l
                ob_rng = ob_high - ob_low
                
                # 50% Mean Threshold Entry (price inserts 50% into OB)
                entry_price = (ob_high + ob_low) / 2.0
                sl_price = ob_low * (1.0 - 0.0015) # 0.15% buffer below OB floor
                risk = entry_price - sl_price
                
                if risk <= 0:
                    continue
                    
                tp_price = entry_price + (2.0 * risk) # 2:4 R:R (1:2 Risk-Reward)
                
                # Freshness window: First tap must happen within 48 bars (~12 hours)
                # First tap only: If price penetrates below entry, this is tap #1
                for tap_idx in range(i + 3, min(i + 3 + 48, n)):
                    b_tap = candles[tap_idx]
                    
                    # Invalidation before tap: If price broke below SL before tapping entry
                    if b_tap["low"] <= sl_price and b_tap["open"] > entry_price:
                        # Broken without valid fill
                        break
                        
                    # First Tap 50% MT Fill
                    if b_tap["low"] <= entry_price and b_tap["high"] >= entry_price:
                        if i in used_obs:
                            break # Strictly first tap only!
                        used_obs.add(i)
                        
                        # Evaluate Trailing SL on subsequent bars
                        active_sl = sl_price
                        current_tier = 0
                        outcome = None
                        pnl_r = 0.0
                        
                        # Trailing Milestones
                        t1_price = entry_price + (1.0 * risk) # +1.0R
                        t2_price = entry_price + (1.5 * risk) # +1.5R
                        
                        for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 96, n)):
                            hb = candles[h_idx]
                            
                            # 1. Check Trailing Milestone 2 (+1.5R) -> Lock +1.0R
                            if current_tier < 2 and hb["high"] >= t2_price:
                                current_tier = 2
                                active_sl = entry_price + (1.0 * risk)
                                
                            # 2. Check Trailing Milestone 1 (+1.0R) -> Move to +0.2R (BE Shield)
                            elif current_tier < 1 and hb["high"] >= t1_price:
                                current_tier = 1
                                active_sl = entry_price + (0.2 * risk)
                                
                            # 3. Check Full TP Hit (+2.0R)
                            if hb["high"] >= tp_price:
                                outcome = "FULL_TP_WIN"
                                pnl_r = 2.0
                                break
                                
                            # 4. Check SL Hit
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
                            last_close = candles[min(tap_idx+96, n-1)]["close"]
                            pnl_r = (last_close - entry_price) / risk
                            
                        # Calculate ROE at 4x leverage
                        risk_pct = risk / entry_price
                        roe_pct = pnl_r * risk_pct * leverage * 100.0
                        
                        trades.append({
                            "symbol": symbol,
                            "side": "LONG",
                            "time": b_tap.get("time", 0),
                            "bar_idx": tap_idx,
                            "entry": entry_price,
                            "sl": sl_price,
                            "tp": tp_price,
                            "risk_pct": risk_pct * 100.0,
                            "outcome": outcome,
                            "pnl_r": round(pnl_r, 2),
                            "roe_pct": round(roe_pct, 2)
                        })
                        break
                        
        # ----------------------------------------------------------------------
        # 2. BEARISH ORDER BLOCK (Supply Base + Displacement Drop + FVG)
        # ----------------------------------------------------------------------
        elif c_c > c_o or (c_h - c_l) > 0:
            disp_drop = (c_h - c_disp["low"]) / c_h
            has_fvg = c_curr["high"] < c_l
            if disp_drop >= 0.015 and has_fvg:
                ob_high = c_h
                ob_low = c_l
                ob_rng = ob_high - ob_low
                
                entry_price = (ob_high + ob_low) / 2.0
                sl_price = ob_high * (1.0 + 0.0015)
                risk = sl_price - entry_price
                
                if risk <= 0:
                    continue
                    
                tp_price = entry_price - (2.0 * risk)
                
                for tap_idx in range(i + 3, min(i + 3 + 48, n)):
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
                        
                        for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 96, n)):
                            hb = candles[h_idx]
                            
                            if current_tier < 2 and hb["low"] <= t2_price:
                                current_tier = 2
                                active_sl = entry_price - (1.0 * risk)
                                
                            elif current_tier < 1 and hb["low"] <= t1_price:
                                current_tier = 1
                                active_sl = entry_price - (0.2 * risk)
                                
                            if hb["low"] <= tp_price:
                                outcome = "FULL_TP_WIN"
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
                            last_close = candles[min(tap_idx+96, n-1)]["close"]
                            pnl_r = (entry_price - last_close) / risk
                            
                        risk_pct = risk / entry_price
                        roe_pct = pnl_r * risk_pct * leverage * 100.0
                        
                        trades.append({
                            "symbol": symbol,
                            "side": "SHORT",
                            "time": b_tap.get("time", 0),
                            "bar_idx": tap_idx,
                            "entry": entry_price,
                            "sl": sl_price,
                            "tp": tp_price,
                            "risk_pct": risk_pct * 100.0,
                            "outcome": outcome,
                            "pnl_r": round(pnl_r, 2),
                            "roe_pct": round(roe_pct, 2)
                        })
                        break
                        
    return trades

def run_1month_backtest():
    all_trades = []
    symbol_breakdown = {}
    
    for sym in CHAMPIONS:
        candles = load_1month_candles(sym, bars=2880)
        if len(candles) < 200:
            continue
        sym_trades = backtest_hermes35_new_rules(candles, sym, leverage=4.0)
        all_trades.extend(sym_trades)
        symbol_breakdown[sym] = sym_trades
        
    # Sort all trades chronologically
    all_trades.sort(key=lambda t: t.get("time", 0))
    
    total = len(all_trades)
    if total == 0:
        print("No trades found!")
        return
        
    full_tp_wins = [t for t in all_trades if t["outcome"] == "FULL_TP_WIN"]
    trail_wins = [t for t in all_trades if "TRAILING_LOCK_WIN" in t["outcome"]]
    be_saves = [t for t in all_trades if "BE_FEE_SHIELD" in t["outcome"]]
    losses = [t for t in all_trades if t["outcome"] == "LOSS (-1.0R)"]
    timeouts = [t for t in all_trades if t["outcome"] == "TIMEOUT"]
    
    pure_wins_count = len(full_tp_wins) + len(trail_wins)
    pure_wr = (pure_wins_count / total) * 100.0
    quality_wr = ((pure_wins_count + len(be_saves)) / total) * 100.0
    
    total_r = sum(t["pnl_r"] for t in all_trades)
    avg_r = total_r / total
    
    # Portfolio simulation: 10 Deca sections ($50 starting each = $500 total)
    # 5% section risk = $2.50 per trade per section
    sections = {str(i): {"balance": 50.0, "trades": 0, "wins": 0, "losses": 0} for i in range(1, 11)}
    portfolio_equity = 500.0
    peak_equity = 500.0
    max_drawdown_pct = 0.0
    
    for t in all_trades:
        sec_id = str(PAIR_MAPPING.get(t["symbol"], 1))
        sec = sections[sec_id]
        
        # Risk amount is 5% of section balance
        risk_usd = sec["balance"] * 0.05
        dollar_pnl = t["pnl_r"] * risk_usd
        
        sec["balance"] += dollar_pnl
        sec["trades"] += 1
        if t["pnl_r"] > 0:
            sec["wins"] += 1
        elif t["pnl_r"] < 0:
            sec["losses"] += 1
            
        cur_port_eq = sum(s["balance"] for s in sections.values())
        if cur_port_eq > peak_equity:
            peak_equity = cur_port_eq
        dd = ((peak_equity - cur_port_eq) / peak_equity) * 100.0
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd
            
    final_equity = sum(s["balance"] for s in sections.values())
    net_profit_usd = final_equity - 500.0
    net_roi_pct = (net_profit_usd / 500.0) * 100.0
    
    # Calculate Profit Factor
    gross_gain_r = sum(t["pnl_r"] for t in all_trades if t["pnl_r"] > 0)
    gross_loss_r = abs(sum(t["pnl_r"] for t in all_trades if t["pnl_r"] < 0))
    profit_factor = (gross_gain_r / gross_loss_r) if gross_loss_r > 0 else 999.0
    
    report = {
        "engine": "HERMES 3.5 RADAR (NEW USER RULES: 4X LEVERAGE + 50% MT 1ST TAP + 2:4 RRR + STEPPED TRAILING SL)",
        "backtest_window": "1 Full Month (30 Days = 2,880 15m Bars)",
        "universe": "Top-20 Champions",
        "total_trades": total,
        "full_tp_wins_2r": len(full_tp_wins),
        "trailing_lock_wins_1r": len(trail_wins),
        "be_fee_shield_saves_02r": len(be_saves),
        "losses_neg_1r": len(losses),
        "timeouts": len(timeouts),
        "pure_win_rate_pct": round(pure_wr, 2),
        "quality_win_rate_pct": round(quality_wr, 2),
        "total_net_pnl_in_r": round(total_r, 2),
        "avg_r_per_trade": round(avg_r, 2),
        "profit_factor": round(profit_factor, 2),
        "starting_capital_usd": 500.00,
        "final_portfolio_equity_usd": round(final_equity, 2),
        "net_profit_usd": round(net_profit_usd, 2),
        "portfolio_roi_pct": round(net_roi_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "sections_breakdown": sections
    }
    
    print("=" * 80)
    print("🎯 HERMES 3.5 RADAR HARVEST — 1 MONTH QUANT BENCHMARK (NEW RULES)")
    print("=" * 80)
    print(json.dumps(report, indent=2))
    
    with open(os.path.join(REPO_ROOT, "scratch", "hermes35_new_rules_1month_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    run_1month_backtest()
