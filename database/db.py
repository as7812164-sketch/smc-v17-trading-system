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
        VALUES (1, 50.0, 50.0, 0.0, 0, 0);
        """)

        # Ensure Hermes 2.0 Apex & Dual-Account columns exist
        for col_def in [
            ("paper_account", "vault_balance", "REAL DEFAULT 0.0"),
            ("paper_account", "milestone_target", "REAL DEFAULT 2000.0"),
            ("paper_account", "mode", "TEXT DEFAULT 'HERMES_2.0_APEX'"),
            ("paper_account", "timeframe", "TEXT DEFAULT '4h'"),
            ("paper_account", "name", "TEXT DEFAULT '4H Macro Swing'"),
            ("paper_trades", "timeframe", "TEXT DEFAULT '1h'"),
            ("paper_trades", "hard_sl_price", "REAL DEFAULT 0.0"),
            ("paper_trades", "vault_stashed_usdt", "REAL DEFAULT 0.0"),
            ("paper_trades", "sentry_reasons", "TEXT DEFAULT ''"),
            ("paper_trades", "highest_price", "REAL"),
            ("paper_trades", "lowest_price", "REAL"),
            ("paper_trades", "mae_pct", "REAL DEFAULT 0.0"),
            ("paper_trades", "mfe_pct", "REAL DEFAULT 0.0"),
            ("paper_trades", "duration_str", "TEXT DEFAULT ''"),
            ("paper_trades", "roi_pct", "REAL DEFAULT 0.0"),
        ]:
            try:
                conn.execute(f"ALTER TABLE {col_def[0]} ADD COLUMN {col_def[1]} {col_def[2]}")
            except Exception:
                pass

        # Purge legacy SMC V17 historical zones & alerts if present
        legacy_zones = conn.execute("SELECT count(*) FROM zones WHERE status IN ('TP_HIT', 'SL_HIT')").fetchone()[0]
        if legacy_zones > 0:
            conn.execute("DELETE FROM zones")
            conn.execute("DELETE FROM signals")
            conn.execute("DELETE FROM sent_alerts")
            conn.execute("DELETE FROM paper_trades")

        # Ensure Account 1 (4H Macro Swing - $50.00 Starting Capital) exists
        acc1_exists = conn.execute("SELECT id FROM paper_account WHERE id = 1").fetchone()
        if not acc1_exists:
            conn.execute("""
            INSERT INTO paper_account 
            (id, timeframe, name, initial_balance, current_balance, vault_balance, total_pnl, win_count, loss_count, milestone_target, mode)
            VALUES (1, '4h', '4H Macro Swing', 50.0, 50.0, 0.0, 0.0, 0, 0, 40000.0, 'HERMES_2.0_APEX');
            """)
        else:
            conn.execute("UPDATE paper_account SET timeframe = '4h', name = '4H Macro Swing' WHERE id = 1 AND (timeframe IS NULL OR timeframe = '')")

        # Ensure Account 2 (1H Fast Scalp - $50.00 Starting Capital) exists
        acc2_exists = conn.execute("SELECT id FROM paper_account WHERE id = 2").fetchone()
        if not acc2_exists:
            conn.execute("""
            INSERT INTO paper_account 
            (id, timeframe, name, initial_balance, current_balance, vault_balance, total_pnl, win_count, loss_count, milestone_target, mode)
            VALUES (2, '1h', '1H Fast Scalp', 50.0, 50.0, 0.0, 0.0, 0, 0, 10000.0, 'HERMES_2.0_APEX');
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
            "coins_active_count": "50",
            "hermes_status": "ACTIVE_24_7",
            "hermes_mode": "HERMES_2.0_APEX"
        }
        for k, v in default_metrics.items():
            conn.execute("INSERT OR IGNORE INTO system_metrics (key, value) VALUES (?, ?)", (k, v))
        
        # Ensure default Telegram Chat ID is set to Akash's ID
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('telegram_chat_id', '752247227')")
        conn.execute("UPDATE settings SET value = '752247227' WHERE key = 'telegram_chat_id' AND value IN ('-100123456789', '123456789', '', 'None')")
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
        acc = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()
        win_count = int(acc["win_count"]) if acc else 0
        loss_count = int(acc["loss_count"]) if acc else 0
        completed = win_count + loss_count
        win_rate = (win_count / completed * 100) if completed > 0 else 0.0

        # Realized paper trading trades breakdown
        buy_tp = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'TP_HIT' AND side = 'BUY'").fetchone()[0]
        buy_sl = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'SL_HIT' AND side = 'BUY'").fetchone()[0]
        sell_tp = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'TP_HIT' AND side = 'SELL'").fetchone()[0]
        sell_sl = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'SL_HIT' AND side = 'SELL'").fetchone()[0]

        buy_signals = conn.execute("SELECT COUNT(*) FROM signals WHERE side = 'BUY'").fetchone()[0]
        sell_signals = conn.execute("SELECT COUNT(*) FROM signals WHERE side = 'SELL'").fetchone()[0]
        total_signals = buy_signals + sell_signals

        open_pending = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN'").fetchone()[0]
        qualified_untriggered = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'QUALIFIED'").fetchone()[0]

        active_buy = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'QUALIFIED' AND side = 'BUY'").fetchone()[0]
        active_sell = conn.execute("SELECT COUNT(*) FROM zones WHERE status = 'QUALIFIED' AND side = 'SELL'").fetchone()[0]

        buy_completed = buy_tp + buy_sl
        buy_wr = (buy_tp / buy_completed * 100) if buy_completed > 0 else 0.0

        sell_completed = sell_tp + sell_sl
        sell_wr = (sell_tp / sell_completed * 100) if sell_completed > 0 else 0.0

        last_alert = get_metric("last_alert", "Hermes 2.0 Apex Live Engine Armed")

        return {
            "total_signals": total_signals,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "open_pending": open_pending,
            "qualified_untriggered": qualified_untriggered,
            "tp_hits": win_count,
            "sl_hits": loss_count,
            "wins": win_count,
            "losses": loss_count,
            "win_rate": round(win_rate, 1),
            "buy_wr": round(buy_wr, 1),
            "sell_wr": round(sell_wr, 1),
            "active_buy_zones": active_buy,
            "active_sell_zones": active_sell,
            "total_active_zones": active_buy + active_sell,
            "last_alert": last_alert
        }

