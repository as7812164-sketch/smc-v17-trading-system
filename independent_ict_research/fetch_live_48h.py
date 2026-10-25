import urllib.request, json
from datetime import datetime, timezone

try:
    url = "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1h&limit=48"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    first_t = datetime.fromtimestamp(data[0][0]/1000.0, tz=timezone.utc)
    last_t = datetime.fromtimestamp(data[-1][0]/1000.0, tz=timezone.utc)
    print(f"Fetched {len(data)} live candles from Binance Futures!")
    print("From:", first_t.strftime("%Y-%m-%d %H:%M UTC"), "to", last_t.strftime("%Y-%m-%d %H:%M UTC"))
    print(f"Current BTC Price: ${float(data[-1][4]):,.2f}")
except Exception as e:
    print("Binance API fetch result:", e)
