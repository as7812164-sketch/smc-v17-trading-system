import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    url = "https://smc-ai-agent.onrender.com/api/hermes/apex/setups"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode())
    
    setups = res.get("setups", [])
    print(f"Total Qualified Setups: {len(setups)}")
    for s in setups:
        print(f"• SETUP: {s.get('symbol')} {s.get('side')} [{s.get('interval')}] | Entry (50% MT): ${s.get('entry_price')} | TP: ${s.get('tp_price')} | Soft SL: ${s.get('soft_sl_price')}")

    url2 = "https://smc-ai-agent.onrender.com/api/signals/recent"
    req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req2, timeout=10) as resp:
        res2 = json.loads(resp.read().decode())
    
    radar = res2.get("radar", [])
    print(f"\nTotal Proximity Radar Candidates: {len(radar)}")
    for r in radar:
        print(f"• RADAR: {r.get('symbol')} {r.get('side')} [{r.get('timeframe')}] | Current: ${r.get('current_price')} | MT Target: ${r.get('mean_threshold')} | Dist: {r.get('distance_pct'):.2f}%")

    # Check cooldowns
    url_cd = "https://smc-ai-agent.onrender.com/api/settings"
    # Or check if any coin is in cooldown
except Exception as e:
    print(f"Error: {e}")
