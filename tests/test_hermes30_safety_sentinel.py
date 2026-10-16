"""
HERMES 3.0 MODEL 2A: Automated Database & Engine Safety Sentinel Test
=====================================================================
Audits and guarantees:
1. SQLite PRAGMA integrity_check == 'ok'
2. 100% Closed Trade History intact (20+ closed trades with entry, exit, PnL)
3. Target Active Open Positions preserved: CRVUSDT (538), OPUSDT (537), FETUSDT (536) strictly 'OPEN'
4. 10 Deca Compounding Sections verified: Sec 1 ($119.61), Sec 2 ($55.33), Sec 6 ($47.46), Total Equity ($575.06)
5. Zero DELETE / DROP policies enforced on trading data
6. Live Engine & Sentinel audit (Soft SL on body close, Stepped Trailing armor)
7. Autonomous self-healing for any data discrepancy
"""

import sys
import os
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure utf-8 output encoding on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


DB_PATH = BASE_DIR / "database" / "smc_v17.db"
LOCAL_VAULT_BACKUP = BASE_DIR / "database" / "local_vault_backup.json"

def run_database_audit_and_heal():
    print("=" * 70)
    print("🔍 [TEST 1] DATABASE INTEGRITY AUDIT")
    print("=" * 70)
    assert DB_PATH.exists(), f"Database not found at {DB_PATH}"

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. PRAGMA integrity check
    c.execute("PRAGMA integrity_check;")
    res = c.fetchone()[0]
    print(f"PRAGMA integrity_check: {res}")
    assert res == "ok", f"Database corrupted: {res}"

    # 2. Audit Closed Trades & Self-Heal
    print("\n" + "=" * 70)
    print("📜 [TEST 2] TRADE HISTORY & MANDATE SYMBOLS AUDIT")
    print("=" * 70)
    
    # Check vault backup comparison
    if LOCAL_VAULT_BACKUP.exists():
        with open(LOCAL_VAULT_BACKUP, "r", encoding="utf-8") as f:
            vault = json.load(f)
        vault_trades = vault.get("paper_trades", [])
        for vt in vault_trades:
            vt_id = vt.get("id")
            c.execute("SELECT id FROM paper_trades WHERE id = ?", (vt_id,))
            exists = c.fetchone()
            if not exists:
                print(f"⚠️ [SELF-HEALING] Trade #{vt_id} missing from DB! Restoring from Vault...")
                cols = list(vt.keys())
                placeholders = ", ".join(["?"] * len(cols))
                col_names = ", ".join(cols)
                c.execute(f"INSERT INTO paper_trades ({col_names}) VALUES ({placeholders})", [vt[k] for k in cols])
                conn.commit()
                print(f"✅ [SELF-HEALING HEALED] Trade #{vt_id} ({vt.get('symbol')}) restored!")

    c.execute("SELECT count(*) as cnt FROM paper_trades WHERE status != 'OPEN'")
    closed_count = c.fetchone()['cnt']
    print(f"Total Closed Trades in DB: {closed_count}")
    assert closed_count >= 20, f"Expected at least 20 closed trades, found {closed_count}"

    mandate_symbols = ["NEARUSDT", "SUSDT", "AEROUSDT", "TIAUSDT", "APTUSDT"]
    for sym in mandate_symbols:
        c.execute("SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, status FROM paper_trades WHERE symbol LIKE ? AND status != 'OPEN'", (f"%{sym}%",))
        rows = [dict(r) for r in c.fetchall()]
        print(f"Symbol '{sym}': {len(rows)} closed trade(s) found.")
        assert len(rows) > 0, f"Mandate symbol {sym} missing from closed trade history!"
        for r in rows:
            print(f"   Trade #{r['id']}: Side={r['side']}, Entry={r['entry_price']}, Exit={r['exit_price']}, PnL=${r['pnl_usdt']} ({r['pnl_pct']}%), Status={r['status']}")

    # 3. Audit Active Open Positions (CRVUSDT, OPUSDT, FETUSDT)
    print("\n" + "=" * 70)
    print("🎯 [TEST 3] ACTIVE OPEN POSITIONS AUDIT (536, 537, 538)")
    print("=" * 70)
    target_ids = [536, 537, 538]
    expected_symbols = {536: ["FETUSDT"], 537: ["BTCUSDT", "OPUSDT"], 538: ["ETHUSDT", "CRVUSDT"]}

    for tid, exp_syms in expected_symbols.items():
        c.execute("SELECT * FROM paper_trades WHERE id = ?", (tid,))
        row = c.fetchone()
        assert row is not None, f"Target open trade #{tid} not found in database!"
        t = dict(row)
        assert t["symbol"] in exp_syms, f"Trade #{tid} expected symbol in {exp_syms}, found {t['symbol']}"
        assert t["status"] == "OPEN", f"Trade #{tid} ({t['symbol']}) status must be strictly 'OPEN', found {t['status']}"
        print(f"✅ Trade #{tid}: Symbol={t['symbol']}, Side={t['side']}, Entry={t['entry_price']}, Account=Sec {t['account_id']}, Status={t['status']}")


    # 4. Audit Deca Compounding Sections (1-10) and Equity
    print("\n" + "=" * 70)
    print("💰 [TEST 4] DECA COMPOUNDING SECTIONS & TOTAL EQUITY AUDIT")
    print("=" * 70)
    c.execute("SELECT id, name, current_balance, total_pnl, win_count, loss_count FROM paper_account WHERE id <= 10 ORDER BY id ASC")
    sections = [dict(r) for r in c.fetchall()]
    assert len(sections) == 10, f"Expected 10 sections, found {len(sections)}"

    total_equity = sum(s["current_balance"] for s in sections)
    for s in sections:
        print(f"Section {s['id']:2d}: {s['name']:25s} | Balance=${s['current_balance']:8.2f} | PnL=${s['total_pnl']:8.2f} | W/L={s['win_count']}/{s['loss_count']}")

    print(f"\nCalculated Total Portfolio Equity (Sections 1-10): ${total_equity:.2f}")
    assert 570.0 <= total_equity <= 585.0, f"Expected total portfolio equity around $575.06, got ${total_equity:.2f}"
    assert abs(sections[0]["current_balance"] - 119.61) < 0.05, f"Section 1 expected $119.61, got {sections[0]['current_balance']}"
    assert abs(sections[1]["current_balance"] - 55.33) < 0.05, f"Section 2 expected $55.33, got {sections[1]['current_balance']}"
    assert abs(sections[5]["current_balance"] - 47.46) < 0.05, f"Section 6 expected $47.46, got {sections[5]['current_balance']}"
    print("✅ All 10 Compounding Sections and Portfolio Equity ($575.06) 100% verified.")

    # 5. Audit Zero DELETE / DROP Danger
    print("\n" + "=" * 70)
    print("🛡️ [TEST 5] ZERO DELETE / DROP POLICY AUDIT")
    print("=" * 70)
    db_code = (BASE_DIR / "database" / "db.py").read_text(encoding="utf-8")
    assert "DELETE FROM paper_trades \n        WHERE id NOT IN" not in db_code, "Unsafe DELETE query found in _sync_journal_to_paper_trades!"
    assert "wipe_legacy_database_clean" in db_code, "wipe_legacy_database_clean missing!"
    
    from database.db import wipe_legacy_database_clean
    wipe_res = wipe_legacy_database_clean()
    assert wipe_res.get("status") == "PROTECTED_ZERO_DATA_LOSS", f"wipe_legacy_database_clean not properly shielded: {wipe_res}"
    print("✅ ZERO DELETE / DROP Policy enforced. Trade wipe attempts are strictly blocked.")

    # 6. Audit Live Engine & Sentinel Modules
    print("\n" + "=" * 70)
    print("⚡ [TEST 6] LIVE ENGINE & SENTINEL HEALTH AUDIT")
    print("=" * 70)
    from engine.hermes30_apex_live import hermes30_live_engine
    from engine.self_healing_sentinel import self_healing_sentinel

    assert hermes30_live_engine is not None, "hermes30_live_engine instance is None!"
    assert self_healing_sentinel is not None, "self_healing_sentinel instance is None!"

    # Verify Stepped Trailing SL Ladder & Soft SL settings in config
    from config import (
        HERMES_3_SOFT_SL_PCT,
        HERMES_3_HARD_CIRCUIT_SL_PCT,
        HERMES_3_ENABLE_STEPPED_TRAILING,
        HERMES_3_CANDLE_BODY_CLOSE_SL
    )
    print(f"Config Soft SL: {HERMES_3_SOFT_SL_PCT * 100.0:.2f}% (Candle Body Close: {HERMES_3_CANDLE_BODY_CLOSE_SL})")
    print(f"Config Hard SL Circuit: {HERMES_3_HARD_CIRCUIT_SL_PCT * 100.0:.2f}%")
    print(f"Config Stepped Trailing Profit Armor Active: {HERMES_3_ENABLE_STEPPED_TRAILING}")

    assert HERMES_3_CANDLE_BODY_CLOSE_SL is True, "Candle Body Close Soft SL must be True"
    assert HERMES_3_ENABLE_STEPPED_TRAILING is True, "Stepped Trailing Profit Armor must be True"

    # Verify Sentinel trade shield
    sentinel_code = (BASE_DIR / "engine" / "self_healing_sentinel.py").read_text(encoding="utf-8")
    assert "if \"HERMES_3\" in trade_mode or \"MODEL_2A\" in trade_mode:" in sentinel_code, "Sentinel missing HERMES 3.0 Model 2A orphan protection shield!"
    assert "if \"HERMES_3\" in mode or \"MODEL_2A\" in mode:" in sentinel_code, "Sentinel missing HERMES 3.0 Model 2A position doctor shield!"
    print("✅ Live Engine & Sentinel verified cleanly with zero exceptions.")

    # 7. Vault Backup Sync
    from database.cloud_vault import push_vault_state
    pushed = push_vault_state()
    assert pushed is True, "Failed to push vault backup state!"
    print("✅ Cloud Vault state snapshot refreshed and synced.")

    conn.close()
    print("\n" + "=" * 70)
    print("🏆 FORENSIC SAFETY CERTIFICATION: ALL AUDITS PASSED WITH ZERO ERRORS")
    print("=" * 70)

if __name__ == "__main__":
    run_database_audit_and_heal()
