import asyncio
import sys
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed
from engine.hermes35_live import hermes35_live_engine, TOP_22_CHAMPIONS
from config import DEFAULT_COINS, TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))

async def check_live_pulse_and_scans():
    tickers = await binance_feed.fetch_all_tickers()
    if not tickers:
        print("Failed to fetch live tickers!")
        return

    # 1. Active ICPUSDT position live status
    icp_price = tickers.get("ICPUSDT", 0.0)
    icp_entry = 3.31
    icp_tp = 3.390764
    icp_sl = 3.23056
    icp_gain_pct = ((icp_price - icp_entry) / icp_entry) * 100.0
    icp_roe = icp_gain_pct * 5.0 # 5x leverage
    pnl_usdt = 218.0 * (icp_gain_pct / 100.0)
    print("=" * 80)
    print("1. CURRENT LIVE POSITION STATUS: ICPUSDT (1H LONG)")
    print("=" * 80)
    print(f"  • Entry Price: ${icp_entry:.4f}")
    print(f"  • Live Current Price: ${icp_price:.4f}")
    print(f"  • Price Move: {icp_gain_pct:+.2f}% | 5x ROE: {icp_roe:+.2f}%")
    print(f"  • Unrealized P&L: ${pnl_usdt:+.2f} USDT")
    print(f"  • TP (+14% ROE Target): ${icp_tp:.4f} (Distance: {((icp_tp - icp_price)/icp_price*100):+.2f}%)")
    print(f"  • SL: ${icp_sl:.4f} (Distance: {((icp_price - icp_sl)/icp_price*100):+.2f}%)")
    
    # Check Stepped Harvest threshold
    harvest_target = round(icp_entry * 1.0180, 4)
    be_target = round(icp_entry * 1.0160, 4)
    print(f"  • Stage 1 Break-Even Armor Trigger (+8% ROE): ${be_target:.4f}")
    print(f"  • Stage 2 Harvest Lock Trigger (+9% ROE -> Lock +4.5%): ${harvest_target:.4f}")

    # 2. Macro King BTC Status
    btc_price = tickers.get("BTCUSDT", 0.0)
    btc_sentry = await hermes35_live_engine.evaluate_btc_macro_sentry()
    print("\n" + "=" * 80)
    print(f"2. KING BITCOIN 4H MACRO CAUSAL SENTRY (${btc_price:,.2f})")
    print("=" * 80)
    print(f"  • Trend: {btc_sentry.get('trend')} | Regime: {btc_sentry.get('regime')}")
    print(f"  • EMA50 (4H): ${btc_sentry.get('ema50', 0):,.2f}")
    print(f"  • Long Veto: {btc_sentry.get('long_veto')} | Short Veto: {btc_sentry.get('short_veto')}")
    print(f"  • Note: {btc_sentry.get('reason')}")

    # 3. Market-wide Hermes 3.5 Radar Harvest Scan
    coins = list(dict.fromkeys(list(TOP_22_CHAMPIONS) + list(TIER1_COINS) + list(DEFAULT_COINS)))
    print("\n" + "=" * 80)
    print(f"3. UPCOMING SETUPS SCAN (HERMES 3.5 RADAR HARVEST - 4H & 1H)")
    print("=" * 80)
    print(f"Scanning {len(coins)} Coins across 4H & 1H for 5% Boundary Penetration & 0.20% Radar...")

    setups_found = []
    for sym in coins:
        cur_p = tickers.get(sym, 0.0)
        if cur_p <= 0:
            continue

        for tf in ["4h", "1h"]:
            try:
                candles = await binance_feed.fetch_klines(sym, interval=tf, limit=80)
                if not candles or len(candles) < 40:
                    continue

                detected = hermes35_live_engine.detect_apex_setups_on_candles(sym, candles, tf, btc_sentry)
                for s in detected:
                    eff_entry = s["entry_price"]
                    radar_p = s["radar_price"]
                    side = s["side"]
                    dist = ((cur_p - eff_entry) / eff_entry * 100.0) if side == "LONG" else ((eff_entry - cur_p) / eff_entry * 100.0)
                    setups_found.append({
                        "symbol": sym,
                        "tf": tf.upper(),
                        "side": side,
                        "cur_price": cur_p,
                        "eff_entry": eff_entry,
                        "radar_price": radar_p,
                        "dist_pct": dist,
                        "status": s["status"],
                        "tp_price": s["tp_price"],
                        "stage1_be": s["armor_stage1_price"],
                        "stage2_harvest": s["armor_stage2_price"],
                        "harvest_lock": s["harvest_lock_price"],
                        "soft_sl": s["soft_sl_price"],
                        "hard_sl": s["hard_sl_price"],
                        "ob_low": s["ob_low"],
                        "ob_high": s["ob_high"],
                        "is_origin": s.get("is_origin", False),
                        "runway_pct": s.get("runway_void_pct", 0.0),
                        "disp_pct": s.get("displacement_pct", 0.0),
                        "wick_pct": s.get("wick_ratio_pct", 0.0),
                        "is_fresh": s.get("is_fresh_trigger", False)
                    })
            except Exception as e:
                continue

    # Sort setups: FRESH_TRIGGERED first, then RADAR_PRE_ARMED, then closest distance
    setups_found.sort(key=lambda x: (
        x["status"] == "FRESH_TRIGGERED",
        x["status"] == "RADAR_PRE_ARMED",
        -abs(x["dist_pct"])
    ), reverse=True)

    if not setups_found:
        print("\nNo qualified setups found currently in radar (waiting for clean institutional OB + FVG retest).")
        return

    print(f"\nFound {len(setups_found)} Qualified Hermes 3.5 Setups:\n")
    for idx, s in enumerate(setups_found, 1):
        origin_str = " ⭐ [ORIGIN BEDROCK]" if s["is_origin"] else ""
        fresh_str = " ⚡ [FRESH TRIGGER]" if s["is_fresh"] else ""
        print(f"#{idx}. {s['symbol']} ({s['tf']} {s['side']}) | Status: {s['status']}{origin_str}{fresh_str}")
        print(f"    • Live Price: ${s['cur_price']} | 5% Boundary Entry: ${s['eff_entry']} | 0.20% Radar: ${s['radar_price']}")
        print(f"    • Distance to Entry: {s['dist_pct']:+.2f}%")
        print(f"    • OB Zone: [${s['ob_low']} - ${s['ob_high']}] | Displacement: {s['disp_pct']:.1f}% | Airspace Void: {s['runway_pct']:.1f}%")
        print(f"    • Targets (5x Isolated):")
        print(f"        - Stage 1 BE Lock (+8% ROE): ${s['stage1_be']}")
        print(f"        - Stage 2 Harvest (+9% ROE -> Lock +4.5%): ${s['stage2_harvest']} (Locked SL: ${s['harvest_lock']})")
        print(f"        - Final TP (+14% ROE): ${s['tp_price']}")
        print(f"        - Soft SL: ${s['soft_sl']} | Hard SL: ${s['hard_sl']}\n")

if __name__ == "__main__":
    asyncio.run(check_live_pulse_and_scans())
