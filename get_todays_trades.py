import urllib.request
import json

url = "https://smc-ai-agent.onrender.com/api/paper/trades"
try:
    data = json.loads(urllib.request.urlopen(url).read())
    trades = data.get("trades", [])
    print(f"Total trades returned: {len(trades)}")
    print("\n--- ALL TRADES TODAY (2026-09-28) ---")
    for t in trades:
        ts = str(t.get("timestamp_ist") or t.get("timestamp") or "")
        if "2026-09-28" in ts:
            print(f"ID: {t.get('id')} | {t.get('symbol')} ({t.get('timeframe')}) | Side: {t.get('side')} | Result: {t.get('result')} | PnL: ${t.get('pnl_usdt')} ({t.get('roi_pct')}%) | Entry: {t.get('entry_price')} | Exit: {t.get('exit_price')} | MAE: {t.get('mae_pct')}% | Sentry: {t.get('sentry_reasons')} | Time: {ts}")
except Exception as e:
    print(f"Error: {e}")
