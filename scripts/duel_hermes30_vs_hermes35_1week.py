import os
import sys
import json
import glob
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

def load_1week_candles(symbol, bars=672):
    """Loads the last 1 week (672 bars of 15m = 7 full days) from the cache."""
    fpath = os.path.join(CACHE_DIR, f"{symbol}_15m.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        candles = json.load(f)
    return candles[-bars:] if len(candles) >= bars else candles

# ==============================================================================
# STRATEGY 1: HERMES 3.0 MODEL 2A
# ==============================================================================
def simulate_hermes30_2a(candles, leverage=5.0):
    trades = []
    n = len(candles)
    
    # 1. Scan for Order Blocks
    for i in range(15, n - 35):
        c = candles[i]
        c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
        c_disp = candles[i+1]
        c_curr = candles[i+2]
        
        # Bullish OB (Red candle followed by displacement pump + FVG)
        if c_c < c_o:
            disp_gain = (c_disp["high"] - c_l) / c_l
            has_fvg = c_curr["low"] > c_h
            if disp_gain >= 0.015 and has_fvg:
                ob_high = c_h
                ob_low = c_l
                mt = (ob_high + ob_low) / 2.0 # 50% Mean Threshold
                
                # Check tap within 28 bars
                for tap_idx in range(i + 3, min(i + 3 + 28, n)):
                    b_tap = candles[tap_idx]
                    if b_tap["low"] <= mt <= b_tap["high"]:
                        # 18% Rejection wick check
                        tap_range = b_tap["high"] - b_tap["low"]
                        lower_wick = min(b_tap["open"], b_tap["close"]) - b_tap["low"]
                        wick_ratio = lower_wick / tap_range if tap_range > 0 else 0
                        if wick_ratio >= 0.18:
                            # Filled! Evaluate Trade
                            entry = mt
                            tp = entry * (1.0 + 0.030) # +3% spot = +15% ROE
                            soft_sl = entry * (1.0 - 0.015) # -1.5% spot = -7.5% ROE
                            be_trig = entry * (1.0 + 0.010) # +1.0% spot = +5.0% ROE
                            
                            active_sl = soft_sl
                            be_active = False
                            outcome = None
                            pnl_roe = 0.0
                            
                            for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 96, n)):
                                hb = candles[h_idx]
                                # Check TP
                                if hb["high"] >= tp:
                                    outcome = "WIN"
                                    pnl_roe = 15.0
                                    break
                                # Check BE trigger
                                if not be_active and hb["high"] >= be_trig:
                                    be_active = True
                                    active_sl = entry * 1.001 # BE + fee buffer
                                # Check SL / Soft SL on close
                                if hb["close"] <= active_sl or hb["low"] <= entry * 0.970:
                                    if be_active:
                                        outcome = "BE_SAVE"
                                        pnl_roe = 0.5
                                    else:
                                        outcome = "LOSS"
                                        pnl_roe = -7.5
                                    break
                            
                            if not outcome:
                                outcome = "TIMEOUT"
                                pnl_roe = ((candles[min(tap_idx+96, n-1)]["close"] - entry) / entry) * leverage * 100.0
                                
                            trades.append({
                                "model": "HERMES_3.0_2A",
                                "bar_idx": tap_idx,
                                "time": b_tap.get("time", 0),
                                "side": "LONG",
                                "entry": entry,
                                "outcome": outcome,
                                "roe": pnl_roe
                            })
                            break
                            
        # Bearish OB
        elif c_c > c_o:
            disp_drop = (c_h - c_disp["low"]) / c_h
            has_fvg = c_curr["high"] < c_l
            if disp_drop >= 0.015 and has_fvg:
                ob_high = c_h
                ob_low = c_l
                mt = (ob_high + ob_low) / 2.0
                
                for tap_idx in range(i + 3, min(i + 3 + 28, n)):
                    b_tap = candles[tap_idx]
                    if b_tap["low"] <= mt <= b_tap["high"]:
                        tap_range = b_tap["high"] - b_tap["low"]
                        upper_wick = b_tap["high"] - max(b_tap["open"], b_tap["close"])
                        wick_ratio = upper_wick / tap_range if tap_range > 0 else 0
                        if wick_ratio >= 0.18:
                            entry = mt
                            tp = entry * (1.0 - 0.030)
                            soft_sl = entry * (1.0 + 0.015)
                            be_trig = entry * (1.0 - 0.010)
                            
                            active_sl = soft_sl
                            be_active = False
                            outcome = None
                            pnl_roe = 0.0
                            
                            for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 96, n)):
                                hb = candles[h_idx]
                                if hb["low"] <= tp:
                                    outcome = "WIN"
                                    pnl_roe = 15.0
                                    break
                                if not be_active and hb["low"] <= be_trig:
                                    be_active = True
                                    active_sl = entry * 0.999
                                if hb["close"] >= active_sl or hb["high"] >= entry * 1.030:
                                    if be_active:
                                        outcome = "BE_SAVE"
                                        pnl_roe = 0.5
                                    else:
                                        outcome = "LOSS"
                                        pnl_roe = -7.5
                                    break
                                    
                            if not outcome:
                                outcome = "TIMEOUT"
                                pnl_roe = ((entry - candles[min(tap_idx+96, n-1)]["close"]) / entry) * leverage * 100.0
                                
                            trades.append({
                                "model": "HERMES_3.0_2A",
                                "bar_idx": tap_idx,
                                "time": b_tap.get("time", 0),
                                "side": "SHORT",
                                "entry": entry,
                                "outcome": outcome,
                                "roe": pnl_roe
                            })
                            break
                            
    return trades

