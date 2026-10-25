from engine.binance_trader import binance_trader
if not binance_trader.exchange: binance_trader._init_exchange()

for sym in ['NEARUSDT', 'AVAXUSDT']:
    print(f"=== Cleaning algo orders for {sym} ===")
    try:
        binance_trader.exchange.fapiPrivateDeleteAlgoOpenOrders({'symbol': sym})
        print(f"Cancelled all algo orders for {sym}.")
    except Exception as e:
        print(f"Error cancelling algo orders for {sym}:", e)

# Now arm exactly 1 SL order for NEAR and 1 for AVAX
# NEAR: 50 contracts LONG, close side sell, SL 4.721
try:
    res = binance_trader.exchange.create_order(
        symbol='NEAR/USDT:USDT',
        type='STOP_MARKET',
        side='sell',
        amount=50,
        params={'stopPrice': 4.721, 'positionSide': 'LONG'}
    )
    print("Clean armed NEAR SL:", res.get('id'))
except Exception as e:
    print("Error arming NEAR SL:", e)

# AVAX: 23 contracts SHORT, close side buy, SL 11.262
try:
    res = binance_trader.exchange.create_order(
        symbol='AVAX/USDT:USDT',
        type='STOP_MARKET',
        side='buy',
        amount=23,
        params={'stopPrice': 11.262, 'positionSide': 'SHORT'}
    )
    print("Clean armed AVAX SL:", res.get('id'))
except Exception as e:
    print("Error arming AVAX SL:", e)
