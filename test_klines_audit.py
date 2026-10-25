import asyncio
import sys
import os
import json

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import get_klines_with_analysis
from feed.binance_feed import binance_feed

async def run():
    print("=" * 70)
    print("AUDIT EXECUTION: /api/klines?symbol=XRPUSDT&interval=1h")
    print("=" * 70)

    res = await get_klines_with_analysis(symbol="XRPUSDT", interval="1h", limit=500)
    candles = res.get("candles", [])
    zones = res.get("zones", [])
    indicator_status = res.get("indicator_status", {})

    print(f"1. Symbol: {res.get('symbol')}")
    print(f"2. Timeframe: {res.get('timeframe')}")
    print(f"3. Current Price: {res.get('current_price')}")
    print(f"4. Candlesticks Count: {len(candles)}")
    assert len(candles) > 0, "Error: No candles returned!"
    print(f"   Latest Candle Time: {candles[-1]['time']} | Close: {candles[-1]['close']}")

    print(f"\n5. Detected Zones Count: {len(zones)}")
    assert len(zones) > 0, "Error: No zones returned for XRPUSDT 1h!"

    # Verify 100% Mathematical Alignment with HERMES_3_5_SINGLE_TIER_OFFICIAL.pine
    all_math_valid = True
    for idx, z in enumerate(zones):
        print(f"\n--- ZONE #{idx+1} ({z['side']}) ---")
        side = z["side"]
        ob_h = z["ob_high"]
        ob_l = z["ob_low"]
        o_rng = ob_h - ob_l
        ent_p = z["entry_price"]
        rad_p = z["radar_price"]
        be_p = z["armor_stage1_price"]
        trig_p = z["armor_stage2_price"]
        lock_p = z["harvest_lock_price"]
        tp_p = z["tp_price"]
        sl_p = z["sl_price"]

        if side == "BUY":
            exp_ent = round(ob_h - (o_rng * 0.05), 8)
            exp_rad = round(ent_p * 1.0020, 8)
            exp_be = round(ent_p * (1.0 + 0.0160), 8)
            exp_trig = round(ent_p * (1.0 + 0.0180), 8)
            exp_lock = round(ent_p * (1.0 + 0.0090), 8)
            exp_tp = round(ent_p * (1.0 + 0.0280), 8)
            exp_sl = round(ent_p * (1.0 - 0.0280), 8)
        else:
            exp_ent = round(ob_l + (o_rng * 0.05), 8)
            exp_rad = round(ent_p * 0.9980, 8)
            exp_be = round(ent_p * (1.0 - 0.0160), 8)
            exp_trig = round(ent_p * (1.0 - 0.0180), 8)
            exp_lock = round(ent_p * (1.0 - 0.0090), 8)
            exp_tp = round(ent_p * (1.0 - 0.0280), 8)
            exp_sl = round(ent_p * (1.0 + 0.0280), 8)

        checks = [
            ("5% Boundary Entry", ent_p, exp_ent),
            ("0.20% Radar Price", rad_p, exp_rad),
            ("+8.0% ROE BE Armor", be_p, exp_be),
            ("+9.0% ROE Harvest Trigger", trig_p, exp_trig),
            ("+4.5% ROE Harvest Lock", lock_p, exp_lock),
            ("+14.0% ROE Take Profit", tp_p, exp_tp),
            ("Dynamic SL (-14.0% ROE)", sl_p, exp_sl)
        ]

        for label, actual, expected in checks:
            match = abs(actual - expected) < 1e-6
            status = "PASS" if match else "FAIL"
            print(f"  [{status}] {label}: actual={actual} | expected={expected}")
            if not match:
                all_math_valid = False

        print(f"  Zone Status: {z['status']}")
        print(f"  Strategy: {z['strategy']}")
        print(f"  Tier Type: {z['tier_type']}")
        print(f"  Rank Label: {z['rank_label']}")

    assert all_math_valid, "Math verification failed!"
    print("\n6. Indicator Status Verification:")
    print(json.dumps(indicator_status, indent=2))
    assert indicator_status.get("strategy") == "HERMES 3.5 SINGLE TIER RADAR HARVEST"
    assert "5% Boundary" in indicator_status.get("entry_method", "")
    assert "+14.00% ROE" in indicator_status.get("target_roe", "")

    print("\n" + "=" * 70)
    print("ALL AUDIT VERIFICATIONS PASSED 100% SUCCESSFULLY!")
    print("=" * 70)

    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(run())
