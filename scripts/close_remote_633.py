import urllib.request
import json

url = "https://smc-ai-agent.onrender.com/api/trade/close/633"
req = urllib.request.Request(url, data=b"{}", headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("Response from Render:", resp.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
