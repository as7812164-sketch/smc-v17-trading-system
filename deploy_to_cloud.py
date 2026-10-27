import os
import sys
import base64
import json
import time
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GITHUB_REPO = "as7812164-sketch/smc-ai-agent"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", os.getenv("GH_TOKEN", "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"))
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
    "static/terminal.html",
    "static/js/lightweight-charts.standalone.production.js",
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
    "engine/trade_master_agent.py",
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

def get_file_sha(filepath: str):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filepath}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Antigravity-Cloud-Deployer"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        return None

def update_github_file(filepath: str):
    if not os.path.exists(filepath):
        return

    with open(filepath, "rb") as f:
        content_bytes = f.read()

    b64_content = base64.b64encode(content_bytes).decode("ascii")
    sha = get_file_sha(filepath)

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filepath}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "Antigravity-Cloud-Deployer"
    }

    payload = {
        "message": f"Upgrade {filepath} - Phase 1 Trading Terminal",
        "content": b64_content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            commit_sha = data.get("commit", {}).get("sha", "")[:7]
            print(f"✓ GitHub Synced: {filepath} (Commit: {commit_sha})")
    except Exception as e:
        print(f"❌ Failed to sync {filepath}: {e}")

def trigger_render_deploy():
    print("\n🚀 Triggering Render Cloud Deployment...")
    url = f"https://api.render.com/v1/services/{RENDER_SRV}/deploys"
    headers = {
        "Authorization": f"Bearer {RENDER_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, data=b'{"clearCache": "do_not_clear"}', headers=headers, method="POST")
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
        print(f"⚠️ Render API trigger notice ({e}) - GitHub webhook auto-deploys main branch.")
        return "webhook"

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
            print(f"   Checking status ({e})...")
    print("Deployment is building in background. Cloud URL will update shortly.")
    return True

if __name__ == "__main__":
    print("📦 Step 1: Pushing upgraded files to GitHub...")
    for f in FILES_TO_SYNC:
        update_github_file(f)

    dep_id = trigger_render_deploy()
    if dep_id:
        wait_for_render_deploy(dep_id)
