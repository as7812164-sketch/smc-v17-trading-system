import sqlite3
import datetime
import sys
import os

# 1. Check database for WLDUSDT
conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("""
    SELECT id, symbol, side, timeframe, entry_price, status, account_id, entry_time, position_size_usdt, sl_price, tp_price, autopsy_diagnosis
    FROM paper_trades 
    WHERE symbol LIKE '%WLD%'
    ORDER BY id DESC
    LIMIT 5
""")
print("=== DATABASE WLD TRADES ===")
rows = c.fetchall()
for r in rows:
    t_str = datetime.datetime.fromtimestamp(r[7]/1000.0) if r[7] else "N/A"
    print(f"ID #{r[0]} | {r[1]} {r[2]} ({r[3]}) | Entry: {r[4]} | Status: {r[5]} | Sec: {r[6]} | Time: {t_str} | Size: ${r[8]} | TP: {r[10]} | SL: {r[9]} | Diag: {r[11]}")

# 2. Check all open trades in DB right now
c.execute("SELECT id, symbol, side, timeframe, entry_price, status, account_id FROM paper_trades WHERE status = 'OPEN'")
print("\n=== ALL OPEN TRADES IN DATABASE ===")
for r in c.fetchall():
    print(r)

# 3. Check Bitget exchange for WLD market rules and recent orders
sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

print("\n=== BITGET WLD MARKET INSPECTION ===")
if bitget_trader.exchange:
    try:
        markets = bitget_trader.exchange.load_markets()
        wld_symbols = [m for m in markets.keys() if "WLD" in m]
        print("WLD symbols on Bitget:", wld_symbols)
        
        ccxt_wld = bitget_trader.format_symbol_for_bitget("WLDUSDT")
        print("Formatted for Bitget:", ccxt_wld)
        m = markets.get(ccxt_wld)
        if m:
            print("Market Found!")
            print("Limits:", m.get('limits'))
            print("Precision:", m.get('precision'))
            print("Contract Size:", m.get('contractSize'))
        else:
            print("Market NOT found for", ccxt_wld)
    except Exception as e:
        print("Error checking market:", e)

    # 4. Check recent order history on Bitget
    try:
        res = bitget_trader.exchange.privateMixGetV2MixOrderOrdersHistory({'productType': 'USDT-FUTURES', 'limit': '15'})
        hist = res.get('data', {}).get('entrustedList', [])
        print(f"\nRecent Order History on Bitget ({len(hist)}):")
        for h in hist:
            print(f"- {h.get('symbol')} {h.get('side')} {h.get('orderType')} | Price: {h.get('price')} | Size: {h.get('size')} | State: {h.get('state')} | Reason: {h.get('cancelReason', h.get('errCode', ''))}")
    except Exception as e:
        print("Error fetching orders history:", e)
