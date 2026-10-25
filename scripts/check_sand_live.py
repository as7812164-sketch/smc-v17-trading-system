import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from datetime import datetime
from database.db import get_connection
from feed.binance_feed import binance_feed
from engine.hermes40_live import hermes40_live_engine

with get_connection() as conn:
    cur = conn.execute("SELECT id, symbol, side, entry_price, status, timeframe, account_id, mode, entry_time FROM paper_trades WHERE symbol LIKE '%SAND%' ORDER BY id DESC LIMIT 5")
    trades = [dict(r) for r in cur.fetchall()]
    print("DB Trades for SAND:")
    for t in trades:
        print(t)
    if not trades:
        print("No trades found in DB for SAND.")
        
    cur_open = conn.execute("SELECT id, symbol, side, entry_price, status, timeframe, account_id, mode FROM paper_trades WHERE status = 'OPEN'")
    open_all = [dict(r) for r in cur_open.fetchall()]
    print(f"\nALL CURRENTLY OPEN TRADES IN ENTIRE SYSTEM: {len(open_all)}")
    for ot in open_all:
        print(ot)

async def check_sand():
    candles_15m = await binance_feed.fetch_klines('SANDUSDT', interval='15m', limit=10)
    print("\nRecent 15m candles for SANDUSDT:")
    for c in candles_15m[-5:]:
        t_str = datetime.fromtimestamp(c['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Time: {t_str}, O: {c['open']}, H: {c['high']}, L: {c['low']}, C: {c['close']}")
    latest = candles_15m[-1]
    print(f"\nCurrent SAND Price: {latest['close']}, Latest Low: {latest['low']}, Latest High: {latest['high']}")

    btc_sentry = await hermes40_live_engine.evaluate_btc_macro()
    candles_4h = await binance_feed.fetch_klines('SANDUSDT', interval='4h', limit=75)
    setups = hermes40_live_engine.detect_hermes40_setups_sync('SANDUSDT', '4h', candles_4h, btc_sentry)
    print(f"\nSAND 4H Setups found: {len(setups)}")
    for s in setups:
        print(s)

if __name__ == '__main__':
    asyncio.run(check_sand())
