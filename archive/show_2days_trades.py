import sqlite3
from datetime import datetime, timezone, timedelta

def get_2day_trades():
    conn = sqlite3.connect("database/smc_v17.db")
    conn.row_factory = sqlite3.Row

    # Trades from the last 2 days
    rows = conn.execute("SELECT * FROM paper_trades WHERE status != 'OPEN' ORDER BY exit_time DESC LIMIT 12").fetchall()
    
    total_pnl = 0.0
    wins = 0
    losses = 0

    print("================== LAST 2 DAYS TRADING SUMMARY ==================")
    for i, r in enumerate(rows, 1):
        t = dict(r)
        etime = t.get("exit_time") or t.get("entry_time") or 0
        # Convert to IST (UTC + 5:30)
        dt_utc = datetime.fromtimestamp(etime / 1000, tz=timezone.utc)
        dt_ist = dt_utc + timedelta(hours=5, minutes=30)
        time_str = dt_ist.strftime("%d %b %Y, %I:%M %p")

        pnl = float(t.get("pnl_usdt") or 0.0)
        roe = float(t.get("roi_pct") or t.get("pnl_pct") or 0.0)
        dur = t.get("duration_str") or "1h"
        stat = t.get("status")
        side = t.get("side")
        tf = (t.get("timeframe") or "4h").upper()
        sym = t.get("symbol")
        ep = t.get("entry_price")
        xp = t.get("exit_price")
        mae = t.get("mae_pct") or 0.0
        mfe = t.get("mfe_pct") or 0.0

        total_pnl += pnl
        if pnl > 0:
            wins += 1
        else:
            losses += 1

        print(f"#{i:02d} | {sym:8s} | {side:5s} ({tf}) | Status: {stat:13s} | Entry: {ep:<9} | Exit: {xp:<9} | PnL: ${pnl:+6.2f} ({roe:+5.1f}%) | Dur: {dur:7s} | MAE: {mae:.1f}% | MFE: {mfe:.1f}% | {time_str}")

    print("-----------------------------------------------------------------")
    completed = wins + losses
    win_rate = (wins / completed * 100) if completed > 0 else 0.0
    print(f"Total Closed Trades: {completed} | Wins: {wins} | Losses: {losses}")
    print(f"Win Rate: {win_rate:.1f}% | Total Net Realized Profit: ${total_pnl:+.2f} USDT")

    # Also fetch currently open positions
    open_rows = conn.execute("SELECT * FROM paper_trades WHERE status = 'OPEN'").fetchall()
    print(f"\n================== CURRENTLY OPEN POSITIONS ({len(open_rows)}) ==================")
    for op in open_rows:
        o = dict(op)
        print(f"{o.get('symbol')} | {o.get('side')} ({o.get('timeframe')}) | Entry: {o.get('entry_price')} | Size: ${o.get('position_size_usdt')} | TP: {o.get('tp_price')} | SL: {o.get('sl_price')}")

if __name__ == "__main__":
    get_2day_trades()
