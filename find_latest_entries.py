import asyncio
import sys
import time
from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17, filter_active_zones
from engine.order_flow import analyze_order_flow
from ai.smart_money_analyzer import evaluate_setup_confluence
from ai.self_improving_engine import mike_brain
from config import DEFAULT_COINS, TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def scan_latest():
    coins = list(dict.fromkeys(list(TIER1_COINS) + list(DEFAULT_COINS)))[:30]
    tickers = await binance_feed.fetch_all_tickers()
    
    entries_1h = []
    entries_4h = []
    
    print("==========================================================================================")
    print("           REAL-TIME 1H & 4H LATEST ENTRY SCANNER (LIVE @ 13:50 IST)")
    print("==========================================================================================")
    
    for sym in coins:
        cur_p = tickers.get(sym)
        if not cur_p:
            continue
            
        elig = mike_brain.evaluate_coin_eligibility(sym)
        if not elig.get("eligible", True):
            continue
            
        # --- 1H SCAN ---
        c_1h = await binance_feed.fetch_klines(sym, interval="1h", limit=70)
        if c_1h and len(c_1h) >= 30:
            zones_1h = filter_active_zones(analyze_candles_smc_v17(sym, c_1h))
            buys_1h = [z for z in zones_1h if z["side"] == "BUY"]
            buys_1h.sort(key=lambda x: x["ob_high"], reverse=True)
            
            if len(buys_1h) >= 2:
                # 2nd OB is index 1
                target_ob = buys_1h[1]
                entry = target_ob["ob_high"]
                dist = (cur_p - entry) / entry * 100.0
                in_zone = target_ob["ob_low"] <= cur_p <= target_ob["ob_high"]
                
                oi_live = await binance_feed.fetch_open_interest(sym)
                oi_hist = await binance_feed.fetch_open_interest_hist(sym, period="1h", limit=5)
                of = analyze_order_flow(sym, c_1h, cur_p, zone=target_ob, live_oi=oi_live, hist_oi=oi_hist)
                conf = evaluate_setup_confluence(sym, target_ob, c_1h, order_flow=of)
                
                entries_1h.append({
                    "symbol": sym,
                    "price": cur_p,
                    "entry": entry,
                    "zone_low": target_ob["ob_low"],
                    "zone_high": target_ob["ob_high"],
                    "dist_pct": dist,
                    "in_zone": in_zone,
                    "has_3_obs": len(buys_1h) >= 3,
                    "total_obs": len(buys_1h),
                    "score": conf.get("score", 0),
                    "delta_pct": of.get("delta_ratio", 0.5) * 100.0,
                    "cvd_rev": of.get("cvd_reversal", False),
                    "oi_chg": of.get("oi_change_1h", 0.0),
                    "is_super_sniper": (of.get("delta_ratio", 0) >= 0.51 or of.get("is_rocket")) and of.get("cvd_reversal", False),
                    "strengths": conf.get("strengths", []),
                    "risks": conf.get("risks", []),
                    "tp": entry * 1.015,
                    "be": entry * 1.0075,
                    "sl": entry * 0.980,
                    "time": time.strftime('%d %b %H:%M', time.gmtime(target_ob.get("origin_time", 0)/1000))
                })

        # --- 4H SCAN ---
        c_4h = await binance_feed.fetch_klines(sym, interval="4h", limit=60)
        if c_4h and len(c_4h) >= 20:
            zones_4h = filter_active_zones(analyze_candles_smc_v17(sym, c_4h))
            buys_4h = [z for z in zones_4h if z["side"] == "BUY"]
            buys_4h.sort(key=lambda x: x["ob_high"], reverse=True)
            
            if len(buys_4h) >= 2:
                target_ob_4h = buys_4h[1]
                entry_4h = target_ob_4h["ob_high"]
                dist_4h = (cur_p - entry_4h) / entry_4h * 100.0
                in_zone_4h = target_ob_4h["ob_low"] <= cur_p <= target_ob_4h["ob_high"]
                
                oi_live = await binance_feed.fetch_open_interest(sym)
                oi_hist = await binance_feed.fetch_open_interest_hist(sym, period="4h", limit=5)
                of_4h = analyze_order_flow(sym, c_4h, cur_p, zone=target_ob_4h, live_oi=oi_live, hist_oi=oi_hist)
                conf_4h = evaluate_setup_confluence(sym, target_ob_4h, c_4h, order_flow=of_4h)
                
                entries_4h.append({
                    "symbol": sym,
                    "price": cur_p,
                    "entry": entry_4h,
                    "zone_low": target_ob_4h["ob_low"],
                    "zone_high": target_ob_4h["ob_high"],
                    "dist_pct": dist_4h,
                    "in_zone": in_zone_4h,
                    "has_3_obs": len(buys_4h) >= 3,
                    "total_obs": len(buys_4h),
                    "score": conf_4h.get("score", 0),
                    "delta_pct": of_4h.get("delta_ratio", 0.5) * 100.0,
                    "cvd_rev": of_4h.get("cvd_reversal", False),
                    "oi_chg": of_4h.get("oi_change_1h", 0.0),
                    "is_super_sniper": (of_4h.get("delta_ratio", 0) >= 0.51 or of_4h.get("is_rocket")) and of_4h.get("cvd_reversal", False),
                    "strengths": conf_4h.get("strengths", []),
                    "risks": conf_4h.get("risks", []),
                    "tp": entry_4h * 1.022,
                    "be": entry_4h * 1.011,
                    "sl": entry_4h * 0.975,
                    "time": time.strftime('%d %b %H:%M', time.gmtime(target_ob_4h.get("origin_time", 0)/1000))
                })

    # Sort 1H candidates
    entries_1h.sort(key=lambda x: (
        x["in_zone"],
        x["is_super_sniper"] and x["has_3_obs"],
        x["score"] >= 95,
        -abs(x["dist_pct"])
    ), reverse=True)
    
    # Sort 4H candidates
    entries_4h.sort(key=lambda x: (
        x["in_zone"],
        x["is_super_sniper"] and x["has_3_obs"],
        x["score"] >= 95,
        -abs(x["dist_pct"])
    ), reverse=True)
    
    print("\n--- TOP 1H SETUPS ---")
    for idx, e in enumerate(entries_1h[:5], 1):
        print(f"#{idx}. {e['symbol']} | Price: ${e['price']} | InZone: {e['in_zone']} | Dist: {e['dist_pct']:+.2f}% | 3-OB: {e['has_3_obs']} | Score: {e['score']}/100 | Delta: {e['delta_pct']:.1f}% | CVD_Rev: {e['cvd_rev']} | Entry: ${e['entry']:.4f} | TP: ${e['tp']:.4f} | SL: ${e['sl']:.4f}")

    print("\n--- TOP 4H SETUPS ---")
    for idx, e in enumerate(entries_4h[:5], 1):
        print(f"#{idx}. {e['symbol']} | Price: ${e['price']} | InZone: {e['in_zone']} | Dist: {e['dist_pct']:+.2f}% | 3-OB: {e['has_3_obs']} | Score: {e['score']}/100 | Delta: {e['delta_pct']:.1f}% | CVD_Rev: {e['cvd_rev']} | Entry: ${e['entry']:.4f} | TP: ${e['tp']:.4f} | SL: ${e['sl']:.4f}")

    with open("latest_scanned_entries.json", "w", encoding="utf-8") as f:
        json.dump({"1h": entries_1h[:8], "4h": entries_4h[:8]}, f, indent=2)

if __name__ == "__main__":
    asyncio.run(scan_latest())
