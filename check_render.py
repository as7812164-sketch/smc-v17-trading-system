import urllib.request
import json
import time

RENDER_KEY = "rnd_IZZkLTzrsSOolykJGGflmGovOuZN"
RENDER_SRV = "srv-d61q691r0fns73f4p720"

def monitor():
    headers = {
        "Authorization": f"Bearer {RENDER_KEY}",
        "Accept": "application/json"
    }
    for i in range(25):
        url = f"https://api.render.com/v1/services/{RENDER_SRV}/deploys?limit=2"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                top = data[0].get("deploy", {})
                status = top.get("status")
                dep_id = top.get("id")
                commit = top.get("commit", {}).get("id", "")[:7]
                print(f"[{i*10}s] Top Deploy: {dep_id} | Status: {status} | Commit: {commit}", flush=True)
                if status == "live" and commit == "5e1e04f":
                    print("\n[OK] LATEST DEPLOYMENT 5e1e04f IS LIVE ON RENDER!", flush=True)
                    return True
                elif status in ("build_failed", "update_failed", "canceled"):
                    print(f"\n[ERROR] Deploy error status: {status}", flush=True)
                    return False
        except Exception as e:
            print("Error checking:", e, flush=True)
        time.sleep(10)

if __name__ == "__main__":
    monitor()
