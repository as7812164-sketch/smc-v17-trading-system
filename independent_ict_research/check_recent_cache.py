import os, json
from datetime import datetime, timezone

cache_dir = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\market_data_cache_15m"
if os.path.exists(cache_dir):
    files = [f for f in os.listdir(cache_dir) if f.endswith(".json")]
    print(f"15m cache files: {len(files)}")
    btc_p = os.path.join(cache_dir, "BTCUSDT_15m.json")
    if os.path.exists(btc_p):
        with open(btc_p, "r") as f:
            d = json.load(f)
        last_t = d[-1]["time"] if "time" in d[-1] else d[-1].get("timestamp", 0)
        dt = datetime.fromtimestamp(last_t/1000.0 if last_t > 1e11 else last_t, tz=timezone.utc)
        print("Latest 15m candle timestamp:", dt.strftime("%Y-%m-%d %H:%M:%S UTC"))
