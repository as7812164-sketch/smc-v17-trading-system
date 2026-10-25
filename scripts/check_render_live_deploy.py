import urllib.request
import json
import os

token = "rnd_jXv3xL1X2vF1g1o1Y1z1Q1w1e1r" # let's check deploy hook or deploy status
# Check status endpoint
try:
    req = urllib.request.Request("https://smc-ai-agent.onrender.com/api/status", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        print("Live status:", json.loads(resp.read().decode('utf-8')))
except Exception as e:
    print("Error:", e)
