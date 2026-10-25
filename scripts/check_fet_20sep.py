import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed

async def check_fet():
    k = await binance_feed.fetch_klines('FETUSDT', interval='4h', limit=200)
    print(f"Total 4H candles fetched for FETUSDT: {len(k)}")
    for c in k:
        dt = datetime.fromtimestamp(c['time'] / 1000, tz=timezone.utc) + timedelta(hours=5, minutes=30)
        dt_str = dt.strftime('%d %b %Y %I:%M %p IST')
        if any(x in dt_str for x in ['19 Sep', '20 Sep', '21 Sep', '22 Sep']):
            print(f"{dt_str} | Open: {c['open']} | High: {c['high']} | Low: {c['low']} | Close: {c['close']}")

if __name__ == "__main__":
    asyncio.run(check_fet())
