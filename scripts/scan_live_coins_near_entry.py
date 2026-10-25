import os
import sys
import asyncio
import json
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from config import TOP_22_CHAMPIONS, IST
from engine.hermes35_live import hermes35_live_engine
from feed.binance_feed import binance_feed
hermes35 = hermes35_live_engine

async def main():
    print("=" * 80)
    print(" 📡 SCANNING LIVE BINANCE FUTURES FOR COINS NEAR ENTRY...")
    print(f" Timestamp: {datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')} IST")
    print(f" Universe: {len(TOP_22_CHAMPIONS)} Champions (1H & 4H Timeframes)")
    print("=" * 80)

    # 1. Evaluate BTC macro sentry
    btc_sentry = await hermes35.evaluate_btc_macro_sentry()
    print(f"King BTC Status: {btc_sentry.get('bias', 'NEUTRAL')} | Change: {btc_sentry.get('change_pct', 0.0)}% | Price: ${btc_sentry.get('close_price', 0):,.2f}")
    print(f"Long Veto: {btc_sentry.get('long_veto')} | Short Veto: {btc_sentry.get('short_veto')}")
    print("-" * 80)

    # 2. Scan all champions
    all_setups = []
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            try:
                klines = await binance_feed.fetch_klines(sym, interval=tf, limit=200)
                if klines and len(klines) >= 40:
                    setups = hermes35.detect_apex_setups_on_candles(sym, klines, tf, btc_sentry)
                    cur_p = float(klines[-1]["close"])
                    for s in setups:
                        entry_p = float(s["entry_price"])
                        # Calculate distance %
                        dist_pct = abs(cur_p - entry_p) / cur_p * 100.0
                        
                        # Check position relative to entry
                        if s["side"] == "LONG":
                            status_rel = "APPROACHING (ABOVE ENTRY)" if cur_p > entry_p else "INSIDE / BELOW ENTRY"
                        else:
                            status_rel = "APPROACHING (BELOW ENTRY)" if cur_p < entry_p else "INSIDE / ABOVE ENTRY"

                        all_setups.append({
                            "symbol": sym,
                            "side": s["side"],
                            "interval": tf,
                            "cur_price": cur_p,
                            "entry_price": entry_p,
                            "dist_pct": round(dist_pct, 2),
                            "status": s["status"],
                            "is_fresh": s.get("is_fresh_trigger", False),
                            "tp_price": float(s["tp_price"]),
                            "sl_price": float(s["soft_sl_price"]),
                            "status_rel": status_rel,
                            "disp_pct": s.get("displacement_pct", 0.0),
                            "airspace": s.get("runway_void_pct", 0.0)
                        })
            except Exception as e:
                # print(f"Error scanning {sym} {tf}: {e}")
                pass

    if not all_setups:
        print("No active qualified setups found across the 39 champions right now.")
        return

    # Sort setups by distance to entry (closest first)
    all_setups.sort(key=lambda x: x["dist_pct"])

    print(f"\nFOUND {len(all_setups)} ACTIVE QUALIFIED SETUPS ON LIVE CHARTS:")
    print(f"{'#':<3} | {'Symbol':<12} | {'Side':<5} | {'TF':<3} | {'Current Price':<14} | {'Entry Price':<14} | {'Distance %':<10} | {'Status':<16}")
    print("-" * 88)

    for idx, s in enumerate(all_setups, 1):
        fresh_tag = " [LIVE TRIGGER!]" if s["is_fresh"] else ""
        print(f"{idx:<3} | {s['symbol']:<12} | {s['side']:<5} | {s['interval']:<3} | ${s['cur_price']:<13.5g} | ${s['entry_price']:<13.5g} | {s['dist_pct']:>6.2f} %   | {s['status']}{fresh_tag}")

    # Output detailed cards for Top 5 closest setups
    print("\n" + "=" * 80)
    print(" 🎯 TOP CLOSEST COINS TO ENTRY RIGHT NOW:")
    print("=" * 80)
    for idx, s in enumerate(all_setups[:5], 1):
        print(f"\n[{idx}] {s['symbol']} ({s['interval'].upper()} {s['side']}):")
        print(f"   • Current Live Price:   ${s['cur_price']}")
        print(f"   • Entry Price:          ${s['entry_price']}")
        print(f"   • Distance to Entry:    {s['dist_pct']}% away ({s['status_rel']})")
        print(f"   • Setup Status:         {s['status']}")
        print(f"   • Planned TP Target:    ${s['tp_price']}")
        print(f"   • Planned Stop Loss:    ${s['sl_price']}")
        print(f"   • Origin Displacement:  {s['disp_pct']}% | Rocket Airspace: {s['airspace']}%")

if __name__ == "__main__":
    asyncio.run(main())
