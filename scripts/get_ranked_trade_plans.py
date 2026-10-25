import sys
import asyncio
import json
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from engine.hermes35_live import hermes35_engine
from feed.binance_feed import binance_feed

async def generate_trade_plans():
    # 1. Fetch live tickers
    tickers = await binance_feed.fetch_all_tickers()

    # 2. Run full scan
    await hermes35_engine.run_full_champion_scan()
    setups = hermes35_engine.detected_setups

    plans = []
    for s in setups:
        sym = s["symbol"]
        cur_p = tickers.get(sym, 0.0)
        if not cur_p:
            continue

        tf = s.get("interval", "4h")
        side = s.get("side", "LONG")
        ent_p = float(s["entry_price"])
        ob_h = float(s["ob_high"])
        ob_l = float(s["ob_low"])
        tp_p = float(s.get("tp_price", 0.0))
        sl_p = float(s.get("soft_sl_price", 0.0))
        disp = float(s.get("displacement_pct", 5.0))
        airspace = float(s.get("runway_void_pct", 5.0))

        # Proximity percentage
        dist_pct = abs(cur_p - ent_p) / ent_p * 100.0
        
        # Check if approaching direction is correct
        # For LONG: cur_p > ent_p means price is coming down towards OB
        # For SHORT: cur_p < ent_p means price is coming up towards OB
        is_favorable_direction = (side == "LONG" and cur_p >= ent_p) or (side == "SHORT" and cur_p <= ent_p)

        radar_active = dist_pct <= 0.20

        plans.append({
            "symbol": sym,
            "tf": tf.upper(),
            "side": side,
            "cur_price": cur_p,
            "entry_price": ent_p,
            "ob_low": ob_l,
            "ob_high": ob_h,
            "dist_pct": dist_pct,
            "direction": "RETRACTING" if is_favorable_direction else "PENETRATED",
            "radar_active": radar_active,
            "tp_price": tp_p,
            "sl_price": sl_p,
            "displacement": disp,
            "airspace": airspace,
            "setup_obj": s
        })

    # Sort plans: closest distance first
    plans.sort(key=lambda x: x["dist_pct"])

    print("RANKED_PLANS_JSON_START")
    # Output top 15 closest setups with forensic lock check
    top_plans = plans[:15]
    results = []
    for p in top_plans:
        # Verify with live klines
        sym = p["symbol"]
        tf = p["tf"].lower()
        try:
            klines = await binance_feed.fetch_klines(sym, interval=tf, limit=200)
            is_valid, forensic_msg = hermes35_engine.verify_setup_forensic_lock(p["setup_obj"], klines)
        except Exception as e:
            is_valid = False
            forensic_msg = str(e)

        p_copy = {k: v for k, v in p.items() if k != "setup_obj"}
        p_copy["forensic_valid"] = is_valid
        p_copy["forensic_msg"] = forensic_msg
        results.append(p_copy)

    print(json.dumps(results, indent=2))
    print("RANKED_PLANS_JSON_END")

if __name__ == "__main__":
    asyncio.run(generate_trade_plans())
