import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3
from database.db import (
    get_connection,
    init_db,
    open_paper_trade,
    close_paper_trade,
    get_paper_account,
    get_compounding_sections,
    get_quad_paper_accounts,
    wipe_legacy_database_clean
)
from database.cloud_vault import push_vault_state, pull_and_restore_vault_state, CHANNEL_MAP

def run_tests():
    print("=" * 60)
    print("STEP 1: Initializing Database & 10 Compounding Sections")
    print("=" * 60)
    init_db()

    with get_connection() as conn:
        # Check wiped tables
        pt_count = conn.execute("SELECT COUNT(*) FROM paper_trades").fetchone()[0]
        tj_count = conn.execute("SELECT COUNT(*) FROM trade_journal").fetchone()[0]
        print(f"[*] paper_trades count: {pt_count} (Expected: 0)")
        assert pt_count == 0, f"paper_trades should be empty, got {pt_count}"

        print(f"[*] trade_journal count: {tj_count} (Expected: 0)")
        assert tj_count == 0, f"trade_journal should be empty, got {tj_count}"

        # Check legacy accounts > 10
        legacy_count = conn.execute("SELECT COUNT(*) FROM paper_account WHERE id > 10").fetchone()[0]
        print(f"[*] Legacy accounts (id > 10): {legacy_count} (Expected: 0)")
        assert legacy_count == 0, f"No legacy accounts > 10 allowed, got {legacy_count}"

        # Check exact 10 accounts
        accounts = [dict(r) for r in conn.execute("SELECT * FROM paper_account ORDER BY id ASC").fetchall()]
        print(f"[*] Total paper accounts: {len(accounts)} (Expected: 10)")
        assert len(accounts) == 10, f"Expected 10 accounts, got {len(accounts)}"

        # Check sections 1-5 (4H Macro)
        for i in range(1, 6):
            acc = accounts[i - 1]
            assert acc["id"] == i, f"Account ID mismatch: {acc['id']}"
            assert acc["timeframe"] == "4h", f"Acc {i} timeframe mismatch: {acc['timeframe']}"
            assert acc["exchange"] == "BITGET", f"Acc {i} exchange mismatch: {acc['exchange']}"
            assert acc["channel"] == f"sec_{i}", f"Acc {i} channel mismatch: {acc['channel']}"
            assert acc["initial_balance"] == 50.0, f"Acc {i} initial_balance mismatch: {acc['initial_balance']}"
            assert acc["current_balance"] == 50.0, f"Acc {i} current_balance mismatch: {acc['current_balance']}"
            assert acc["vault_balance"] == 0.0, f"Acc {i} vault_balance mismatch: {acc['vault_balance']}"
            assert acc["total_pnl"] == 0.0, f"Acc {i} total_pnl mismatch: {acc['total_pnl']}"
            assert acc["win_count"] == 0, f"Acc {i} win_count mismatch: {acc['win_count']}"
            assert acc["loss_count"] == 0, f"Acc {i} loss_count mismatch: {acc['loss_count']}"
            assert acc["win_streak"] == 0, f"Acc {i} win_streak mismatch: {acc['win_streak']}"
            assert acc["milestone_target"] == 2000.0, f"Acc {i} milestone_target mismatch: {acc['milestone_target']}"
            assert acc["mode"] == "HERMES_3.5_SINGLE_TIER", f"Acc {i} mode mismatch: {acc['mode']}"
            print(f"    [OK] Section {i} (4H Macro): ${acc['current_balance']} | {acc['channel']} | {acc['mode']}")

        # Check sections 6-10 (1H Intraday)
        for i in range(6, 11):
            acc = accounts[i - 1]
            assert acc["id"] == i, f"Account ID mismatch: {acc['id']}"
            assert acc["timeframe"] == "1h", f"Acc {i} timeframe mismatch: {acc['timeframe']}"
            assert acc["exchange"] == "BITGET", f"Acc {i} exchange mismatch: {acc['exchange']}"
            assert acc["channel"] == f"sec_{i}", f"Acc {i} channel mismatch: {acc['channel']}"
            assert acc["initial_balance"] == 50.0, f"Acc {i} initial_balance mismatch: {acc['initial_balance']}"
            assert acc["current_balance"] == 50.0, f"Acc {i} current_balance mismatch: {acc['current_balance']}"
            assert acc["vault_balance"] == 0.0, f"Acc {i} vault_balance mismatch: {acc['vault_balance']}"
            assert acc["total_pnl"] == 0.0, f"Acc {i} total_pnl mismatch: {acc['total_pnl']}"
            assert acc["win_count"] == 0, f"Acc {i} win_count mismatch: {acc['win_count']}"
            assert acc["loss_count"] == 0, f"Acc {i} loss_count mismatch: {acc['loss_count']}"
            assert acc["win_streak"] == 0, f"Acc {i} win_streak mismatch: {acc['win_streak']}"
            assert acc["milestone_target"] == 2000.0, f"Acc {i} milestone_target mismatch: {acc['milestone_target']}"
            assert acc["mode"] == "HERMES_3.5_SINGLE_TIER", f"Acc {i} mode mismatch: {acc['mode']}"
            print(f"    [OK] Section {i} (1H Intraday): ${acc['current_balance']} | {acc['channel']} | {acc['mode']}")

        # Check Settings
        strat_ver = conn.execute("SELECT value FROM settings WHERE key = 'strategy_version'").fetchone()[0]
        entry_mode = conn.execute("SELECT value FROM settings WHERE key = 'hermes35_entry_mode'").fetchone()[0]
        print(f"[*] strategy_version: {strat_ver} (Expected: HERMES_3.5_SINGLE_TIER)")
        print(f"[*] hermes35_entry_mode: {entry_mode} (Expected: 5% Boundary Penetration)")
        assert strat_ver == "HERMES_3.5_SINGLE_TIER"
        assert entry_mode == "5% Boundary Penetration"

    print("\n" + "=" * 60)
    print("STEP 2: Testing Intelligent Section Allocation (open_paper_trade)")
    print("=" * 60)
    # Open 5 4H trades sequentially
    opened_4h = []
    for s_idx in range(1, 6):
        zone_fake = {
            "id": 100 + s_idx,
            "symbol": f"COIN{s_idx}USDT",
            "side": "BUY",
            "timeframe": "4h",
            "entry_price": 100.0
        }
        res = open_paper_trade(zone_fake)
        assert "error" not in res, f"Failed to open 4H trade {s_idx}: {res}"
        assert res["account_id"] == s_idx, f"Expected allocation to account {s_idx}, got {res['account_id']}"
        assert res["channel"] == f"sec_{s_idx}"
        assert res["position_size_usdt"] == 250.0  # 50.0 * 5.0
        assert res["mode"] == "HERMES_3.5_SINGLE_TIER"
        opened_4h.append(res)
        print(f"    [OK] 4H Trade {s_idx} allocated to Section {res['account_id']} ({res['channel']}), pos_size=${res['position_size_usdt']}")

    # 6th 4H trade should fail (all 5 sections busy)
    zone_overflow = {
        "id": 199,
        "symbol": "OVERFLOWUSDT",
        "side": "BUY",
        "timeframe": "4h",
        "entry_price": 100.0
    }
    overflow_res = open_paper_trade(zone_overflow)
    assert "error" in overflow_res, f"Expected error when all 4H sections busy, got {overflow_res}"
    print(f"    [OK] 6th 4H trade correctly rejected when all 5 sections busy: {overflow_res['error']}")

    # Open 1H trade (should allocate to Section 6)
    zone_1h = {
        "id": 201,
        "symbol": "INTRUSDT",
        "side": "SELL",
        "timeframe": "1h",
        "entry_price": 50.0
    }
    res_1h = open_paper_trade(zone_1h)
    assert "error" not in res_1h, f"Failed to open 1H trade: {res_1h}"
    assert res_1h["account_id"] == 6, f"Expected allocation to account 6, got {res_1h['account_id']}"
    assert res_1h["channel"] == "sec_6"
    print(f"    [OK] 1H Trade allocated to Section {res_1h['account_id']} ({res_1h['channel']})")

    print("\n" + "=" * 60)
    print("STEP 3: Testing 100% Compounding Close (close_paper_trade)")
    print("=" * 60)
    # Close Section 1 trade with TP_HIT
    # Position: BUY @ 100.0, TP @ 102.80 (2.8% move, 5x lev = 14% ROE)
    # Gross PnL: $250.0 * 0.028 = +$7.00. Fee = 250 * 0.0016 = $0.40. Net = +$6.60
    close_res = close_paper_trade({"id": 101, "symbol": "COIN1USDT", "side": "BUY"}, "TP_HIT", exit_price=102.80)
    assert close_res is not None
    assert close_res["outcome"] == "TP_HIT"
    assert close_res["pnl_usdt"] > 0
    print(f"    [OK] Closed Section 1 trade: PnL=+${close_res['pnl_usdt']}, New Section 1 Balance=${close_res['new_balance']}")
    assert close_res["new_balance"] == round(50.0 + close_res["pnl_usdt"], 2)
    assert close_res["win_count"] == 1
    assert close_res["win_rate"] == 100.0

    print("\n" + "=" * 60)
    print("STEP 4: Testing get_compounding_sections() and get_quad_paper_accounts()")
    print("=" * 60)
    deca_stats = get_compounding_sections()
    assert "sections" in deca_stats
    assert "combined" in deca_stats
    assert len(deca_stats["sections"]) == 10
    comb = deca_stats["combined"]
    print(f"    [*] Total starting balance: ${comb['total_starting_balance']} (Expected: 500.0)")
    assert comb["total_starting_balance"] == 500.0
    print(f"    [*] Total current balance: ${comb['total_current_balance']}")
    print(f"    [*] Total PnL: ${comb['total_pnl']}")
    print(f"    [*] Active open trades: {comb['total_open_trades']}")
    print(f"    [*] Overall win rate: {comb['overall_win_rate']}%")

    quad_stats = get_quad_paper_accounts()
    assert "sections" in quad_stats
    assert "sec_1" in quad_stats
    assert "sec_10" in quad_stats
    assert "bitget_4h_1" in quad_stats
    assert "combined" in quad_stats
    print("    [OK] get_quad_paper_accounts provides full backward-compatibility and deca breakdown.")

    print("\n" + "=" * 60)
    print("STEP 5: Cloud Vault Push & Clean Re-initialization")
    print("=" * 60)
    # Wipe clean for live trading start ($50 x 10 = $500, zero active trades)
    wipe_res = wipe_legacy_database_clean()
    print(f"    [OK] wipe_legacy_database_clean: {wipe_res['message']}")

    clean_state = get_compounding_sections()
    assert clean_state["combined"]["total_starting_balance"] == 500.0
    assert clean_state["combined"]["total_current_balance"] == 500.0
    assert clean_state["combined"]["total_open_trades"] == 0
    assert clean_state["combined"]["total_pnl"] == 0.0
    print("    [OK] Verified clean state: $500.00 capital, 0 open trades, 0 PnL across all 10 sections.")

    # Push to cloud vault backup
    push_res = push_vault_state()
    print(f"    [OK] push_vault_state result: {push_res} (Local backup synced)")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
