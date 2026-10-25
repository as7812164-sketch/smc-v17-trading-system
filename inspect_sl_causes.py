import json
from datetime import datetime, timezone, timedelta
ist = timezone(timedelta(hours=5, minutes=30))

with open('database/live_render_trades.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for t in data.get('trades', []):
    en_dt = datetime.fromtimestamp(t['entry_time']/1000, ist).strftime('%Y-%m-%d %H:%M:%S IST') if t.get('entry_time') else 'N/A'
    ex_dt = datetime.fromtimestamp(t['exit_time']/1000, ist).strftime('%Y-%m-%d %H:%M:%S IST') if t.get('exit_time') else 'N/A'
    symbol = t['symbol']
    side = t['side']
    status = t['status']
    entry = t['entry_price']
    sl = t.get('sl_price')
    exit_p = t['exit_price']
    pnl = t['pnl_usdt']
    roe = t.get('roi_pct') or t.get('pnl_pct')
    mfe = t.get('mfe_pct')
    mae = t.get('mae_pct')
    sentry = t.get('sentry_reasons', '')
    autopsy = t.get('autopsy_diagnosis', '')
    
    print(f"=== {symbol} {side} | {status} ===")
    print(f"Entry: {entry} at {en_dt}")
    print(f"Exit:  {exit_p} (SL: {sl}) at {ex_dt}")
    print(f"PnL:   ${pnl} ({roe}%) | MFE: +{mfe}% | MAE: -{mae}%")
    sentry = sentry.encode('ascii', 'ignore').decode('ascii')
    autopsy = autopsy.encode('ascii', 'ignore').decode('ascii')
    print(f"Sentry: {sentry}")
    if autopsy:
        print(f"Autopsy: {autopsy}")
    print("-" * 65)