# ==============================================================================
# STRATEGY 2: HERMES 3.5 RADAR HARVEST
# ==============================================================================
def simulate_hermes35_radar_harvest(candles, leverage=5.0):
    trades = []
    n = len(candles)
    
    for i in range(15, n - 35):
        c = candles[i]
        c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
        c_disp = candles[i+1]
        c_curr = candles[i+2]
        
        # Bullish OB (5% Boundary Penetration + Airspace Void >= 5% + Maturation >= 18 bars)
        if c_c < c_o:
            disp_gain = (c_disp["high"] - c_l) / c_l
            has_fvg = c_curr["low"] > c_h
            if disp_gain >= 0.015 and has_fvg:
                ob_high = c_h
                ob_low = c_l
                ob_rng = ob_high - ob_low
                # 5% Boundary Entry (outer rim)
                entry = ob_high - (ob_rng * 0.05)
                
                # Check maturation & runway void
                peak_runway = max(b["high"] for b in candles[i+1:i+18]) if i+18 < n else ob_high
                runway_pct = ((peak_runway - ob_high) / ob_high) * 100.0
                
                if runway_pct >= 3.0: # Valid airspace void
                    for tap_idx in range(i + 18, min(i + 150, n)):
                        b_tap = candles[tap_idx]
                        if b_tap["low"] <= entry:
                            # Filled! Evaluate Stepped Harvest Engine
                            tp = entry * (1.0 + 0.0280)       # +14.0% ROE
                            sl = entry * (1.0 - 0.0280)       # -14.0% ROE
                            be_trig = entry * (1.0 + 0.0160)  # +8.0% ROE -> BE Lock
                            step_trig = entry * (1.0 + 0.0180)# +9.0% ROE -> Lock +4.5% ROE
                            step_lock = entry * (1.0 + 0.0090)# +4.5% ROE locked SL
                            
                            active_sl = sl
                            be_locked = False
                            harvest_locked = False
                            outcome = None
                            pnl_roe = 0.0
                            
                            for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 96, n)):
                                hb = candles[h_idx]
                                # 1. Stage 1 BE
                                if not be_locked and hb["high"] >= be_trig:
                                    be_locked = True
                                    active_sl = entry * 1.001
                                # 2. Stage 2 Harvest Lock
                                if not harvest_locked and hb["high"] >= step_trig:
                                    harvest_locked = True
                                    active_sl = step_lock
                                # 3. Stage 3 TP Hit
                                if hb["high"] >= tp:
                                    outcome = "WIN"
                                    pnl_roe = 14.0
                                    break
                                # Check SL Hit
                                if hb["low"] <= active_sl:
                                    if harvest_locked:
                                        outcome = "HARVEST_WIN"
                                        pnl_roe = 4.5
                                    elif be_locked:
                                        outcome = "BE_SAVE"
                                        pnl_roe = 0.5
                                    else:
                                        outcome = "LOSS"
                                        pnl_roe = -14.0
                                    break
                                    
                            if not outcome:
                                outcome = "TIMEOUT"
                                pnl_roe = ((candles[min(tap_idx+96, n-1)]["close"] - entry) / entry) * leverage * 100.0
                                
                            trades.append({
                                "model": "HERMES_3.5_RADAR_HARVEST",
                                "bar_idx": tap_idx,
                                "time": b_tap.get("time", 0),
                                "side": "LONG",
                                "entry": entry,
                                "outcome": outcome,
                                "roe": pnl_roe
                            })
                            break
                            
        # Bearish OB
        elif c_c > c_o:
            disp_drop = (c_h - c_disp["low"]) / c_h
            has_fvg = c_curr["high"] < c_l
            if disp_drop >= 0.015 and has_fvg:
                ob_high = c_h
                ob_low = c_l
                ob_rng = ob_high - ob_low
                entry = ob_low + (ob_rng * 0.05)
                
                trough_runway = min(b["low"] for b in candles[i+1:i+18]) if i+18 < n else ob_low
                runway_pct = ((ob_low - trough_runway) / ob_low) * 100.0
                
                if runway_pct >= 3.0:
                    for tap_idx in range(i + 18, min(i + 150, n)):
                        b_tap = candles[tap_idx]
                        if b_tap["high"] >= entry:
                            tp = entry * (1.0 - 0.0280)
                            sl = entry * (1.0 + 0.0280)
                            be_trig = entry * (1.0 - 0.0160)
                            step_trig = entry * (1.0 - 0.0180)
                            step_lock = entry * (1.0 - 0.0090)
                            
                            active_sl = sl
                            be_locked = False
                            harvest_locked = False
                            outcome = None
                            pnl_roe = 0.0
                            
                            for h_idx in range(tap_idx + 1, min(tap_idx + 1 + 96, n)):
                                hb = candles[h_idx]
                                if not be_locked and hb["low"] <= be_trig:
                                    be_locked = True
                                    active_sl = entry * 0.999
                                if not harvest_locked and hb["low"] <= step_trig:
                                    harvest_locked = True
                                    active_sl = step_lock
                                if hb["low"] <= tp:
                                    outcome = "WIN"
                                    pnl_roe = 14.0
                                    break
                                if hb["high"] >= active_sl:
                                    if harvest_locked:
                                        outcome = "HARVEST_WIN"
                                        pnl_roe = 4.5
                                    elif be_locked:
                                        outcome = "BE_SAVE"
                                        pnl_roe = 0.5
                                    else:
                                        outcome = "LOSS"
                                        pnl_roe = -14.0
                                    break
                                    
                            if not outcome:
                                outcome = "TIMEOUT"
                                pnl_roe = ((entry - candles[min(tap_idx+96, n-1)]["close"]) / entry) * leverage * 100.0
                                
                            trades.append({
                                "model": "HERMES_3.5_RADAR_HARVEST",
                                "bar_idx": tap_idx,
                                "time": b_tap.get("time", 0),
                                "side": "SHORT",
                                "entry": entry,
                                "outcome": outcome,
                                "roe": pnl_roe
                            })
                            break
                            
    return trades

