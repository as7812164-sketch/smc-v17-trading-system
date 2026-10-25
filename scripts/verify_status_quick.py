import sqlite3

con = sqlite3.connect('database/smc_v17.db')
con.row_factory = sqlite3.Row
cur = con.cursor()

print("=== OPEN TRADES ===")
for r in cur.execute("SELECT id, symbol, side, entry_price, sl_price, tp_price, trailing_sl_price, locked_roi_pct, status, pnl_pct, pnl_usdt FROM paper_trades WHERE status='OPEN'").fetchall():
    print(dict(r))

print("\n=== COMPOUNDING SECTIONS (paper_account) ===")
for r in cur.execute("SELECT id, name, timeframe, current_balance, vault_balance, win_count, loss_count FROM paper_account ORDER BY id").fetchall():
    print(dict(r))

print("\n=== TOTAL TRADES COUNT ===")
print("Total trades:", cur.execute("SELECT count(*) FROM paper_trades").fetchone()[0])
print("Closed trades:", cur.execute("SELECT count(*) FROM paper_trades WHERE status='CLOSED'").fetchone()[0])
con.close()
