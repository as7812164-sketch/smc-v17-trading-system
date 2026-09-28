import os
import sys
import base64
import json
import time
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GITHUB_REPO = "as7812164-sketch/smc-ai-agent"
GITHUB_TOKEN = "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"
RENDER_KEY = "rnd_IZZkLTzrsSOolykJGGflmGovOuZN"
RENDER_SRV = "srv-d61q691r0fns73f4p720"

FILES_TO_SYNC = [
    "config.py",
    "requirements.txt",
    "engine/chart_image_generator.py",
    "engine/bitget_trader.py",
    "engine/binance_trader.py",
    "engine/order_flow.py",
    "engine/trade_journal.py",
    "alerts/telegram_service.py",
    "database/db.py",
    "scanner.py",
    "static/index.html",
    "static/positions.html",
    "static/compounding.html",
    "static/brain.html",
    "static/signals.html",
    "static/settings.html",
    "static/style.css",
    "static/app.js",
    "ai/smart_money_analyzer.py",
    "ai/gemini_analyst.py",
    "ai/mike_agent_hub.py",
    "ai/self_improving_engine.py",
    "ai/agent_knowledge_base.json",
    "app.py",
    "feed/binance_feed.py",
    "engine/smc_v17.py",
    "trade_journal_ledger.csv",
    "database/smc_v17.db",
    "database/mongo_client.py",
    "database/cloud_vault.py",
    "engine/hermes2_apex_live.py",
    "ai/hermes_agent.py",
    "ai/hermes_knowledge_base.json",
    "engine/dual_timeframe_sniper.py",
    "docs/PRD.md",
    "docs/ARCHITECTURE.md",
    "docs/RULES.md",
    "docs/DESIGN.md",
    "docs/TASKS.md",
    "docs/MEMORY.md",
    "SMC_V17_TradingView_Indicator.pine",
    "SYSTEM_LEDGER_AND_RECOVERY_GUIDE.md"
]

def update_github_file(rel_path: str):
    local_path = os.path.join(os.path.dirname(__file__), rel_path)
    if not os.path.exists(local_path):
        local_path = os.path.join(os.getcwd(), rel_path)
        
    with open(local_path, "rb") as f:
        content_bytes = f.read()
    b64_content = base64.b64encode(content_bytes).decode("utf-8")
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{rel_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": "Antigravity-Agent",
        "Accept": "application/vnd.github.v3+json"
    }
    
    for attempt in range(4):
        try:
            # 1. Get current SHA
            req = urllib.request.Request(url, headers=headers)
            sha = None
            try:
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode())
                    sha = data.get("sha")
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise e
                    
            payload = {
                "message": f"Deploy: HERMES 2.0 APEX 24/7 Live Streaming Forward-Test Engine ({rel_path})",
                "content": b64_content
            }
            if sha:
                payload["sha"] = sha
                
            req_put = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="PUT"
            )
            with urllib.request.urlopen(req_put, timeout=15) as resp:
                res = json.loads(resp.read().decode())
                print(f"✓ GitHub Synced: {rel_path} (Commit: {res['commit']['sha'][:7]})")
                return True
        except Exception as e:
            if attempt < 3:
                time.sleep(2)
            else:
                print(f"❌ Failed to sync {rel_path}: {e}")
                return False

def trigger_render_deploy():
    print("\n🚀 Triggering Render Cloud Deployment...")
    url = f"https://api.render.com/v1/services/{RENDER_SRV}/deploys"
    headers = {
        "Authorization": f"Bearer {RENDER_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode().strip()
            deploy_id = None
            if content:
                try:
                    data = json.loads(content)
                    deploy_id = data.get("id")
                except Exception:
                    pass
            print(f"✓ Render Deploy Initiated! Status: {resp.status}")
            return deploy_id or "latest"
    except Exception as e:
        print(f"❌ Deploy error: {e}")
        return None

def wait_for_render_deploy(deploy_id: str):
    print("⏳ Waiting for cloud container to build and activate...")
    headers = {
        "Authorization": f"Bearer {RENDER_KEY}",
        "Accept": "application/json"
    }
    for i in range(25):
        time.sleep(10)
        url = f"https://api.render.com/v1/services/{RENDER_SRV}/deploys?limit=1"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                if isinstance(data, list) and len(data) > 0:
                    status = data[0].get("deploy", {}).get("status")
                    print(f"   Status at {i*10 + 10}s: {status}")
                    if status == "live":
                        print("\n🎉 CLOUD DEPLOYMENT IS LIVE!")
                        return True
                    elif status in ("deactivated", "build_failed", "update_failed", "canceled"):
                        print(f"\n❌ Deploy finished with status: {status}")
                        return False
        except Exception as e:
            print(f"   Checking error: {e}")
    print("Deployment is building in background. Cloud URL will update shortly.")
    return True

if __name__ == "__main__":
    print("📦 Step 1: Pushing upgraded files to GitHub...")
    for f in FILES_TO_SYNC:
        update_github_file(f)
        
    dep_id = trigger_render_deploy()
    if dep_id:
        wait_for_render_deploy(dep_id)
