import asyncio
import time
import json
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config import DEFAULT_COINS, TIER1_COINS
from feed.binance_feed import binance_feed
from engine.hermes35_live import hermes35_live_engine, TOP_22_CHAMPIONS

async def scan_live_market_buy_opportunities():
    print("=" * 80)
    print("       HERMES 3.5 RADAR HARVEST - LIVE MARKET SCANNER")
    print("=" * 80)
    print("Connecting to live exchange data feeds...", flush=True)

    tickers = await binance_feed.fetch_all_tickers()
    if not tickers:
        print("Failed to fetch tickers, retrying...")
        return

    btc_candles_4h = await binance_feed.fetch_klines("BTCUSDT", interval="4h", limit=20)
    btc_price = tickers.get("BTCUSDT", 0.0)
    btc_status = "STABLE / BULLISH"
    if btc_candles_4h and len(btc_candles_4h) >= 2:
        btc_change = ((btc_price - btc_candles_4h[-2]["close"]) / btc_candles_4h[-2]["close"]) * 100.0
        if btc_change < -1.5:
            btc_status = f"⚠️ DUMP WARNING ({btc_change:.2f}%)"
        else:
            btc_status = f"🟢 HEALTHY ({btc_change:+.2f}%)"
    print(f"👑 King Bitcoin Status: {btc_status} | Live BTC Price: ${btc_price:,.2f}\n")

    scan_coins = list(dict.fromkeys(list(TOP_22_CHAMPIONS) + list(TIER1_COINS) + list(DEFAULT_COINS)))
    print(f"Scanning {len(scan_coins)} high-liquidity coins across 1H and 4H timeframes...\n")

    setups_found = []

    for sym in scan_coins:
        curr_p = tickers.get(sym, 0.0)
        if curr_p <= 0:
            continue

        for tf in ["4h", "1h"]:
            candles = await binance_feed.fetch_klines(sym, interval=tf, limit=80)
            if not candles or len(candles) < 30:
                continue

            detected = hermes35_live_engine.detect_apex_setups_on_candles(sym, tf, candles, curr_p)
            for s in detected:
                dist = (curr_p - s["entry_price"]) / s["entry_price"] * 100.0
                setups_found.append({
                    "symbol": sym,
                    "tf": tf.upper(),
                    "side": s["side"],
                    "price": curr_p,
                    "entry": s["entry_price"],
                    "radar": s["radar_price"],
                    "dist": dist,
                    "status": s["status"],
                    "tp": s["tp_price"],
                    "armor2": s["armor_stage2_price"],
                    "sl": s["soft_sl_price"],
                    "is_origin": s.get("is_origin", False)
                })

    setups_found.sort(key=lambda x: (x["status"] == "FRESH_TRIGGERED", x["status"] == "RADAR_PRE_ARMED", -abs(x["dist"])), reverse=True)

    if not setups_found:
        print("No active setups currently in radar window.")
        return

    for idx, s in enumerate(setups_found[:10], 1):
        origin_str = " [ORIGIN BEDROCK]" if s["is_origin"] else ""
        print(f"#{idx}. {s['symbol']} ({s['tf']} {s['side']}) | Price: ${s['price']} | 5% Entry: ${s['entry']} | Radar: ${s['radar']} | Dist: {s['dist']:+.2f}% | Status: {s['status']}{origin_str}")
        print(f"   TP: ${s['tp']} | Stage 2 Harvest (+9% -> Lock +4.5%): ${s['armor2']} | SL: ${s['sl']}\n")

if __name__ == "__main__":
    asyncio.run(scan_live_market_buy_opportunities())
