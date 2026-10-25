"""
RENDER 24/7 KEEPALIVE PINGER DAEMON
===================================
Prevents Render free tier from sleeping (cold start).
Pings both smc-ai-agent and nexuspro-terminal every 3 minutes.
"""

import time
import urllib.request
import ssl
from datetime import datetime, timezone
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

URLS = [
    "https://nexuspro-terminal.onrender.com/api/status",
    "https://smc-ai-agent.onrender.com/api/status"
]

def ping_once():
    ctx = ssl._create_unverified_context()
    headers = {"User-Agent": "RenderKeepaliveSentinel/1.0"}
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    for url in URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                print(f"[{now_str}] PING OK: {url} -> HTTP {resp.status}")
        except Exception as e:
            print(f"[{now_str}] PING WARN: {url} -> {e}")

def main():
    print("=" * 80)
    print("🚀 RENDER 24/7 KEEPALIVE PINGER STARTED")
    print("Keeping Render Web Services Awake (Zero Sleep / Zero Cold-Start)")
    print("=" * 80)
    
    while True:
        ping_once()
        # Ping every 180 seconds (3 minutes) — Render sleeps after 900 seconds (15 mins)
        time.sleep(180)

if __name__ == "__main__":
    main()
