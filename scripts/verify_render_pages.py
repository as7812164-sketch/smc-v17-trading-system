import urllib.request
import json
import ssl
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8')

ctx = ssl._create_unverified_context()
base = 'https://smc-ai-agent.onrender.com'

tests = [
    ('/trade', 'HTML', 'Futures Terminal page'),
    ('/nexus/markets', 'HTML', 'Markets page'),
    ('/nexus/deca', 'HTML', 'BB 2.0 Deca Hub page'),
    ('/nexus/assets', 'HTML', 'Assets & Wallet page'),
    ('/api/ticker/BTCUSDT', 'JSON', 'BTC Live Ticker'),
    ('/api/klines/BTCUSDT?interval=15m&limit=10', 'JSON', 'Candlestick Klines'),
    ('/api/orderbook/BTCUSDT?depth=5', 'JSON', 'Order Book Depth'),
    ('/api/markets', 'JSON', '20 Champions + Markets'),
    ('/api/deca/summary', 'JSON', 'Deca Portfolio Summary'),
    ('/api/deca/sections', 'JSON', '10 Compounding Sections'),
    ('/api/deca/setups', 'JSON', 'BB 2.0 Setup Radar'),
    ('/api/trade/positions', 'JSON', 'Live Trade Positions')
]

print("=" * 70)
print(f"VERIFYING RENDER PRODUCTION: {base}")
print("=" * 70)

all_ok = True
for ep, exp_type, label in tests:
    url = base + ep
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            code = resp.getcode()
            body = resp.read()
            if exp_type == 'JSON':
                data = json.loads(body.decode())
                keys_str = str(list(data.keys())[:3])
                extra = ""
                if 'candles' in data:
                    c = data['candles']
                    extra = f" ({len(c)} candles, time={c[0]['time']})" if c else " (0)"
                elif 'setups' in data:
                    extra = f" ({len(data['setups'])} setups)"
                elif 'sections' in data:
                    extra = f" ({len(data['sections'])} sections)"
                elif 'last_price' in data:
                    extra = f" (Price: ${data['last_price']})"
                print(f"✅ [{code}] {label:<30} | {keys_str}{extra}")
            else:
                print(f"✅ [{code}] {label:<30} | Size: {len(body):,} bytes")
    except Exception as e:
        all_ok = False
        print(f"❌ FAIL [{url}]: {e}")

print("=" * 70)
if all_ok:
    print("🎯 100% HEALTH CHECK PASSED! ALL PAGES AND DATA APIS ARE LIVE!")
else:
    print("⚠️ Some endpoints failed. Review logs above.")
print("=" * 70)
