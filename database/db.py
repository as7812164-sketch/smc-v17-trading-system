import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import DB_PATH

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,              -- 'BUY' or 'SELL'
            origin_time INTEGER NOT NULL,    -- Candle open timestamp ms
            origin_open REAL NOT NULL,
            origin_high REAL NOT NULL,
            origin_low REAL NOT NULL,
            origin_close REAL NOT NULL,
            displacement_time INTEGER NOT NULL,
            ob_high REAL NOT NULL,
            ob_low REAL NOT NULL,
            target_7pct REAL NOT NULL,
            qualified INTEGER DEFAULT 0,     -- 1 if reached 7% without pre-test
            qualified_time INTEGER,
            status TEXT NOT NULL,            -- 'QUALIFIED', 'ACTIVE', 'TP_HIT', 'SL_HIT', 'INVALIDATED'
            entry_price REAL,
            entry_time INTEGER,
            tp_price REAL,
            sl_price REAL,
            tags TEXT,                       -- JSON string of soft tags e.g. ["FVG", "SWEEP"]
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            UNIQUE(symbol, side, origin_time)
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id INTEGER,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,              -- 'BUY' or 'SELL'
            signal_type TEXT NOT NULL,       -- 'QUALIFIED', 'FIRST_TAP_ENTRY', 'TP_HIT', 'SL_HIT'
            price REAL NOT NULL,
            timestamp INTEGER NOT NULL,
            details TEXT,
            telegram_sent INTEGER DEFAULT 0,
            FOREIGN KEY (zone_id) REFERENCES zones(id)
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_account (
            id INTEGER PRIMARY KEY DEFAULT 1,
            initial_balance REAL DEFAULT 100.0,
            current_balance REAL DEFAULT 100.0,
            total_pnl REAL DEFAULT 0.0,
            win_count INTEGER DEFAULT 0,
            loss_count INTEGER DEFAULT 0
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id INTEGER,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            position_size_usdt REAL NOT NULL,
            tp_price REAL NOT NULL,
            sl_price REAL NOT NULL,
            status TEXT NOT NULL,
            entry_time INTEGER NOT NULL,
            exit_time INTEGER,
            exit_price REAL,
            pnl_usdt REAL,
            pnl_pct REAL
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS sent_alerts (
            alert_key TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            origin_time INTEGER NOT NULL,
            sent_at INTEGER NOT NULL,
            msg_id INTEGER
        );
        """)

        conn.execute("""
        INSERT OR IGNORE INTO paper_account (id, initial_balance, current_balance, total_pnl, win_count, loss_count)
        VALUES (1, 100.0, 100.0, 0.0, 0, 0);
        """)

        # Initialize default metrics if not present
        default_metrics = {
            "reconnects": "0",
            "watchdog_restarts": "0",
            "errors": "0",
            "start_time": str(int(time.time())),
            "last_scan_time": "",
            "last_ob_refresh": "",
            "next_refresh": "",
            "last_alert": "None yet",
            "binance_status": "DISCONNECTED",
            "network_status": "STABLE",
            "coins_active_count": "50"
        }
        for k, v in default_metrics.items():
            conn.execute("INSERT OR IGNORE INTO system_metrics (key, value) VALUES (?, ?)", (k, v))
        conn.commit()

# --- Zone CRUD ---
def save_or_update_zone(z: Dict[str, Any]) -> int:
    now = int(time.time() * 1000)
    tags_str = json.dumps(z.get("tags", [])) if isinstance(z.get("tags"), list) else str(z.get("tags", "[]"))
    with get_connection() as conn:
        cursor = conn.execute("""
        INSERT INTO zones (
            symbol, side, origin_time, origin_open, origin_high, origin_low, origin_close,
            displacement_time, ob_high, ob_low, target_7pct, qualified, qualified_time,
            status, entry_price, entry_time, tp_price, sl_price, tags, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(symbol, side, origin_time) DO UPDATE SET
            status = CASE 
                WHEN zones.status IN ('ACTIVE', 'TP_HIT', 'SL_HIT', 'INVALIDATED') AND excluded.status = 'QUALIFIED' THEN zones.status
                ELSE excluded.status
            END,
            qualified = MAX(zones.qualified, excluded.qualified),
            qualified_time = COALESCE(zones.qualified_time, excluded.qualified_time),
            entry_price = COALESCE(excluded.entry_price, zones.entry_price),
            entry_time = COALESCE(excluded.entry_time, zones.entry_time),
            tp_price = COALESCE(excluded.tp_price, zones.tp_price),
            sl_price = COALESCE(excluded.sl_price, zones.sl_price),
            tags = excluded.tags,
            updated_at = excluded.updated_at
        """, (
            z["symbol"], z["side"], z["origin_time"], z["origin_open"], z["origin_high"],
            z["origin_low"], z["origin_close"], z["displacement_time"], z["ob_high"],
            z["ob_low"], z["target_7pct"], z.get("qualified", 0), z.get("qualified_time"),
            z["status"], z.get("entry_price"), z.get("entry_time"), z.get("tp_price"),
            z.get("sl_price"), tags_str, z.get("created_at", now), now
        ))
        conn.commit()
        return cursor.lastrowid or 0

def get_active_zones(symbol: Optional[str] = None, side: Optional[str] = None) -> List[Dict[str, Any]]:
    query = "SELECT * FROM zones WHERE status IN ('QUALIFIED', 'ACTIVE')"
    params = []
    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)
    if side:
        query += " AND side = ?"
        params.append(side)
    query += " ORDER BY origin_time DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def get_all_zones(symbol: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    query = "SELECT * FROM zones"
    params = []
    if symbol:
        query += " WHERE symbol = ?"
        params.append(symbol)
    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

# --- Signals CRUD ---
def add_signal(zone_id: Optional[int], symbol: str, side: str, signal_type: str,
               price: float, timestamp: int, details: str = "") -> int:
    with get_connection() as conn:
        # Check if identical signal for this zone already exists to prevent duplicate entries
        if zone_id:
            existing = conn.execute(
                "SELECT id FROM signals WHERE zone_id = ? AND signal_type = ?",
                (zone_id, signal_type)
            ).fetchone()
            if existing:
                return existing[0]

        cursor = conn.execute("""
        INSERT INTO signals (zone_id, symbol, side, signal_type, price, timestamp, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (zone_id, symbol, side, signal_type, price, timestamp, details))
        conn.commit()
        return cursor.lastrowid

# --- Sent Alerts Deduplication ---
def is_alert_sent(alert_key: str) -> bool:
    """Checks if this exact alert was already broadcasted to Telegram."""
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM sent_alerts WHERE alert_key = ?", (alert_key,)).fetchone()
        return row is not None

def record_sent_alert(alert_key: str, symbol: str, side: str, signal_type: str, origin_time: int, msg_id: Optional[int] = None):
    """Records an alert as sent so it is NEVER sent again."""
    now = int(time.time() * 1000)
    with get_connection() as conn:
        conn.execute("""
        INSERT OR IGNORE INTO sent_alerts (alert_key, symbol, side, signal_type, origin_time, sent_at, msg_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (alert_key, symbol, side, signal_type, origin_time, now, msg_id))
        conn.commit()

def get_recent_signals(limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("""
        SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

# --- Metrics & Performance Tracking ---
def get_performance_stats() -> Dict[str, Any]:
    with get_connection() as conn:
        total_signals = conn.execute("SELECT COUNT(*) FROM signals WHERE signal_type = 'FIRST_TAP_ENTRY'").fetchone()[0]
        buy_signals = conn.execute("SELECT COUNT(*) FROM signals WHERE signal_type = 'FIRST_TAP_ENTRY' AND side = 'BUY'").fetchone()[0]
        sell_signals = conn.execute("SELECT COUNT(*) FROM signals WHERE signal_type = 'FIRST_TAP_ENTRY' AND side = 'SELL'").fetchone()[0]

        open_pending = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'ACTIVE'").fetchone()[0]
        qualified_untriggered = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'QUALIFIED'").fetchone()[0]

        tp_hits = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'TP_HIT'").fetchone()[0]
        sl_hits = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'SL_HIT'").fetchone()[0]

        buy_tp = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'TP_HIT' AND side = 'BUY'").fetchone()[0]
        buy_sl = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'SL_HIT' AND side = 'BUY'").fetchone()[0]
        sell_tp = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'TP_HIT' AND side = 'SELL'").fetchone()[0]
        sell_sl = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'SL_HIT' AND side = 'SELL'").fetchone()[0]

        active_buy = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'QUALIFIED' AND side = 'BUY'").fetchone()[0]
        active_sell = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'QUALIFIED' AND side = 'SELL'").fetchone()[0]

        completed = tp_hits + sl_hits
        win_rate = (tp_hits / completed * 100) if completed > 0 else 0.0

        buy_completed = buy_tp + buy_sl
        buy_wr = (buy_tp / buy_completed * 100) if buy_completed > 0 else 0.0

        sell_completed = sell_tp + sell_sl
        sell_wr = (sell_tp / sell_completed * 100) if sell_completed > 0 else 0.0

        last_alert = get_metric("last_alert", "None yet")

        return {
            "total_signals": total_signals,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "open_pending": open_pending,
            "qualified_untriggered": qualified_untriggered,
            "tp_hits": tp_hits,
            "sl_hits": sl_hits,
            "wins": tp_hits,
            "losses": sl_hits,
            "win_rate": round(win_rate, 1),
            "buy_wr": round(buy_wr, 1),
            "sell_wr": round(sell_wr, 1),
            "active_buy_zones": active_buy,
            "active_sell_zones": active_sell,
            "total_active_zones": active_buy + active_sell,
            "last_alert": last_alert
        }

# --- System Metrics ---
def set_metric(key: str, value: Any):
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO system_metrics (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        conn.commit()

def get_metric(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM system_metrics WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

def get_all_metrics() -> Dict[str, str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM system_metrics").fetchall()
        return {r["key"]: r["value"] for r in rows}

def increment_metric(key: str, by: int = 1):
    current = int(get_metric(key, "0"))
    set_metric(key, current + by)

# --- Settings ---
def set_setting(key: str, value: str):
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        conn.commit()

def get_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

# --- Paper Trading Simulator (100 USDT) ---
def get_paper_account() -> Dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()
        if not row:
            conn.execute("INSERT OR IGNORE INTO paper_account (id, initial_balance, current_balance, total_pnl, win_count, loss_count) VALUES (1, 100.0, 100.0, 0.0, 0, 0)")
            conn.commit()
            row = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()

        acc = dict(row)
        open_trades = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN'").fetchone()[0]
        acc["open_trades_count"] = open_trades
        completed = acc["win_count"] + acc["loss_count"]
        acc["win_rate"] = round((acc["win_count"] / completed * 100), 1) if completed > 0 else 0.0
        acc["return_pct"] = round(((acc["current_balance"] - acc["initial_balance"]) / acc["initial_balance"] * 100), 2)
        return acc

def open_paper_trade(zone: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deploys exactly 10% of current paper wallet balance into the signal.
    """
    with get_connection() as conn:
        row = conn.execute("SELECT current_balance FROM paper_account WHERE id = 1").fetchone()
        balance = float(row[0]) if row else 100.0

        # Check if already open for this zone
        existing = conn.execute("SELECT * FROM paper_trades WHERE zone_id = ? AND status = 'OPEN'", (zone.get("id"),)).fetchone()
        if existing:
            tr = dict(existing)
            tr["balance_at_entry"] = balance
            tr["expected_tp_usdt"] = round(tr["position_size_usdt"] * 0.04, 2)
            tr["max_sl_usdt"] = round(tr["position_size_usdt"] * 0.03, 2)
            return tr

        # 10% allocation
        position_size = round(balance * 0.10, 2)
        if position_size < 1.0:
            position_size = 1.0

        now = int(time.time() * 1000)
        cursor = conn.execute("""
        INSERT INTO paper_trades (
            zone_id, symbol, side, entry_price, position_size_usdt,
            tp_price, sl_price, status, entry_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        """, (
            zone.get("id"), zone["symbol"], zone["side"], float(zone["entry_price"]),
            position_size, float(zone["tp_price"]), float(zone["sl_price"]), now
        ))
        conn.commit()
        trade_id = cursor.lastrowid
        return {
            "id": trade_id,
            "zone_id": zone.get("id"),
            "symbol": zone["symbol"],
            "side": zone["side"],
            "entry_price": float(zone["entry_price"]),
            "position_size_usdt": position_size,
            "tp_price": float(zone["tp_price"]),
            "sl_price": float(zone["sl_price"]),
            "balance_at_entry": balance,
            "expected_tp_usdt": round(position_size * 0.04, 2),
            "max_sl_usdt": round(position_size * 0.03, 2)
        }

def close_paper_trade(zone: Dict[str, Any], outcome: str) -> Optional[Dict[str, Any]]:
    """
    Closes open paper trade on TP_HIT (+4%) or SL_HIT (-3%).
    Updates balance and total PnL.
    """
    with get_connection() as conn:
        trade = conn.execute("""
        SELECT * FROM paper_trades 
        WHERE (zone_id = ? OR (symbol = ? AND side = ?)) AND status = 'OPEN'
        ORDER BY entry_time DESC LIMIT 1
        """, (zone.get("id"), zone.get("symbol"), zone.get("side"))).fetchone()

        now = int(time.time() * 1000)
        if not trade:
            pos_size = 10.0
            pnl_pct = 4.0 if outcome == "TP_HIT" else -3.0
            pnl_usdt = round(pos_size * (pnl_pct / 100.0), 2)
            exit_price = float(zone.get("tp_price" if outcome == "TP_HIT" else "sl_price", 0))
            cursor = conn.execute("""
            INSERT INTO paper_trades (
                zone_id, symbol, side, entry_price, position_size_usdt,
                tp_price, sl_price, status, entry_time, exit_time, exit_price, pnl_usdt, pnl_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                zone.get("id"), zone["symbol"], zone["side"], float(zone.get("entry_price", 0)),
                pos_size, float(zone.get("tp_price", 0)), float(zone.get("sl_price", 0)),
                outcome, now - 3600000, now, exit_price, pnl_usdt, pnl_pct
            ))
            trade_id = cursor.lastrowid
        else:
            trade_id = trade["id"]
            pos_size = float(trade["position_size_usdt"])
            pnl_pct = 4.0 if outcome == "TP_HIT" else -3.0
            pnl_usdt = round(pos_size * (pnl_pct / 100.0), 2)
            exit_price = float(zone.get("tp_price" if outcome == "TP_HIT" else "sl_price", trade["tp_price"]))
            conn.execute("""
            UPDATE paper_trades SET
                status = ?, exit_time = ?, exit_price = ?, pnl_usdt = ?, pnl_pct = ?
            WHERE id = ?
            """, (outcome, now, exit_price, pnl_usdt, pnl_pct, trade_id))

        is_win = 1 if outcome == "TP_HIT" else 0
        is_loss = 1 if outcome == "SL_HIT" else 0
        conn.execute("""
        UPDATE paper_account SET
            current_balance = round(current_balance + ?, 2),
            total_pnl = round(total_pnl + ?, 2),
            win_count = win_count + ?,
            loss_count = loss_count + ?
        WHERE id = 1
        """, (pnl_usdt, pnl_usdt, is_win, is_loss))
        conn.commit()

        acc = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()
        completed = acc["win_count"] + acc["loss_count"]
        win_rate = round((acc["win_count"] / completed * 100), 1) if completed > 0 else 0.0
        return {
            "trade_id": trade_id,
            "outcome": outcome,
            "pnl_usdt": pnl_usdt,
            "pnl_pct": pnl_pct,
            "position_size": pos_size,
            "new_balance": round(acc["current_balance"], 2),
            "total_pnl": round(acc["total_pnl"], 2),
            "win_count": acc["win_count"],
            "loss_count": acc["loss_count"],
            "win_rate": win_rate
        }

def close_paper_trade_manually(trade_id: int, exit_price: float) -> Dict[str, Any]:
    """Manually close an open position at current mark price."""
    with get_connection() as conn:
        trade = conn.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,)).fetchone()
        if not trade or trade["status"] != "OPEN":
            return {"success": False, "error": "Trade not found or already closed"}

        pos_size = float(trade["position_size_usdt"] or 10.0)
        entry_price = float(trade["entry_price"])
        side = trade["side"].upper()
        now = int(time.time() * 1000)

        if side == "BUY":
            pnl_pct = ((exit_price - entry_price) / entry_price * 100.0) if entry_price > 0 else 0.0
        else:
            pnl_pct = ((entry_price - exit_price) / entry_price * 100.0) if entry_price > 0 else 0.0

        pnl_usdt = round(pos_size * (pnl_pct / 100.0), 4)
        status = "MANUAL_CLOSED"

        conn.execute("""
        UPDATE paper_trades SET
            status = ?, exit_time = ?, exit_price = ?, pnl_usdt = ?, pnl_pct = ?
        WHERE id = ?
        """, (status, now, exit_price, pnl_usdt, round(pnl_pct, 2), trade_id))

        is_win = 1 if pnl_usdt > 0 else 0
        is_loss = 1 if pnl_usdt <= 0 else 0
        conn.execute("""
        UPDATE paper_account SET
            current_balance = round(current_balance + ?, 2),
            total_pnl = round(total_pnl + ?, 2),
            win_count = win_count + ?,
            loss_count = loss_count + ?
        WHERE id = 1
        """, (pnl_usdt, pnl_usdt, is_win, is_loss))
        conn.commit()

        return {
            "success": True,
            "trade_id": trade_id,
            "pnl_usdt": pnl_usdt,
            "pnl_pct": round(pnl_pct, 2),
            "exit_price": exit_price
        }

def get_paper_trades_history(limit: int = 20) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM paper_trades ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def get_open_paper_trades() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM paper_trades WHERE status = 'OPEN' ORDER BY entry_time DESC").fetchall()
        return [dict(r) for r in rows]

def reset_paper_account() -> Dict[str, Any]:
    with get_connection() as conn:
        conn.execute("DELETE FROM paper_trades")
        conn.execute("""
        UPDATE paper_account SET
            initial_balance = 100.0,
            current_balance = 100.0,
            total_pnl = 0.0,
            win_count = 0,
            loss_count = 0
        WHERE id = 1
        """)
        conn.commit()
    return {
        "initial_balance": 100.0,
        "current_balance": 100.0,
        "total_pnl": 0.0,
        "win_count": 0,
        "loss_count": 0,
        "win_rate": 0.0
    }

def get_daily_trades_summary(since_timestamp_ms: int) -> Dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute("""
        SELECT * FROM paper_trades 
        WHERE exit_time >= ? AND status IN ('TP_HIT', 'SL_HIT')
        ORDER BY exit_time ASC
        """, (since_timestamp_ms,)).fetchall()
        trades = [dict(r) for r in rows]

        tp_count = sum(1 for t in trades if t["status"] == "TP_HIT")
        sl_count = sum(1 for t in trades if t["status"] == "SL_HIT")
        day_pnl = sum(t["pnl_usdt"] for t in trades)

        return {
            "trades_count": len(trades),
            "tp_count": tp_count,
            "sl_count": sl_count,
            "day_pnl": round(day_pnl, 2),
            "trades": trades
        }

# Run initialization on import
init_db()

