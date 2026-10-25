import os, json, glob, datetime
from engine.smc2_experimental import SMC2ApexMatrixDetector

detector = SMC2ApexMatrixDetector(
    min_displacement_pct=0.045,
    tp_roe_pct=12.20,
    sl_roe_pct=12.00,
    leverage=5.0
)

for sym in ['SOLUSDT', 'ETHUSDT', 'BTCUSDT', 'AVAXUSDT', 'NEARUSDT']:
    fn = f'historical_data/{sym}_4h.json'
    if not os.path.exists(fn): 
        continue
    with open(fn, 'r') as fp:
        raw = json.load(fp)
    formatted = [
        {
            'time': c.get('time', c.get('open_time')),
            'open': float(c['open']),
            'high': float(c['high']),
            'low': float(c['low']),
            'close': float(c['close']),
            'volume': float(c.get('volume', 0))
        } for c in raw
    ]
    setups = detector.detect_setups(sym, formatted, interval='4h', full_scan=True)
    for s in setups:
        if s['side'] == 'LONG':
            e_idx = s['tap_bar_idx']
            tp = s['tp_price']
            sl = s['sl_price']
            for k in range(e_idx + 1, min(e_idx + 25, len(formatted))):
                if formatted[k]['high'] >= tp:
                    t1 = datetime.datetime.fromtimestamp(s['tap_time']/1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
                    t2 = datetime.datetime.fromtimestamp(formatted[k]['time']/1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
                    print(f"WINNER: {sym} 4H LONG")
                    print(f"OB Range: {s['ob_low']} to {s['ob_high']}")
                    print(f"Entry (50% MT): {s['entry_price']}")
                    print(f"TP Price: {tp} (+12.20% ROE)")
                    print(f"SL Price: {sl} (-12.00% ROE)")
                    print(f"Displacement: {s['displacement_pct']}%")
                    print(f"Entry Candle Time: {t1}")
                    print(f"Exit (TP Hit) Time: {t2}")
                    print(f"Duration: {k - e_idx} bars ({(k - e_idx)*4} hours)")
                    
                    # Also collect the surrounding candles
                    candles_slice = formatted[max(0, e_idx - 14):min(len(formatted), k + 6)]
                    data_to_save = {
                        'symbol': sym,
                        'timeframe': '4h',
                        'side': 'LONG',
                        'setup': s,
                        'entry_time_str': t1,
                        'exit_time_str': t2,
                        'exit_bar': formatted[k],
                        'candles': candles_slice
                    }
                    with open('verify_trade.json', 'w') as out_f:
                        json.dump(data_to_save, out_f, indent=2)
                    print("Saved verify_trade.json successfully!")
                    exit(0)
                elif formatted[k]['low'] <= sl:
                    break
