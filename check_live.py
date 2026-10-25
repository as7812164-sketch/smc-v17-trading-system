import urllib.request
import json
import sqlite3

try:
    req = urllib.request.Request('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', headers={'User-Agent': 'Mozilla/5.0'})
    btc = float(json.loads(urllib.request.urlopen(req, timeout=5).read())['price'])
    print(f"BTC_PRICE: ${btc:,.2f}")
except Exception as e:
    print(f"BTC_PRICE: Error {e}")

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("PRAGMA table_info(paper_trades)")
cols = [col[1] for col in c.fetchall()]
print("Columns:", cols)
c.execute("SELECT * FROM paper_trades WHERE status='OPEN' ORDER BY id DESC LIMIT 5")
rows = c.fetchall()
print(f"OPEN_COUNT: {len(rows)}")
prices = {}
for r in rows:
    sym = r[2] # symbol
    if sym not in prices:
        try:
            req = urllib.request.Request(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', headers={'User-Agent': 'Mozilla/5.0'})
            prices[sym] = float(json.loads(urllib.request.urlopen(req, timeout=5).read())['price'])
        except Exception:
            prices[sym] = 0.0

for r in rows:
    row_dict = dict(zip(cols, r))
    sym = row_dict.get('symbol')
    side = row_dict.get('side')
    entry = float(row_dict.get('entry_price'))
    mark = prices.get(sym, entry)
    lev = 5.0
    if side == 'LONG':
        roe = ((mark - entry) / entry) * lev * 100.0
    else:
        roe = ((entry - mark) / entry) * lev * 100.0
    print(f"Trade #{row_dict.get('id')}: {sym} {side} ({row_dict.get('timeframe')}) @ {entry} | Mark: {mark} | ROE: {roe:+.2f}%")
conn.close()




