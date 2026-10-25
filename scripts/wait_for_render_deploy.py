import urllib.request
import json
import time

url = "https://smc-ai-agent.onrender.com/api/paper/positions"
print("Waiting for Render to deploy commit ee407c2...")

for i in range(12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Linux; Android 14)"})
        with urllib.request.urlopen(req, timeout=10) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                positions = data.get("positions", [])
                if positions and positions[0].get("mmr") == "5.30%":
                    print(f"Deploy LIVE! Detected MMR = 5.30% on {positions[0].get('symbol')}")
                    print("Updated positions data:")
                    for p in positions:
                        print(f"  {p.get('symbol')}: Size={p.get('size_coin')}, MMR={p.get('mmr')}, Liq={p.get('liq_price')}, Margin={p.get('margin_mode')}")
                    break
                else:
                    print(f"Attempt {i+1}: Still on prior build (MMR={positions[0].get('mmr') if positions else 'None'}). Waiting 15s...")
    except Exception as e:
        print(f"Attempt {i+1}: {e}. Waiting 15s...")
    time.sleep(15)
