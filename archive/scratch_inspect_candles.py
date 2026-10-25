import asyncio
from feed.binance_feed import binance_feed

async def inspect():
    for sym in ['BTCUSDT', 'ALGOUSDT', 'FETUSDT', 'ADAUSDT']:
        k = await binance_feed.fetch_klines(sym, interval='1h', limit=5)
        print(f"=== {sym} LAST 5 1H CANDLES ===")
        for c in k:
            print("  O:", c['open'], "H:", c['high'], "L:", c['low'], "C:", c['close'], "Vol:", c.get('volume', 0))

asyncio.run(inspect())
