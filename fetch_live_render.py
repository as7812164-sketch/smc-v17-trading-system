import urllib.request
import json
import os

url = 'https://smc-ai-agent.onrender.com/api/paper/trades'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode('utf-8'))

os.makedirs('database', exist_ok=True)
with open('database/live_render_trades.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

from datetime import datetime, timezone, timedelta

ist = timezone(timedelta(hours=5, minutes=30))
print(f"Total live trades fetched: {len(data.get('trades', []))}\n")
for i, t in enumerate(data.get('trades', []), 1):
    symbol = t.get('symbol')
    side = t.get('side')
    entry = t.get('entry_price')
    exit_p = t.get('exit_price')
    pnl = t.get('pnl_usdt')
    roi = t.get('roi_pct')
    status = t.get('status')
    mfe = t.get('mfe_pct')
    mae = t.get('mae_pct')
    en_dt = datetime.fromtimestamp(t['entry_time']/1000, ist).strftime('%Y-%m-%d %H:%M:%S IST') if t.get('entry_time') else 'N/A'
    ex_dt = datetime.fromtimestamp(t['exit_time']/1000, ist).strftime('%Y-%m-%d %H:%M:%S IST') if t.get('exit_time') else 'N/A'
    sentry = t.get('sentry_reasons', '').encode('ascii', 'ignore').decode('ascii')
    autopsy = t.get('autopsy_diagnosis', '').encode('ascii', 'ignore').decode('ascii')
    print(f"Trade #{i}: {symbol} | {side} | Result: {status} | PnL: ${pnl} ({roi}%)")
    print(f"   Entry: {entry} ({en_dt})")
    print(f"   Exit:  {exit_p} ({ex_dt})")
    print(f"   MFE (Peak Profit): +{mfe}% | MAE (Max Drawdown): -{mae}%")
    print(f"   Sentry: {sentry}")
    if autopsy:
        print(f"   Autopsy: {autopsy}")
    print("-" * 75)


