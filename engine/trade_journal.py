import os
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import BASE_DIR, get_ist_now
from database.db import get_connection

JOURNAL_CSV_PATH = BASE_DIR / "trade_journal_ledger.csv"

from datetime import datetime, timezone

JOURNAL_CSV_PATH = BASE_DIR / "trade_journal_ledger.csv"

QUAD_ACCOUNT_NAMES = {
    1: "Binance 4H Macro",
    2: "Binance 1H Intraday",
    3: "Bitget 4H Macro",
    4: "Bitget 1H Intraday"
}

QUAD_CHANNELS = {
    1: "binance_4h",
    2: "binance_1h",
    3: "bitget_4h",
    4: "bitget_1h"
}

CSV_HEADERS = [
    "Trade #",
    "Timestamp (IST)",
    "Account #",
    "Account Name",
    "Compounding Channel",
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
            account_id INTEGER DEFAULT 1,
            channel TEXT DEFAULT 'binance_4h',
            account_name TEXT DEFAULT 'Binance 4H Macro',
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
            paper_trade_id INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );
        """)
        # Ensure migration columns exist
        for col_name, col_type in [
            ("account_id", "INTEGER DEFAULT 1"),
            ("channel", "TEXT DEFAULT 'binance_4h'"),
            ("account_name", "TEXT DEFAULT 'Binance 4H Macro'"),
            ("paper_trade_id", "INTEGER DEFAULT 0")
        ]:
            try:
                conn.execute(f"ALTER TABLE trade_journal ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass
        conn.commit()

        # Sanitize database from any legacy backtests (2025 historical data, Super Sniper)
        _sanitize_legacy_trades(conn)

    # Ensure CSV exists with headers and is in sync
    _sync_db_to_csv()

def _sanitize_legacy_trades(conn):
    """
    Purges any historical backtest trades (2025 dates, Super Sniper, Decisional) so that
    the live forward-test ledger strictly contains genuine forward-test trades.
    """
    # 1. Purge legacy backtests
    conn.execute("DELETE FROM trade_journal WHERE timestamp_ist LIKE '%2025%' OR notes LIKE '%Super Sniper%' OR notes LIKE '%Decisional%'")
    conn.commit()

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
            r_keys = r.keys() if hasattr(r, 'keys') else []
            acc_id = r["account_id"] if "account_id" in r_keys and r["account_id"] else 1
            acc_name = r["account_name"] if "account_name" in r_keys and r["account_name"] else QUAD_ACCOUNT_NAMES.get(acc_id, f"Account {acc_id}")
            channel = r["channel"] if "channel" in r_keys and r["channel"] else QUAD_CHANNELS.get(acc_id, "binance_4h")
            
            pnl = r["pnl_usdt"]
            roe = r["roe_pct"]
            status = r["status"]
            if status in ("CLOSED_LEGACY", "BREAKEVEN") or (pnl is not None and abs(pnl) < 0.001):
                pnl = 0.0
                roe = 0.0
                status = "BREAKEVEN"

            writer.writerow([
                r["trade_num"],
                r["timestamp_ist"],
                f"Account {acc_id}",
                acc_name,
                channel.upper(),
                r["exchange"],
                r["timeframe"],
                r["symbol"],
                r["side"],
                f"{r['entry_price']:.6f}" if r["entry_price"] else "",
                f"{r['exit_price']:.6f}" if r["exit_price"] else "-",
                f"{r['tp_price']:.6f}" if r["tp_price"] else "",
                f"{r['soft_sl_price']:.6f}" if r["soft_sl_price"] else "",
                f"{r['hard_sl_price']:.6f}" if r["hard_sl_price"] else "",
                status,
                f"${r['margin_usdt']:.2f}",
                f"{r['leverage']}x",
                f"${pnl:+.2f}" if pnl is not None else "$0.00",
                f"{roe:+.2f}%" if roe is not None else "0.00%",
                f"${r['account_balance']:.2f}",
                f"{r['duration_hours']:.1f}h",
                f"{r['mike_score']}/100",
                r["notes"] or ""
            ])

def sync_quad_accounts_to_ledger():
    """
    Synchronizes all trades across Account 1, 2, 3, and 4 from paper_trades into trade_journal and CSV.
    Ensures every entry, exit, PnL, ROE, status, and resulting balance is saved permanently in the ledger.
    """
    init_journal_db_and_csv()
    with get_connection() as conn:
        acc_rows = conn.execute("SELECT id, current_balance, name, channel FROM paper_account").fetchall()
        balances = {r["id"]: float(r["current_balance"] or 50.0) for r in acc_rows}

        pts = conn.execute("""
            SELECT * FROM paper_trades 
            ORDER BY id ASC
        """).fetchall()

        # Delete orphan journal rows that no longer exist in paper_trades
        valid_pt_ids = [r["id"] for r in pts if r["id"]]
        if valid_pt_ids:
            placeholders = ",".join("?" for _ in valid_pt_ids)
            conn.execute(f"DELETE FROM trade_journal WHERE paper_trade_id > 0 AND paper_trade_id NOT IN ({placeholders})", valid_pt_ids)
        else:
            conn.execute("DELETE FROM trade_journal WHERE paper_trade_id > 0")
        conn.commit()

        for pt_row in pts:
            pt = dict(pt_row)
            pt_id = pt["id"]
            status = pt["status"]
            # Skip purely archived reboot duplicates with 0 pnl and matching entry/exit
            if status == "CLOSED_LEGACY" and (pt["pnl_usdt"] is None or abs(float(pt["pnl_usdt"] or 0)) < 0.001):
                continue

            acc_id = pt["account_id"] or 1
            channel = pt["channel"] or QUAD_CHANNELS.get(acc_id, "binance_4h")
            acc_name = QUAD_ACCOUNT_NAMES.get(acc_id, f"Account {acc_id}")
            exchange = (pt["exchange"] or ("BINANCE" if "binance" in channel else "BITGET")).capitalize()
            tf = (pt["timeframe"] or "4h").lower()
            sym = pt["symbol"]
            side = pt["side"]
            entry_p = float(pt["entry_price"] or 0.0)
            exit_p = float(pt["exit_price"]) if pt["exit_price"] is not None else None
            tp_p = float(pt["tp_price"] or 0.0)
            sl_p = float(pt["sl_price"] or 0.0)
            hard_sl_p = float(pt["hard_sl_price"] or 0.0)
            margin = float(pt.get("margin_usdt") or (float(pt.get("position_size_usdt") or 250.0) / 5.0))
            pnl = float(pt["pnl_usdt"]) if pt["pnl_usdt"] is not None else None
            roe = float(pt["roi_pct"]) if pt["roi_pct"] is not None else None

            if exit_p is not None and abs(entry_p - exit_p) < 0.00001 and (pnl is None or abs(pnl) < 0.001):
                pnl = 0.0
                roe = 0.0
                status = "BREAKEVEN"

            entry_time = pt["entry_time"] or int(time.time() * 1000)
            exit_time = pt["exit_time"] or entry_time
            dur_ms = max(0, exit_time - entry_time)
            dur_h = round(max(0.1, dur_ms / 3600000.0), 2)
            ts_ist = datetime.fromtimestamp(entry_time / 1000.0 + 19800, timezone.utc).strftime("%Y-%m-%d %H:%M:%S IST")

            existing = conn.execute("SELECT id FROM trade_journal WHERE paper_trade_id = ? OR (symbol = ? AND side = ? AND abs(entry_price - ?) < 0.0001 AND timestamp_ist LIKE ?)",
                                    (pt_id, sym, side, entry_p, f"{ts_ist[:10]}%")).fetchone()

            notes = f"Hermes 3.0 Quantum [{channel.upper()}] - {pt.get('sentry_reasons', '')}"

            if not existing:
                count = conn.execute("SELECT COUNT(*) as c FROM trade_journal").fetchone()["c"]
                trade_num = count + 1
                conn.execute("""
                    INSERT INTO trade_journal (
                        trade_num, timestamp_ist, account_id, channel, account_name,
                        exchange, timeframe, symbol, side, entry_price, exit_price,
                        tp_price, soft_sl_price, hard_sl_price, status, margin_usdt,
                        leverage, pnl_usdt, roe_pct, account_balance, duration_hours,
                        mike_score, notes, paper_trade_id, created_at, updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        5, ?, ?, ?, ?,
                        95, ?, ?, ?, ?
                    )
                """, (
                    trade_num, ts_ist, acc_id, channel, acc_name,
                    exchange, tf, sym, side, entry_p, exit_p,
                    tp_p, sl_p, hard_sl_p, status, margin,
                    pnl, roe, balances.get(acc_id, 50.0), dur_h,
                    notes, pt_id, entry_time, exit_time
                ))
            else:
                conn.execute("""
                    UPDATE trade_journal SET
                        account_id = ?, channel = ?, account_name = ?,
                        exit_price = ?, status = ?, pnl_usdt = ?, roe_pct = ?,
                        account_balance = ?, duration_hours = ?, notes = ?,
                        updated_at = ?, paper_trade_id = ?
                    WHERE id = ?
                """, (
                    acc_id, channel, acc_name,
                    exit_p, status, pnl, roe,
                    balances.get(acc_id, 50.0), dur_h, notes,
                    exit_time, pt_id, existing["id"]
                ))
        conn.commit()

    _sync_db_to_csv()

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
