import sqlite3, requests, json

conn = sqlite3.connect('C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system/database/smc_v17.db')
c = conn.cursor()

c.execute("SELECT id, symbol, side, timeframe, entry_price, tp_price, sl_price, mode, tier, sentry_reasons FROM paper_trades WHERE status='OPEN'")
open_trades = c.fetchall()

print("=== OPEN TRADES ON WEBSITE ===")
for r in open_trades:
    print(f"Trade #{r[0]}: {r[1]} {r[2]} ({r[3]})")
    print(f"  Entry: {r[4]} | TP: {r[5]} | SL: {r[6]}")
    print(f"  Mode: {r[7]} | Tier: {r[8]}")
    print(f"  Sentry Reasons: {r[9]}")
    print("------------------------------------------")

c.execute("SELECT id, name, mode, current_balance, equity FROM paper_account")
print("\n=== PAPER ACCOUNTS ===")
for a in c.fetchall():
    print(f"Account {a[0]}: {a[1]} | Mode: {a[2]} | Balance: ${a[3]:.2f} | Equity: ${a[4]:.2f}")

c.execute("SELECT key, value FROM settings")
print("\n=== SETTINGS ===")
for s in c.fetchall():
    if any(k in s[0].upper() for k in ['STRATEGY', 'MODE', 'LEVERAGE', 'TP', 'SL', 'ARMOR']):
        print(f"  {s[0]} = {s[1]}")

btc = requests.get('https://fapi.binance.com/fapi/v1/ticker/price?symbol=BTCUSDT', timeout=3).json().get('price')
print(f"\nKing BTC Mark: ${btc}")
