import asyncio
import aiohttp
import sys
from config import DEFAULT_COINS, TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RENDER_BASE = "https://smc-ai-agent.onrender.com"

async def scan_all_coins_exact_render():
    coins = list(dict.fromkeys(TIER1_COINS + DEFAULT_COINS))
    
    print("================================================================================")
    print("  EXACT LIVE CHART SCREEN 2ND OB (BICH WALA OB) ANALYSIS - ALL COINS (1H & 4H)")
    print("================================================================================")
    
    async with aiohttp.ClientSession() as session:
        for tf in ["1h", "4h"]:
            tf_key = tf.upper()
            tp_mult = 1.0150 if tf == "1h" else 1.0204     # 1H: +7.5% ROE | 4H: +10.2% ROE
            sl_mult = 0.9800 if tf == "1h" else 0.9750     # 1H: -10.0% ROE | 4H: -12.5% ROE
            
            print(f"\n========================== [ TIMEFRAME: {tf_key} ] ==========================")
            
            results = []
            
            for sym in coins:
                url = f"{RENDER_BASE}/api/klines?symbol={sym}&interval={tf}&limit=500"
                try:
                    async with session.get(url, timeout=12) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        cur_p = data.get("current_price", 0.0)
                        zones = data.get("zones", [])
                        
                        # Filter BUY qualified/active zones in exact order returned
                        buy_zones = [z for z in zones if z.get("side") == "BUY" and z.get("status") in ("QUALIFIED", "ACTIVE")]
                        
                        # When 3 OBs exist on chart:
                        # Index 0 = Top OB (Freshest)
                        # Index 1 = Middle OB (Bich wala 2nd OB ⭐)
                        # Index 2 = Bottom OB (Base)
                        if len(buy_zones) >= 2:
                            mid_ob = buy_zones[1] # Exact Middle 2nd OB
                            entry_p = mid_ob["ob_high"]
                            low_p = mid_ob["ob_low"]
                            tp_p = entry_p * tp_mult
                            sl_p = entry_p * sl_mult
                            dist_pct = ((cur_p - entry_p) / cur_p) * 100 if cur_p > 0 else 0.0
                            prob = mid_ob.get("prob_score", 85)
                            
                            top_entry = buy_zones[0]["ob_high"]
                            bot_entry = buy_zones[2]["ob_high"] if len(buy_zones) >= 3 else None
                            
                            results.append({
                                "symbol": sym,
                                "cur_p": cur_p,
                                "top_ob": top_entry,
                                "mid_ob_range": f"{low_p:.6f} - {entry_p:.6f}",
                                "mid_entry": entry_p,
                                "bot_ob": bot_entry,
                                "tp_p": tp_p,
                                "sl_p": sl_p,
                                "dist_pct": dist_pct,
                                "prob": prob,
                                "total_obs": len(buy_zones)
                            })
                except Exception:
                    pass
                    
            results.sort(key=lambda x: abs(x["dist_pct"]))
            
            print(f"{'Symbol':<10} | {'Cur Price':<10} | {'Top OB (1st)':<14} | {'⭐ Bich Wala 2nd OB':<22} | {'TP (+ROE)':<12} | {'SL (-ROE)':<12} | {'Dist %':<8} | {'Prob'}")
            print("-" * 125)
            for r in results:
                tp_str = f"{r['tp_p']:.5f}" if r['tp_p'] < 10 else f"{r['tp_p']:.2f}"
                sl_str = f"{r['sl_p']:.5f}" if r['sl_p'] < 10 else f"{r['sl_p']:.2f}"
                cur_str = f"{r['cur_p']:.5f}" if r['cur_p'] < 10 else f"{r['cur_p']:.2f}"
                top_str = f"{r['top_ob']:.5f}" if r['top_ob'] < 10 else f"{r['top_ob']:.2f}"
                mid_str = f"{r['mid_entry']:.5f}" if r['mid_entry'] < 10 else f"{r['mid_entry']:.2f}"
                
                print(f"{r['symbol']:<10} | {cur_str:<10} | {top_str:<14} | {mid_str:<10} ({r['mid_ob_range']}) | {tp_str:<12} | {sl_str:<12} | {r['dist_pct']:+6.2f}% | 🚀 {r['prob']}%")

if __name__ == "__main__":
    asyncio.run(scan_all_coins_exact_render())
