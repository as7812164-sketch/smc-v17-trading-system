import sqlite3

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()

# Check columns related to trailing
c.execute("""
    SELECT count(*), 
           sum(case when be_locked = 1 then 1 else 0 end) as be_locked_count,
           sum(case when trailing_step > 0 then 1 else 0 end) as trailing_step_count,
           sum(case when roi_pct > 0 and roi_pct < 15.0 then 1 else 0 end) as partial_or_trailed_wins,
           sum(case when roi_pct >= 14.9 then 1 else 0 end) as full_tp_wins,
           sum(case when roi_pct < 0 then 1 else 0 end) as losses
    FROM paper_trades 
    WHERE status = 'CLOSED'
""")
row = c.fetchone()
print(f"Total Closed Trades: {row[0]}")
print(f"Trades with BE locked: {row[1]}")
print(f"Trades with trailing_step > 0: {row[2]}")
print(f"Trades closed at partial / trailed profit (0 < ROI < 15%): {row[3]}")
print(f"Trades closed at Full TP (ROI >= 15%): {row[4]}")
print(f"Trades closed at Loss (ROI < 0): {row[5]}")

# Let's inspect some specific winning trades to see their exit prices and trailing behavior
c.execute("""
    SELECT id, symbol, side, timeframe, entry_price, exit_price, tp_price, sl_price, roi_pct, pnl_usdt, be_locked, trailing_step, locked_roi_pct, trailing_sl_price
    FROM paper_trades 
    WHERE status = 'CLOSED' AND roi_pct > 0
    ORDER BY id DESC
    LIMIT 20
""")
wins = c.fetchall()
print("\nSample 20 Winning Trades:")
for w in wins:
    print(w)
