import sqlite3

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()
c.execute("SELECT id, symbol, side, tier, be_lock_pct, trail_lock_pct, sentry_reasons, mode FROM paper_trades WHERE status='OPEN'")
for r in c.fetchall():
    print(f"ID: {r[0]} | {r[1]} {r[2]} | Tier: {r[3]} | Mode: {r[7]}")
    print(f"  BE Lock: {r[4]} | Trail: {r[5]}")
    print(f"  Sentry Reasons: {r[6]}")
    print("-" * 70)
conn.close()
