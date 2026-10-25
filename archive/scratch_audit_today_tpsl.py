import sqlite3
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
today_start_ist = datetime(2026, 10, 2, 0, 0, 0, tzinfo=IST)
today_start_ms = int(today_start_ist.timestamp() * 1000)

conn = sqlite3.connect('database/smc_v17.db')
c = conn.cursor()

# 1. Closed trades today
c.execute("""
    SELECT id, symbol, side, timeframe, entry_price, exit_price, pnl_usdt, status, entry_time, exit_time
    FROM paper_trades
    WHERE exit_time >= ?
    ORDER BY exit_time ASC
""", (today_start_ms,))

rows = c.fetchall()

tp_trades = []
sl_trades = []
be_trades = []

for r in rows:
    t_id, sym, side, tf, ep, xp, pnl, status, in_t, out_t = r
    out_dt = datetime.fromtimestamp(out_t / 1000, tz=IST).strftime("%I:%M %p") if out_t else "N/A"
    item = {
        "id": t_id, "sym": sym, "side": side, "tf": tf, "entry": ep, "exit": xp,
        "pnl": pnl or 0.0, "status": status, "time": out_dt
    }
    if status == 'TP_HIT':
        tp_trades.append(item)
    elif status == 'SL_HIT':
        sl_trades.append(item)
    else:
        be_trades.append(item)

print(f"=== TODAY'S CLOSED TRADES (2-OCT-2026) ===")
print(f"Total Closed Today: {len(rows)}")
print(f"  Take Profits (TP): {len(tp_trades)}")
print(f"  Stop Losses (SL):  {len(sl_trades)}")
print(f"  Breakeven/Closed:  {len(be_trades)}")

total_pnl = sum(r[6] or 0.0 for r in rows)
print(f"  Total Realized PnL: ${total_pnl:+.2f} USDT")

print("\n--- TP HITS TODAY ---")
for t in tp_trades:
    print(f"  #{t['id']} | {t['sym']} {t['side']} ({t['tf']}) | Out: {t['time']} | PnL: +${t['pnl']:.2f}")

print("\n--- SL HITS TODAY ---")
for t in sl_trades:
    print(f"  #{t['id']} | {t['sym']} {t['side']} ({t['tf']}) | Out: {t['time']} | PnL: ${t['pnl']:.2f}")

print("\n--- BREAKEVEN / CLEARED EXITS TODAY ---")
for t in be_trades:
    print(f"  #{t['id']} | {t['sym']} {t['side']} ({t['tf']}) | Out: {t['time']} | Status: {t['status']} | PnL: ${t['pnl']:.2f}")

# Active open trades
c.execute("SELECT id, symbol, side, timeframe, entry_price, status, entry_time FROM paper_trades WHERE status='OPEN'")
open_rows = c.fetchall()
print(f"\n=== CURRENTLY ACTIVE OPEN TRADES ({len(open_rows)}) ===")
for r in open_rows:
    in_dt = datetime.fromtimestamp(r[6] / 1000, tz=IST).strftime("%I:%M %p") if r[6] else "N/A"
    print(f"  #{r[0]} | {r[1]} {r[2]} ({r[3]}) | Entry: {r[4]} | Opened: {in_dt}")

conn.close()
