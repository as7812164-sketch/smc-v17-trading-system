with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    \"\"\"Returns complete real-time Futures positions matching the Bitget UI format (1H & 4H concurrent).\"\"\"
    tickers = await get_live_tickers()
    open_trades_raw = get_open_paper_trades(timeframe=timeframe)

    positions = []
    total_unrealized_pnl = 0.0
    total_margin = 0.0
    now_ms = int(time.time() * 1000)

    for ot in open_trades_raw:
        trade_id = ot["id"]
        sym = ot.get("symbol", "")
        coin_name = sym.replace("USDT", "")"""

replacement = """    \"\"\"Returns complete real-time Futures positions matching the Bitget UI format (1H & 4H concurrent).\"\"\"
    tickers = await get_live_tickers()
    open_trades_raw = get_open_paper_trades(timeframe=timeframe)

    # 1:1 Live Exchange Parity Guard: If Bitget auto-trading is active, verify filled status on exchange
    active_exchange_symbols = None
    try:
        from engine.bitget_trader import bitget_trader
        if bitget_trader.is_configured() and bitget_trader.is_auto_trade_enabled():
            res = bitget_trader.exchange.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES'})
            active_exchange_symbols = set()
            for p in res.get('data', []):
                if float(p.get('total', 0) or 0) > 0:
                    clean = p.get('symbol', '').replace('/', '').replace(':USDT', '').upper()
                    active_exchange_symbols.add(clean)
    except Exception:
        active_exchange_symbols = None

    positions = []
    total_unrealized_pnl = 0.0
    total_margin = 0.0
    now_ms = int(time.time() * 1000)

    for ot in open_trades_raw:
        trade_id = ot["id"]
        sym = ot.get("symbol", "")
        if active_exchange_symbols is not None and sym not in active_exchange_symbols:
            continue
        coin_name = sym.replace("USDT", "")"""

target_norm = target.replace('\r\n', '\n')
content_norm = content.replace('\r\n', '\n')

if target_norm in content_norm:
    content_norm = content_norm.replace(target_norm, replacement.replace('\r\n', '\n'))
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content_norm)
    print("SUCCESS: Updated app.py with 1:1 Live Exchange Parity Guard!")
else:
    print("Target not found.")
