import asyncio
import sys
from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17, calculate_avg_body, find_true_origin

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def debug_coin(symbol="UNIUSDT"):
    print(f"================================================================================")
    print(f"      DEBUGGING EXACT ORDER BLOCK BOUNDARIES FOR {symbol}")
    print(f"================================================================================")
    
    for tf in ["1h", "4h"]:
        print(f"\n--- [ Timeframe: {tf.upper()} ] ---")
        candles = await binance_feed.fetch_klines(symbol, interval=tf, limit=200, force_fresh=True)
        if not candles:
            print("No candles fetched.")
            continue
            
        print(f"Latest Close: {candles[-1]['close']}")
        
        # Check if any candle has high or low near 8.6545
        target_matches = []
        for i, c in enumerate(candles):
            if abs(c["high"] - 8.6545) < 0.05 or abs(c["low"] - 8.6545) < 0.05 or abs(c["open"] - 8.6545) < 0.05 or abs(c["close"] - 8.6545) < 0.05:
                target_matches.append((i, c))
                
        print(f"\nCandles near 8.6545:")
        for idx, c in target_matches:
            print(f"  Bar #{idx} ({c['time']}): Open={c['open']}, High={c['high']}, Low={c['low']}, Close={c['close']}")
            
        # Run python detector
        zones = analyze_candles_smc_v17(symbol, candles)
        print(f"\nDetected Zones in Python ({len(zones)}):")
        for z in zones:
            print(f"  {z['side']} | Status: {z['status']} | Origin High: {z['ob_high']} | Origin Low: {z['ob_low']} | Disp Time: {z['displacement_time']}")
            
    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(debug_coin("UNIUSDT"))
