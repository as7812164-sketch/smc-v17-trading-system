import urllib.request
import json

url = "https://fapi.binance.com/fapi/v1/ticker/price?symbol=SNXUSDT"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print("SNX Current Market Price:", data.get('price'))

# Also check ATOM trade that closed:
# Line from history: "ATOMUSDT buy market | Price: | Size: 14 | Time: 2026-10-22 14:42:27"
# ATOM closed at 14:42 in profit!