def run_duel():
    h30_all = []
    h35_all = []
    
    for sym in CHAMPIONS:
        candles = load_1week_candles(sym, bars=672)
        if len(candles) < 100:
            continue
        t30 = simulate_hermes30_2a(candles)
        t35 = simulate_hermes35_radar_harvest(candles)
        h30_all.extend(t30)
        h35_all.extend(t35)
        
    def analyze_stats(trades_list, name):
        total = len(trades_list)
        if total == 0:
            return {"name": name, "total": 0}
        wins = [t for t in trades_list if t["outcome"] in ["WIN", "HARVEST_WIN"]]
        pure_wins = [t for t in trades_list if t["outcome"] == "WIN"]
        harvest_wins = [t for t in trades_list if t["outcome"] == "HARVEST_WIN"]
        be_saves = [t for t in trades_list if t["outcome"] == "BE_SAVE"]
        losses = [t for t in trades_list if t["outcome"] == "LOSS"]
        
        pure_wr = (len(pure_wins) / total) * 100.0
        qual_wr = ((len(wins) + len(be_saves)) / total) * 100.0
        total_roe = sum(t["roe"] for t in trades_list)
        avg_roe = total_roe / total
        
        # Calculate capital growth starting at $500 (10 sections of $50 each, 5% risk per trade = $2.50 risk unit)
        capital = 500.0
        peak = capital
        max_dd = 0.0
        for t in trades_list:
            dollar_change = (t["roe"] / 100.0) * (capital * 0.05) # 5% position risk
            capital += dollar_change
            if capital > peak:
                peak = capital
            dd = ((peak - capital) / peak) * 100.0
            if dd > max_dd:
                max_dd = dd
                
        return {
            "name": name,
            "total_trades": total,
            "pure_wins": len(pure_wins),
            "harvest_wins": len(harvest_wins),
            "be_saves": len(be_saves),
            "losses": len(losses),
            "pure_win_rate": round(pure_wr, 1),
            "quality_win_rate": round(qual_wr, 1),
            "total_roe_pct": round(total_roe, 1),
            "avg_roe_per_trade": round(avg_roe, 2),
            "final_capital": round(capital, 2),
            "net_profit_usd": round(capital - 500.0, 2),
            "roi_pct": round(((capital - 500.0) / 500.0) * 100.0, 1),
            "max_drawdown_pct": round(max_dd, 1)
        }
        
    s30 = analyze_stats(h30_all, "HERMES 3.0 MODEL 2A")
    s35 = analyze_stats(h35_all, "HERMES 3.5 RADAR HARVEST")
    
    print("=" * 80)
    print("⚔️ 1-WEEK QUANT DUEL: HERMES 3.0 MODEL 2A vs HERMES 3.5 RADAR HARVEST")
    print(f"Period: 1 Full Week (672 15m Bars) | Universe: Top-20 Champions")
    print("=" * 80)
    print(json.dumps({"Hermes_30_2A": s30, "Hermes_35_Radar": s35}, indent=2))
    
    with open(os.path.join(REPO_ROOT, "scratch", "duel_1week_h30_vs_h35.json"), "w", encoding="utf-8") as f:
        json.dump({"Hermes_30_2A": s30, "Hermes_35_Radar": s35}, f, indent=2)

if __name__ == "__main__":
    run_duel()
