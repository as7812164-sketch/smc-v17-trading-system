import sqlite3
import json
import os
from pathlib import Path

WORKSPACE = Path(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system")
DB_PATH = WORKSPACE / "database" / "smc_v17.db"
SHADOW_PATH = WORKSPACE / "bb20_shadow_ledger.json"

def audit_database():
    print(f"=== DATABASE AUDIT: {DB_PATH} ===")
    assert DB_PATH.exists(), f"Database not found at {DB_PATH}"
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 1. Closed trades verification
    closed_trades = c.execute("SELECT * FROM paper_trades WHERE status != 'OPEN' ORDER BY id ASC").fetchall()
    print(f"Total Closed Trades in paper_trades: {len(closed_trades)}")
    
    wins = [t for t in closed_trades if (t['pnl_usdt'] or 0) > 0 or t['status'] == 'WIN']
    losses = [t for t in closed_trades if (t['pnl_usdt'] or 0) < 0 or t['status'] == 'LOSS']
    total_pnl = sum((t['pnl_usdt'] or 0.0) for t in closed_trades)
    print(f"  Closed Wins: {len(wins)}, Closed Losses: {len(losses)}, Total Closed PnL: ${total_pnl:.2f}")
    
    # 2. Check open positions in paper_trades
    open_trades = c.execute("SELECT * FROM paper_trades WHERE status = 'OPEN' ORDER BY id ASC").fetchall()
    print(f"\nOpen Trades in paper_trades ({len(open_trades)}):")
    for ot in open_trades:
        d = dict(ot)
        print(f"  Trade #{d.get('id')}: {d.get('symbol')} {d.get('side')} Entry={d.get('entry_price')} SL={d.get('sl_price')} TP={d.get('tp_price')} Size={d.get('position_size_usdt')} Sec={d.get('account_id')}")

    # Check specifically for CRVUSDT, OPUSDT, FETUSDT
    print("\nSearch for CRVUSDT, OPUSDT, FETUSDT across all trades in paper_trades:")
    for sym in ["CRVUSDT", "OPUSDT", "FETUSDT"]:
        rows = c.execute("SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, status, account_id, entry_time FROM paper_trades WHERE symbol = ? ORDER BY id DESC LIMIT 5", (sym,)).fetchall()
        print(f"  Symbol {sym} (found {len(rows)} trades):")
        for r in rows:
            print(f"    ID={r['id']} Side={r['side']} Status={r['status']} Entry={r['entry_price']} Exit={r['exit_price']} PnL={r['pnl_usdt']} Section={r['account_id']}")

    # 3. Check paper_account (all rows, especially 1..10)
    print("\n--- paper_account Details ---")
    acc_rows = c.execute("SELECT id, name, initial_balance, current_balance, total_pnl, win_count, loss_count, mode, channel FROM paper_account ORDER BY id ASC").fetchall()
    print(f"Total rows in paper_account: {len(acc_rows)}")
    sum_1_10 = 0.0
    for r in acc_rows:
        d = dict(r)
        bal = d.get('current_balance')
        if d['id'] <= 10:
            sum_1_10 += (bal or 0.0)
        print(f"  Acc #{d['id']}: '{d['name']}' Bal=${bal} PnL=${d.get('total_pnl')} W/L={d.get('win_count')}/{d.get('loss_count')} Mode={d.get('mode')} Chan={d.get('channel')}")
    print(f"\nTotal Balance of Hermes 3.0 Compounding Sections (IDs 1-10): ${sum_1_10:.2f}")

    conn.close()

def audit_shadow_ledger():
    print(f"\n=== SHADOW LEDGER AUDIT: {SHADOW_PATH} ===")
    assert SHADOW_PATH.exists(), f"Shadow ledger not found at {SHADOW_PATH}"
    
    with open(SHADOW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Top-level keys: {list(data.keys())}")
    print(f"total_initial_capital: {data.get('total_initial_capital')}")
    print(f"total_current_equity: {data.get('total_current_equity')}")
    
    sections = data.get("sections", {})
    print(f"\nSections ({len(sections)} sections):")
    total_sec_balance = 0.0
    for s_id, s_info in sections.items():
        bal = s_info.get("balance", 0.0)
        total_sec_balance += float(bal)
        print(f"  Sec #{s_id}: Balance=${bal} Status={s_info.get('status')} ActiveTrade={s_info.get('active_trade')} Coins={s_info.get('coins')}")
    print(f"Sum of section balances: ${total_sec_balance:.2f}")

    active_positions = data.get("active_positions", [])
    print(f"\nActive Positions in shadow ledger ({len(active_positions)}):")
    for pos in active_positions:
        print(f"  - {pos}")

    active_setups = data.get("active_setups", [])
    print(f"\nActive Setups in shadow ledger ({len(active_setups)}):")
    for s in active_setups:
        print(f"  - Setup: {s.get('symbol')} {s.get('side')} Sec={s.get('section_id')} Entry={s.get('entry_price')} Dist={s.get('distance_pct')}")

    closed_trades = data.get("closed_trades", [])
    print(f"\nClosed Trades in shadow ledger ({len(closed_trades)}):")
    closed_pnl_sum = 0.0
    for ct in closed_trades:
        pnl = ct.get("pnl_usdt", 0.0)
        closed_pnl_sum += pnl
        print(f"  - Closed: {ct.get('symbol')} {ct.get('side')} Entry={ct.get('entry_price')} Exit={ct.get('exit_price')} PnL=${pnl} Reason={ct.get('exit_reason')}")
    print(f"Total Closed PnL in shadow ledger: ${closed_pnl_sum:.2f}")

if __name__ == "__main__":
    audit_database()
    audit_shadow_ledger()
