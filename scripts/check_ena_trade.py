import sqlite3
import os
import requests

db_paths = [
    'database/trading_system.db',
    'database/smc_trading.db',
    'database/smc_v17.db',
    'database/trades.db'
]

print("=== CHECKING LOCAL DATABASES FOR ENA ===")
for p in db_paths:
    if os.path.exists(p):
        print(f"\n--- Checking DB: {p} ---")
        conn = sqlite3.connect(p)
        c = conn.cursor()
        tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in tables:
            try:
                # check if symbol column exists
                cols = [col[1] for col in c.execute(f"PRAGMA table_info({t})").fetchall()]
                if 'symbol' in cols:
                    c.execute(f"SELECT * FROM {t} WHERE symbol LIKE '%ENA%'")
                    rows = c.fetchall()
                    if rows:
                        print(f"Table '{t}' has {len(rows)} ENA rows:")
                        for r in rows:
                            print(dict(zip(cols, r)))
            except Exception as e:
                pass
        conn.close()

# Also check Render cloud live API for ENA
print("\n=== CHECKING LIVE CLOUD TRADES & ZONES ===")
try:
    r = requests.get("https://smc-ai-agent.onrender.com/api/paper/trades", timeout=5)
    if r.status_code == 200:
        trades = r.json().get('trades', [])
        ena_trades = [t for t in trades if 'ENA' in str(t.get('symbol', ''))]
        print(f"Render Cloud Paper Trades count for ENA: {len(ena_trades)}")
        for et in ena_trades:
            print("Trade:", et)
except Exception as e:
    print("Render trades error:", e)

try:
    r = requests.get("https://smc-ai-agent.onrender.com/api/paper/positions", timeout=5)
    if r.status_code == 200:
        pos = r.json().get('positions', [])
        ena_pos = [p for p in pos if 'ENA' in str(p.get('symbol', ''))]
        print(f"Render Cloud Open Positions for ENA: {len(ena_pos)}")
        for ep in ena_pos:
            print("Position:", ep)
except Exception as e:
    print("Render positions error:", e)

# Fetch latest ENA price & 1H/4H candles from Binance
print("\n=== FETCHING LATEST ENAUSDT CANDLES FROM BINANCE ===")
try:
    # 1h candles
    resp = requests.get("https://api.binance.com/api/v3/klines?symbol=ENAUSDT&interval=1h&limit=24", timeout=5)
    if resp.status_code == 200:
        klines = resp.json()
        print(f"Recent 1H candles count: {len(klines)}")
        # Print last 5 candles: time, open, high, low, close
        for k in klines[-6:]:
            import datetime
            t = datetime.datetime.fromtimestamp(k[0]/1000).strftime('%Y-%m-%d %H:%M')
            print(f"1H {t}: O={k[1]}, H={k[2]}, L={k[3]}, C={k[4]}")
        
    curr_price = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ENAUSDT", timeout=5).json()
    print("Current Live ENAUSDT Price:", curr_price.get('price'))
except Exception as e:
    print("Binance klines error:", e)
