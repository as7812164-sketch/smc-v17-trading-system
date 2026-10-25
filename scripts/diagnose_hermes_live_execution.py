import urllib.request
import json
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("🔍 HERMES 3.0 MODEL 2A LIVE EXECUTION & SENTRY DIAGNOSTIC")
print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
print("=" * 80)

# 1. Check Platform Status
try:
    url_stat = "https://smc-ai-agent.onrender.com/api/status"
    req = urllib.request.Request(url_stat, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode())
    print(f"• Render Platform Status: {res.get('status')} | Version: {res.get('version')}")
except Exception as e:
    print(f"• Error checking status: {e}")

# 2. Check Open Positions
try:
    url_pos = "https://smc-ai-agent.onrender.com/api/paper/positions"
    req = urllib.request.Request(url_pos, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        res_pos = json.loads(resp.read().decode())
    positions = res_pos.get("positions", [])
    print(f"• Active Positions Count: {len(positions)}")
    for p in positions:
        print(f"   -> {p.get('symbol')} {p.get('side')} | Entry: {p.get('entry_price')} | Unrealized: ${p.get('unrealized_pnl')}")
except Exception as e:
    print(f"• Error checking positions: {e}")

# 3. Check Live Prices vs Entry Targets for top candidates
candidates = [
    ("CRVUSDT", "LONG", 0.3438),
    ("APTUSDT", "LONG", 0.7867),
    ("AEROUSDT", "SHORT", 0.8504),
    ("STXUSDT", "LONG", 0.4095),
    ("FILUSDT", "LONG", 1.0414)
]

print("\n📊 CANDIDATE COINS LIVE PRICING & TAP CHECK:")
print("-" * 80)
print(f"{'Coin':<12} {'Side':<6} {'50% MT Target':<16} {'Live Price':<14} {'Recent Low/High':<18} {'Tapped MT?'}")
print("-" * 80)

for sym, side, mt in candidates:
    try:
        url_k = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=15m&limit=12"
        req = urllib.request.Request(url_k, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            klines = json.loads(resp.read().decode())
        
        cur_price = float(klines[-1][4])
        # Look at low/high of last 4 bars (last 1 hour)
        last_4_bars = klines[-4:]
        min_low = min(float(k[3]) for k in last_4_bars)
        max_high = max(float(k[2]) for k in last_4_bars)

        tapped = False
        if side == "LONG" and min_low <= mt:
            tapped = True
        elif side == "SHORT" and max_high >= mt:
            tapped = True

        ext_str = f"Low: {min_low:.4f}" if side == "LONG" else f"High: {max_high:.4f}"
        tap_str = "✅ YES (TAPPED)" if tapped else "❌ NO (Still Waiting)"
        
        print(f"{sym:<12} {side:<6} ${mt:<15.4f} ${cur_price:<13.4f} {ext_str:<18} {tap_str}")
    except Exception as e:
        print(f"{sym:<12} Error: {e}")

# 4. Check BTC Sentry Status (Macro Veto Check)
try:
    url_btc = "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=4h&limit=3"
    req = urllib.request.Request(url_btc, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        btc_k = json.loads(resp.read().decode())
    b_open = float(btc_k[-1][1])
    b_cur = float(btc_k[-1][4])
    b_chg = (b_cur - b_open) / b_open * 100.0
    print("\n🛡️ SENTRY 1: BTC CAUSAL BRAKE CHECK:")
    print("-" * 80)
    print(f"• BTC 4H Current Candle Change: {b_chg:+.2f}%")
    if b_chg <= -2.0:
        print("⚠️ BTC DUMP VETO ACTIVE: Long trades are temporarily vetoed to prevent catching falling knives!")
    elif b_chg >= 2.0:
        print("⚠️ BTC PUMP VETO ACTIVE: Short trades are temporarily vetoed!")
    else:
        print("✅ BTC SENTRY CLEAR: No macro veto. All Long and Short trades are permitted.")
except Exception as e:
    print(f"Error checking BTC: {e}")
