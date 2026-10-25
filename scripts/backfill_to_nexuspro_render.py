import json
import time
import urllib.request
import ssl

ctx = ssl._create_unverified_context()
RENDER_SYNC_URL = "https://nexuspro-terminal.onrender.com/api/sync/trade"
RENDER_HISTORY_URL = "https://nexuspro-terminal.onrender.com/api/trade/history"

def wait_for_deploy(max_retries=30):
    print("Checking if Render deployment is live with /api/sync/trade...")
    for i in range(max_retries):
        try:
            req = urllib.request.Request(
                RENDER_SYNC_URL,
                data=json.dumps({"action": "PING"}).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Deploy-Checker"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
                print(f"[{i+1}/{max_retries}] Render response:", data)
                if data.get("status") in ["SUCCESS", "ERROR"]:
                    print("Render deployment is LIVE with sync endpoint!")
                    return True
        except Exception as e:
            print(f"[{i+1}/{max_retries}] Waiting for deploy... ({e})")
        time.sleep(10)
    return False

def backfill_all_trades():
    with open("bb20_shadow_ledger.json", "r", encoding="utf-8") as f:
        ledger = json.load(f)

    closed_trades = ledger.get("closed_trades", [])
    print(f"Found {len(closed_trades)} closed trades in bb20_shadow_ledger.json")

    for t in closed_trades:
        sym = t.get("symbol")
        pnl = t.get("dollar_pnl")
        print(f"Pushing trade {sym} PnL ${pnl}...")
        payload = {
            "action": "CLOSE",
            "data": t
        }
        try:
            req = urllib.request.Request(
                RENDER_SYNC_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Backfill-Script"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                res = json.loads(r.read().decode("utf-8"))
                print(f"  Result for {sym}:", res)
        except Exception as e:
            print(f"  Error pushing {sym}:", e)
        time.sleep(1)

    print("\n--- Verifying Live Trade History on Render ---")
    try:
        req = urllib.request.Request(RENDER_HISTORY_URL, headers={"User-Agent": "Verifier"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            hist = json.loads(r.read().decode("utf-8"))
            trades = hist.get("trades", [])
            print(f"Total trades on website: {len(trades)}")
            for tr in trades[:10]:
                print(f"  #{tr.get('id')} {tr.get('symbol')} {tr.get('side')} | PnL: ${tr.get('realized_pnl')} | Reason: {tr.get('exit_reason')}")
    except Exception as e:
        print("Error reading history:", e)

if __name__ == "__main__":
    if wait_for_deploy():
        backfill_all_trades()
    else:
        print("Deploy wait timed out. Try again shortly.")
