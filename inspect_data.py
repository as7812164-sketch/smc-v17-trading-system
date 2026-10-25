import os
import glob
import json
import urllib.request
import sqlite3

try:
    req = urllib.request.Request('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', headers={'User-Agent': 'Mozilla/5.0'})
    btc = float(json.loads(urllib.request.urlopen(req, timeout=5).read())['price'])
    print(f"BTC_PRICE: ${btc:,.2f}")
except Exception as e:
    print(f"BTC_PRICE err: {e}")

try:
    conn = sqlite3.connect('database/smc_v17.db')
    c = conn.cursor()
    c.execute("SELECT id, symbol, side, timeframe, entry_price FROM paper_trades WHERE status='OPEN' ORDER BY id DESC")
    rows = c.fetchall()
    print("OPEN_COUNT:", len(rows))
    prices = {}
    for r in rows:
        sym = r[1]
        if sym not in prices:
            try:
                req = urllib.request.Request(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', headers={'User-Agent': 'Mozilla/5.0'})
                prices[sym] = float(json.loads(urllib.request.urlopen(req, timeout=5).read())['price'])
            except Exception:
                prices[sym] = 0.0
        entry = float(r[4])
        mark = prices.get(sym, entry)
        lev = 5.0
        side = r[2]
        roe = ((mark - entry) / entry) * lev * 100.0 if side == 'LONG' else ((entry - mark) / entry) * lev * 100.0
        print(f"Trade #{r[0]}: {sym} {side} ({r[3]}) @ {entry} | Mark: {mark} | ROE: {roe:+.2f}%")
    conn.close()
except Exception as e:
    print(f"DB err: {e}")

files = glob.glob('historical_data/*')
print(f"Historical data files count: {len(files)}")
for f in files:
    print(f"  {f} ({os.path.getsize(f):,} bytes)")
