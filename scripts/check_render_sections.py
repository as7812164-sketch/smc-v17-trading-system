import urllib.request
import json

url = "https://smc-ai-agent.onrender.com/api/deca/sections"
with urllib.request.urlopen(url, timeout=10) as resp:
    data = json.loads(resp.read().decode())
    sections = data.get("sections", [])
    print(f"Total live sections on Render: {len(sections)}")
    for s in sections:
        print(f"ID {s['id']}: {s['name']} | Initial: ${s['initial_balance']} | Balance: ${s['balance']} | Status: {s['status']}")
