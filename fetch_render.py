import urllib.request
import json

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

try:
    req = urllib.request.Request("https://smc-ai-agent.onrender.com/api/paper/positions", headers=headers)
    with urllib.request.urlopen(req) as resp:
        pos = json.loads(resp.read().decode('utf-8'))
        print("=== LIVE POSITIONS ON RENDER ===")
        for p in pos.get("positions", []):
            print(f"{p.get('symbol')} {p.get('side')} Entry: {p.get('entry_price')} Mark: {p.get('mark_price')} PnL: {p.get('unrealized_pnl')} USDT ({p.get('roe_percent')}%)")
except Exception as e:
    print("Error fetching positions:", e)

try:
    req2 = urllib.request.Request("https://smc-ai-agent.onrender.com/api/paper/trades", headers=headers)
    with urllib.request.urlopen(req2) as resp:
        trades = json.loads(resp.read().decode('utf-8'))
        print("\n=== CLOSED TRADES ON RENDER ===")
        for t in trades.get("trades", []):
            print(f"{t.get('symbol')} {t.get('side')} Entry: {t.get('entry_price')} Exit: {t.get('exit_price')} PnL: {t.get('pnl')} USDT ({t.get('roe')}%) Reason: {t.get('exit_reason')}")
except Exception as e:
    print("Error fetching trades:", e)

try:
    req3 = urllib.request.Request("https://smc-ai-agent.onrender.com/api/paper/account", headers=headers)
    with urllib.request.urlopen(req3) as resp:
        acc = json.loads(resp.read().decode('utf-8'))
        print("\n=== ACCOUNT METRICS ON RENDER ===")
        print(acc)
except Exception as e:
    print("Error fetching account:", e)
