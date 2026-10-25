import urllib.request
import json
import sys

base_url = 'https://smc-ai-agent.onrender.com'
print("--- FETCHING POSITIONS ---")
try:
    req = urllib.request.Request(f'{base_url}/api/paper/positions', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    pos = json.loads(resp.read().decode())
    print('OPEN POSITIONS:', json.dumps(pos, indent=2))
except Exception as e:
    print('POSITIONS ERROR:', e)

print("\n--- FETCHING RECENT TRADES ---")
try:
    req = urllib.request.Request(f'{base_url}/api/paper/trades?limit=20', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    trades = json.loads(resp.read().decode())
    if isinstance(trades, list):
        print(f"Total trades returned: {len(trades)}")
        for t in trades[:15]:
            print(f"Trade #{t.get('id')}: {t.get('symbol')} {t.get('side')} entry={t.get('entry_price')} exit={t.get('exit_price')} pnl={t.get('realized_pnl')} status={t.get('status')} time={t.get('timestamp')}")
    else:
        print("Trades response:", trades)
except Exception as e:
    print('TRADES ERROR:', e)

print("\n--- FETCHING ACCOUNT STATUS ---")
try:
    req = urllib.request.Request(f'{base_url}/api/paper/account', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    acc = json.loads(resp.read().decode())
    print('ACCOUNT:', json.dumps(acc, indent=2))
except Exception as e:
    print('ACCOUNT ERROR:', e)
