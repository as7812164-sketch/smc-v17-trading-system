import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed

def format_ist(ts_ms):
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) + timedelta(hours=5, minutes=30)
    return dt.strftime("%d %b %Y %I:%M %p IST")

async def inspect_fet_setup():
    k4 = await binance_feed.fetch_klines('FETUSDT', interval='4h', limit=200)
    # Find candle on 20 Sep 2026 05:30 AM IST
    tap_idx = -1
    for idx, c in enumerate(k4):
        if format_ist(c['time']) == "20 Sep 2026 05:30 AM IST":
            tap_idx = idx
            break
            
    print(f"Tap candle index: {tap_idx}")
    if tap_idx != -1:
        tap_c = k4[tap_idx]
        print(f"Tap Candle: {format_ist(tap_c['time'])} | Open: {tap_c['open']}, High: {tap_c['high']}, Low: {tap_c['low']}, Close: {tap_c['close']}")
        # Look backwards to see what origin and decisional was detected
        # Check prior candles
        for i in range(max(0, tap_idx - 30), tap_idx):
            print(f"[{i}] {format_ist(k4[i]['time'])} | O:{k4[i]['open']} H:{k4[i]['high']} L:{k4[i]['low']} C:{k4[i]['close']}")

if __name__ == "__main__":
    asyncio.run(inspect_fet_setup())
