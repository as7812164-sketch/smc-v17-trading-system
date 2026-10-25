import sys
import os
import sqlite3
import datetime

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

print("=== 1. CHECKING BITGET ORDER HISTORY FOR SNX ===")
if bitget_trader.exchange:
    try:
        res = bitget_trader.exchange.privateMixGetV2MixOrderOrdersHistory({'productType': 'USDT-FUTURES', 'symbol': 'SNXUSDT', 'limit': '5'})
        print("SNX History on Bitget:")
        orders = res.get('data', {}).get('entrustedList', [])
        for o in orders:
            print(f"- OrderId: {o.get('orderId')} | State: {o.get('state')} | Price: {o.get('price')} | Size: {o.get('size')} | Reason: {o.get('cancelReason')}")
        if not orders:
            print("No SNX orders in Bitget history!")
    except Exception as e:
        print("Error checking Bitget history for SNX:", e)

    # Check SNX market rules on Bitget
    try:
        markets = bitget_trader.exchange.load_markets()
        ccxt_snx = bitget_trader.format_symbol_for_bitget("SNXUSDT")
        print(f"\nSNX CCXT Symbol: {ccxt_snx}")
        m = markets.get(ccxt_snx)
        if m:
            print("Market found!")
            print("Limits:", m.get('limits'))
            print("Precision:", m.get('precision'))
        else:
            print("Market NOT FOUND for", ccxt_snx)
            print("Matches for SNX in markets:", [k for k in markets if 'SNX' in k])
    except Exception as e:
        print("Error checking market rules for SNX:", e)

print("\n=== 2. CHECKING DATABASE FOR SNX ===")
conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("SELECT id, symbol, side, timeframe, entry_price, status, account_id, entry_time FROM paper_trades WHERE symbol LIKE '%SNX%' ORDER BY id DESC LIMIT 5")
for r in c.fetchall():
    t_str = datetime.datetime.fromtimestamp(r[7]/1000.0) if r[7] else "N/A"
    print(r[0], r[1], r[2], r[3], "Entry:", r[4], "Status:", r[5], "Sec:", r[6], "Time:", t_str)

# 3. Check Render live paper positions
import urllib.request, json
try:
    req = urllib.request.Request('https://smc-ai-agent.onrender.com/api/paper/positions', headers={'User-Agent': 'Mozilla/5.0'})
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    print("\n=== 3. RENDER ACTIVE POSITIONS ===")
    for p in res.get('positions', []):
        print(p.get('id'), p.get('symbol'), p.get('side'), p.get('entry_price'), 'Sec:', p.get('account_id'))
except Exception as e:
    print("Render error:", e)
