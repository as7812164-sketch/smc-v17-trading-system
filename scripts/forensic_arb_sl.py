import urllib.request
import json
import ssl
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8')

ctx = ssl._create_unverified_context()

print("=" * 75)
print("🔍 ARBUSDT SL FORENSIC AUDIT — HERMES 3.0 MODEL 2A")
print("=" * 75)

# 1. Fetch recent trades from Render
render_url = "https://smc-ai-agent.onrender.com/api/paper/trades?limit=30"
try:
    req = urllib.request.Request(render_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
        trades_data = json.loads(resp.read().decode())
        trades = trades_data.get("trades", [])
        print(f"\n📊 Total Render Closed Trades: {len(trades)}")
        
        # Search for ARB trades
        arb_trades = [t for t in trades if "ARB" in t.get("symbol", "")]
        if arb_trades:
            print(f"🎯 Found {len(arb_trades)} ARB Trades in History:")
            for t in arb_trades[:5]:
                print(f"  • ID #{t.get('id')} | Mode: {t.get('mode')} | Side: {t.get('side_raw') or t.get('side')}")
                print(f"    Entry: ${t.get('entry_price')} | Exit: ${t.get('exit_price')} | Result: {t.get('result')}")
                print(f"    PnL: ${t.get('realized_pnl')} ({t.get('pnl_pct')}%) | Duration: {t.get('duration_str')}")
                print(f"    BE Locked: {t.get('be_locked')} | BE Status: {t.get('be_status_str')}")
                print(f"    Exit Time: {t.get('exit_time_str') or t.get('timestamp')}")
                print(f"    Raw Exit Time: {t.get('raw_timestamp')}\n")
        else:
            print("⚠️ No ARB trade found in the last 30 closed trades. Checking recent 5 trades overall:")
            for t in trades[:5]:
                print(f"  • ID #{t.get('id')} {t.get('symbol')} {t.get('side_raw')} | PnL: ${t.get('realized_pnl')} ({t.get('result')}) | Exit: {t.get('exit_time_str') or t.get('timestamp')}")
except Exception as e:
    print(f"❌ Error fetching from Render: {e}")

# 2. Check open positions on Render
pos_url = "https://smc-ai-agent.onrender.com/api/paper/positions"
try:
    req = urllib.request.Request(pos_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
        pos_data = json.loads(resp.read().decode())
        positions = pos_data.get("positions", [])
        print(f"\n📍 Render Open Positions ({len(positions)}):")
        for p in positions:
            print(f"  • #{p.get('id')} {p.get('symbol')} {p.get('side')} | Entry: ${p.get('entry_price')} | Mark: ${p.get('mark_price')} | SL: ${p.get('sl_price')} | UnPnL: ${p.get('unrealized_pnl')}")
except Exception as e:
    print(f"❌ Error checking positions: {e}")

# 3. Check Live ARBUSDT 15m & 1h candles
print("\n🕯️ Fetching Live ARBUSDT Price Action (Binance Vision)...")
try:
    klines_url = "https://data-api.binance.vision/api/v3/klines?symbol=ARBUSDT&interval=15m&limit=12"
    req = urllib.request.Request(klines_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        candles = json.loads(resp.read().decode())
        print(f"Latest {len(candles)} 15m Candlesticks for ARBUSDT:")
        for c in candles:
            t = datetime.fromtimestamp(int(c[0])/1000, tz=timezone.utc).strftime("%H:%M UTC")
            o, h, l, cl = float(c[1]), float(c[2]), float(c[3]), float(c[4])
            move_pct = ((cl - o) / o) * 100
            wick_low_pct = ((min(o, cl) - l) / (h - l)) * 100 if h > l else 0
            wick_high_pct = ((h - max(o, cl)) / (h - l)) * 100 if h > l else 0
            print(f"  [{t}] O: {o:.4f} | H: {h:.4f} | L: {l:.4f} | C: {cl:.4f} | Move: {move_pct:+.2f}% | L-Wick: {wick_low_pct:.0f}%")
except Exception as e:
    print(f"❌ Error fetching candles: {e}")

print("=" * 75)
