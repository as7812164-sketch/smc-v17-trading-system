import os
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import BASE_DIR, get_ist_now
from database.db import get_connection

JOURNAL_CSV_PATH = BASE_DIR / "trade_journal_ledger.csv"

CSV_HEADERS = [
    "Trade #",
    "Timestamp (IST)",
    "Exchange",
    "Timeframe",
    "Symbol",
    "Side",
    "Entry Price",
    "Exit Price",
    "Take Profit",
    "Soft Stop Loss",
    "Hard Stop Loss",
    "Status / Outcome",
    "Margin (USDT)",
    "Leverage",
    "PnL (USDT)",
    "ROE (%)",
    "Account Balance (USDT)",
    "Duration (Hours)",
    "Mike AI Score",
    "Notes"
]

def init_journal_db_and_csv():
    """Initializes trade_journal SQL table and CSV sheet if not exists."""
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS trade_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_num INTEGER,
            timestamp_ist TEXT NOT NULL,
            exchange TEXT NOT NULL,          -- 'Binance' or 'Bitget'
            timeframe TEXT NOT NULL,         -- '1h' or '4h'
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,              -- 'BUY' or 'SELL'
            entry_price REAL NOT NULL,
            exit_price REAL,
            tp_price REAL NOT NULL,
            soft_sl_price REAL,
            hard_sl_price REAL,
            status TEXT NOT NULL,            -- 'OPEN', 'TP_HIT', 'BREAKEVEN', 'SL_HIT'
            margin_usdt REAL NOT NULL,
            leverage INTEGER DEFAULT 5,
            pnl_usdt REAL DEFAULT 0.0,
            roe_pct REAL DEFAULT 0.0,
            account_balance REAL NOT NULL,
            duration_hours REAL DEFAULT 0.0,
            mike_score INTEGER DEFAULT 90,
            notes TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );
        """)
        conn.commit()

    # Ensure CSV exists with headers
    if not JOURNAL_CSV_PATH.exists():
        with open(JOURNAL_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def record_trade_entry(
    exchange: str,
    timeframe: str,
    symbol: str,
    side: str,
    entry_price: float,
    tp_price: float,
    soft_sl_price: float,
    hard_sl_price: float,
    margin_usdt: float,
    account_balance: float,
    mike_score: int = 95,
    notes: str = "First-Tap Order Block Entry"
) -> int:
    """Records a new opened position in DB and CSV."""
    init_journal_db_and_csv()
    now_ist = get_ist_now().strftime("%Y-%m-%d %H:%M:%S IST")
    now_ms = int(time.time() * 1000)

    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM trade_journal").fetchone()["c"]
        trade_num = count + 1
        
        cursor = conn.execute("""
        INSERT INTO trade_journal (
            trade_num, timestamp_ist, exchange, timeframe, symbol, side,
            entry_price, tp_price, soft_sl_price, hard_sl_price, status,
            margin_usdt, leverage, account_balance, mike_score, notes,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, 5, ?, ?, ?, ?, ?)
        """, (
            trade_num, now_ist, exchange, timeframe, symbol, side.upper(),
            entry_price, tp_price, soft_sl_price, hard_sl_price,
            margin_usdt, account_balance, mike_score, notes,
            now_ms, now_ms
        ))
        trade_id = cursor.lastrowid
        conn.commit()

    _sync_db_to_csv()
    return trade_id

def record_trade_exit(
    trade_id: int,
    exit_price: float,
    status: str,  # 'TP_HIT', 'BREAKEVEN', 'SL_HIT'
    pnl_usdt: float,
    roe_pct: float,
    new_balance: float,
    duration_hours: float,
    notes: str = ""
):
    """Updates a closed trade outcome and synchronizes spreadsheet."""
    init_journal_db_and_csv()
    now_ms = int(time.time() * 1000)
    
    with get_connection() as conn:
        conn.execute("""
        UPDATE trade_journal SET
            exit_price = ?,
            status = ?,
            pnl_usdt = ?,
            roe_pct = ?,
            account_balance = ?,
            duration_hours = ?,
            notes = CASE WHEN ? != '' THEN ? ELSE notes END,
            updated_at = ?
        WHERE id = ?
        """, (exit_price, status, pnl_usdt, roe_pct, new_balance, duration_hours, notes, notes, now_ms, trade_id))
        conn.commit()

        # Fetch trade data for Mike's Self-Improving Reflection
        row = conn.execute("SELECT * FROM trade_journal WHERE id = ?", (trade_id,)).fetchone()
        if row:
            try:
                from ai.self_improving_engine import mike_brain
                mike_brain.reflect_on_trade({
                    "symbol": row["symbol"],
                    "status": status,
                    "pnl_usdt": pnl_usdt,
                    "roe_pct": roe_pct,
                    "duration_hours": duration_hours,
                    "entry_price": row["entry_price"],
                    "exit_price": exit_price
                })
            except Exception as e:
                print(f"Error in Mike AI trade reflection: {e}")

    _sync_db_to_csv()

def _sync_db_to_csv():
    """Dumps all database trade entries into trade_journal_ledger.csv cleanly."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM trade_journal ORDER BY trade_num ASC").fetchall()

    with open(JOURNAL_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for r in rows:
            writer.writerow([
                r["trade_num"],
                r["timestamp_ist"],
                r["exchange"],
                r["timeframe"],
                r["symbol"],
                r["side"],
                f"{r['entry_price']:.6f}" if r["entry_price"] else "",
                f"{r['exit_price']:.6f}" if r["exit_price"] else "-",
                f"{r['tp_price']:.6f}" if r["tp_price"] else "",
                f"{r['soft_sl_price']:.6f}" if r["soft_sl_price"] else "",
                f"{r['hard_sl_price']:.6f}" if r["hard_sl_price"] else "",
                r["status"],
                f"${r['margin_usdt']:.2f}",
                f"{r['leverage']}x",
                f"${r['pnl_usdt']:+.2f}" if r["pnl_usdt"] is not None else "$0.00",
                f"{r['roe_pct']:+.2f}%" if r["roe_pct"] is not None else "0.00%",
                f"${r['account_balance']:.2f}",
                f"{r['duration_hours']:.1f}h",
                f"{r['mike_score']}/100",
                r["notes"] or ""
            ])

    # Optional sync to MongoDB Atlas if available
    try:
        from database.mongo_client import sync_trades_to_mongo, is_mongo_connected
        if is_mongo_connected():
            trade_dicts = [dict(r) for r in rows]
            for t in trade_dicts:
                t["trade_id"] = t.get("trade_num") or t.get("id")
            sync_trades_to_mongo(trade_dicts)
    except Exception:
        pass

def get_all_journal_trades() -> List[Dict[str, Any]]:
    """Returns list of all trades for Web Dashboard and API."""
    init_journal_db_and_csv()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM trade_journal ORDER BY trade_num DESC").fetchall()
        return [dict(r) for r in rows]

# Initialize on import
init_journal_db_and_csv()
