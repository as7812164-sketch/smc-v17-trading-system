import sqlite3

conn = sqlite3.connect("database/smc_v17.db")
c = conn.cursor()

# 1. Inspect mode and settings in paper_trades
c.execute("SELECT DISTINCT mode FROM paper_trades")
modes = c.fetchall()
print("Distinct modes in paper_trades:", modes)

c.execute("SELECT DISTINCT timeframe FROM paper_trades")
timeframes = c.fetchall()
print("Distinct timeframes in paper_trades:", timeframes)

# Compare Trade 629 (AERO live SL), Trade 627 (MANA Win), Trade 623 (MANA Win), Trade 614 (ICP Win)
c.execute("SELECT id, symbol, side, timeframe, mode, entry_price, tp_price, sl_price, status, autopsy_diagnosis, roi_pct FROM paper_trades WHERE id IN (613, 614, 617, 623, 627, 629, 631)")
sample_trades = c.fetchall()
print("\n--- Sample Trades Comparison (Paper vs Recent Live) ---")
for t in sample_trades:
    id_, sym, side, tf, mode, entry, tp, sl, status, autopsy, roi = t
    tp_pct = abs((tp - entry)/entry)*100 if (tp and entry) else 0
    sl_pct = abs((sl - entry)/entry)*100 if (sl and entry) else 0
    print(f"ID {id_}: {sym} {side} {tf} | Mode: {mode} | Entry: {entry} | TP: {tp} ({tp_pct:.2f}%) | SL: {sl} ({sl_pct:.2f}%) | Status: {status} | ROI: {roi}%")

# Check settings table
c.execute("SELECT * FROM settings")
settings = c.fetchall()
print("\n--- Current Settings Table ---")
for s in settings:
    print(f"  {s[0]}: {s[1]}")

# Check paper_account configuration
c.execute("SELECT id, name, mode, leverage, exchange FROM paper_account WHERE id <= 10")
accounts = c.fetchall()
print("\n--- 10 Compounding Sections Configuration ---")
for a in accounts:
    print(f"  Section {a[0]}: {a[1]} | Mode: {a[2]} | Leverage: {a[3]}x | Exchange: {a[4]}")
