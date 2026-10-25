import asyncio
import sys
import json
from config import DEFAULT_COINS, TIER1_COINS
from feed.binance_feed import binance_feed
from engine.hermes35_live import hermes35_live_engine, TOP_22_CHAMPIONS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def scan_live_market():
    coins = list(dict.fromkeys(list(TOP_22_CHAMPIONS) + list(TIER1_COINS) + list(DEFAULT_COINS)))
    print(f"Scanning {len(coins)} coins across Binance live market (Hermes 3.5 Radar Harvest)...")
    tickers = await binance_feed.fetch_all_tickers()
    
    results = []
    for sym in coins:
        cur_price = tickers.get(sym)
        if not cur_price:
            continue
            
        for tf in ["4h", "1h"]:
            c = await binance_feed.fetch_klines(sym, interval=tf, limit=80)
            if not c or len(c) < 30:
                continue
                
            setups = hermes35_live_engine.detect_apex_setups_on_candles(sym, tf, c, cur_price)
            for s in setups:
                eff_entry = s["entry_price"]
                dist = (cur_price - eff_entry) / eff_entry * 100.0
                results.append({
                    "symbol": sym,
                    "tf": tf.upper(),
                    "side": s["side"],
                    "cur_price": cur_price,
                    "entry_price": eff_entry,
                    "radar_price": s["radar_price"],
                    "dist": dist,
                    "status": s["status"],
                    "tp_price": s["tp_price"],
                    "armor2": s["armor_stage2_price"],
                    "sl_price": s["soft_sl_price"],
                    "is_origin": s.get("is_origin", False)
                })
        
    results.sort(key=lambda x: (x["status"] == "FRESH_TRIGGERED", x["status"] == "RADAR_PRE_ARMED", -abs(x["dist"])), reverse=True)
    
    print("\n" + "=" * 90)
    print("        HERMES 3.5 SINGLE TIER RADAR HARVEST - LIVE MARKET RADAR")
    print("=" * 90)
    for idx, r in enumerate(results[:10], 1):
        origin_str = " [ORIGIN BEDROCK]" if r["is_origin"] else ""
        print(f"\n#{idx}. [{r['symbol']} - {r['tf']} {r['side']}] | Live: ${r['cur_price']} | 5% Entry: ${r['entry_price']:.4f} | Radar: ${r['radar_price']:.4f} | Dist: {r['dist']:+.2f}% | Status: {r['status']}{origin_str}")
        print(f"    • Targets: TP ${r['tp_price']:.4f} | Stage 2 Harvest ${r['armor2']:.4f} | Soft SL ${r['sl_price']:.4f}")

if __name__ == "__main__":
    asyncio.run(scan_live_market())
