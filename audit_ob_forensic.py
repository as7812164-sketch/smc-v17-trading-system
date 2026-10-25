import asyncio
import json
import time
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17, filter_active_zones

async def audit_obs():
    symbols = ['AAVEUSDT', 'ZECUSDT', 'SUIUSDT', 'LINKUSDT']
    for sym in symbols:
        print("=" * 80)
        print(f"FORENSIC AUDIT OF ORDER BLOCKS FOR: {sym}")
        print("=" * 80)
        
        # 4H Audit
        candles_4h = await binance_feed.fetch_klines(sym, interval="4h", limit=100)
        print(f"Fetched {len(candles_4h)} 4H candles from Binance for {sym}.")
        zones_4h = analyze_candles_smc_v17(sym, candles_4h)
        buy_4h = [z for z in zones_4h if z["side"] == "BUY"]
        filt_4h = filter_active_zones(buy_4h)
        print(f"4H Buy Zones Detected: {len(buy_4h)}, Kept Active: {len(filt_4h)}")
        
        for idx, z in enumerate(filt_4h):
            orig_dt = datetime.fromtimestamp(z["origin_time"] / 1000).strftime("%Y-%m-%d %H:%M:%S UTC")
            disp_dt = datetime.fromtimestamp(z["displacement_time"] / 1000).strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"  [4H Zone #{idx+1}]")
            print(f"    Origin Candle Time: {orig_dt} (Epoch: {z['origin_time']})")
            print(f"    Origin OHLC: Open={z['origin_open']}, High={z['origin_high']}, Low={z['origin_low']}, Close={z['origin_close']}")
            print(f"    Displacement Time: {disp_dt}")
            print(f"    OB High (Locked Entry): {z['entry_price']}")
            print(f"    OB Low (Zone Floor): {z['ob_low']}")
            print(f"    Status: {z['status']}, 2nd OB: {z.get('is_second_ob')}, Mode: {z.get('engine_mode')}")
            print(f"    TP Price: {z['tp_price']}, SL Price: {z['sl_price']}")
            
            # Match directly with the candle in candles_4h
            matched_candle = next((c for c in candles_4h if c["time"] == z["origin_time"]), None)
            if matched_candle:
                print(f"    MATCH IN RAW CANDLES: High={matched_candle['high']}, Low={matched_candle['low']}, Close={matched_candle['close']}")
                is_exact = (matched_candle['high'] == z['origin_high'] and matched_candle['low'] == z['ob_low'])
                print(f"    EXACT PRICE INTEGRITY CHECK: {'PASS (100% MATCH)' if is_exact else 'FAIL'}")

        # 1H Audit
        candles_1h = await binance_feed.fetch_klines(sym, interval="1h", limit=100)
        print(f"\nFetched {len(candles_1h)} 1H candles from Binance for {sym}.")
        zones_1h = analyze_candles_smc_v17(sym, candles_1h)
        buy_1h = [z for z in zones_1h if z["side"] == "BUY"]
        filt_1h = filter_active_zones(buy_1h)
        print(f"1H Buy Zones Detected: {len(buy_1h)}, Kept Active: {len(filt_1h)}")
        
        for idx, z in enumerate(filt_1h):
            orig_dt = datetime.fromtimestamp(z["origin_time"] / 1000).strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"  [1H Zone #{idx+1}]")
            print(f"    Origin Candle Time: {orig_dt} (Epoch: {z['origin_time']})")
            print(f"    Origin OHLC: Open={z['origin_open']}, High={z['origin_high']}, Low={z['origin_low']}, Close={z['origin_close']}")
            print(f"    OB High (Locked Entry): {z['entry_price']}")
            print(f"    OB Low: {z['ob_low']}")
            print(f"    Status: {z['status']}, 2nd OB: {z.get('is_second_ob')}")
            
            matched_candle = next((c for c in candles_1h if c["time"] == z["origin_time"]), None)
            if matched_candle:
                is_exact = (matched_candle['high'] == z['origin_high'] and matched_candle['low'] == z['ob_low'])
                print(f"    EXACT PRICE INTEGRITY CHECK: {'PASS (100% MATCH)' if is_exact else 'FAIL'}")

    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(audit_obs())
