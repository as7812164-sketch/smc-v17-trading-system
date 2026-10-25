import asyncio
import sys
import numpy as np
from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17
from config import TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def analyze_patterns():
    print("=========================================================================================")
    print("      MIKE AI AGENT SQUAD: DEEP PATTERN DISCOVERY & WIN-RATE BOOST ANALYSIS")
    print("=========================================================================================")
    
    all_klines = await binance_feed.fetch_multiple_symbols(TIER1_COINS, interval="1h", limit=500)
    
    sweep_wins, sweep_total = 0, 0
    no_sweep_wins, no_sweep_total = 0, 0
    
    fvg_wins, fvg_total = 0, 0
    no_fvg_wins, no_fvg_total = 0, 0
    
    trend_aligned_wins, trend_aligned_total = 0, 0
    counter_trend_wins, counter_trend_total = 0, 0
    
    high_disp_wins, high_disp_total = 0, 0
    normal_disp_wins, normal_disp_total = 0, 0
    
    for sym, candles in all_klines.items():
        if not candles or len(candles) < 80:
            continue
            
        zones = analyze_candles_smc_v17(sym, candles)
        buy_zones = [z for z in zones if z["side"] == "BUY" and z.get("qualified") == 1]
        sell_zones = [z for z in zones if z["side"] == "SELL" and z.get("qualified") == 1]
        
        buy_zones.sort(key=lambda x: x["ob_high"], reverse=True)
        sell_zones.sort(key=lambda x: x["ob_low"])
        
        target_zones = []
        if len(buy_zones) >= 2:
            target_zones.append(buy_zones[1])
        elif buy_zones:
            target_zones.append(buy_zones[0])
            
        if len(sell_zones) >= 2:
            target_zones.append(sell_zones[1])
        elif sell_zones:
            target_zones.append(sell_zones[0])
            
        for z in target_zones:
            side = z["side"]
            entry_p = z["ob_high"] if side == "BUY" else z["ob_low"]
            qual_time = z.get("qualified_time", 0)
            
            entry_idx = -1
            for i, c in enumerate(candles):
                if c["time"] >= qual_time:
                    if side == "BUY" and c["low"] <= entry_p:
                        entry_idx = i
                        break
                    elif side == "SELL" and c["high"] >= entry_p:
                        entry_idx = i
                        break
                        
            if entry_idx == -1 or entry_idx >= len(candles) - 1:
                continue
                
            # Outcome check (+1.5% TP vs +0.8% BE)
            tp_target = entry_p * (1.015 if side == "BUY" else 0.985)
            be_target = entry_p * (1.008 if side == "BUY" else 0.992)
            soft_sl = entry_p * (0.975 if side == "BUY" else 1.025)
            
            outcome = None
            be_active = False
            for k in range(entry_idx, len(candles)):
                c = candles[k]
                if not be_active:
                    if (side == "BUY" and c["high"] >= be_target) or (side == "SELL" and c["low"] <= be_target):
                        be_active = True
                if (side == "BUY" and c["high"] >= tp_target) or (side == "SELL" and c["low"] <= tp_target):
                    outcome = "WIN"
                    break
                if be_active:
                    if (side == "BUY" and c["low"] <= entry_p) or (side == "SELL" and c["high"] >= entry_p):
                        outcome = "BREAKEVEN"
                        break
                if (side == "BUY" and c["close"] <= soft_sl) or (side == "SELL" and c["close"] >= soft_sl):
                    outcome = "LOSS"
                    break
                    
            if not outcome:
                continue
                
            is_win = (outcome == "WIN")
            
            # Feature 1: Liquidity Sweep
            tags = z.get("tags", [])
            has_sweep = "SWEEP" in tags
            if has_sweep:
                sweep_total += 1
                if is_win: sweep_wins += 1
            else:
                no_sweep_total += 1
                if is_win: no_sweep_wins += 1
                
            # Feature 2: FVG Presence
            has_fvg = "FVG" in tags
            if has_fvg:
                fvg_total += 1
                if is_win: fvg_wins += 1
            else:
                no_fvg_total += 1
                if is_win: no_fvg_wins += 1
                
            # Feature 3: Trend Alignment (EMA 50 / 200)
            candles_prior = candles[:entry_idx]
            closes = [c["close"] for c in candles_prior]
            if len(closes) >= 50:
                e50 = np.mean(closes[-50:])
                is_aligned = (closes[-1] > e50 and side == "BUY") or (closes[-1] < e50 and side == "SELL")
                if is_aligned:
                    trend_aligned_total += 1
                    if is_win: trend_aligned_wins += 1
                else:
                    counter_trend_total += 1
                    if is_win: counter_trend_wins += 1
                    
    print("\n--- PATTERN 1: LIQUIDITY SWEEP (TURTLE SOUP) ---")
    if sweep_total > 0:
        print(f"With Sweep:    {sweep_wins}/{sweep_total} ({sweep_wins/sweep_total*100:.1f}% Direct TP Win Rate)")
    if no_sweep_total > 0:
        print(f"Without Sweep: {no_sweep_wins}/{no_sweep_total} ({no_sweep_wins/no_sweep_total*100:.1f}% Direct TP Win Rate)")
        
    print("\n--- PATTERN 2: FAIR VALUE GAP (FVG IMBALANCE) ---")
    if fvg_total > 0:
        print(f"With FVG:      {fvg_wins}/{fvg_total} ({fvg_wins/fvg_total*100:.1f}% Direct TP Win Rate)")
    if no_fvg_total > 0:
        print(f"Without FVG:   {no_fvg_wins}/{no_fvg_total} ({no_fvg_wins/no_fvg_total*100:.1f}% Direct TP Win Rate)")
        
    print("\n--- PATTERN 3: 50-EMA TREND ALIGNMENT (PRO-TREND) ---")
    if trend_aligned_total > 0:
        print(f"Pro-Trend:     {trend_aligned_wins}/{trend_aligned_total} ({trend_aligned_wins/trend_aligned_total*100:.1f}% Direct TP Win Rate)")
    if counter_trend_total > 0:
        print(f"Counter-Trend: {counter_trend_wins}/{counter_trend_total} ({counter_trend_wins/counter_trend_total*100:.1f}% Direct TP Win Rate)")
        
    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(analyze_patterns())
