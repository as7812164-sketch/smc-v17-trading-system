import asyncio
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from engine.hermes35_live import hermes35_engine
from feed.binance_feed import binance_feed

async def scan_closest():
    print("=" * 70)
    print("  SCANNING LIVE BINANCE FUTURES FOR CLOSEST ENTRY SETUPS RIGHT NOW")
    print("=" * 70)

    tickers = await binance_feed.fetch_all_tickers()
    await hermes35_engine.run_full_champion_scan()
    setups = hermes35_engine.detected_setups

    ranked = []
    for s in setups:
        sym = s["symbol"]
        cur_p = tickers.get(sym, 0.0)
        if not cur_p:
            continue
        ent_p = float(s["entry_price"])
        side = s.get("side", "LONG")
        tf = s.get("interval", "4h").upper()
        ob_l = float(s["ob_low"])
        ob_h = float(s["ob_high"])
        tp_p = float(s.get("tp_price", 0.0))
        sl_p = float(s.get("soft_sl_price", 0.0))
        disp = float(s.get("displacement_pct", 0.0))
        air = float(s.get("runway_void_pct", 0.0))

        dist_pct = abs(cur_p - ent_p) / ent_p * 100.0
        in_radar = dist_pct <= 0.20

        # Is approaching from correct side?
        # For LONG: current price is above entry coming down
        # For SHORT: current price is below entry coming up
        is_approaching = (side == "LONG" and cur_p >= ent_p) or (side == "SHORT" and cur_p <= ent_p)

        ranked.append({
            "symbol": sym,
            "tf": tf,
            "side": side,
            "cur_price": cur_p,
            "entry_price": ent_p,
            "ob_low": ob_l,
            "ob_high": ob_h,
            "dist_pct": dist_pct,
            "in_radar": in_radar,
            "is_approaching": is_approaching,
            "tp_price": tp_p,
            "sl_price": sl_p,
            "disp": disp,
            "air": air,
            "setup_obj": s
        })

    # Sort closest distance first
    ranked.sort(key=lambda x: x["dist_pct"])

    print(f"\nTotal Tracked Setups: {len(ranked)}")
    print("\nTOP 10 CLOSEST COINS TO ENTRY RIGHT NOW:")
    print("-" * 70)

    for idx, r in enumerate(ranked[:10], 1):
        sym = r["symbol"]
        tf_lower = r["tf"].lower()
        try:
            klines = await binance_feed.fetch_klines(sym, interval=tf_lower, limit=150)
            is_valid, msg = hermes35_engine.verify_setup_forensic_lock(r["setup_obj"], klines)
        except Exception as e:
            is_valid, msg = False, str(e)

        lock_badge = "[CERTIFIED PASS]" if is_valid else "[REJECTED]"
        radar_badge = ">>> IN RADAR! <<<" if r["in_radar"] else f"{r['dist_pct']:.2f}% away"
        appr_str = "Retracing towards entry" if r["is_approaching"] else "Past entry boundary"

        print(f"#{idx} | {r['symbol']:<10} {r['tf']} {r['side']:<5} | Dist: {radar_badge:<18} | Live: ${r['cur_price']} -> Entry: ${r['entry_price']}")
        print(f"     OB: [${r['ob_low']} - ${r['ob_high']}] | TP: ${r['tp_price']} | SL: ${r['sl_price']}")
        print(f"     Forensic Lock: {lock_badge} | {msg}")
        print("-" * 70)

if __name__ == "__main__":
    asyncio.run(scan_closest())
