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

print("Monitoring Render production for commit deployment & trade healing...")
url_trades = 'https://smc-ai-agent.onrender.com/api/paper/trades?limit=5'
url_status = 'https://smc-ai-agent.onrender.com/api/status'

for i in range(12):
    try:
        req = urllib.request.Request(url_trades, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = json.loads(r.read().decode())
            for t in data.get('trades', []):
                if t.get('id') == 535:
                    status = t.get('status')
                    pnl = t.get('realized_pnl')
                    print(f"[{i+1}/12] Trade 535: Status={status} | PnL=${pnl}")
                    if 'HEALED' in str(status) or pnl == 0.0:
                        print("\n🎉 CONFIRMED: Render has loaded the healed vault state!")
                        # Check Section 1 Balance
                        req_stat = urllib.request.Request(url_status, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req_stat, context=ctx, timeout=10) as r_s:
                            s_data = json.loads(r_s.read().decode())
                            pt = s_data.get('paper_trading', {})
                            print(f"Section 1 Current Balance: ${pt.get('current_balance')} USDT (P&L: ${pt.get('total_pnl')})")
                            print(f"Section 1 Win Rate: {pt.get('win_rate')}% ({pt.get('win_count')}W / {pt.get('loss_count')}L)")
                        sys.exit(0)
    except Exception as e:
        print(f"[{i+1}/12] Deploy in progress: {e}")
    time.sleep(10)

print("Timeout waiting for deploy. Will check again.")
