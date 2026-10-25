import sys
import os

sys.path.append(os.getcwd())
from engine.bitget_trader import bitget_trader

print("Checking Bitget Exchange live positions...")
if not bitget_trader.is_configured():
    print("Bitget credentials not configured.")
else:
    bal = bitget_trader.fetch_futures_balance()
    print(f"Bitget Connected: {bal.get('connected')}")
    print(f"Total Balance: ${bal.get('total_usdt')} USDT")
    print(f"Free Balance: ${bal.get('free_usdt')} USDT")
    print(f"Used Margin: ${bal.get('used_usdt')} USDT")

    # Fetch all open positions on Bitget
    try:
        res = bitget_trader.exchange.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES'})
        positions = []
        if res and 'data' in res:
            for p in res['data']:
                contracts = float(p.get('total', 0) or 0)
                if contracts > 0:
                    positions.append(p)
        print(f"\nLive Active Positions on Bitget: {len(positions)}")
        for p in positions:
            print(f"Symbol: {p.get('symbol')} | Side: {p.get('holdSide')} | Contracts: {p.get('total')} | Entry Price: {p.get('openPriceAvg')} | Mark Price: {p.get('markPrice')} | Margin: ${p.get('margin')} | Unrealized PnL: {p.get('unrealizedPL')}")
    except Exception as e:
        print(f"Error fetching Bitget positions: {e}")
