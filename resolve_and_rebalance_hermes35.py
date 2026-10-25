import sqlite3
import time

conn = sqlite3.connect("database/smc_v17.db")
conn.row_factory = sqlite3.Row
now_ms = int(time.time() * 1000)

print("--- RESOLVING OPEN TRADES ---")
trades = conn.execute("SELECT * FROM paper_trades WHERE status = 'OPEN'").fetchall()
for t in trades:
    tid = t["id"]
    sym = t["symbol"]
    side = t["side"]
    entry = t["entry_price"]
    pos_size = t["position_size_usdt"]

    if sym == "APTUSDT":
        exit_p = 0.8060
        outcome = "TP_HIT"
        roe = 12.27
        pnl = round(pos_size * (exit_p - entry) / entry, 2)
    elif sym == "LDOUSDT":
        exit_p = 0.4586
        outcome = "TP_HIT"
        roe = 9.44
        pnl = round(pos_size * (exit_p - entry) / entry, 2)
    elif sym == "TIAUSDT":
        exit_p = 0.4741
        outcome = "SL_HIT"
        roe = -28.95
        pnl = round(pos_size * (entry - exit_p) / entry, 2)
    elif sym == "AVAXUSDT":
        exit_p = 11.056
        outcome = "SL_HIT"
        roe = -9.52
        pnl = round(pos_size * (entry - exit_p) / entry, 2)
    else:
        exit_p = entry
        outcome = "CLOSED"
        roe = 0.0
        pnl = 0.0

    conn.execute("""
    UPDATE paper_trades SET
        status = ?, exit_time = ?, exit_price = ?,
        pnl_usdt = ?, pnl_pct = ?, roi_pct = ?,
        duration_str = 'Closed during Hermes 3.5 Upgrade'
    WHERE id = ?
    """, (outcome, now_ms, exit_p, pnl, roe, roe, tid))
    print(f"Closed Trade #{tid}: {sym} {side} -> {outcome} @ {exit_p} (ROE: {roe:+.2f}%)")

print("\n--- REBALANCING 4 QUAD PAPER ACCOUNTS TO $50.00 FRESH CAPITAL ---")
for acc_id in [1, 2, 3, 4]:
    conn.execute("""
    UPDATE paper_account SET
        initial_balance = 50.0,
        current_balance = 50.0,
        vault_balance = 0.0,
        total_pnl = 0.0,
        win_count = 0,
        loss_count = 0,
        win_streak = 0,
        milestone_target = 2000.0,
        mode = 'HERMES_3.5_SINGLE_TIER'
    WHERE id = ?
    """, (acc_id,))
    print(f"Account #{acc_id} reset to $50.00 • Mode: HERMES_3.5_SINGLE_TIER")

print("\n--- SETTING SYSTEM CONFIG & METRICS ---")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('strategy_version', 'HERMES_3.5_SINGLE_TIER')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('hermes35_entry_mode', '5% Boundary Penetration')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('hermes_margin_allocation_pct', '0.15')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_4h_1_compounding_balance', '50.0')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_4h_2_compounding_balance', '50.0')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_1h_1_compounding_balance', '50.0')")
conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bitget_1h_2_compounding_balance', '50.0')")
conn.execute("UPDATE system_metrics SET value = 'HERMES_3.5_SINGLE_TIER' WHERE key = 'hermes_mode'")

conn.commit()
conn.close()
print("All trades resolved and accounts clean! Ready for Hermes 3.5 Single Tier autonomous execution.")
