import sqlite3
import json

print("=== SQLITE DATABASE (smc_v17.db) ===")
conn = sqlite3.connect("database/smc_v17.db")
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])

for tbl in ["paper_account", "compounding_sections", "paper_trades"]:
    if (tbl,) in tables:
        count = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"Table {tbl}: {count} rows")

print("--- paper_trades Schema ---")
cols = [c[1] for c in c.execute("PRAGMA table_info(paper_trades)").fetchall()]
print("Columns:", cols)

print("\n--- Open Trades in paper_trades ---")
open_trades = c.execute("SELECT id, symbol, side, entry_price, status, pnl_usdt, mode, account_id FROM paper_trades WHERE status='OPEN'").fetchall()
for t in open_trades:
    print(t)

print("\n--- paper_account Summary ---")
accounts = c.execute("SELECT id, name, initial_balance, current_balance, vault_balance, win_count, loss_count FROM paper_account").fetchall()
tot_init = sum(a[2] for a in accounts)
tot_curr = sum(a[3] for a in accounts)
tot_vault = sum(a[4] for a in accounts)
print(f"Total Initial: ${tot_init:.2f} | Current Bal: ${tot_curr:.2f} | Vault: ${tot_vault:.2f} | Net: ${tot_curr + tot_vault:.2f}")

conn.close()

print("\n=== BB 3.0 SHADOW LEDGER (bb20_shadow_ledger.json) ===")
with open("bb20_shadow_ledger.json", "r") as f:
    bb = json.load(f)

print("Starting Capital: $500.00")
total_bal = sum(s["balance"] for s in bb.get("sections", {}).values())
print(f"Current Total BB 3.0 Equity: ${total_bal:.2f} USDT")
print(f"Closed Trades: {len(bb.get('closed_trades', []))}")
print(f"Active Positions: {len(bb.get('active_positions', {}))}")
for s_id, s in sorted(bb.get("sections", {}).items(), key=lambda x: int(x[0])):
    coins = "/".join(s.get("assigned_coins", []))
    print(f"Section {s_id} ({coins}): Balance = ${s['balance']:.2f} | Record: {s.get('wins',0)}W-{s.get('saves',0)}S-{s.get('losses',0)}L | PnL: ${s.get('pnl_usd',0.0):+.2f}")
