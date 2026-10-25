import asyncio
import sys
from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17, filter_active_zones
from ai.smart_money_analyzer import evaluate_setup_confluence
from config import TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def hunt():
    print("================================================================================")
    print("      MIKE AI AGENT SQUAD: COMPREHENSIVE LIVE SETUP HUNT (1H & 4H)")
    print("================================================================================")
    
    for tf in ["1h", "4h"]:
        print(f"\n========================== [ TIMEFRAME: {tf.upper()} ] ==========================")
        active_candidates = []
        
        # Batch fetch all coins
        all_klines = await binance_feed.fetch_multiple_symbols(TIER1_COINS, interval=tf, limit=200)
        
        for sym, candles in all_klines.items():
            if not candles or len(candles) < 30:
                continue
            
            cur_price = candles[-1]["close"]
            zones = analyze_candles_smc_v17(sym, candles)
            filtered = filter_active_zones(zones)
            
            # Separate into BUY and SELL zones to evaluate 3-OB Sandwich Pattern
            buy_zones = [z for z in filtered if z["side"] == "BUY" and z["status"] in ("QUALIFIED", "ACTIVE")]
            sell_zones = [z for z in filtered if z["side"] == "SELL" and z["status"] in ("QUALIFIED", "ACTIVE")]
            buy_zones.sort(key=lambda x: x["ob_high"], reverse=True)
            sell_zones.sort(key=lambda x: x["ob_low"])
            
            # Strict Rule: Exactly/At least 3 OBs must be present, and trade ONLY on the 2nd (Middle) OB
            target_zones = []
            if len(buy_zones) >= 3:
                # buy_zones[0] = Top OB, buy_zones[1] = Middle (2nd OB), buy_zones[2] = Bottom OB
                target_zones.append((buy_zones[1], "⭐ 2nd OB (Middle)", len(buy_zones), "BUY"))
            elif len(buy_zones) > 0:
                # Note presence of incomplete setups (1 or 2 OBs)
                pass

            if len(sell_zones) >= 3:
                # sell_zones[0] = Bottom OB, sell_zones[1] = Middle (2nd OB), sell_zones[2] = Top OB
                target_zones.append((sell_zones[1], "⭐ 2nd OB (Middle)", len(sell_zones), "SELL"))
            elif len(sell_zones) > 0:
                pass
            
            for z, ob_label, total_obs, side in target_zones:
                ob_high = z["ob_high"]
                ob_low = z["ob_low"]
                status = z["status"]
                
                # Entry price is strictly the outer boundary of the Middle 2nd OB
                entry_p = ob_high if side == "BUY" else ob_low
                if side == "BUY":
                    dist_pct = ((cur_price - entry_p) / cur_price) * 100
                else:
                    dist_pct = ((entry_p - cur_price) / cur_price) * 100
                    
                conf = evaluate_setup_confluence(sym, z, candles)
                score = conf.get("mike_score", conf.get("score", 75))
                
                active_candidates.append({
                    "symbol": sym,
                    "timeframe": tf,
                    "ob_label": ob_label,
                    "side": side,
                    "status": status,
                    "ob_high": ob_high,
                    "ob_low": ob_low,
                    "entry_p": entry_p,
                    "price": cur_price,
                    "dist_pct": dist_pct,
                    "score": score,
                    "tags": z.get("tags", [])
                })
                
        active_candidates.sort(key=lambda x: abs(x["dist_pct"]))
        
        print(f"Discovered {len(active_candidates)} active structural zones on {tf.upper()}.\n")
        print(f"{'Symbol':<12} | {'Priority':<8} | {'Side':<4} | {'Price':<10} | {'2nd OB Entry':<12} | {'OB Range':<22} | {'Dist %':<8} | {'Score'}")
        print("-" * 105)
        for c in active_candidates[:10]:
            ob_range = f"{c['ob_low']:.4f} - {c['ob_high']:.4f}"
            print(f"{c['symbol']:<12} | {c['ob_label']:<8} | {c['side']:<4} | {c['price']:<10.4f} | {c['entry_p']:<12.4f} | {ob_range:<22} | {c['dist_pct']:+6.2f}% | {c['score']:3d}/100")
            
    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(hunt())
