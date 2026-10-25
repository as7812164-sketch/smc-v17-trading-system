import json
import urllib.request
import datetime

def test_fetch(symbol, interval, limit=60):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Fetched {len(data)} candles for {symbol} {interval}")
        first_t = datetime.datetime.fromtimestamp(data[0][0]/1000.0)
        last_t = datetime.datetime.fromtimestamp(data[-1][0]/1000.0)
        print(f"Range: {first_t} to {last_t}")
        return data

test_fetch("MANAUSDT", "4h")
test_fetch("AEROUSDT", "4h")
