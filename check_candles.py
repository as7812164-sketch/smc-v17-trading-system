import asyncio
import datetime
from feed.binance_feed import binance_feed

async def check():
    # 1. Check AVAXUSDT (Short entry: 10.9030, TP: 10.6631, SL: 11.1756 at 07:43 IST)
    candles_avax = await binance_feed.fetch_klines('AVAXUSDT', '15m', 25)
    print('=== AVAXUSDT Candles (15m) ===')
    lowest_since_entry = 999999
    highest_since_entry = 0
    for c in candles_avax[-18:]:
        dt = datetime.datetime.fromtimestamp(c['time']/1000, datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        print(str(dt) + " O:" + str(c['open']) + " H:" + str(c['high']) + " L:" + str(c['low']) + " C:" + str(c['close']))
        if dt.hour >= 7 and dt.minute >= 40 or dt.hour > 7:
            lowest_since_entry = min(lowest_since_entry, float(c['low']))
            highest_since_entry = max(highest_since_entry, float(c['high']))

    print(f"AVAX Entry: 10.9030, Lowest: {lowest_since_entry}, Highest: {highest_since_entry}, TP: 10.6631, SL: 11.1756")

    # 2. Check OPUSDT (Long entry: 0.1453, TP: 0.1485, SL: 0.1417 at 08:28 IST)
    candles_op = await binance_feed.fetch_klines('OPUSDT', '15m', 25)
    print('\n=== OPUSDT Candles (15m) ===')
    lowest_op = 999999
    highest_op = 0
    for c in candles_op[-18:]:
        dt = datetime.datetime.fromtimestamp(c['time']/1000, datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        print(str(dt) + " O:" + str(c['open']) + " H:" + str(c['high']) + " L:" + str(c['low']) + " C:" + str(c['close']))
        if dt.hour >= 8 and dt.minute >= 25 or dt.hour > 8:
            lowest_op = min(lowest_op, float(c['low']))
            highest_op = max(highest_op, float(c['high']))

    print(f"OP Entry: 0.1453, Highest: {highest_op}, Lowest: {lowest_op}, TP: 0.1485, SL: 0.1417")

asyncio.run(check())
