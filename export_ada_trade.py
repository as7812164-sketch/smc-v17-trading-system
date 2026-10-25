import os, json, datetime
from engine.smc2_experimental import SMC2ApexMatrixDetector

detector = SMC2ApexMatrixDetector(
    min_displacement_pct=0.045,
    tp_roe_pct=12.20,
    sl_roe_pct=12.00,
    leverage=5.0
)

with open('historical_data/ADAUSDT_1h.json') as fp:
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

setups = detector.detect_setups('ADAUSDT', formatted, interval='1h', full_scan=True)
target_setup = None

for s in setups:
    t_str = datetime.datetime.fromtimestamp(s['tap_time'] / 1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    if '2026-09-09' in t_str and s['side'] == 'LONG':
        target_setup = s
        break

if not target_setup:
    # fallback to first long setup
    for s in setups:
        if s['side'] == 'LONG':
            target_setup = s
            break

e_idx = target_setup['tap_bar_idx']
tp = target_setup['tp_price']
sl = target_setup['sl_price']

# Find exit candle
exit_idx = -1
for k in range(e_idx + 1, min(e_idx + 25, len(formatted))):
    if formatted[k]['high'] >= tp:
        exit_idx = k
        break

candles_slice = formatted[max(0, e_idx - 16) : min(len(formatted), (exit_idx if exit_idx > 0 else e_idx + 8) + 5)]

entry_time_str = datetime.datetime.fromtimestamp(target_setup['tap_time'] / 1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
exit_time_str = datetime.datetime.fromtimestamp(formatted[exit_idx]['time'] / 1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if exit_idx > 0 else "N/A"

pkg = {
    'symbol': 'ADAUSDT',
    'timeframe': '1H',
    'side': 'LONG',
    'ob_low': target_setup['ob_low'],
    'ob_high': target_setup['ob_high'],
    'entry_price': target_setup['entry_price'],
    'tp_price': target_setup['tp_price'],
    'sl_price': target_setup['sl_price'],
    'displacement_pct': target_setup['displacement_pct'],
    'entry_time': entry_time_str,
    'exit_time': exit_time_str,
    'bars_duration': exit_idx - e_idx if exit_idx > 0 else 0,
    'candles': candles_slice
}

with open('ada_verification_trade.json', 'w') as out_f:
    json.dump(pkg, out_f, indent=2)

print("SUCCESS: Exported ADA verification package!")
print(f"Symbol: ADAUSDT 1H LONG")
print(f"OB: {pkg['ob_low']} - {pkg['ob_high']} | Entry (50% MT): {pkg['entry_price']}")
print(f"TP Price: {pkg['tp_price']} | SL Price: {pkg['sl_price']}")
print(f"Displacement: {pkg['displacement_pct']}%")
print(f"Entry Time: {pkg['entry_time']} | Exit Time: {pkg['exit_time']}")
