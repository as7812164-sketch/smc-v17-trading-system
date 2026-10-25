import urllib.request
import json

req = urllib.request.Request('https://smc-ai-agent.onrender.com/api/paper/trades?limit=5', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())
print('Total trades returned:', len(data.get('trades', [])))
for t in data.get('trades', [])[:5]:
    print(f"Trade #{t.get('id')}: {t.get('symbol')} {t.get('side')} | Status: {t.get('status')} | PnL: ${t.get('pnl_usdt')} | ROI: {t.get('pnl_pct')}% | Section: {t.get('account_id')}")
