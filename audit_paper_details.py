import sqlite3
import glob
import os
import json
import urllib.request

print("--- Live Ticker & Open Trades ---")
req = urllib.request.Request('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', headers={'User-Agent': 'Mozilla/5.0'})
btc = float(json.loads(urllib.request.urlopen(req, timeout=5).read())['price'])
print(f"King BTC: ${btc:,.2f}")

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("PRAGMA table_info(paper_trades)")
cols = [col[1] for col in c.fetchall()]

c.execute("SELECT * FROM paper_trades WHERE status='OPEN'")
open_rows = c.fetchall()
print(f"Open Trades: {len(open_rows)}")
for r in open_rows:
    rd = dict(zip(cols, r))
    sym = rd['symbol']
    req = urllib.request.Request(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', headers={'User-Agent': 'Mozilla/5.0'})
    mark = float(json.loads(urllib.request.urlopen(req, timeout=5).read())['price'])
    entry = float(rd['entry_price'])
    side = rd['side']
    lev = 5.0
    roe = ((mark - entry)/entry)*lev*100.0 if side == 'LONG' else ((entry - mark)/entry)*lev*100.0
    print(f"  Trade #{rd['id']}: {sym} {side} ({rd['timeframe']}) @ {entry} | Mark: {mark} | TP: {rd['tp_price']} | SL: {rd['sl_price']} | Live ROE: {roe:+.2f}%")

print("\n--- All Trades in database/smc_v17.db ---")
c.execute("SELECT id, symbol, side, timeframe, entry_price, exit_price, pnl_usdt, pnl_pct, status, duration_str, exchange, account_id, mode FROM paper_trades ORDER BY id ASC")
all_trades = c.fetchall()
for t in all_trades:
    print(t)

conn.close()
