import urllib.request
import json

def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

history = fetch_url("https://smc-ai-agent.onrender.com/api/trade/history")
with open("render_history_dump.json", "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2)

pos = fetch_url("https://smc-ai-agent.onrender.com/api/trade/positions")
with open("render_pos_dump.json", "w", encoding="utf-8") as f:
    json.dump(pos, f, indent=2)

print("Saved dumps to render_history_dump.json and render_pos_dump.json")
