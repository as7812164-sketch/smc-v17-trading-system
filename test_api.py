import urllib.request
import json

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/paper/account", timeout=5) as resp:
        data = json.loads(resp.read().decode())
        quad = data.get("quad", {})
        for k in ["binance_4h", "binance_1h", "bitget_4h", "bitget_1h"]:
            v = quad.get(k, {})
            print(k, "=> Balance:", v.get("current_balance"), "PnL:", v.get("total_pnl"), "Trades:", v.get("win_count", 0) + v.get("loss_count", 0), "Open:", v.get("open_trades_count"))
except Exception as e:
    print("Error querying /api/paper/account:", e)

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/paper/positions", timeout=5) as resp:
        data = json.loads(resp.read().decode())
        print("Live open positions count:", len(data))
except Exception as e:
    print("Error querying /api/paper/positions:", e)
