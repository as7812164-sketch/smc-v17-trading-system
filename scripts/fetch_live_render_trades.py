import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

base_url = "https://smc-ai-agent.onrender.com"

endpoints = [
    "/api/status",
    "/api/paper/trades",
    "/api/paper/positions",
    "/api/paper/sections"
]

for ep in endpoints:
    url = base_url + ep
    print("=" * 60)
    print(f"Fetching: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if ep == "/api/paper/trades":
                print(f"Trades Count: {len(data) if isinstance(data, list) else data}")
                if isinstance(data, list) and len(data) > 0:
                    for t in data[:10]:
                        print(f"Trade: {t.get('id')} | {t.get('symbol')} | {t.get('side')} | {t.get('status')} | PnL: ${t.get('pnl_usdt')} | Exit: {t.get('exit_reason')} | Time: {t.get('entry_time')}")
                else:
                    print("No trades found in paper_trades on Render.")
            elif ep == "/api/paper/positions":
                print(f"Open Positions: {data}")
            elif ep == "/api/paper/sections":
                print(f"Sections Data: {data}")
            else:
                print(f"Status Data: {json.dumps(data, indent=2)[:300]}...")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
