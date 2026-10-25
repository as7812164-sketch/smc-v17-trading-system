import sqlite3

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()

c.execute("""
    SELECT count(*), 
           sum(pnl_usdt), 
           avg(roi_pct), 
           min(roi_pct), 
           max(roi_pct),
           sum(case when roi_pct > 0 then 1 else 0 end),
           sum(case when roi_pct <= 0 then 1 else 0 end)
    FROM paper_trades 
    WHERE status = 'TRAILING_SL_HIT'
""")
row = c.fetchone()
print("--- TRAILING_SL_HIT TRADES STATS ---")
print(f"Total Trailing SL Exits: {row[0]}")
print(f"Total Net PnL from Trailing SL: +${row[1]:.2f} USDT")
print(f"Average ROI%: {row[2]:.2f}%")
print(f"Min ROI%: {row[3]}% | Max ROI%: {row[4]}%")
print(f"Winning Trailed Trades (Profit Locked): {row[5]}")
print(f"Loss/BE Trailed Trades: {row[6]}")

# Breakdown by all exit statuses
print("\n--- ALL EXIT STATUS BREAKDOWN ---")
c.execute("""
    SELECT status, 
           count(*), 
           round(sum(pnl_usdt), 2), 
           round(avg(roi_pct), 2),
           sum(case when pnl_usdt > 0 or roi_pct > 0 then 1 else 0 end) as wins,
           sum(case when pnl_usdt < 0 or roi_pct < 0 then 1 else 0 end) as losses
    FROM paper_trades 
    WHERE status != 'OPEN'
    GROUP BY status
    ORDER BY count(*) DESC
""")
for r in c.fetchall():
    print(f"Status: {r[0]:28} | Trades: {r[1]:2} | Total PnL: ${r[2]:7.2f} | Avg ROI: {r[3]:6.2f}% | Wins: {r[4]:2} | Losses: {r[5]:2}")

# Sample of Trailing SL trades
print("\n--- SAMPLE OF TRAILING SL HIT TRADES ---")
c.execute("""
    SELECT id, symbol, side, timeframe, entry_price, exit_price, pnl_usdt, roi_pct, trailing_step, locked_roi_pct
    FROM paper_trades 
    WHERE status = 'TRAILING_SL_HIT'
    ORDER BY id DESC
    LIMIT 15
""")
for r in c.fetchall():
    print(f"ID #{r[0]} | {r[1]} {r[2]} ({r[3]}) | Entry: {r[4]} -> Exit: {r[5]} | PnL: +${r[6]} USDT | ROI: +{r[7]}% | Step: {r[8]} | Locked: {r[9]}%")
