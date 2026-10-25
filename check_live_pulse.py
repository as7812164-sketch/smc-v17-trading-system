import sqlite3
import requests

try:
    r = requests.get('https://fapi.binance.com/fapi/v1/ticker/price?symbol=BTCUSDT', timeout=5)
    btc_price = float(r.json()['price'])
except Exception as e:
    btc_price = 84795.0

conn = sqlite3.connect('database/smc_v17.db')
conn.row_factory = sqlite3.Row
trades = conn.execute("SELECT * FROM paper_trades WHERE status = 'OPEN'").fetchall()

print(f"BTC PRICE: {btc_price:.2f}")
print(f"OPEN TRADES: {len(trades)}")
for t in trades:
    sym = t['symbol']
    try:
        pr = float(requests.get(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={sym}", timeout=3).json()['price'])
    except:
        pr = t['entry_price']
    entry = t['entry_price']
    side = t['side']
    roe = ((pr - entry)/entry if side in ('BUY','LONG') else (entry - pr)/entry) * 5.0 * 100.0
    print(f"Trade #{t['id']}: {sym} {side} ({t['timeframe']}) Entry: {entry} Mark: {pr} ROE: {roe:+.2f}% Account: {t['account_id']} TP: {t['tp_price']} SL: {t['sl_price']}")

conn.close()
