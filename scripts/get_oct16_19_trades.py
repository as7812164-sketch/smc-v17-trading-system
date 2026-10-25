import sqlite3
import json
from datetime import datetime

def check_trades_oct16_19():
    conn = sqlite3.connect("database/smc_v17.db")
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, status, entry_time, exit_time, account_id, mode
        FROM paper_trades
        ORDER BY id DESC
    """).fetchall()

    print(f"Total trades in database: {len(rows)}")

    oct_trades = []
    for r in rows:
        etime = r["exit_time"] or r["entry_time"]
        if etime:
            dt = datetime.fromtimestamp(etime / 1000.0)
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            # Check if between Oct 16 and Oct 19
            if "2026-10-16" <= dt_str[:10] <= "2026-10-19":
                entry_dt = datetime.fromtimestamp((r["entry_time"] or etime) / 1000.0).strftime("%d-%b %H:%M")
                exit_dt = datetime.fromtimestamp((r["exit_time"] or etime) / 1000.0).strftime("%d-%b %H:%M") if r["exit_time"] else "OPEN"
                oct_trades.append((r, entry_dt, exit_dt))

    print(f"\n==================================================================================")
    print(f"TRADES IN PRODUCTION DATABASE BETWEEN 16-OCT AND 19-OCT: {len(oct_trades)} TRADES")
    print(f"==================================================================================")
    
    tot_pnl = 0.0
    wins = 0
    losses = 0
    for r, ent, ext in oct_trades:
        pnl = r["pnl_usdt"] if r["pnl_usdt"] is not None else 0.0
        tot_pnl += pnl
        st = r["status"]
        if st != "OPEN":
            if pnl > 0: wins += 1
            else: losses += 1
        print(f"ID #{r['id']:3d} | {r['symbol']:12} {r['side']:5} | Sec #{r['account_id']:2d} | Entry: {ent} | Exit: {ext:12} | PnL: {pnl:+6.2f} USDT | Status: {st}")

    print("----------------------------------------------------------------------------------")
    print(f"Completed: {wins + losses} (Wins: {wins}, Losses: {losses}) | Total PnL: ${tot_pnl:+.2f} USDT")
    print("==================================================================================\n")
    conn.close()

    # Also check bb20_shadow_ledger.json
    try:
        with open("bb20_shadow_ledger.json", "r") as f:
            bb_data = json.load(f)
        bb_trades = bb_data.get("closed_trades", [])
        print(f"BB 2.0 / 3.0 SHADOW LEDGER TRADES: {len(bb_trades)}")
        oct_bb = []
        for t in bb_trades:
            ts = t.get("exit_time") or t.get("entry_time") or ""
            # parse date
            oct_bb.append(t)
        for t in oct_bb[-10:]:
            print(f"  {t.get('symbol')} {t.get('side')} | PnL: {t.get('pnl_usdt', t.get('pnl_r', 0))} | Outcome: {t.get('outcome')}")
    except Exception as e:
        print("Shadow ledger error:", e)

if __name__ == "__main__":
    check_trades_oct16_19()
