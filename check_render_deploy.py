import urllib.request
import json
import os

render_key = ""
service_id = ""

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.startswith("RENDER_API_KEY="):
                render_key = line.strip().split("=", 1)[1].strip()
            elif line.startswith("RENDER_SERVICE_ID="):
                service_id = line.strip().split("=", 1)[1].strip()

if not service_id:
    # Try fetching services
    req = urllib.request.Request("https://api.render.com/v1/services?limit=5", headers={"Authorization": f"Bearer {render_key}", "Accept": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        svcs = json.loads(resp.read().decode())
        for s in svcs:
            svc = s.get("service", {})
            if "smc" in svc.get("name", "").lower():
                service_id = svc.get("id")
                print("Found service:", service_id, svc.get("name"))
    except Exception as e:
        print("Service list error:", e)

if service_id:
    req = urllib.request.Request(f"https://api.render.com/v1/services/{service_id}/deploys?limit=3", headers={"Authorization": f"Bearer {render_key}", "Accept": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        deploys = json.loads(resp.read().decode())
        for d in deploys:
            dep = d.get("deploy", {})
            print(f"Deploy ID: {dep.get('id')} | Status: {dep.get('status')} | Commit: {dep.get('commit', {}).get('message')}")
    except Exception as e:
        print("Deploy check error:", e)
