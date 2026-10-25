import urllib.request
import time
import json

base = "https://smc-ai-agent.onrender.com"

for attempt in range(1, 15):
    time.sleep(10)
    try:
        url_k = f"{base}/api/klines/BTCUSDT?interval=15m&limit=5"
        req_k = urllib.request.Request(url_k, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_k, timeout=8) as resp_k:
            kdata = json.loads(resp_k.read().decode())
            candles = kdata.get("candles", [])

        url_m = f"{base}/api/markets"
        req_m = urllib.request.Request(url_m, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_m, timeout=8) as resp_m:
            mdata = json.loads(resp_m.read().decode())
            champions = mdata.get("champions", [])

        url_t = f"{base}/api/ticker/BTCUSDT"
        req_t = urllib.request.Request(url_t, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_t, timeout=8) as resp_t:
            tdata = json.loads(resp_t.read().decode())
            btc_price = tdata.get("last_price", 0.0)

        if candles and champions and btc_price > 0:
            print(f"Attempt {attempt}: DEPLOYMENT COMPLETE & 100% LIVE!")
            print(f" • BTC Price: ${btc_price}")
            print(f" • Candles: {len(candles)} candles | Time in seconds: {candles[0]['time']}")
            print(f" • Markets Champions: {len(champions)} pairs populated")
            break
        else:
            print(f"Attempt {attempt}: Waiting for full data... (Candles: {len(candles)}, Champions: {len(champions)}, Price: {btc_price})")
    except Exception as e:
        print(f"Attempt {attempt}: Building on Render... ({e})")
