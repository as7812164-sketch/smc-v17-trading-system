with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """@app.get("/api/futures/open_orders")
async def get_futures_open_orders():"""

replacement = """@app.get("/api/bitget/open_orders")
@app.get("/api/trade/open_orders")
@app.get("/api/futures/open_orders")
async def get_futures_open_orders():
    \"\"\"Returns real live open limit orders currently resting in Bitget orderbook.\"\"\"
    orders = []
    try:
        from engine.bitget_trader import bitget_trader
        if bitget_trader.is_configured():
            raw_orders = bitget_trader.exchange.fetch_open_orders()
            tickers = await get_live_tickers()
            for o in raw_orders:
                raw_sym = o.get('symbol', '')
                sym = raw_sym.replace('/', '').replace(':USDT', '').upper()
                side = str(o.get('side', 'buy')).upper()
                lim_p = float(o.get('price') or 0.0)
                amount = float(o.get('amount') or 0.0)
                cur_p = float(tickers.get(sym, lim_p) or lim_p)
                dist_pct = (abs(cur_p - lim_p) / cur_p * 100.0) if cur_p > 0 else 0.0
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
            orders.sort(key=lambda x: x["distance_pct"])
            return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.warning(f"Error fetching Bitget open orders: {e}")"""

if target in content:
    content = content.replace(target, replacement)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Added /api/bitget/open_orders to app.py!")
else:
    target_norm = target.replace('\r\n', '\n')
    content_norm = content.replace('\r\n', '\n')
    if target_norm in content_norm:
        content_norm = content_norm.replace(target_norm, replacement.replace('\r\n', '\n'))
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content_norm)
        print("SUCCESS (norm): Added /api/bitget/open_orders to app.py!")
    else:
        print("FAILED to find target in app.py")
