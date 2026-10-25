import sys
sys.path.append('.')
import urllib.request
import json

# Check BTC price and EMA50 on 4H
url = "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=4h&limit=60"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as res:
    klines = json.loads(res.read().decode())

closes = [float(k[4]) for k in klines]
current_btc = closes[-1]

# Calculate EMA 50
def calculate_ema(data, period=50):
    k = 2.0 / (period + 1.0)
    ema = data[0]
    for p in data[1:]:
        ema = (p * k) + (ema * (1.0 - k))
    return ema

btc_ema50 = calculate_ema(closes, 50)
print(f"BTC 4H Current Price: ${current_btc:,.2f}")
print(f"BTC 4H EMA50: ${btc_ema50:,.2f}")

if current_btc > btc_ema50:
    btc_regime = "BULLISH_BIAS (Safe for LONG & selective short)"
else:
    btc_regime = "BEARISH_REGIME (Safe for SHORT, long filtered if dump)"
print(f"BTC Macro Brake Regime: {btc_regime}")

# Check local watchdog loop status
import sqlite3
conn = sqlite3.connect("database/smc_v17.db")
c = conn.cursor()
c.execute("SELECT key, value FROM settings WHERE key LIKE '%cooldown%'")
cooldowns = c.fetchall()
print(f"\nActive Cooldowns: {len(cooldowns)}")
for k, v in cooldowns:
    print(f"  {k}: {v}")
