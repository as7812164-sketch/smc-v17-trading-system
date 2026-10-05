import asyncio
import json
import urllib.request
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from engine.hermes35_live import hermes35_engine
from feed.binance_feed import binance_feed

async def inspect_atom():
    sym = "ATOMUSDT"
    print("=" * 65)
    print(f"      LIVE STRUCTURAL SMC AUDIT FOR {sym}")
    print("=" * 65)

    # 1. Fetch live ticker price
    tickers = await binance_feed.fetch_all_tickers()
    live_price = tickers.get(sym, 0.0)
    print(f"Live Price on Binance Futures: ${live_price}")

    # 2. Check 4H Timeframe
    print("\n--- 4H MACRO TIMEFRAME SCAN ---")
    klines_4h = await binance_feed.fetch_klines(sym, interval="4h", limit=200)
    if klines_4h:
        btc_sentry = {"long_veto": False, "short_veto": False, "bias": "INDEPENDENT_ASSET_SMC"}
        setups_4h = hermes35_engine.detect_apex_setups_on_candles(sym, klines_4h, "4h", btc_sentry)
        print(f"4H Setups Detected: {len(setups_4h)}")
        for idx, s in enumerate(setups_4h, 1):
            side = s["side"]
            ent = float(s["entry_price"])
            ob_l = float(s["ob_low"])
            ob_h = float(s["ob_high"])
            tp = float(s.get("tp_price", 0.0))
            sl = float(s.get("soft_sl_price", 0.0))
            disp = float(s.get("displacement_pct", 0.0))
            air = float(s.get("runway_void_pct", 0.0))
            dist_pct = abs(live_price - ent) / ent * 100.0

            # Forensic lock check
            is_valid, msg = hermes35_engine.verify_setup_forensic_lock(s, klines_4h)
            
            print(f"\n  [Setup 4H #{idx}] {side} Setup:")
            print(f"    - Base OB Range:  [${ob_l} - ${ob_h}]")
            print(f"    - 5% Entry Price: ${ent}")
            print(f"    - Live Distance:  {dist_pct:.2f}% away (Current: ${live_price})")
            print(f"    - Take Profit:    ${tp} (+14% ROE / +2.80% price move)")
            print(f"    - Stop Loss:      ${sl} (-14% ROE)")
            print(f"    - Displacement:   +{disp:.2f}% (Req >= 5.0%)")
            print(f"    - Airspace Void:  +{air:.2f}% (Req >= 5.0%)")
            print(f"    - Forensic Lock:  {'PASS (CERTIFIED)' if is_valid else 'REJECTED'}")
            print(f"    - Details:        {msg}")
    else:
        print("Failed to fetch 4H klines")

    # 3. Check 1H Timeframe
    print("\n--- 1H INTRADAY TIMEFRAME SCAN ---")
    klines_1h = await binance_feed.fetch_klines(sym, interval="1h", limit=200)
    if klines_1h:
        btc_sentry = {"long_veto": False, "short_veto": False, "bias": "INDEPENDENT_ASSET_SMC"}
        setups_1h = hermes35_engine.detect_apex_setups_on_candles(sym, klines_1h, "1h", btc_sentry)
        print(f"1H Setups Detected: {len(setups_1h)}")
        for idx, s in enumerate(setups_1h, 1):
            side = s["side"]
            ent = float(s["entry_price"])
            ob_l = float(s["ob_low"])
            ob_h = float(s["ob_high"])
            tp = float(s.get("tp_price", 0.0))
            sl = float(s.get("soft_sl_price", 0.0))
            disp = float(s.get("displacement_pct", 0.0))
            air = float(s.get("runway_void_pct", 0.0))
            dist_pct = abs(live_price - ent) / ent * 100.0

            is_valid, msg = hermes35_engine.verify_setup_forensic_lock(s, klines_1h)

            print(f"\n  [Setup 1H #{idx}] {side} Setup:")
            print(f"    - Base OB Range:  [${ob_l} - ${ob_h}]")
            print(f"    - 5% Entry Price: ${ent}")
            print(f"    - Live Distance:  {dist_pct:.2f}% away (Current: ${live_price})")
            print(f"    - Take Profit:    ${tp} (+12% ROE / +2.44% price move)")
            print(f"    - Stop Loss:      ${sl} (-12% ROE)")
            print(f"    - Displacement:   +{disp:.2f}% (Req >= 5.0%)")
            print(f"    - Airspace Void:  +{air:.2f}% (Req >= 5.0%)")
            print(f"    - Forensic Lock:  {'PASS (CERTIFIED)' if is_valid else 'REJECTED'}")
            print(f"    - Details:        {msg}")
    else:
        print("Failed to fetch 1H klines")

    print("\n" + "=" * 65)

if __name__ == "__main__":
    asyncio.run(inspect_atom())
