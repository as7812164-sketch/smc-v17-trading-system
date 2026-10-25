import urllib.request
import json
import ssl
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8')

ctx = ssl._create_unverified_context()
url = 'https://smc-ai-agent.onrender.com/api/admin/heal-trade'

print("Waiting for Render deployment to complete and calling heal-trade...")
for i in range(15):
    try:
        req = urllib.request.Request(url, data=b'{}', headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='POST')
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            res = json.loads(r.read().decode())
            print(f"Attempt {i+1}: Success! Response: {res}")
            
            # Now verify /api/status
            stat_url = 'https://smc-ai-agent.onrender.com/api/status'
            with urllib.request.urlopen(urllib.request.Request(stat_url, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx, timeout=10) as s_r:
                stat = json.loads(s_r.read().decode())
                pt = stat.get('paper_trading', {})
                print(f"Section 1 Bal: ${pt.get('current_balance')} | Losses: {pt.get('loss_count')} | Wins: {pt.get('win_count')} | WR: {pt.get('win_rate')}%")
            sys.exit(0)
    except Exception as e:
        print(f"Attempt {i+1}: Waiting for deploy... ({e})")
        time.sleep(12)

print("Deploy monitoring timed out.")
