import asyncio
import sys
import json
from config import DEFAULT_COINS, TIER1_COINS
from feed.binance_feed import binance_feed
from engine.hermes35_live import hermes35_live_engine, TOP_22_CHAMPIONS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def select_live_trades():
    coins = list(dict.fromkeys(list(TOP_22_CHAMPIONS) + list(TIER1_COINS) + list(DEFAULT_COINS)))
    tickers = await binance_feed.fetch_all_tickers()
    
    candidates = []
    
    print("\n" + "=" * 90)
    print("   HERMES 3.5 SINGLE TIER RADAR HARVEST - LIVE SCANNER RADAR")
    print("=" * 90)
    
    for sym in coins:
        cur_p = tickers.get(sym)
        if not cur_p:
            continue

        for tf in ["4h", "1h"]:
            try:
                candles = await binance_feed.fetch_klines(sym, interval=tf, limit=80)
                if not candles or len(candles) < 35:
                    continue
                
                setups = hermes35_live_engine.detect_apex_setups_on_candles(sym, tf, candles, cur_p)
                for s in setups:
                    eff_entry = s["entry_price"]
                    radar_p = s["radar_price"]
                    dist_to_entry = (cur_p - eff_entry) / eff_entry * 100.0
                    candidates.append({
                        "symbol": sym,
                        "tf": tf.upper(),
                        "side": s["side"],
                        "price": cur_p,
                        "entry": eff_entry,
                        "radar": radar_p,
                        "ob_low": s["ob_low"],
                        "ob_high": s["ob_high"],
                        "tp": s["tp_price"],
                        "armor_stage1": s["armor_stage1_price"],
                        "armor_stage2": s["armor_stage2_price"],
                        "harvest_lock": s["harvest_lock_price"],
                        "sl": s["soft_sl_price"],
                        "hard_sl": s["hard_sl_price"],
                        "dist_pct": dist_to_entry,
                        "status": s["status"],
                        "runway": s.get("runway_void_pct", 0.0),
                        "disp": s.get("displacement_pct", 0.0),
                        "is_origin": s.get("is_origin", False)
                    })
            except Exception:
                continue

    # Sort candidates by status (FRESH_TRIGGERED / RADAR_PRE_ARMED first, then closest distance)
    candidates.sort(key=lambda x: (
        x["status"] == "FRESH_TRIGGERED",
        x["status"] == "RADAR_PRE_ARMED",
        -abs(x["dist_pct"])
    ), reverse=True)

    if not candidates:
        print("\nNo active Hermes 3.5 setups currently in radar window.")
        return

    for idx, q in enumerate(candidates[:8], 1):
        origin_str = " [ORIGIN BEDROCK]" if q["is_origin"] else ""
        print(f"\n#{idx}. [{q['symbol']} - {q['tf']} {q['side']}] | Live Price: ${q['price']} | Status: {q['status']}{origin_str}")
        print(f"    • 5% Boundary Entry: ${q['entry']:.4f} | 0.20% Radar: ${q['radar']:.4f} | Dist: {q['dist_pct']:+.2f}%")
        print(f"    • Void Airspace: {q['runway']:.1f}% | Displacement: {q['disp']:.1f}%")
        print(f"    • Targets: TP (+14% ROE) ${q['tp']:.4f} | Harvest (+9% -> Lock +4.5%) ${q['armor_stage2']:.4f} | Soft SL ${q['sl']:.4f}")
        print(f"    • OB Zone Span: [${q['ob_low']:.4f} - ${q['ob_high']:.4f}]")

if __name__ == "__main__":
    asyncio.run(select_live_trades())
