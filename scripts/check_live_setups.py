import urllib.request
import json

req = urllib.request.Request('https://smc-ai-agent.onrender.com/api/hermes/apex/setups', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())
print('Setups detected:', len(data.get('setups', [])))
print('BTC Sentry:', data.get('btc_sentry'))
print('Kill switch active:', data.get('kill_switch_active'))
print('Fresh triggers:', data.get('fresh_triggers'))
for s in data.get('setups', [])[:5]:
    prox = s.get('proximity_pct', 0)
    print(f"Setup: {s.get('symbol')} {s.get('side')} {s.get('interval')} | Triggered: {s.get('is_fresh_trigger')} | Prox: {prox}")
