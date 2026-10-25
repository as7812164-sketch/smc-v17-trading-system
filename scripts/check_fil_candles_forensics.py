import asyncio
import datetime
import sys
sys.path.insert(0, '.')
from feed.binance_feed import binance_feed

async def main():
    candles = await binance_feed.fetch_klines('FILUSDT', interval='1m', limit=35)
    print("--- FILUSDT 1m CANDLES ---")
    for c in candles:
        t_ist = datetime.datetime.fromtimestamp(
            c['time'] / 1000.0,
            datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        ).strftime('%Y-%m-%d %H:%M:%S IST')
        print(f"{t_ist} | O: {c['open']} | H: {c['high']} | L: {c['low']} | C: {c['close']}")
    await binance_feed.close()

if __name__ == '__main__':
    asyncio.run(main())
