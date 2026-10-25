import asyncio
import sys
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17

IST = timezone(timedelta(hours=5, minutes=30))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def audit_multiple_coins():
    coins = [("ETHUSDT", "4h"), ("SOLUSDT", "4h"), ("UNIUSDT", "1h"), ("ARBUSDT", "1h"), ("DOGEUSDT", "4h")]
    
    print("=========================================================================================")
    print("        COMPREHENSIVE MULTI-COIN ORDER BLOCK AUDIT FOR MANUAL VERIFICATION")
    print("=========================================================================================")
    
    for sym, tf in coins:
        candles = await binance_feed.fetch_klines(sym, interval=tf, limit=300)
        zones = analyze_candles_smc_v17(sym, candles)
        buy_zones = [z for z in zones if z["side"] == "BUY" and z.get("qualified") == 1]
        sell_zones = [z for z in zones if z["side"] == "SELL" and z.get("qualified") == 1]
        
        buy_zones.sort(key=lambda x: x["ob_high"], reverse=True)
        sell_zones.sort(key=lambda x: x["ob_low"])
        
        print(f"\n======================================================================")
        print(f"   COIN: {sym} | TIMEFRAME: {tf.upper()} (Binance Futures USDT-M)")
        print(f"======================================================================")
        
        # Audit top 2 Buy zones
        for i, z in enumerate(buy_zones[:2], 1):
            o_dt = datetime.fromtimestamp(z["origin_time"]/1000, IST).strftime("%d %b %Y, %I:%M %p IST")
            o_utc = datetime.fromtimestamp(z["origin_time"]/1000, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            d_dt = datetime.fromtimestamp(z["displacement_time"]/1000, IST).strftime("%d %b %Y, %I:%M %p IST")
            q_dt = datetime.fromtimestamp(z["qualified_time"]/1000, IST).strftime("%d %b %Y, %I:%M %p IST")
            label = "1st OB (Upper / Shallow Zone)" if i == 1 else "2nd OB (Institutional Target Zone)"
            
            print(f"\n>>> [{label} - BUY] <<<")
            print(f"  📅 1. Origin Red Candle Time:       {o_dt} (UTC: {o_utc})")
            print(f"  📊 2. Origin Candle OHLC Values:")
            print(f"        - Open:  ${z['origin_open']:.4f}")
            print(f"        - High:  ${z['ob_high']:.4f}  <--- [ZONE TOP / EXACT ENTRY PRICE]")
            print(f"        - Low:   ${z['ob_low']:.4f}  <--- [ZONE BOTTOM / STOP LEVEL]")
            print(f"        - Close: ${z['origin_close']:.4f}")
            print(f"  🚀 3. Displacement Candle Time:     {d_dt}")
            print(f"  🎯 4. +7% Qualification Target:     ${z['target_7pct']:.4f}")
            print(f"  ✅ 5. +7% Reached Without Touch at: {q_dt}")
            print(f"  🏷️ 6. Soft Tags Detected:          {z.get('tags', [])}")
            print(f"  📌 7. Current Status:               {z['status']}")

    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(audit_multiple_coins())
