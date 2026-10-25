import urllib.request
import json
import time

url = "https://smc-ai-agent.onrender.com/api/deca/summary"
for i in range(5):
    try:
        print(f"Attempt {i+1} connecting to {url}...")
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            print(f"SUCCESS! Render is LIVE.")
            print(f"Starting Capital: ${data.get('starting_capital')}")
            print(f"Total Balance: ${data.get('total_balance')}")
            print(f"Mode: {data.get('mode')}")
            print(f"Used Margin: ${data.get('used_margin')}")
            break
    except Exception as e:
        print(f"Waiting for Render container to finish boot: {e}")
        time.sleep(5)
