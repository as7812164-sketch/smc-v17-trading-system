import sqlite3
import os
import glob
import asyncio
import aiohttp
import json
from datetime import datetime, timezone

dbs = ['smc_trading.db', 'database/smc_trading.db', 'database/trades.db', 'database/trading_system.db']

print("--- CHECKING SQLITE DATABASES ---")
for p in dbs:
    if os.path.exists(p):
        print(f"\nDB: {p}")
        try:
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cur.fetchall()]
            print("  Tables:", tables)
            for tbl in ['paper_trades', 'trades', 'positions', 'paper_positions', 'open_trades', 'paper_account']:
                if tbl in tables:
                    cur.execute(f"SELECT count(*) FROM {tbl}")
                    cnt = cur.fetchone()[0]
                    print(f"  {tbl} count: {cnt}")
                    if cnt > 0:
                        cur.execute(f"SELECT * FROM {tbl} ORDER BY rowid DESC LIMIT 5")
                        rows = cur.fetchall()
                        for r in rows:
                            print(f"    row: {r}")
            conn.close()
        except Exception as e:
            print("  Error:", e)

# Also check live binance klines for the candidate setups to see their lowest / highest price since yesterday!
SETUPS = [
    {"symbol": "LDOUSDT", "side": "LONG", "tf": "4h", "entry": 0.4477, "tp": 0.4602, "sl": 0.4352},
    {"symbol": "RUNEUSDT", "side": "LONG", "tf": "1h", "entry": 0.7576, "tp": 0.7788, "sl": 0.7364},
    {"symbol": "TIAUSDT", "side": "LONG", "tf": "4h", "entry": 0.4503, "tp": 0.4629, "sl": 0.4377},
    {"symbol": "FETUSDT", "side": "SHORT", "tf": "4h", "entry": 0.2585, "tp": 0.2513, "sl": 0.2658},
    {"symbol": "ATOMUSDT", "side": "SHORT", "tf": "4h", "entry": 1.8578, "tp": 1.8057, "sl": 1.9098},
    {"symbol": "AXSUSDT", "side": "LONG", "tf": "4h", "entry": 1.2082, "tp": 1.2420, "sl": 1.1744},
]

async def check_klines():
    print("\n--- CHECKING 24H PRICE EXTREMES ON BINANCE FUTURES ---")
    async with aiohttp.ClientSession() as session:
        for s in SETUPS:
            sym = s["symbol"]
            url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1h&limit=24"
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        klines = await resp.json()
                        lows = [float(k[3]) for k in klines]
                        highs = [float(k[2]) for k in klines]
                        current = float(klines[-1][4])
                        min_24h = min(lows)
                        max_24h = max(highs)
                        entry = s["entry"]
                        side = s["side"]
                        
                        hit_status = "NO"
                        if side == "LONG":
                            # Did price reach <= entry?
                            if min_24h <= entry:
                                hit_status = f"YES! (Lowest was {min_24h} <= {entry})"
                            else:
                                diff_pct = ((min_24h - entry) / entry) * 100
                                cur_diff_pct = ((current - entry) / current) * 100
                                hit_status = f"NOT YET. Lowest reached: {min_24h} (+{diff_pct:.2f}% above entry). Current: {current} (+{cur_diff_pct:.2f}% above entry)"
                        else: # SHORT
                            # Did price reach >= entry?
                            if max_24h >= entry:
                                hit_status = f"YES! (Highest was {max_24h} >= {entry})"
                            else:
                                diff_pct = ((entry - max_24h) / entry) * 100
                                cur_diff_pct = ((entry - current) / current) * 100
                                hit_status = f"NOT YET. Highest reached: {max_24h} (-{diff_pct:.2f}% below entry). Current: {current} (-{cur_diff_pct:.2f}% below entry)"
                        
                        print(f"[{sym} {side} - Entry: {entry}] -> {hit_status}")
            except Exception as e:
                print(f"Error {sym}: {e}")

asyncio.run(check_klines())
