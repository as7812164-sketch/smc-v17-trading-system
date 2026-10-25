import asyncio
from feed.binance_feed import binance_feed
from engine.hermes2_apex_live import hermes2_apex_engine

async def main():
    print("Testing King BTC Macro Sentry...")
    btc_sentry = await hermes2_apex_engine.evaluate_btc_macro_sentry()
    print(f"BTC Bias: {btc_sentry.get('bias')}")
    print(f"BTC EMA50: ${btc_sentry.get('btc_ema50'):,.2f}")
    print(f"BTC Price: ${btc_sentry.get('close_price'):,.2f}")
    print(f"Long Veto: {btc_sentry.get('long_veto')}")
    print(f"Short Veto: {btc_sentry.get('short_veto')} (Alt shorts blocked in BTC Bull Trend!)")

    print("\nTesting Setup Detection on APTUSDT and BTCUSDT...")
    for sym in ["APTUSDT", "BTCUSDT", "LDOUSDT"]:
        klines = await binance_feed.fetch_klines(sym, interval="4h", limit=50)
        setups = hermes2_apex_engine.detect_apex_setups_on_candles(sym, klines, "4h", btc_sentry)
        print(f"  {sym} 4H Setups detected: {len(setups)}")
        for s in setups:
            print(f"    -> {s['symbol']} {s['side']} Status: {s['status']} Entry: {s['entry_price']} Sentry: {s['sentry_reasons'][:60]}...")

    await binance_feed.close()
    print("\n✅ Verification complete! 0 syntax/runtime errors.")

if __name__ == "__main__":
    asyncio.run(main())
