import asyncio
import sys
from config import DEFAULT_COINS, TIER1_COINS
from feed.binance_feed import binance_feed
from engine.hermes35_live import hermes35_live_engine, TOP_22_CHAMPIONS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def scan_4h():
    coins = list(dict.fromkeys(list(TOP_22_CHAMPIONS) + list(TIER1_COINS) + list(DEFAULT_COINS)))
    tickers = await binance_feed.fetch_all_tickers()
    
    print("=== HERMES 3.5 RADAR HARVEST (4H TIMEFRAME LIVE SCAN) ===")
    matches = []
    for sym in coins:
        cur_p = tickers.get(sym)
        if not cur_p:
            continue
        c_4h = await binance_feed.fetch_klines(sym, interval="4h", limit=80)
        if not c_4h:
            continue
        setups = hermes35_live_engine.detect_apex_setups_on_candles(sym, "4h", c_4h, cur_p)
        for s in setups:
            dist = (cur_p - s["entry_price"]) / s["entry_price"] * 100.0
            matches.append({
                "symbol": sym,
                "side": s["side"],
                "price": cur_p,
                "entry": s["entry_price"],
                "radar": s["radar_price"],
                "dist": dist,
                "status": s["status"],
                "tp": s["tp_price"],
                "armor2": s["armor_stage2_price"],
                "sl": s["soft_sl_price"],
                "low": s["ob_low"],
                "high": s["ob_high"],
                "origin": s.get("is_origin", False)
            })
        
    matches.sort(key=lambda x: (x["status"] == "FRESH_TRIGGERED", x["status"] == "RADAR_PRE_ARMED", -abs(x["dist"])), reverse=True)
    for m in matches[:10]:
        origin_flag = " [ORIGIN BEDROCK]" if m["origin"] else ""
        print(f"\n{m['symbol']} ({m['side']}) | Price: {m['price']} | 5% Entry: {m['entry']} | Radar: {m['radar']} | Dist: {m['dist']:+.2f}% | Status: {m['status']}{origin_flag}")
        print(f"  TP: {m['tp']} | Stage 2 Harvest: {m['armor2']} | SL: {m['sl']} | Zone: [{m['low']} - {m['high']}]")

if __name__ == "__main__":
    asyncio.run(scan_4h())
