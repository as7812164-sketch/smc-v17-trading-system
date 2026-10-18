"""
Cloud Vault Persistence Engine for Hermes 2.0 / 2.5 Trading System.
Provides 100% persistent storage for paper trades, accounts, and journal
across Render Free Tier container restarts, redeployments, and crashes.
Stores state snapshots on GitHub branch 'data-vault' (which never triggers redeployments).
"""

import os
import json
import base64
import time
import logging
import urllib.request
import urllib.error
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path
from config import BASE_DIR, DB_PATH, STRATEGY_VERSION
from database.db import get_connection

logger = logging.getLogger("CloudVault")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", os.getenv("GH_TOKEN", "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"))
GITHUB_REPO = os.getenv("GITHUB_REPO", "as7812164-sketch/smc-ai-agent")
VAULT_BRANCH = "data-vault"
VAULT_FILE = "vault_state.json"
LOCAL_VAULT_BACKUP = BASE_DIR / "database" / "local_vault_backup.json"

def get_vault_headers() -> Dict[str, str]:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": "Hermes-Cloud-Vault",
        "Accept": "application/vnd.github.v3+json"
    }

CHANNEL_MAP = {
    # Hermes 3.0 Model 2A (Sections 1-10)
    1: ("BITGET", "sec_1", "Section 1 (4H Macro)", "4h", "HERMES_3.0_MODEL_2A"),
    2: ("BITGET", "sec_2", "Section 2 (4H Macro)", "4h", "HERMES_3.0_MODEL_2A"),
    3: ("BITGET", "sec_3", "Section 3 (4H Macro)", "4h", "HERMES_3.0_MODEL_2A"),
    4: ("BITGET", "sec_4", "Section 4 (4H Macro)", "4h", "HERMES_3.0_MODEL_2A"),
    5: ("BITGET", "sec_5", "Section 5 (4H Macro)", "4h", "HERMES_3.0_MODEL_2A"),
    6: ("BITGET", "sec_6", "Section 6 (1H Intraday)", "1h", "HERMES_3.0_MODEL_2A"),
    7: ("BITGET", "sec_7", "Section 7 (1H Intraday)", "1h", "HERMES_3.0_MODEL_2A"),
    8: ("BITGET", "sec_8", "Section 8 (1H Intraday)", "1h", "HERMES_3.0_MODEL_2A"),
    9: ("BITGET", "sec_9", "Section 9 (1H Intraday)", "1h", "HERMES_3.0_MODEL_2A"),
    10: ("BITGET", "sec_10", "Section 10 (1H Intraday)", "1h", "HERMES_3.0_MODEL_2A"),
    # Hermes 4.0 Balanced Apex (Sections 11-20)
    11: ("BITGET", "hermes4_sec_1", "Hermes 4.0 - Section 1 (4H Macro)", "4h", "HERMES_4.0_BALANCED_APEX"),
    12: ("BITGET", "hermes4_sec_2", "Hermes 4.0 - Section 2 (4H Macro)", "4h", "HERMES_4.0_BALANCED_APEX"),
    13: ("BITGET", "hermes4_sec_3", "Hermes 4.0 - Section 3 (4H Macro)", "4h", "HERMES_4.0_BALANCED_APEX"),
    14: ("BITGET", "hermes4_sec_4", "Hermes 4.0 - Section 4 (4H Macro)", "4h", "HERMES_4.0_BALANCED_APEX"),
    15: ("BITGET", "hermes4_sec_5", "Hermes 4.0 - Section 5 (4H Macro)", "4h", "HERMES_4.0_BALANCED_APEX"),
    16: ("BITGET", "hermes4_sec_6", "Hermes 4.0 - Section 6 (1H Intraday)", "1h", "HERMES_4.0_BALANCED_APEX"),
    17: ("BITGET", "hermes4_sec_7", "Hermes 4.0 - Section 7 (1H Intraday)", "1h", "HERMES_4.0_BALANCED_APEX"),
    18: ("BITGET", "hermes4_sec_8", "Hermes 4.0 - Section 8 (1H Intraday)", "1h", "HERMES_4.0_BALANCED_APEX"),
    19: ("BITGET", "hermes4_sec_9", "Hermes 4.0 - Section 9 (1H Intraday)", "1h", "HERMES_4.0_BALANCED_APEX"),
    20: ("BITGET", "hermes4_sec_10", "Hermes 4.0 - Section 10 (1H Intraday)", "1h", "HERMES_4.0_BALANCED_APEX"),
}

