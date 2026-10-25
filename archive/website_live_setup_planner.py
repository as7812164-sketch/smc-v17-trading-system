import asyncio
import aiohttp
import sys
import json
from config import DEFAULT_COINS, TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

async def scan_website_chart_data():
    print("================================================================================")
    print("      LIVE WEBSITE CHART ACCESS & 2ND OB (MIDDLE) SETUP PLANNER")
    print("================================================================================")
    
    coins_to_scan = list(dict.fromkeys(TIER1_COINS + DEFAULT_COINS))
    
    planned_setups = {"1H": [], "4H": []}
    
    async with aiohttp.ClientSession() as session:
        for tf in ["1h", "4h"]:
            tf_key = tf.upper()
            tp_pct = 0.0150 if tf == "1h" else 0.0204     # 1H: +7.5% ROE | 4H: +10.2% ROE
            sl_pct = 0.0200 if tf == "1h" else 0.0250     # 1H: -10% ROE | 4H: -12.5% ROE
            be_pct = 0.0075 if tf == "1h" else 0.0102     # 1H: +3.75% ROE | 4H: +5.1% ROE
            
            print(f"\n>>> Fetching live website chart feeds for [{tf_key}]...")
            
            for sym in coins_to_scan:
                url = f"{BASE_URL}/api/klines?symbol={sym}&interval={tf}&limit=500"
                try:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        
                        cur_price = data.get("current_price", 0.0)
                        zones = data.get("zones", [])
                        
                        if not zones:
                            continue
                            
                        # Filter BUY unmitigated zones
                        buy_zones = [z for z in zones if z.get("side") == "BUY" and z.get("status") in ("QUALIFIED", "ACTIVE")]
                        # Sort by origin_time descending (Freshest OB #1, Middle 2nd OB #2, Base OB #3) matching TradingView
                        buy_zones.sort(key=lambda x: x["origin_time"], reverse=True)
                        
                        # Strict User Rule: 3-OB structure present, trade ONLY on 2nd (Middle) OB
                        if len(buy_zones) >= 3:
                            fresh_ob = buy_zones[0] # OB #1 (Freshest)
                            mid_ob   = buy_zones[1] # ⭐ OB #2 (2nd OB - Exact Boundary Match!)
                            base_ob  = buy_zones[2] # OB #3 (Base)
                            
                            entry_price = mid_ob["ob_high"]
                            mid_ob_low = mid_ob["ob_low"]
                            
                            tp_price = entry_price * (1.0 + tp_pct)
                            sl_price = entry_price * (1.0 - sl_pct)
                            be_price = entry_price * (1.0 + be_pct)
                            
                            dist_pct = ((cur_price - entry_price) / cur_price) * 100 if cur_price > 0 else 0.0
                            
                            prob_score = mid_ob.get("prob_score", 95)
                            has_sweep = mid_ob.get("has_sweep", False) or "SWEEP" in (mid_ob.get("tags") or [])
                            
                            planned_setups[tf_key].append({
                                "symbol": sym,
                                "timeframe": tf_key,
                                "cur_price": cur_price,
                                "entry_price": entry_price,
                                "mid_ob_range": f"{mid_ob_low:.4f} - {entry_price:.4f}",
                                "top_ob_high": top_ob["ob_high"],
                                "bot_ob_low": bot_ob["ob_low"],
                                "tp_price": tp_price,
                                "sl_price": sl_price,
                                "be_price": be_price,
                                "dist_pct": dist_pct,
                                "score": prob_score,
                                "has_sweep": has_sweep,
                                "status": mid_ob.get("status")
                            })
                except Exception as e:
                    pass
                    
    # Display Planned Setups sorted by distance to entry
    for tf_key, setups in planned_setups.items():
        setups.sort(key=lambda x: abs(x["dist_pct"]))
        
        print(f"\n================================================================================")
        print(f"   🎯 CONFIRMED LIVE SETUPS: [{tf_key}] 3-OB MIDDLE PATTERN (Total: {len(setups)})")
        print(f"================================================================================")
        print(f"{'Symbol':<12} | {'Cur Price':<10} | {'⭐ 2nd OB Entry':<14} | {'TP Price (+ROE)':<16} | {'SL Price (-ROE)':<16} | {'Dist %':<8} | {'Prob Score'}")
        print("-" * 105)
        
        for s in setups[:10]:
            tp_label = f"{s['tp_price']:.4f} (+7.5%)" if tf_key == "1H" else f"{s['tp_price']:.4f} (+10.2%)"
            sl_label = f"{s['sl_price']:.4f} (-10%)" if tf_key == "1H" else f"{s['sl_price']:.4f} (-12.5%)"
            print(f"{s['symbol']:<12} | {s['cur_price']:<10.4f} | {s['entry_price']:<14.4f} | {tp_label:<16} | {sl_label:<16} | {s['dist_pct']:+6.2f}% | 🚀 {s['score']}%")

if __name__ == "__main__":
    asyncio.run(scan_website_chart_data())
