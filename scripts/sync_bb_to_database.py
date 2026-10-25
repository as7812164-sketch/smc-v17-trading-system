"""
SYNC BB 3.0 SNIPER TRADES & BALANCES TO SMC_V17.DB
===================================================
Unifies bb20_shadow_ledger.json with sqlite database/smc_v17.db
so all BB 3.0 trades, SL hits, and section balances appear on the website in real-time.
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
DB_PATH = os.path.join(ROOT_DIR, "database", "smc_v17.db")
LEDGER_PATH = os.path.join(ROOT_DIR, "bb20_shadow_ledger.json")

def parse_iso_ms(iso_str: str) -> int:
    try:
        dt = datetime.fromisoformat(iso_str)
        return int(dt.timestamp() * 1000)
    except Exception:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

def sync():
    if not os.path.exists(LEDGER_PATH) or not os.path.exists(DB_PATH):
        print("Files not found.")
        return

    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Backfill closed trades
    closed_trades = ledger.get("closed_trades", [])
    print(f"Syncing {len(closed_trades)} closed BB 3.0 trades to paper_trades table...")

    inserted_cnt = 0
    for t in closed_trades:
        sym = t.get("symbol")
        side = t.get("side")
        entry_p = float(t.get("mt_entry", 0.0))
        exit_p = float(t.get("exit_price", 0.0))
        dollar_pnl = float(t.get("dollar_pnl", 0.0))
        sec_id = int(t.get("section_id", 1))
        outcome = t.get("outcome", "CLOSED")
        
        entry_ms = parse_iso_ms(t.get("filled_at") or t.get("armed_at"))
        exit_ms = parse_iso_ms(t.get("closed_at"))

        # Check if trade already exists in paper_trades
        c.execute("""
            SELECT id FROM paper_trades 
            WHERE symbol = ? AND side = ? AND mode = 'BB_3.0_SNIPER' 
            AND ABS(entry_price - ?) < 0.0001 AND status = 'CLOSED'
        """, (sym, side, entry_p))
        row = c.fetchone()

        pnl_pct = round((dollar_pnl / 2.50) * 100.0, 2) # based on $2.50 risk

        if not row:
            c.execute("""
                INSERT INTO paper_trades (
                    symbol, side, entry_price, position_size_usdt, tp_price, sl_price,
                    status, entry_time, exit_time, exit_price, pnl_usdt, pnl_pct,
                    timeframe, exchange, channel, account_id, mode, autopsy_diagnosis, roi_pct
                ) VALUES (
                    ?, ?, ?, 250.0, ?, ?,
                    'CLOSED', ?, ?, ?, ?, ?,
                    '15m', 'BITGET', ?, ?, 'BB_3.0_SNIPER', ?, ?
                )
            """, (
                sym, side, entry_p, float(t.get("target_1r", 0.0)), float(t.get("sl", 0.0)),
                entry_ms, exit_ms, exit_p, dollar_pnl, pnl_pct,
                f"sec_{sec_id}", sec_id, outcome, pnl_pct
            ))
            inserted_cnt += 1
            print(f"  [INSERTED] #{sym} {side} | PnL: ${dollar_pnl:+.2f} ({outcome}) | Exit: {t.get('closed_at')}")
        else:
            print(f"  [EXISTS] #{sym} {side} already in paper_trades (id {row[0]})")

    # 2. Update active positions if any
    active_positions = ledger.get("active_positions", {})
    for sym, pos in active_positions.items():
        sec_id = int(pos.get("section_id", 1))
        side = pos.get("side")
        entry_p = float(pos.get("mt_entry", 0.0))
        entry_ms = parse_iso_ms(pos.get("filled_at"))
        
        c.execute("""
            SELECT id FROM paper_trades 
            WHERE symbol = ? AND side = ? AND status = 'OPEN' AND mode = 'BB_3.0_SNIPER'
        """, (sym, side))
        if not c.fetchone():
            c.execute("""
                INSERT INTO paper_trades (
                    symbol, side, entry_price, position_size_usdt, tp_price, sl_price,
                    status, entry_time, pnl_usdt, pnl_pct, timeframe, exchange, channel, account_id, mode
                ) VALUES (
                    ?, ?, ?, 250.0, ?, ?,
                    'OPEN', ?, 0.0, 0.0, '15m', 'BITGET', ?, ?, 'BB_3.0_SNIPER'
                )
            """, (
                sym, side, entry_p, float(pos.get("target_1r", 0.0)), float(pos.get("sl", 0.0)),
                entry_ms, f"sec_{sec_id}", sec_id
            ))
            print(f"  [ACTIVE INSERTED] #{sym} {side} OPEN")

    # 3. Sync Section Balances in paper_account
    sections = ledger.get("sections", {})
    for s_id_str, s in sections.items():
        s_id = int(s_id_str)
        curr_bal = float(s.get("balance", 50.0))
        pnl = float(s.get("pnl_usd", 0.0))
        wins = int(s.get("wins", 0))
        losses = int(s.get("losses", 0))
        
        c.execute("""
            UPDATE paper_account 
            SET current_balance = ?, total_pnl = ?, win_count = ?, loss_count = ?
            WHERE id = ?
        """, (curr_bal, pnl, wins, losses, s_id))
        print(f"  [SECTION UPDATED] Sec #{s_id}: Bal ${curr_bal:.2f} | PnL ${pnl:+.2f} | {wins}W {losses}L")

    conn.commit()
    conn.close()
    print(f"\n[SUCCESS] Sync Complete! {inserted_cnt} new trades inserted into paper_trades.")

if __name__ == "__main__":
    sync()
