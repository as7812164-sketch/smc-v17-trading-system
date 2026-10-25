import urllib.request
import json
import time

url = "https://smc-ai-agent.onrender.com/api/deca/summary"
try:
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print(f"Starting Capital: ${data.get('starting_capital')}")
        print(f"Total Balance: ${data.get('total_balance')}")
        print(f"Mode: {data.get('mode')}")
        print(f"Open Positions: {data.get('used_margin')}")
except Exception as e:
    print(f"Status check notice: {e}")
