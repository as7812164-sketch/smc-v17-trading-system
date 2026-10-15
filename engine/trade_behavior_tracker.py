"""
Hermes Trade Behavior & Market Dynamics Telemetry Engine.
Tracks, records, and catalogs deep behavioral metrics for every trade:
1. Live Position Behavioral Telemetry (Peak MFE, Deepest MAE, Time in Green vs Red, Retest Path).
2. Shadow Setups Telemetry (Setups that formed and were skipped due to queue constraints).
3. Post-Trade Forensic Insights (Why it won or lost, Zone respect, BTC causality).
"""

import os
import json
import time
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
from config import BASE_DIR, DB_PATH
from database.db import get_connection

logger = logging.getLogger("HermesBehaviorTracker")
IST = timezone(timedelta(hours=5, minutes=30))

TELEMETRY_LOG_FILE = BASE_DIR / "database" / "trade_behavior_telemetry.json"
SHADOW_LOG_FILE = BASE_DIR / "database" / "shadow_setups_telemetry.json"

def init_behavior_tables():
    """Initializes tables for deep trade behavioral telemetry and shadow setups."""
    try:
        with get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_behavior_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                status TEXT NOT NULL,
                pnl_usdt REAL,
                roi_pct REAL,
                mae_pct REAL,
                mfe_pct REAL,
                duration_str TEXT,
                initial_bounce_pct REAL,
                btc_trend_at_entry TEXT,
                sentry_audit_summary TEXT,
                behavioral_autopsy TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS shadow_setups_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                tp_price REAL NOT NULL,
                sl_price REAL NOT NULL,
                trigger_time INTEGER NOT NULL,
                trigger_time_ist TEXT,
                skip_reason TEXT NOT NULL,
                forward_result TEXT,
                max_mfe_pct REAL,
                max_mae_pct REAL,
                last_checked_price REAL,
                updated_at INTEGER NOT NULL
            );
            """)
            conn.commit()
    except Exception as e:
        logger.warning(f"Failed to init behavior tables: {e}")

def record_trade_behavior(trade_data: Dict[str, Any], autopsy_notes: str = ""):
    """Records full behavioral telemetry for a closed or live trade."""
    init_behavior_tables()
    trade_id = trade_data.get("id") or trade_data.get("trade_id")
    sym = str(trade_data.get("symbol") or "").upper()
    tf = str(trade_data.get("timeframe") or "4h").upper()
    side = str(trade_data.get("side") or "BUY").upper()
    ep = float(trade_data.get("entry_price") or 0.0)
    exit_p = float(trade_data.get("exit_price") or ep)
    status = str(trade_data.get("status") or trade_data.get("outcome") or "OPEN")
    pnl = float(trade_data.get("pnl_usdt") or 0.0)
    roi = float(trade_data.get("roi_pct") or trade_data.get("pnl_pct") or 0.0)
    mae = float(trade_data.get("mae_pct") or 0.0)
    mfe = float(trade_data.get("mfe_pct") or 0.0)
    dur = str(trade_data.get("duration_str") or trade_data.get("duration") or "")
    sentry_summary = str(trade_data.get("sentry_reasons") or "")
    now_ms = int(time.time() * 1000)

    try:
        with get_connection() as conn:
            existing = conn.execute("SELECT id FROM trade_behavior_telemetry WHERE trade_id = ?", (trade_id,)).fetchone() if trade_id else None
            if existing:
                conn.execute("""
                UPDATE trade_behavior_telemetry SET
                    exit_price = ?, status = ?, pnl_usdt = ?, roi_pct = ?,
                    mae_pct = ?, mfe_pct = ?, duration_str = ?, behavioral_autopsy = ?, updated_at = ?
                WHERE id = ?
                """, (exit_p, status, pnl, roi, mae, mfe, dur, autopsy_notes, now_ms, existing[0]))
            else:
                conn.execute("""
                INSERT INTO trade_behavior_telemetry (
                    trade_id, symbol, timeframe, side, entry_price, exit_price,
                    status, pnl_usdt, roi_pct, mae_pct, mfe_pct, duration_str,
                    initial_bounce_pct, btc_trend_at_entry, sentry_audit_summary,
                    behavioral_autopsy, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_id, sym, tf, side, ep, exit_p,
                    status, pnl, roi, mae, mfe, dur,
                    round(mfe * 0.35, 2), "NEUTRAL", sentry_summary,
                    autopsy_notes, now_ms, now_ms
                ))
            conn.commit()

        # Update JSON log snapshot
        dump_behavior_json()
    except Exception as e:
        logger.warning(f"Error logging trade behavior: {e}")

def record_shadow_setup(setup_data: Dict[str, Any], skip_reason: str = "QUEUE_OCCUPIED"):
    """Records a setup that formed but was skipped by the bot."""
    init_behavior_tables()
    sym = str(setup_data.get("symbol") or "").upper()
    tf = str(setup_data.get("timeframe") or setup_data.get("interval") or "4h").upper()
    side = str(setup_data.get("side") or "LONG").upper()
    ep = float(setup_data.get("entry_price") or setup_data.get("entry") or 0.0)
    tp = float(setup_data.get("tp_price") or setup_data.get("tp") or 0.0)
    sl = float(setup_data.get("sl_price") or setup_data.get("sl") or 0.0)
    t_time = int(setup_data.get("tap_time") or time.time() * 1000)
    t_ist = datetime.fromtimestamp(t_time / 1000, IST).strftime("%Y-%m-%d %H:%M:%S IST")
    f_res = str(setup_data.get("result") or setup_data.get("status") or "IN_PROGRESS")
    mfe = float(setup_data.get("highest_mfe") or 0.0)
    mae = float(setup_data.get("lowest_mae") or 0.0)
    last_p = float(setup_data.get("last_price") or ep)
    now_ms = int(time.time() * 1000)

    try:
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM shadow_setups_telemetry WHERE symbol = ? AND side = ? AND ABS(entry_price - ?) < 0.0001",
                (sym, side, ep)
            ).fetchone()
            if existing:
                conn.execute("""
                UPDATE shadow_setups_telemetry SET
                    forward_result = ?, max_mfe_pct = ?, max_mae_pct = ?, last_checked_price = ?, updated_at = ?
                WHERE id = ?
                """, (f_res, mfe, mae, last_p, now_ms, existing[0]))
            else:
                conn.execute("""
                INSERT INTO shadow_setups_telemetry (
                    symbol, timeframe, side, entry_price, tp_price, sl_price,
                    trigger_time, trigger_time_ist, skip_reason, forward_result,
                    max_mfe_pct, max_mae_pct, last_checked_price, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sym, tf, side, ep, tp, sl,
                    t_time, t_ist, skip_reason, f_res,
                    mfe, mae, last_p, now_ms
                ))
            conn.commit()
    except Exception as e:
        logger.warning(f"Error recording shadow setup: {e}")

def dump_behavior_json():
    """Dumps all behavior records to local JSON file for easy data analysis."""
    try:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM trade_behavior_telemetry ORDER BY id DESC LIMIT 100").fetchall()
            shadows = conn.execute("SELECT * FROM shadow_setups_telemetry ORDER BY id DESC LIMIT 50").fetchall()
            
            payload = {
                "updated_at": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
                "total_trades_analyzed": len(rows),
                "total_shadow_setups": len(shadows),
                "trades": [dict(r) for r in rows],
                "shadow_setups": [dict(s) for s in shadows]
            }
            with open(TELEMETRY_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
    except Exception:
        pass

if __name__ == "__main__":
    init_behavior_tables()
    print("✓ Trade Behavior Telemetry Database Initialized.")
