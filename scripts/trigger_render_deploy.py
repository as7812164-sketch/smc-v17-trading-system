import urllib.request
import json

RENDER_KEY = "rnd_IZZkLTzrsSOolykJGGflmGovOuZN"
RENDER_SRV = "srv-d61q691r0fns73f4p720"
url = f"https://api.render.com/v1/services/{RENDER_SRV}/deploys"
req = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {RENDER_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    },
    data=json.dumps({"clearCache": "do_not_clear"}).encode("utf-8")
)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print("Triggered Deploy ID:", data.get("id"), "Status:", data.get("status"), "Commit:", data.get("commit", {}).get("id", "")[:7])
except Exception as e:
    print("Deploy trigger error:", e)