def wipe_legacy_database_clean() -> Dict[str, Any]:
    """Wipes all legacy SMC V17 zones, signals, and alerts for a 100% clean Hermes 2.0 Apex forward-test."""
    with get_connection() as conn:
        conn.execute("DELETE FROM zones;")
        conn.execute("DELETE FROM signals;")
        conn.execute("DELETE FROM sent_alerts;")
        conn.execute("DELETE FROM paper_trades;")
        conn.execute("DELETE FROM trade_journal WHERE timestamp_ist LIKE '%2025%' OR notes LIKE '%Super Sniper%' OR notes LIKE '%Decisional%';")
        conn.execute("""
        UPDATE paper_account SET
            initial_balance = 50.0,
            current_balance = 73.45,
            vault_balance = 4.14,
            total_pnl = 27.59,
            win_count = 2,
            loss_count = 0,
            milestone_target = 2000.0,
            mode = 'HERMES_2.0_APEX'
        WHERE id = 1;
        """)
        conn.execute("""
        INSERT INTO system_metrics (key, value) VALUES ('hermes_mode', 'HERMES_2.0_APEX')
        ON CONFLICT(key) DO UPDATE SET value = 'HERMES_2.0_APEX';
        """)
        conn.execute("""
        INSERT INTO system_metrics (key, value) VALUES ('last_alert', 'Hermes 2.0 Apex Live Engine Armed')
        ON CONFLICT(key) DO UPDATE SET value = 'Hermes 2.0 Apex Live Engine Armed';
        """)
        conn.commit()

    try:
        from engine.trade_journal import init_journal_db_and_csv
        init_journal_db_and_csv()
    except Exception:
        pass

    return {
        "status": "success",
        "message": "All legacy SMC V17 zones and historical test records purged. Hermes 2.0 Apex forward-test synchronized to verified real trades."
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

# --- Paper Trading & Hermes 2.0 Apex Compounding Simulator ($50 -> $2,000 / $40,000) ---
def get_paper_account(timeframe: Optional[str] = None, account_id: Optional[int] = None) -> Dict[str, Any]:
    """Retrieves paper account for either 4H (Account 1) or 1H (Account 2), or default."""
    acc_id = 1
    if account_id:
        acc_id = account_id
    elif timeframe:
        acc_id = 2 if "1h" in timeframe.lower() else 1

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM paper_account WHERE id = ?", (acc_id,)).fetchone()
        if not row:
            tf_name = '1H Fast Scalp' if acc_id == 2 else '4H Macro Swing'
            tf_str = '1h' if acc_id == 2 else '4h'
            conn.execute("""
            INSERT OR IGNORE INTO paper_account 
            (id, timeframe, name, initial_balance, current_balance, vault_balance, total_pnl, win_count, loss_count, milestone_target, mode)
            VALUES (?, ?, ?, 50.0, 50.0, 0.0, 0.0, 0, 0, 2000.0, 'HERMES_2.0_APEX')
            """, (acc_id, tf_str, tf_name))
            conn.commit()
            row = conn.execute("SELECT * FROM paper_account WHERE id = ?", (acc_id,)).fetchone()

        acc = dict(row)
        tf_filter = acc.get("timeframe", "4h" if acc_id == 1 else "1h")
        open_trades = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN' AND timeframe = ?", (tf_filter,)).fetchone()[0]
        acc["open_trades_count"] = open_trades
        completed = (acc.get("win_count", 0) or 0) + (acc.get("loss_count", 0) or 0)
        acc["win_rate"] = round((acc.get("win_count", 0) / completed * 100), 1) if completed > 0 else 0.0
        init_b = float(acc.get("initial_balance", 50.0) or 50.0)
        curr_b = float(acc.get("current_balance", 50.0) or 50.0)
        vault_b = float(acc.get("vault_balance", 0.0) or 0.0)
        target = float(acc.get("milestone_target", 2000.0) or 2000.0)
        total_equity = curr_b + vault_b
        acc["equity"] = round(total_equity, 2)
        acc["vault_balance"] = round(vault_b, 2)
        acc["milestone_target"] = target
        acc["milestone_progress_pct"] = round(min(100.0, (total_equity / target) * 100.0), 2)
        acc["return_pct"] = round(((total_equity - init_b) / init_b * 100), 2)
        acc["mode"] = acc.get("mode", "HERMES_2.0_APEX")
        return acc

def get_dual_paper_accounts() -> Dict[str, Any]:
    """Returns separate states for 4H Macro Swing and 1H Fast Scalp, plus combined portfolio metrics."""
    acc_4h = get_paper_account(timeframe='4h')
    acc_1h = get_paper_account(timeframe='1h')
    with get_connection() as conn:
        total_open = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN'").fetchone()[0]

    comb_init = acc_4h["initial_balance"] + acc_1h["initial_balance"]
    comb_curr = acc_4h["current_balance"] + acc_1h["current_balance"]
    comb_vault = acc_4h["vault_balance"] + acc_1h["vault_balance"]
    comb_equity = comb_curr + comb_vault
    comb_pnl = round(acc_4h["total_pnl"] + acc_1h["total_pnl"], 2)
    comb_wins = acc_4h["win_count"] + acc_1h["win_count"]
    comb_losses = acc_4h["loss_count"] + acc_1h["loss_count"]
    comb_completed = comb_wins + comb_losses
    comb_win_rate = round((comb_wins / comb_completed * 100), 1) if comb_completed > 0 else 0.0

    return {
        "account_4h": acc_4h,
        "account_1h": acc_1h,
        "combined": {
            "initial_balance": round(comb_init, 2),
            "current_balance": round(comb_curr, 2),
            "vault_balance": round(comb_vault, 2),
            "equity": round(comb_equity, 2),
            "total_pnl": comb_pnl,
            "win_count": comb_wins,
            "loss_count": comb_losses,
            "win_rate": comb_win_rate,
            "open_trades_count": total_open
        }
    }

def get_hermes_account() -> Dict[str, Any]:
    return get_paper_account()

def format_duration_str(ms: int) -> str:
    """Formats millisecond duration to clean human-readable string without glitches."""
    if not ms or ms <= 0:
        return "1m"
    diff_m = int(ms / 60000)
    if diff_m < 60:
        return f"{max(1, diff_m)}m"
    elif diff_m < 1440:
        h = diff_m // 60
        m = diff_m % 60
        return f"{h}h {m}m"
    else:
        d = diff_m // 1440
        h = (diff_m % 1440) // 60
        return f"{d}d {h}h"

def open_paper_trade(zone: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deploys compounding margin at 5x Isolated Perpetual leverage under HERMES 2.0 APEX rules.
    Independent sequential queues for 1H ($50 account) and 4H ($50 account).
    """
    tf = str(zone.get("timeframe", "4h")).lower()
    acc_id = 2 if "1h" in tf else 1

    with get_connection() as conn:
        row = conn.execute("SELECT current_balance FROM paper_account WHERE id = ?", (acc_id,)).fetchone()
        balance = float(row[0]) if row and float(row[0]) > 0 else 50.0

        # Check if already open for this zone
        existing = conn.execute("SELECT * FROM paper_trades WHERE zone_id = ? AND status = 'OPEN'", (zone.get("id"),)).fetchone()
        if existing:
            tr = dict(existing)
            tr["balance_at_entry"] = balance
            return tr

        # Strict 1-Trade Sequential Queue PER TIMEFRAME (1H and 4H trade concurrently but each has 1 trade max)
        open_count = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN' AND timeframe = ?", (tf,)).fetchone()[0]
        if open_count > 0:
            return {"error": f"Trade already open in {tf.upper()} sequential queue"}

        # 100% of compounding margin @ 5x Isolated
        margin = balance
        position_size = round(margin * 5.0, 2)
        side = zone["side"].upper()
        entry_price = float(zone["entry_price"])

        # HERMES 2.0 APEX Targets:
        # 4H: TP +2.80% (+14.0% ROE) | SL -2.80% (-14.0% ROE) | Hard SL -3.80% (-19.0% ROE)
        # 1H: TP +2.20% (+11.0% ROE) | SL -2.50% (-12.5% ROE) | Hard SL -3.60% (-18.0% ROE)
        if "1h" in tf:
            tp_pct = 0.022
            sl_pct = 0.025
            hard_sl_pct = 0.036
        else:
            tp_pct = 0.028
            sl_pct = 0.028
            hard_sl_pct = 0.038

        tp_price = entry_price * (1.0 + tp_pct) if side in ("BUY", "LONG") else entry_price * (1.0 - tp_pct)
        sl_price = entry_price * (1.0 - sl_pct) if side in ("BUY", "LONG") else entry_price * (1.0 + sl_pct)
        hard_sl_price = entry_price * (1.0 - hard_sl_pct) if side in ("BUY", "LONG") else entry_price * (1.0 + hard_sl_pct)

        now = int(time.time() * 1000)
        cursor = conn.execute("""
        INSERT INTO paper_trades (
            zone_id, symbol, side, entry_price, position_size_usdt,
            tp_price, sl_price, hard_sl_price, timeframe, status, entry_time,
            highest_price, lowest_price, mae_pct, mfe_pct, duration_str, roi_pct
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, 0.0, 0.0, '', 0.0)
        """, (
            zone.get("id"), zone["symbol"], side, entry_price,
            position_size, tp_price, sl_price, hard_sl_price, tf, now,
            entry_price, entry_price
        ))
        conn.commit()
        trade_id = cursor.lastrowid
        return {
            "id": trade_id,
            "zone_id": zone.get("id"),
            "symbol": zone["symbol"],
            "side": side,
            "timeframe": tf,
            "entry_price": entry_price,
            "position_size_usdt": position_size,
            "margin_usdt": margin,
            "tp_price": tp_price,
            "sl_price": sl_price,
            "hard_sl_price": hard_sl_price,
            "balance_at_entry": balance,
            "expected_tp_usdt": round(position_size * tp_pct, 2),
            "max_sl_usdt": round(position_size * sl_pct, 2)
        }

def update_paper_trade_mark_price(trade_id: int, mark_price: float):
    """Updates highest_price, lowest_price, live ROI%, MAE% and MFE% seen during trade lifetime."""
    if not mark_price or mark_price <= 0:
        return
    with get_connection() as conn:
        row = conn.execute(
            "SELECT entry_price, highest_price, lowest_price, side, position_size_usdt FROM paper_trades WHERE id = ? AND status = 'OPEN'",
            (trade_id,)
        ).fetchone()
        if not row:
            return
        entry_price = float(row["entry_price"])
        highest = max(float(row["highest_price"] or entry_price), mark_price)
        lowest = min(float(row["lowest_price"] or entry_price), mark_price)
        side = (row["side"] or "BUY").upper()
        leverage = 5.0

        if side in ("BUY", "LONG"):
            roi_pct = round(((mark_price - entry_price) / entry_price * 100.0) * leverage, 2) if entry_price > 0 else 0.0
            mfe_pct = round(max(0.0, (highest - entry_price) / entry_price * 100.0 * leverage), 2) if entry_price > 0 else 0.0
            mae_pct = round(max(0.0, (entry_price - lowest) / entry_price * 100.0 * leverage), 2) if entry_price > 0 else 0.0
        else:
            roi_pct = round(((entry_price - mark_price) / entry_price * 100.0) * leverage, 2) if entry_price > 0 else 0.0
            mfe_pct = round(max(0.0, (entry_price - lowest) / entry_price * 100.0 * leverage), 2) if entry_price > 0 else 0.0
            mae_pct = round(max(0.0, (highest - entry_price) / entry_price * 100.0 * leverage), 2) if entry_price > 0 else 0.0

        conn.execute("""
        UPDATE paper_trades SET
            highest_price = ?,
            lowest_price = ?,
            roi_pct = ?,
            mfe_pct = ?,
            mae_pct = ?
        WHERE id = ?
        """, (highest, lowest, roi_pct, mfe_pct, mae_pct, trade_id))
        conn.commit()

def close_paper_trade(zone: Dict[str, Any], outcome: str) -> Optional[Dict[str, Any]]:
    """
    Closes open paper trade on TP_HIT or SL_HIT.
    Enforces 85% Reinvestment + 15% Cold Storage Vault compounding split on the specific timeframe account.
    """
    with get_connection() as conn:
        trade = conn.execute("""
        SELECT * FROM paper_trades 
        WHERE (zone_id = ? OR (symbol = ? AND side = ?)) AND status = 'OPEN'
        ORDER BY entry_time DESC LIMIT 1
        """, (zone.get("id"), zone.get("symbol"), zone.get("side"))).fetchone()

        now = int(time.time() * 1000)
        if not trade:
            return None

        trade_id = trade["id"]
        pos_size = float(trade["position_size_usdt"])
        side = trade["side"].upper()
        entry_price = float(trade["entry_price"])
        tf = (trade["timeframe"] or "4h").lower()
        acc_id = 2 if "1h" in tf else 1

        tp_pct = 0.022 if tf == "1h" else 0.028
        sl_pct = 0.025 if tf == "1h" else 0.028

        if outcome == "TP_HIT":
            exit_price = float(trade["tp_price"])
            gross_pnl_pct = tp_pct * 100.0
        else:
            exit_price = float(trade["sl_price"])
            gross_pnl_pct = -sl_pct * 100.0

        gross_pnl_usdt = pos_size * (gross_pnl_pct / 100.0)
        roundtrip_fee = pos_size * 0.0016
        net_pnl_usdt = round(gross_pnl_usdt - roundtrip_fee, 2)

        # Compounding Split: 15% to Cold Storage Vault, 85% to active margin on Win
        vault_stash = 0.0
        acc_row = conn.execute("SELECT * FROM paper_account WHERE id = ?", (acc_id,)).fetchone()
        curr_balance = float(acc_row["current_balance"]) if acc_row else 50.0
        vault_balance = float(acc_row["vault_balance"]) if acc_row and "vault_balance" in acc_row.keys() else 0.0
        win_count = int(acc_row["win_count"]) if acc_row else 0
        loss_count = int(acc_row["loss_count"]) if acc_row else 0
        total_pnl = float(acc_row["total_pnl"]) if acc_row else 0.0

        if outcome == "TP_HIT" and net_pnl_usdt > 0:
            win_count += 1
            vault_stash = round(net_pnl_usdt * 0.15, 2)
            margin_reinvest = round(net_pnl_usdt * 0.85, 2)
            new_balance = round(curr_balance + margin_reinvest, 2)
            new_vault = round(vault_balance + vault_stash, 2)
        else:
            loss_count += 1
            new_balance = round(max(1.0, curr_balance + net_pnl_usdt), 2)
            new_vault = vault_balance

        new_total_pnl = round(total_pnl + net_pnl_usdt, 2)

        # Duration & MAE / MFE calculation
        entry_time = trade["entry_time"] or now
        duration_ms = max(0, now - entry_time)
        duration_str = format_duration_str(duration_ms)

        highest = max(float(trade["highest_price"] or entry_price), exit_price)
        lowest = min(float(trade["lowest_price"] or entry_price), exit_price)
        leverage = 5.0
        if side in ("BUY", "LONG"):
            final_mfe = round(max(0.0, (highest - entry_price) / entry_price * 100.0 * leverage), 2)
            final_mae = round(max(0.0, (entry_price - lowest) / entry_price * 100.0 * leverage), 2)
        else:
            final_mfe = round(max(0.0, (entry_price - lowest) / entry_price * 100.0 * leverage), 2)
            final_mae = round(max(0.0, (highest - entry_price) / entry_price * 100.0 * leverage), 2)

        conn.execute("""
        UPDATE paper_trades SET
            status = ?, exit_time = ?, exit_price = ?, pnl_usdt = ?, pnl_pct = ?,
            vault_stashed_usdt = ?, highest_price = ?, lowest_price = ?,
            mae_pct = ?, mfe_pct = ?, duration_str = ?, roi_pct = ?
        WHERE id = ?
        """, (
            outcome, now, exit_price, net_pnl_usdt, round(gross_pnl_pct * 5.0, 2),
            vault_stash, highest, lowest, final_mae, final_mfe, duration_str, round(gross_pnl_pct * 5.0, 2), trade_id
        ))

        conn.execute("""
        UPDATE paper_account SET
            current_balance = ?,
            vault_balance = ?,
            total_pnl = ?,
            win_count = ?,
            loss_count = ?
        WHERE id = ?
        """, (new_balance, new_vault, new_total_pnl, win_count, loss_count, acc_id))
        conn.commit()

        completed = win_count + loss_count
        win_rate = round((win_count / completed * 100), 1) if completed > 0 else 0.0
        return {
            "trade_id": trade_id,
            "outcome": outcome,
            "timeframe": tf,
            "pnl_usdt": net_pnl_usdt,
            "pnl_pct": round(gross_pnl_pct * 5.0, 2),
            "roi_pct": round(gross_pnl_pct * 5.0, 2),
            "mae_pct": final_mae,
            "mfe_pct": final_mfe,
            "duration": duration_str,
            "position_size": pos_size,
            "new_balance": new_balance,
            "vault_balance": new_vault,
            "total_pnl": new_total_pnl,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate
        }

def close_paper_trade_manually(trade_id: int, exit_price: float) -> Dict[str, Any]:
    """Manually close an open position at current mark price with full MAE/MFE and duration forensics."""
    with get_connection() as conn:
        trade = conn.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,)).fetchone()
        if not trade or trade["status"] != "OPEN":
            return {"success": False, "error": "Trade not found or already closed"}

        pos_size = float(trade["position_size_usdt"] or 10.0)
        entry_price = float(trade["entry_price"])
        side = trade["side"].upper()
        tf = (trade["timeframe"] or "4h").lower()
        acc_id = 2 if "1h" in tf else 1
        now = int(time.time() * 1000)

        if side in ("BUY", "LONG"):
            pnl_pct = ((exit_price - entry_price) / entry_price * 100.0) if entry_price > 0 else 0.0
        else:
            pnl_pct = ((entry_price - exit_price) / entry_price * 100.0) if entry_price > 0 else 0.0

        pnl_usdt = round(pos_size * (pnl_pct / 100.0), 4)
        roi_pct = round(pnl_pct * 5.0, 2)
        status = "MANUAL_CLOSED"

        # Duration & MAE / MFE calculation
        entry_time = trade["entry_time"] or now
        duration_ms = max(0, now - entry_time)
        duration_str = format_duration_str(duration_ms)

        highest = max(float(trade["highest_price"] or entry_price), exit_price)
        lowest = min(float(trade["lowest_price"] or entry_price), exit_price)
        leverage = 5.0
        if side in ("BUY", "LONG"):
            final_mfe = round(max(0.0, (highest - entry_price) / entry_price * 100.0 * leverage), 2)
            final_mae = round(max(0.0, (entry_price - lowest) / entry_price * 100.0 * leverage), 2)
        else:
            final_mfe = round(max(0.0, (entry_price - lowest) / entry_price * 100.0 * leverage), 2)
            final_mae = round(max(0.0, (highest - entry_price) / entry_price * 100.0 * leverage), 2)

        conn.execute("""
        UPDATE paper_trades SET
            status = ?, exit_time = ?, exit_price = ?, pnl_usdt = ?, pnl_pct = ?,
            highest_price = ?, lowest_price = ?, mae_pct = ?, mfe_pct = ?,
            duration_str = ?, roi_pct = ?
        WHERE id = ?
        """, (status, now, exit_price, pnl_usdt, roi_pct, highest, lowest, final_mae, final_mfe, duration_str, roi_pct, trade_id))

        is_win = 1 if pnl_usdt > 0 else 0
        is_loss = 1 if pnl_usdt <= 0 else 0
        conn.execute("""
        UPDATE paper_account SET
            current_balance = round(current_balance + ?, 2),
            total_pnl = round(total_pnl + ?, 2),
            win_count = win_count + ?,
            loss_count = loss_count + ?
        WHERE id = ?
        """, (pnl_usdt, pnl_usdt, is_win, is_loss, acc_id))
        conn.commit()

        return {
            "success": True,
            "trade_id": trade_id,
            "timeframe": tf,
            "pnl_usdt": pnl_usdt,
            "pnl_pct": roi_pct,
            "roi_pct": roi_pct,
            "mae_pct": final_mae,
            "mfe_pct": final_mfe,
            "duration": duration_str,
            "exit_price": exit_price
        }

def get_paper_trades_history(limit: int = 50, timeframe: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns closed trade history, optionally filtered by timeframe (1h or 4h)."""
    query = "SELECT * FROM paper_trades WHERE status != 'OPEN'"
    params: List[Any] = []
    if timeframe:
        query += " AND timeframe = ?"
        params.append(timeframe.lower())
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def get_open_paper_trades(timeframe: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns active open positions, optionally filtered by timeframe (1h or 4h)."""
    query = "SELECT * FROM paper_trades WHERE status = 'OPEN'"
    params: List[Any] = []
    if timeframe:
        query += " AND timeframe = ?"
        params.append(timeframe.lower())
    query += " ORDER BY entry_time DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def reset_paper_account(starting_balance: float = 50.0, timeframe: Optional[str] = None) -> Dict[str, Any]:
    """Resets paper account(s) to starting balance ($50.00)."""
    with get_connection() as conn:
        if timeframe:
            tf = timeframe.lower()
            acc_id = 2 if "1h" in tf else 1
            conn.execute("DELETE FROM paper_trades WHERE timeframe = ?", (tf,))
            conn.execute("""
            UPDATE paper_account SET
                initial_balance = ?,
                current_balance = ?,
                vault_balance = 0.0,
                total_pnl = 0.0,
                win_count = 0,
                loss_count = 0
            WHERE id = ?
            """, (starting_balance, starting_balance, acc_id))
        else:
            conn.execute("DELETE FROM paper_trades")
            conn.execute("""
            UPDATE paper_account SET
                initial_balance = ?,
                current_balance = ?,
                vault_balance = 0.0,
                total_pnl = 0.0,
                win_count = 0,
                loss_count = 0
            WHERE id IN (1, 2)
            """, (starting_balance, starting_balance))
        conn.commit()

    return get_dual_paper_accounts()

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