def push_vault_state() -> bool:
    """
    Dumps all accounts, open/closed paper trades, and trade journal
    to GitHub branch 'data-vault' and local disk backup.
    Never triggers Render builds because Render builds only from 'main'.
    """
    try:
        if not DB_PATH.exists():
            return False

        conn = get_connection()

        # 1. Accounts
        accounts = [dict(r) for r in conn.execute("SELECT * FROM paper_account").fetchall()]

        # 2. Paper Trades
        paper_trades = [dict(r) for r in conn.execute("SELECT * FROM paper_trades ORDER BY id ASC").fetchall()]

        # 3. Trade Journal
        try:
            journal_trades = [dict(r) for r in conn.execute("SELECT * FROM trade_journal ORDER BY id ASC").fetchall()]
        except Exception:
            journal_trades = []

        # 4. System Metrics
        try:
            metrics = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM system_metrics").fetchall()}
        except Exception:
            metrics = {}

        # 5. Settings
        try:
            settings = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM settings").fetchall()}
        except Exception:
            settings = {}

        conn.close()

        channel_map = CHANNEL_MAP
        for acc in accounts:
            acc_id = acc.get("id")
            if acc_id in channel_map:
                map_tuple = channel_map[acc_id]
                acc["exchange"] = map_tuple[0]
                acc["channel"] = map_tuple[1]
                acc["name"] = map_tuple[2]
                acc["timeframe"] = map_tuple[3]
                acc["mode"] = map_tuple[4] if len(map_tuple) > 4 else ("HERMES_4.0_BALANCED_APEX" if acc_id > 10 else "HERMES_3.0_MODEL_2A")
            else:
                acc["mode"] = "HERMES_4.0_BALANCED_APEX" if (acc_id and acc_id > 10) else "HERMES_3.0_MODEL_2A"
        for pt in paper_trades:
            if not pt.get("mode"):
                pt_acc = int(pt.get("account_id") or 1)
                pt["mode"] = "HERMES_4.0_BALANCED_APEX" if pt_acc > 10 else "HERMES_3.0_MODEL_2A"

        metrics["hermes_mode"] = "DUAL_ENGINE_3.5_AND_4.0"
        settings["strategy_version"] = "DUAL_ENGINE_3.5_AND_4.0"

        payload_data = {
            "version": "1.0",
            "updated_at": int(time.time() * 1000),
            "updated_at_str": time.strftime("%Y-%m-%d %H:%M:%S IST", time.localtime()),
            "accounts": accounts,
            "paper_trades": paper_trades,
            "journal_trades": journal_trades,
            "metrics": metrics,
            "settings": settings
        }

        # 6. BB 2.0 Shadow Ledger
        bb20_file = BASE_DIR / "bb20_shadow_ledger.json"
        if bb20_file.exists():
            try:
                with open(bb20_file, "r", encoding="utf-8") as f:
                    payload_data["bb20_shadow_ledger"] = json.load(f)
            except Exception:
                pass

        # Save local disk backup first
        try:
            LOCAL_VAULT_BACKUP.parent.mkdir(parents=True, exist_ok=True)
            with open(LOCAL_VAULT_BACKUP, "w", encoding="utf-8") as f:
                json.dump(payload_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Local backup error: {e}")

        if not GITHUB_TOKEN:
            return True

        # Push to GitHub branch data-vault
        content_bytes = json.dumps(payload_data, indent=2).encode("utf-8")
        b64_content = base64.b64encode(content_bytes).decode("utf-8")

        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{VAULT_FILE}?ref={VAULT_BRANCH}"
        headers = get_vault_headers()

        # Check existing file SHA and prevent regression
        sha = None
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                sha = data.get("sha")
                existing_b64 = data.get("content", "")
                if existing_b64:
                    try:
                        existing_vault = json.loads(base64.b64decode(existing_b64).decode("utf-8"))
                        existing_trades = len(existing_vault.get("paper_trades", []))
                        # Anti-Regression Armor: NEVER overwrite if remote has more trades!
                        if len(paper_trades) < existing_trades:
                            logger.error(f"ABORTED VAULT PUSH: Local trade count ({len(paper_trades)}) is smaller than remote ({existing_trades})! Potential data loss blocked.")
                            return False
                    except Exception as parse_err:
                        logger.warning(f"Could not parse existing vault json: {parse_err}")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                logger.warning(f"Could not check vault sha: {e}")

        put_payload = {
            "message": f"Vault Snapshot: {len(paper_trades)} trades, {len(journal_trades)} journal ({time.strftime('%H:%M:%S')})",
            "content": b64_content,
            "branch": VAULT_BRANCH
        }
        if sha:
            put_payload["sha"] = sha

        put_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{VAULT_FILE}"
        req_put = urllib.request.Request(
            put_url,
            data=json.dumps(put_payload).encode("utf-8"),
            headers=headers,
            method="PUT"
        )
        with urllib.request.urlopen(req_put, timeout=12) as resp:
            if resp.status in (200, 201):
                logger.info("Successfully pushed state to Cloud Vault (branch: data-vault)!")
                return True

    except Exception as e:
        logger.warning(f"Failed to push state to Cloud Vault: {e}")
        return False
    return False

def pull_and_restore_vault_state() -> bool:
    """
    Pulls vault state from GitHub branch 'data-vault' (or local disk backup)
    and restores missing trades, accounts, and metrics into local SQLite.
    Guarantees zero data loss after Render redeployments or container restarts.
    """
    vault_data = None

    # 1. Try pulling from GitHub branch data-vault
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{VAULT_FILE}?ref={VAULT_BRANCH}"
        headers = get_vault_headers()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            content_b64 = data.get("content", "")
            if content_b64:
                decoded = base64.b64decode(content_b64).decode("utf-8")
                vault_data = json.loads(decoded)
                logger.info(f"Loaded Cloud Vault data from GitHub (updated {vault_data.get('updated_at_str')})")
    except Exception as e:
        logger.warning(f"Could not load Cloud Vault from GitHub: {e}. Checking local backup.")

    # 2. Fallback to local backup if GitHub was unreachable
    if not vault_data and LOCAL_VAULT_BACKUP.exists():
        try:
            with open(LOCAL_VAULT_BACKUP, "r", encoding="utf-8") as f:
                vault_data = json.load(f)
                logger.info("Loaded Cloud Vault data from local backup file.")
        except Exception as e:
            logger.warning(f"Could not read local vault backup: {e}")

    if not vault_data:
        logger.info("No Cloud Vault data available to restore.")
        return False

    # 3. Restore data into SQLite
    try:
        conn = get_connection()

        # Restore accounts for all compounding sections (Hermes 3.0: 1-10, Hermes 4.0: 11-20)
        channel_map = CHANNEL_MAP

        for acc in vault_data.get("accounts", []):
            acc_id = acc.get("id", 1)
            if acc_id not in channel_map:
                continue
            map_entry = channel_map[acc_id]
            exch, ch, acc_name, tf = map_entry[0], map_entry[1], map_entry[2], map_entry[3]
            conn.execute("""
            INSERT INTO paper_account (
                id, initial_balance, current_balance, vault_balance, total_pnl, win_count,
                loss_count, milestone_target, mode, timeframe, name, win_streak, exchange, channel
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                current_balance = excluded.current_balance,
                vault_balance = excluded.vault_balance,
                total_pnl = excluded.total_pnl,
                win_count = excluded.win_count,
                loss_count = excluded.loss_count,
                win_streak = excluded.win_streak,
                exchange = excluded.exchange,
                channel = excluded.channel,
                name = excluded.name,
                timeframe = excluded.timeframe,
                mode = ?
            """, (
                acc_id, acc.get("initial_balance", 50.0), acc.get("current_balance", 50.0),
                acc.get("vault_balance", 0.0), acc.get("total_pnl", 0.0), acc.get("win_count", 0),
                acc.get("loss_count", 0), acc.get("milestone_target", 2000.0),
                "HERMES_4.0_BALANCED_APEX" if (acc_id and acc_id > 10) else "HERMES_3.0_MODEL_2A",
                tf, acc_name, acc.get("win_streak", 0),
                exch, ch,
                "HERMES_4.0_BALANCED_APEX" if (acc_id and acc_id > 10) else "HERMES_3.0_MODEL_2A"
            ))

        # Ensure all sections from channel_map (1 to 20) are created
        for sec_id, map_val in channel_map.items():
            s_exch, s_ch, s_name, s_tf = map_val[0], map_val[1], map_val[2], map_val[3]
            s_mode = map_val[4] if len(map_val) > 4 else ("HERMES_4.0_BALANCED_APEX" if sec_id > 10 else "HERMES_3.0_MODEL_2A")
            sec_exists = conn.execute("SELECT id FROM paper_account WHERE id = ?", (sec_id,)).fetchone()
            if not sec_exists:
                conn.execute("""
                INSERT INTO paper_account 
                (id, timeframe, name, exchange, channel, initial_balance, current_balance, vault_balance, total_pnl, win_count, loss_count, win_streak, milestone_target, mode)
                VALUES (?, ?, ?, ?, ?, 50.0, 50.0, 0.0, 0.0, 0, 0, 0, 2000.0, ?);
                """, (sec_id, s_tf, s_name, s_exch, s_ch, s_mode))

        # Restore paper_trades
        for pt in vault_data.get("paper_trades", []):
            pt_id = pt.get("id")
            sym = pt.get("symbol")
            side = pt.get("side")
            ep = pt.get("entry_price")
            status = pt.get("status")
            trade_mode = pt.get("mode") or STRATEGY_VERSION
            
            existing = None
            if pt_id:
                existing = conn.execute("SELECT id FROM paper_trades WHERE id = ?", (pt_id,)).fetchone()
            if not existing and sym and ep:
                existing = conn.execute("SELECT id FROM paper_trades WHERE symbol = ? AND side = ? AND ABS(entry_price - ?) < 0.0001", (sym, side, ep)).fetchone()

            if not existing:
                conn.execute("""
                INSERT INTO paper_trades (
                    id, symbol, side, entry_price, exit_price, position_size_usdt,
                    tp_price, sl_price, hard_sl_price, status, entry_time, exit_time,
                    pnl_usdt, pnl_pct, timeframe, sentry_reasons, highest_price, lowest_price,
                    mae_pct, mfe_pct, duration_str, roi_pct, exchange, channel, account_id, mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pt_id, sym, side, ep, pt.get("exit_price"), pt.get("position_size_usdt", 250.0),
                    pt.get("tp_price"), pt.get("sl_price"), pt.get("hard_sl_price", 0.0), status,
                    pt.get("entry_time", int(time.time()*1000)), pt.get("exit_time"),
                    pt.get("pnl_usdt"), pt.get("pnl_pct"), pt.get("timeframe", "1h"),
                    pt.get("sentry_reasons", ""), pt.get("highest_price"), pt.get("lowest_price"),
                    pt.get("mae_pct", 0.0), pt.get("mfe_pct", 0.0), pt.get("duration_str", ""), pt.get("roi_pct", 0.0),
                    pt.get("exchange", "BINANCE"), pt.get("channel", "binance_4h"), pt.get("account_id", 1), trade_mode
                ))
            else:
                # Update existing trade status if changed in vault
                conn.execute("""
                UPDATE paper_trades SET
                    status = ?, exit_price = COALESCE(?, exit_price), exit_time = COALESCE(?, exit_time),
                    pnl_usdt = COALESCE(?, pnl_usdt), pnl_pct = COALESCE(?, pnl_pct), roi_pct = COALESCE(?, roi_pct),
                    highest_price = COALESCE(?, highest_price), lowest_price = COALESCE(?, lowest_price),
                    mae_pct = COALESCE(?, mae_pct), mfe_pct = COALESCE(?, mfe_pct), duration_str = COALESCE(?, duration_str)
                WHERE id = ?
                """, (
                    status, pt.get("exit_price"), pt.get("exit_time"), pt.get("pnl_usdt"), pt.get("pnl_pct"),
                    pt.get("roi_pct"), pt.get("highest_price"), pt.get("lowest_price"), pt.get("mae_pct"),
                    pt.get("mfe_pct"), pt.get("duration_str"), existing["id"]
                ))

        # Restore trade_journal
        try:
            for jt in vault_data.get("journal_trades", []):
                t_num = jt.get("trade_num")
                sym = jt.get("symbol")
                side = jt.get("side")
                ep = jt.get("entry_price")
                existing = conn.execute("SELECT id FROM trade_journal WHERE (trade_num = ? AND trade_num IS NOT NULL) OR (symbol = ? AND side = ? AND ABS(entry_price - ?) < 0.0001)", (t_num, sym, side, ep)).fetchone()
                if not existing:
                    conn.execute("""
                    INSERT INTO trade_journal (
                        trade_num, timestamp_ist, exchange, timeframe, symbol, side,
                        entry_price, exit_price, tp_price, soft_sl_price, hard_sl_price,
                        status, margin_usdt, leverage, pnl_usdt, roe_pct,
                        account_balance, duration_hours, mike_score, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        t_num, jt.get("timestamp_ist", ""), jt.get("exchange", "Binance"), jt.get("timeframe", "1h"),
                        sym, side, ep, jt.get("exit_price"), jt.get("tp_price"), jt.get("soft_sl_price"),
                        jt.get("hard_sl_price"), jt.get("status", "OPEN"), jt.get("margin_usdt", 50.0),
                        jt.get("leverage", 5), jt.get("pnl_usdt", 0.0), jt.get("roe_pct", 0.0),
                        jt.get("account_balance", 50.0), jt.get("duration_hours", 0.0), jt.get("mike_score", 95),
                        jt.get("notes", ""), jt.get("created_at", int(time.time()*1000)), jt.get("updated_at", int(time.time()*1000))
                    ))
        except Exception as e:
            logger.warning(f"Error restoring trade_journal from vault: {e}")

        # CRITICAL GUARANTEE: Enforce active HERMES_3.0_MODEL_2A on container restart or vault re-pull
        conn.execute("UPDATE paper_account SET mode = 'HERMES_3.0_MODEL_2A'")
        conn.execute("UPDATE paper_trades SET mode = 'HERMES_3.0_MODEL_2A' WHERE mode IS NULL OR mode = '' OR mode != 'HERMES_3.0_MODEL_2A'")
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('strategy_version', 'HERMES_3.0_MODEL_2A')")
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('hermes35_entry_mode', '50% Mean Threshold (MT)')")
        conn.execute("INSERT OR REPLACE INTO system_metrics (key, value) VALUES ('hermes_mode', 'HERMES_3.0_MODEL_2A')")

        conn.commit()
        conn.close()

        # Restore BB 2.0 Shadow Ledger if present in vault
        bb20_ledger_data = vault_data.get("bb20_shadow_ledger")
        if bb20_ledger_data:
            try:
                bb20_file = BASE_DIR / "bb20_shadow_ledger.json"
                with open(bb20_file, "w", encoding="utf-8") as f:
                    json.dump(bb20_ledger_data, f, indent=2)
                logger.info("Restored BB 2.0 Shadow Ledger from Cloud Vault!")
            except Exception as e:
                logger.warning(f"Error restoring BB 2.0 Shadow Ledger: {e}")

        logger.info(f"Cloud Vault successfully restored into SQLite database ({STRATEGY_VERSION} active)!")
        return True

    except Exception as e:
        logger.error(f"Error restoring from Cloud Vault: {e}")
        return False
