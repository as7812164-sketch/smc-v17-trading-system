import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

url_pos = "https://smc-ai-agent.onrender.com/api/futures/positions"
req = urllib.request.Request(url_pos, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        positions = data.get("positions", [])
except Exception as e:
    print("Error fetching positions:", e)
    positions = []

print(f"Closing {len(positions)} open positions on Render Cloud...")
for p in positions:
    close_url = "https://smc-ai-agent.onrender.com/api/futures/close_position"
    payload = json.dumps({"trade_id": p["id"], "symbol": p["symbol"]}).encode("utf-8")
    r_close = urllib.request.Request(close_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(r_close, timeout=10) as res:
            print(f"  • Closed {p['symbol']} (ID: {p['id']})")
    except Exception as e:
        print(f"  • Error closing {p['symbol']}: {e}")

# Reset paper account once more to ensure 0 trades, 0 open positions, 0 balance
reset_url = "https://smc-ai-agent.onrender.com/api/paper_trading/reset"
req_reset = urllib.request.Request(reset_url, data=b"{}", headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req_reset, timeout=10) as res_reset:
        print("Final Cloud Paper Account Reset Complete!")
except Exception as e:
    print("Reset error:", e)

# Final verification
verify_url = "https://smc-ai-agent.onrender.com/api/futures/positions"
req_v = urllib.request.Request(verify_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_v, timeout=10) as r_v:
    d_v = json.loads(r_v.read().decode())
    print(f"Remaining Open Positions on Cloud: {len(d_v.get('positions', []))}")
