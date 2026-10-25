import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from database.db import get_connection
from feed.binance_feed import binance_feed
from datetime import datetime

with get_connection() as conn:
    cur = conn.execute("SELECT id, symbol, side, entry_price, status, timeframe, account_id, mode, entry_time FROM paper_trades WHERE symbol LIKE '%FIL%' ORDER BY id DESC LIMIT 5")
    trades = [dict(r) for r in cur.fetchall()]
    print("DB Trades for FIL:")
    for t in trades:
        print(t)
    if not trades:
        print("No trades found in DB for FIL.")

async def check_fil():
    candles = await binance_feed.fetch_klines('FILUSDT', interval='15m', limit=10)
    if candles:
        print("\nRecent 15m candles for FILUSDT:")
        for c in candles[-5:]:
            t_str = datetime.fromtimestamp(c["time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
            print(f"Time: {t_str}, O: {c['open']}, H: {c['high']}, L: {c['low']}, C: {c['close']}")
        latest = candles[-1]
        print(f"\nCurrent FIL Price: {latest['close']}, Latest Candle High: {latest['high']}")

if __name__ == '__main__':
    asyncio.run(check_fil())
