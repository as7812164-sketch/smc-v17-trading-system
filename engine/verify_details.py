import sqlite3

db_path = r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\database\smc_v17.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- MANDATE CLOSED SYMBOLS SEARCH ---")
mandate_syms = ['NEARUSDT', 'SUSDT', 'AEROUSDT', 'TIAUSDT', 'APTUSDT']
for sym in mandate_syms:
    cursor.execute("SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, status, exit_time FROM paper_trades WHERE symbol LIKE ? ORDER BY id DESC", (f"%{sym}%",))
    rows = [dict(r) for r in cursor.fetchall()]
    print(f"Symbol '{sym}': {len(rows)} trades")
    for r in rows:
        print("   ", r)

print("\n--- ALL CLOSED TRADES IN DB ---")
cursor.execute("SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, status, exit_time FROM paper_trades WHERE status != 'OPEN' ORDER BY id ASC")
all_closed = [dict(r) for r in cursor.fetchall()]
print(f"Total closed trades count: {len(all_closed)}")
for r in all_closed:
    print(f"ID {r['id']:3d} | {r['symbol']:12s} | {r['side']:5s} | Entry: {r['entry_price']} | Exit: {r['exit_price']} | PnL: {r['pnl_usdt']} ({r['pnl_pct']}%) | Status: {r['status']}")

print("\n--- ALL OPEN TRADES IN DB ---")
cursor.execute("SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, status, exit_time, highest_price, lowest_price, roi_pct FROM paper_trades WHERE status = 'OPEN' ORDER BY id ASC")
all_open = [dict(r) for r in cursor.fetchall()]
print(f"Total open trades count: {len(all_open)}")
for r in all_open:
    print(f"ID {r['id']:3d} | {r['symbol']:12s} | {r['side']:5s} | Entry: {r['entry_price']} | Exit: {r['exit_price']} | ROI: {r['roi_pct']}% | Status: {r['status']}")

print("\n--- PAPER_ACCOUNT SECTIONS 1 TO 10 ---")
cursor.execute("SELECT id, name, current_balance, total_pnl, win_count, loss_count, mode, timeframe FROM paper_account WHERE id <= 10 ORDER BY id ASC")
secs = [dict(r) for r in cursor.fetchall()]
total_equity_1_to_10 = 0.0
for s in secs:
    bal = s['current_balance']
    total_equity_1_to_10 += bal
    print(f"Section {s['id']:2d}: Name='{s['name']:25s}' | Balance=${bal:8.2f} | PnL=${s['total_pnl']:8.2f} | W/L={s['win_count']}/{s['loss_count']}")

print(f"\nTotal Portfolio Equity (Sections 1-10): ${total_equity_1_to_10:.2f}")

conn.close()
