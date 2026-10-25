import asyncio
from engine.hermes35_live import Hermes35LiveEngine
from feed.binance_feed import binance_feed
from config import TOP_28_CHAMPIONS

async def live_scan():
    eng = Hermes35LiveEngine()
    sentry = await eng.evaluate_btc_macro_sentry()
    print("=" * 75)
    print("HERMES 3.5 LIVE PULSE SCAN (CALIBRATED WITH 18H RETEST + MULTI-EMA)")
    print("=" * 75)
    print(f"BTC Sentry Bias: {sentry.get('bias')} | Long Veto: {sentry.get('long_veto')}")
    print(f"BTC 4H EMAs: EMA20=${sentry.get('btc_ema20'):,.2f} | EMA50=${sentry.get('btc_ema50'):,.2f} | EMA200=${sentry.get('btc_ema200'):,.2f}")
    print(f"BTC Price: ${sentry.get('close_price'):,.2f}\n")
    
    qualified = []
    for sym in TOP_28_CHAMPIONS:
        for tf in ["1h", "4h"]:
            try:
                candles = await binance_feed.fetch_klines(sym, interval=tf, limit=120)
                setups = eng.detect_apex_setups_on_candles(sym, candles, tf, sentry)
                for s in setups:
                    cur_p = float(candles[-1]["close"])
                    dist = (cur_p - s["entry_price"]) / s["entry_price"] * 100.0 if s["side"] == "LONG" else (s["entry_price"] - cur_p) / s["entry_price"] * 100.0
                    qualified.append({
                        "symbol": s["symbol"], "side": s["side"], "tf": s["interval"],
                        "entry": s["entry_price"], "radar": s["radar_price"],
                        "cur": cur_p, "dist": round(dist, 2), "status": s["status"]
                    })
            except Exception:
                pass
    
    qualified.sort(key=lambda x: abs(x["dist"]))
    print(f"Total Qualified Setups Live: {len(qualified)} setups across 28 pairs!")
    print("\nTop 6 Setups Nearest to Entry / Radar:")
    for q in qualified[:6]:
        print(f"  • {q['symbol']:<10} ({q['tf']} {q['side']:<5}) | Price: {q['cur']:<10} | 5% Entry: {q['entry']:<10} | Radar: {q['radar']:<10} | Distance: {q['dist']:+.2f}% | Status: {q['status']}")

if __name__ == "__main__":
    asyncio.run(live_scan())
