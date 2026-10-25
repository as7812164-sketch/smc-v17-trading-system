import asyncio
import time
import sys
from typing import List, Dict, Any
from feed.binance_feed import binance_feed
from engine.smc_v17 import calculate_avg_body, find_true_origin
from config import DEFAULT_COINS, TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def run_fine_tuning():
    coins = list(dict.fromkeys(TIER1_COINS + DEFAULT_COINS))
    
    print("================================================================================")
    print("      SMC V17 STRATEGY MULTI-PARAMETER FINE-TUNING & OPTIMIZATION MATRIX")
    print("================================================================================")
    
    all_klines_1h = await binance_feed.fetch_multiple_symbols(coins, interval="1h", limit=1000)
    all_klines_4h = await binance_feed.fetch_multiple_symbols(coins, interval="4h", limit=1000)
    
    # We will test 5 distinct Fine-Tuning configurations:
    # 1. Base Setup (Current)
    # 2. Base + Strict FVG Imbalance Filter
    # 3. Base + 50 EMA Macro Trend Filter
    # 4. Base + Strong Displacement (1.6x) + Sweep
    # 5. Elite Combo (FVG + Sweep + Trend + Dynamic BE Lock)
    
    tuning_configs = [
        {"name": "1. Base Setup (Current)", "disp_mult": 1.4, "require_fvg": False, "require_ema": False, "be_ratio": 0.50},
        {"name": "2. + Strict FVG Imbalance", "disp_mult": 1.4, "require_fvg": True, "require_ema": False, "be_ratio": 0.50},
        {"name": "3. + 50 EMA Trend Filter", "disp_mult": 1.4, "require_fvg": False, "require_ema": True, "be_ratio": 0.50},
        {"name": "4. + Strong Imbalance (1.6x)", "disp_mult": 1.6, "require_fvg": False, "require_ema": False, "be_ratio": 0.50},
        {"name": "5. 👑 ELITE MASTER COMBO (Sweep+FVG+Trend+Opt BE)", "disp_mult": 1.5, "require_fvg": True, "require_ema": True, "be_ratio": 0.45}
    ]
    
    for tf_name, klines_dict, tp_pct, sl_pct, qual_pct in [
        ("1H Timeframe (Binance 5x | TP: +7.50% ROE)", all_klines_1h, 0.0150, 0.0200, 0.025),
        ("4H Timeframe (Bitget 5x | TP: +10.20% ROE)", all_klines_4h, 0.0204, 0.0250, 0.040)
    ]:
        print(f"\n================================================================================")
        print(f"               OPTIMIZATION RESULTS: [{tf_name}]")
        print(f"================================================================================")
        print(f"{'Configuration':<42} | {'Win %':<8} | {'BE %':<8} | {'Loss %':<8} | {'🛡️ Safety':<10} | {'Final Balance ($50)':<20} | {'Max DD'}")
        print("-" * 125)
        
        for cfg in tuning_configs:
            completed_trades = []
            be_trig_pct = tp_pct * cfg["be_ratio"]
            
            for sym, candles in klines_dict.items():
                if not candles or len(candles) < 60:
                    continue
                n = len(candles)
                active_zones = []
                
                for cur_idx in range(20, n):
                    c = candles[cur_idx]
                    avg_b = calculate_avg_body(candles, cur_idx, 10)
                    
                    if avg_b > 0:
                        c_body = abs(c["close"] - c["open"])
                        if c["close"] > c["open"] and c_body >= cfg["disp_mult"] * avg_b:
                            o_idx = find_true_origin(candles, cur_idx, "BUY")
                            if o_idx is not None:
                                o_c = candles[o_idx]
                                ob_h = o_c["high"]
                                ob_l = o_c["low"]
                                target_q = ob_h * (1.0 + qual_pct)
                                
                                # Check Sweep
                                has_sweep = False
                                if o_idx >= 3:
                                    prev_lows = [candles[k]["low"] for k in range(max(0, o_idx - 12), o_idx)]
                                    if prev_lows and ob_l <= min(prev_lows) * 1.001:
                                        has_sweep = True
                                        
                                # Check FVG Imbalance
                                has_fvg = False
                                if cur_idx + 1 < n and o_idx + 2 <= cur_idx:
                                    # Gap between origin high and candle 2 low
                                    if candles[min(n-1, o_idx + 2)]["low"] > ob_h:
                                        has_fvg = True
                                        
                                # Check EMA trend
                                ema_ok = True
                                if cfg["require_ema"] and cur_idx >= 50:
                                    sma50 = sum(candles[k]["close"] for k in range(cur_idx - 50, cur_idx)) / 50.0
                                    ema_ok = c["close"] > sma50
                                    
                                if cfg["require_fvg"] and not has_fvg:
                                    continue
                                if cfg["require_ema"] and not ema_ok:
                                    continue
                                    
                                if not any(z["origin_time"] == o_c["time"] and z["side"] == "BUY" for z in active_zones):
                                    active_zones.append({
                                        "symbol": sym, "side": "BUY", "origin_time": o_c["time"],
                                        "ob_high": ob_h, "ob_low": ob_l, "target_qual": target_q,
                                        "has_sweep": has_sweep, "status": "PENDING",
                                        "entry_price": None, "entry_time": None, "be_activated": False
                                    })
                                    
                    for z in list(active_zones):
                        if z["status"] == "PENDING":
                            if c["low"] <= z["ob_low"]:
                                z["status"] = "INVALIDATED"
                            elif c["high"] >= z["target_qual"]:
                                z["status"] = "QUALIFIED"
                        elif z["status"] == "QUALIFIED":
                            # Rank BUY zones by ob_high descending (Top #1, Middle #2, Bottom #3)
                            side_zones = [sz for sz in active_zones if sz["side"] == "BUY" and sz["status"] in ("QUALIFIED", "ACTIVE")]
                            side_zones.sort(key=lambda x: x["ob_high"], reverse=True)
                            
                            is_middle_2nd_ob = (len(side_zones) >= 2 and z["origin_time"] == side_zones[1]["origin_time"])
                            
                            if c["low"] <= z["ob_high"]:
                                if is_middle_2nd_ob:
                                    z["status"] = "ACTIVE"
                                    z["entry_price"] = z["ob_high"]
                                    z["entry_time"] = c["time"]
                                    z["tp_price"] = z["entry_price"] * (1.0 + tp_pct)
                                    z["sl_price"] = z["entry_price"] * (1.0 - sl_pct)
                                    z["be_trigger"] = z["entry_price"] * (1.0 + be_trig_pct)
                                else:
                                    z["status"] = "MITIGATED"
                        elif z["status"] == "ACTIVE":
                            ep = z["entry_price"]
                            tp = z["tp_price"]
                            sl = z["sl_price"]
                            be_p = z["be_trigger"]
                            
                            if not z["be_activated"] and c["high"] >= be_p:
                                z["be_activated"] = True
                                
                            if c["high"] >= tp:
                                z["status"] = "TP_HIT"
                                completed_trades.append({"time": c["time"], "result": "WIN", "pnl": tp_pct * 5.0})
                            elif c["low"] <= (ep if z["be_activated"] else sl):
                                if z["be_activated"]:
                                    z["status"] = "BE_HIT"
                                    completed_trades.append({"time": c["time"], "result": "BE", "pnl": 0.0})
                                else:
                                    z["status"] = "SL_HIT"
                                    completed_trades.append({"time": c["time"], "result": "LOSS", "pnl": -sl_pct * 5.0})
                                    
                    active_zones = [z for z in active_zones if z["status"] in ("PENDING", "QUALIFIED", "ACTIVE")]

            completed_trades.sort(key=lambda x: x["time"])
            target_100 = completed_trades[:100]
            cnt = len(target_100)
            
            w = len([t for t in target_100 if t["result"] == "WIN"])
            b = len([t for t in target_100 if t["result"] == "BE"])
            l = len([t for t in target_100 if t["result"] == "LOSS"])
            
            w_rate = (w / cnt * 100) if cnt else 0
            b_rate = (b / cnt * 100) if cnt else 0
            l_rate = (l / cnt * 100) if cnt else 0
            safety = ((w + b) / cnt * 100) if cnt else 0
            
            bal = 50.0
            peak = bal
            mdd = 0.0
            for t in target_100:
                bal += bal * t["pnl"]
                if bal > peak:
                    peak = bal
                dd = (peak - bal) / peak * 100
                if dd > mdd:
                    mdd = dd
                    
            print(f"{cfg['name']:<42} | {w_rate:>5.1f}% | {b_rate:>5.1f}% | {l_rate:>5.1f}% | {safety:>7.1f}% | ${bal:>18,.2f} | {mdd:>5.1f}%")
            
    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(run_fine_tuning())
