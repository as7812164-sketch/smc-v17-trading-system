import urllib.request
import json

url = "https://smc-ai-agent.onrender.com/api/paper/trades"
data = json.loads(urllib.request.urlopen(url).read())

for t in data["trades"]:
    if t["symbol"] in ("THETAUSDT", "SANDUSDT"):
        print(f"ID: {t.get('id')} | Sym: {t.get('symbol')} | Side: {t.get('side')} | Entry: {t.get('entry_price')} | Exit: {t.get('exit_price')} | PnL: {t.get('pnl_usdt')} | MAE: {t.get('mae_pct')} | MFE: {t.get('mfe_pct')} | Status: {t.get('status')} | Time: {t.get('timestamp')}")
