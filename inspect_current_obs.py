import asyncio
import sys
import time
from datetime import datetime
from config import DEFAULT_COINS, TIER1_COINS
from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17, filter_active_zones
from engine.order_flow import analyze_order_flow
from ai.smart_money_analyzer import evaluate_setup_confluence

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    coins = ["ARBUSDT", "SUIUSDT", "UNIUSDT", "DOGEUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
    tickers = await binance_feed.fetch_all_tickers()
    
    print(f"==========================================================================================")
    print(f"       CURRENT SMC V17 ORDER BLOCKS AUDIT (LIVE TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"==========================================================================================")
    
    for sym in coins:
        cur_p = tickers.get(sym)
        if not cur_p:
            continue
            
        c_1h = await binance_feed.fetch_klines(sym, interval="1h", limit=100)
        if not c_1h:
            continue
            
        detected = analyze_candles_smc_v17(sym, c_1h)
        active_buys = [z for z in filter_active_zones(detected) if z["side"] == "BUY"]
        active_buys.sort(key=lambda x: x["ob_high"], reverse=True)
        
        # Check order flow
        oi_live = await binance_feed.fetch_open_interest(sym)
        oi_hist = await binance_feed.fetch_open_interest_hist(sym, period="1h", limit=5)
        of = analyze_order_flow(sym, c_1h, cur_p, live_oi=oi_live, hist_oi=oi_hist)
        
        print(f"\n--- {sym} (Current Price: ${cur_p}) ---")
        print(f"  Total Active BUY OBs: {len(active_buys)} | Order Flow: Delta {of.get('delta_ratio', 0.5)*100:.1f}% | CVD_Rev: {of.get('cvd_reversal')} | OI 1H: {of.get('oi_change_1h', 0.0):+.2f}%")
        
        for idx, z in enumerate(active_buys, 1):
            tag = ""
            if idx == 1:
                tag = "1st OB (Top / Ceiling)"
            elif idx == 2:
                tag = "⭐ 2ND OB (MIDDLE / SANDWICH - TRADE ZONE)"
            elif idx == 3:
                tag = "3rd OB (Bottom / Anchor)"
            else:
                tag = f"{idx}th OB"
                
            dist = (cur_p - z["ob_high"]) / z["ob_high"] * 100
            in_zone = z["ob_low"] <= cur_p <= z["ob_high"]
            zone_time = time.strftime('%d %b %H:%M', time.gmtime(z.get('origin_time', 0)/1000)) if z.get('origin_time') else 'N/A'
            
            print(f"  [{idx}] {tag}")
            print(f"      Zone Span:  ${z['ob_low']:.4f}  ───  ${z['ob_high']:.4f}")
            print(f"      Distance:   {dist:+.2f}%  {'🎯 [INSIDE ZONE]' if in_zone else ''}")
            print(f"      Formed:     {zone_time} UTC | Status: {z.get('status')}")
            
            if idx == 2 or (len(active_buys) < 3 and idx == 1):
                # Trade levels
                entry = z["ob_high"]
                tp = entry * 1.015
                be = entry * 1.0075
                sl = entry * 0.980
                print(f"      👉 Planned Trade:")
                print(f"         Entry Limit: ${entry:.4f}")
                print(f"         TP (+7.5% ROE @ 5x): ${tp:.4f} (+1.50%)")
                print(f"         BE Lock (+3.75% ROE): ${be:.4f} (+0.75%)")
                print(f"         SL (-10% ROE): ${sl:.4f} (-2.00%)")

if __name__ == "__main__":
    asyncio.run(main())
