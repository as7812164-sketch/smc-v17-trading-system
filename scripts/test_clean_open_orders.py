import sys, os
sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader
import json

def get_open_orders():
    orders = []
    if bitget_trader.exchange:
        try:
            raw_orders = bitget_trader.exchange.fetch_open_orders()
            # Fetch tickers to calculate distance %
            tickers = bitget_trader.exchange.fetch_tickers()
            for o in raw_orders:
                raw_sym = o.get('symbol', '')
                sym = raw_sym.replace('/', '').replace(':USDT', '').upper()
                side = str(o.get('side', 'buy')).upper()
                lim_p = float(o.get('price') or 0.0)
                amount = float(o.get('amount') or 0.0)
                
                t = tickers.get(raw_sym, {})
                cur_p = float(t.get('last') or t.get('close') or lim_p)
                dist_pct = abs(cur_p - lim_p) / cur_p * 100.0 if cur_p > 0 else 0.0
                
                orders.append({
                    "id": o.get('id'),
                    "symbol": sym,
                    "side": "LONG" if side == "BUY" else "SHORT",
                    "badge": "L" if side == "BUY" else "S",
                    "order_type": "Limit (50% MT)",
                    "price": lim_p,
                    "current_price": cur_p,
                    "distance_pct": round(dist_pct, 2),
                    "amount": amount,
                    "status": "WAITING_FILL",
                    "leverage": "5x Isolated",
                    "timestamp": o.get('timestamp')
                })
        except Exception as e:
            print("Error:", e)
    return {"orders": orders, "count": len(orders)}

res = get_open_orders()
print("Result:")
print(json.dumps(res, indent=2))
