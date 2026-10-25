import sys

with open('engine/hermes30_apex_live.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''            # Real exchange auto-trading execution (Bitget / Binance)
            try:
                from engine.bitget_trader import bitget_trader
                if bitget_trader.is_configured() and bitget_trader.is_auto_trade_enabled():
                    setup_copy = {**setup, "managed_by_hermes": True}
                    if "4h" in timeframe:
                        await bitget_trader.execute_4h_trade(setup_copy)
                    else:
                        await bitget_trader.execute_1h_trade(setup_copy)
                    logger.info(f"\U0001f48e Bitget real trade submitted for {symbol}")
            except Exception as bge:
                logger.error(f"Error executing real Bitget trade: {bge}")'''

replacement = '''            # Real exchange auto-trading execution (Bitget / Binance)
            try:
                from engine.bitget_trader import bitget_trader
                if bitget_trader.is_configured() and bitget_trader.is_auto_trade_enabled():
                    setup_copy = {**setup, "managed_by_hermes": True}
                    if "4h" in timeframe:
                        bg_res = await bitget_trader.execute_4h_trade(setup_copy)
                    else:
                        bg_res = await bitget_trader.execute_1h_trade(setup_copy)
                    
                    if bg_res and not bg_res.get("success"):
                        err_reason = bg_res.get("error") or bg_res.get("reason", "Bitget rejected order")
                        logger.error(f"Bitget execution failed for {symbol}: {err_reason}")
                        from database.db import close_paper_trade
                        close_paper_trade(setup, outcome="EXCHANGE_REJECTED", exit_price=ep)
                        return
                    else:
                        logger.info(f"Bitget real trade submitted for {symbol}")
            except Exception as bge:
                logger.error(f"Error executing real Bitget trade: {bge}")'''

if target in content:
    content = content.replace(target, replacement)
    with open('engine/hermes30_apex_live.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Updated hermes30_apex_live.py with exchange failure auto-reconciliation!")
else:
    print("Target not found directly, checking normalized line endings...")
    target_norm = target.replace('\r\n', '\n')
    content_norm = content.replace('\r\n', '\n')
    if target_norm in content_norm:
        content_norm = content_norm.replace(target_norm, replacement.replace('\r\n', '\n'))
        with open('engine/hermes30_apex_live.py', 'w', encoding='utf-8') as f:
            f.write(content_norm)
        print("SUCCESS (normalized): Updated hermes30_apex_live.py!")
    else:
        print("FAILED to locate target block.")
