import sqlite3, urllib.request, json

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("SELECT id, symbol, side, entry_price, status, timeframe, pnl_usdt, be_lock_pct, trail_lock_pct, highest_price, lowest_price FROM paper_trades WHERE status='OPEN'")
open_trades = c.fetchall()
print("OPEN TRADES:")
for t in open_trades:
    print(" ", t)

c.execute("SELECT id, symbol, side, entry_price, exit_price, status, pnl_usdt, exit_time FROM paper_trades ORDER BY id DESC LIMIT 5")
recent_trades = c.fetchall()
print("\nRECENT TRADES:")
for t in recent_trades:
    print(" ", t)

conn.close()

res = urllib.request.urlopen('https://fapi.binance.com/fapi/v1/ticker/price').read()
data = json.loads(res)
symbols = {'BTCUSDT', 'ALGOUSDT', 'FETUSDT', 'ADAUSDT'}
prices = {item['symbol']: float(item['price']) for item in data if item['symbol'] in symbols}
print("\nLIVE PRICES:", prices)
