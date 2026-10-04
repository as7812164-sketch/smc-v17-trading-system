"""
SCAN TODAY'S LIVE HERMES 3.5 SETUPS ACROSS TOP CHAMPIONS
=======================================================
Scans live Binance Futures market data across 4H and 1H for:
- Live BTC Macro Sentry status (Bias, EMA50, Vetoes)
- All valid Hermes 3.5 Single Tier order blocks & IDM sweeps
- Distance from current live price to 50% Mean Threshold entry
- Ranking coins with highest probability of executing today
"""

import os
import sys
import asyncio
from datetime import datetime

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from feed.binance_feed import binance_feed
from engine.hermes2_apex_live import hermes2_apex_engine
from config import TOP_22_CHAMPIONS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def scan_market():
    print("=" * 80)
    print("📡 SCANNING LIVE MARKET FOR TODAY'S HERMES 3.5 SETUPS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")
    print("=" * 80)
    
    # 1. Evaluate BTC Macro Sentry
    print("\n🔍 Checking King BTC 4H Macro Sentry...")
    btc_sentry = await hermes2_apex_engine.evaluate_btc_macro_sentry()
    btc_price = btc_sentry.get("close_price", 0.0)
    btc_ema50 = btc_sentry.get("btc_ema50", 0.0)
    btc_bias = btc_sentry.get("bias", "UNKNOWN")
    short_veto = btc_sentry.get("short_veto", False)
    long_veto = btc_sentry.get("long_veto", False)
    
    print(f"  BTC Price: ${btc_price:,.2f}")
    print(f"  BTC 4H EMA50: ${btc_ema50:,.2f}")
    print(f"  BTC Macro Bias: {btc_bias.upper()}")
    print(f"  Altcoin Short Veto: {'ACTIVE (Shorts Strictly Blocked)' if short_veto else 'Inactive'}")
    print(f"  Altcoin Long Veto: {'ACTIVE' if long_veto else 'Inactive (Longs Fully Allowed)'}")
    
    # 2. Scan Coins across 4H & 1H
    print(f"\n🔎 Scanning {len(TOP_22_CHAMPIONS)} Champions across 4H Macro & 1H Intraday...")
    all_setups = []
    
    for sym in TOP_22_CHAMPIONS:
        for tf in ["4h", "1h"]:
            try:
                klines = await binance_feed.fetch_klines(sym, interval=tf, limit=60)
                if not klines or len(klines) < 30:
                    continue
                    
                curr_price = float(klines[-1]["close"])
                setups = hermes2_apex_engine.detect_apex_setups_on_candles(sym, klines, tf, btc_sentry)
                
                for s in setups:
                    entry = float(s.get("entry_price", 0.0))
                    side = s.get("side", "BUY")
                    
                    if entry <= 0: continue
                    
                    # Calculate distance percentage to entry
                    if side in ["BUY", "LONG"]:
                        dist_pct = ((curr_price - entry) / entry) * 100.0
                    else:
                        dist_pct = ((entry - curr_price) / entry) * 100.0
                        
                    s["current_price"] = curr_price
                    s["dist_pct"] = round(dist_pct, 2)
                    s["abs_dist_pct"] = abs(round(dist_pct, 2))
                    s["tf"] = tf
                    all_setups.append(s)
            except Exception as e:
                # print error briefly
                pass
                
    await binance_feed.close()
    
    # Sort by absolute distance to entry (closest first)
    all_setups.sort(key=lambda x: x["abs_dist_pct"])
    
    print("\n" + "=" * 80)
    print(f"🎯 TOTAL QUALIFIED HERMES 3.5 SETUPS FOUND: {len(all_setups)}")
    print("=" * 80)
    
    if not all_setups:
        print("ℹ️ No active qualified setups at this exact moment. All sentries are guarding capital.")
        return
        
    print(f"\n{'SYM':<10} {'TF':<4} {'SIDE':<5} {'CURR PRICE':<12} {'ENTRY (50% MT)':<14} {'DIST %':<10} {'STATUS':<14} {'TP (+2.8%)':<12} {'SL':<12}")
    print("-" * 90)
    
    for s in all_setups[:15]:
        sym = s["symbol"]
        tf = s["tf"].upper()
        side = s["side"]
        curr_p = s["current_price"]
        entry_p = s["entry_price"]
        dist = s["dist_pct"]
        status = s.get("status", "PENDING_TAP")
        tp_p = s.get("tp_price", 0.0)
        sl_p = s.get("sl_price", 0.0)
        
        dist_str = f"{dist:+.2f}%"
        print(f"{sym:<10} {tf:<4} {side:<5} {curr_p:<12.4f} {entry_p:<14.4f} {dist_str:<10} {status:<14} {tp_p:<12.4f} {sl_p:<12.4f}")
        
    print("\n" + "=" * 80)
    print("💡 TOP PICKS NEARING EXECUTION (CLOSEST TO 50% MEAN THRESHOLD):")
    for s in all_setups[:5]:
        sym = s["symbol"]
        side = s["side"]
        tf = s["tf"].upper()
        curr_p = s["current_price"]
        entry_p = s["entry_price"]
        dist = s["dist_pct"]
        reasons = s.get("sentry_reasons", "Standard Hermes 3.5 Sentry confluence")
        
        direction_desc = "above entry (waiting to dip to MT)" if dist > 0 else "below entry (mitigating MT)"
        print(f"\n📌 {sym} ({tf}) - {side}")
        print(f"   • Current Price: ${curr_p:,.4f} | Entry Limit (50% MT): ${entry_p:,.4f}")
        print(f"   • Proximity: {abs(dist):.2f}% {direction_desc}")
        print(f"   • TP: ${s.get('tp_price', 0.0):,.4f} (+2.80% | +14.0% ROE @ 5x)")
        print(f"   • SL: ${s.get('sl_price', 0.0):,.4f} (Dynamic ATR Buffer)")
        print(f"   • Confluence: {reasons[:100]}...")

if __name__ == "__main__":
    asyncio.run(scan_market())
