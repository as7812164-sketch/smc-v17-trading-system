import json
import os
import sys
import sqlite3
import urllib.request
import traceback

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 80)
print(" 🔍 BINANCE LIVE AUTO-TRADE FORENSIC DIAGNOSTIC")
print("=" * 80)

# 1. Check local SQLite settings
conn = sqlite3.connect("database/smc_v17.db")
c = conn.cursor()
settings = dict(c.execute("SELECT key, value FROM settings").fetchall())

print("\n--- 1. SETTINGS AUDIT ---")
print(f"BINANCE_AUTO_TRADE: {settings.get('binance_auto_trade')}")
print(f"BITGET_AUTO_TRADE:  {settings.get('bitget_auto_trade')}")
print(f"TELEGRAM_CHAT_ID:   {settings.get('telegram_chat_id')}")

# 2. Check Binance API Live Connection directly
print("\n--- 2. BINANCE FUTURES API LIVE STATUS CHECK ---")
try:
    from engine.binance_client import binance_trader
    client = binance_trader
    acc = client.get_account()
    if acc.get("code") == 200:
        data = acc.get("data", {})
        total_bal = float(data.get("totalMarginBalance", 0.0))
        avail_bal = float(data.get("availableBalance", 0.0))
        can_trade = data.get("canTrade", False)
        positions = [p for p in data.get("positions", []) if float(p.get("positionAmt", 0.0)) != 0.0]
        print(f"✅ Binance Futures API: CONNECTED & AUTHENTICATED!")
        print(f"   • Total Margin Balance: ${total_bal:.2f} USDT")
        print(f"   • Available Free Margin: ${avail_bal:.2f} USDT")
        print(f"   • Can Trade: {can_trade}")
        print(f"   • Open Positions on Binance: {len(positions)}")
        for p in positions:
            print(f"     - {p.get('symbol')}: Amt={p.get('positionAmt')}, Entry={p.get('entryPrice')}, PnL={p.get('unrealizedProfit')}")
    else:
        print(f"❌ Binance API Error: {acc}")
except Exception as e:
    print(f"❌ Exception connecting to Binance: {e}")
    traceback.print_exc()

# 3. Check Live Render Production Server Endpoints
print("\n--- 3. RENDER PRODUCTION BACKEND STATUS ---")
endpoints = [
    ("Status", "https://smc-ai-agent.onrender.com/api/status"),
    ("Binance Status", "https://smc-ai-agent.onrender.com/api/binance/status"),
    ("Recent Signals", "https://smc-ai-agent.onrender.com/api/signals/recent"),
    ("Challenge Status", "https://smc-ai-agent.onrender.com/api/challenge/dual-status"),
]

for label, url in endpoints:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            print(f"\n[+] {label} ({url}):")
            if label == "Recent Signals":
                print(f"    Total recent signals: {len(data) if isinstance(data, list) else data}")
                if isinstance(data, list):
                    for s in data[:5]:
                        print(f"    - {s.get('symbol')} | {s.get('timeframe')} | {s.get('side') or s.get('type')} | Status={s.get('status')}")
            else:
                print("    " + json.dumps(data, indent=4)[:400] + "...")
    except Exception as e:
        print(f"[-] {label} failed: {e}")

# 4. Check Recent System Logs / Sent Alerts in SQLite
print("\n--- 4. RECENT SIGNALS & SENTRY LOGS (SQLite) ---")
try:
    sig_rows = c.execute("SELECT id, symbol, timeframe, type, status, created_at FROM signals ORDER BY id DESC LIMIT 10").fetchall()
    print(f"Recent signals in DB (Total {len(sig_rows)}):")
    for r in sig_rows:
        print(f"  #{r[0]}: {r[1]} {r[2]} {r[3]} | Status: {r[4]} | Created: {r[5]}")
except Exception as e:
    print("Signals query error:", e)
