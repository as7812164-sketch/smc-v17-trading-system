import sqlite3
import datetime
import os
import sys

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("""
    SELECT id, symbol, side, timeframe, entry_price, status, account_id, entry_time, pnl_usdt, roi_pct, order_type
    FROM paper_trades 
    WHERE symbol IN ('ONEUSDT', 'UNIUSDT') OR status = 'OPEN'
    ORDER BY id DESC
""")
print("=== DATABASE TRADES ===")
for r in c.fetchall():
    t_str = datetime.datetime.fromtimestamp(r[7]/1000.0) if r[7] else "N/A"
    print(r[0], r[1], r[2], r[3], "Entry:", r[4], "Status:", r[5], "Sec:", r[6], "Time:", t_str, "OrderType:", r[10])

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

print("\n=== BITGET LIVE STATUS ===")
if bitget_trader.is_configured():
    bal = bitget_trader.fetch_futures_balance()
    print("Balance:", bal)
    
    # 1. Check Positions
    try:
        res = bitget_trader.exchange.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES'})
        pos_list = [p for p in res.get('data', []) if float(p.get('total', 0) or 0) > 0]
        print(f"\nLive Bitget Open Positions ({len(pos_list)}):")
        for p in pos_list:
            print(f"- {p.get('symbol')} {p.get('holdSide')} | Total: {p.get('total')} | OpenAvg: {p.get('openPriceAvg')} | Mark: {p.get('markPrice')} | PnL: {p.get('unrealizedPL')}")
    except Exception as e:
        print("Error fetching Bitget positions:", e)

    # 2. Check Open Orders / Plan Orders (Orders(3) from the screenshot!)
    try:
        ord_res = bitget_trader.exchange.privateMixGetV2MixOrderCurrentOrder({'productType': 'USDT-FUTURES'})
        orders = ord_res.get('data', {}).get('entrustedList', [])
        print(f"\nLive Bitget Open Regular Orders ({len(orders)}):")
        for o in orders:
            print(f"- {o.get('symbol')} {o.get('side')} {o.get('orderType')} | Price: {o.get('price')} | Size: {o.get('size')} | State: {o.get('state')}")
    except Exception as e:
        print("Error fetching Bitget open orders:", e)

    try:
        plan_res = bitget_trader.exchange.privateMixGetV2MixOrderCurrentPlanOrder({'productType': 'USDT-FUTURES'})
        plans = plan_res.get('data', {}).get('entrustedList', [])
        print(f"\nLive Bitget Open Plan/Trigger Orders ({len(plans)}):")
        for p in plans:
            print(f"- {p.get('symbol')} {p.get('planType')} | TriggerPrice: {p.get('triggerPrice')} | ExecutePrice: {p.get('executePrice')} | Size: {p.get('size')}")
    except Exception as e:
        print("Error fetching Bitget plan orders:", e)
else:
    print("Bitget not configured.")
