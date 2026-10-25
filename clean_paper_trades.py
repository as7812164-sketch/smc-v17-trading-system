import sqlite3
import os
import shutil
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATABASES = [
    r"C:\Users\power\Desktop\SMC_V17_MASTER_SYSTEM\SMC_V17_CODEBASE\database\smc_v17.db",
    r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\database\smc_v17.db"
]

def clean_database(db_path):
    if not os.path.exists(db_path):
        print(f"Skipping (not found): {db_path}")
        return

    print("=" * 80)
    print(f"🧹 CLEANING PAPER TRADING DATA IN: {db_path}")
    print("=" * 80)

    # 1. Create a safety backup first
    backup_path = db_path + f".backup_{int(time.time())}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Safety backup saved to: {backup_path}")

    conn = sqlite3.connect(db_path, timeout=30.0)
    c = conn.cursor()

    # Get trade count before
    c.execute("SELECT COUNT(*) FROM paper_trades")
    trades_before = c.fetchone()[0]

    # Delete all paper trades
    c.execute("DELETE FROM paper_trades")
    deleted_trades = c.rowcount

    # Reset paper account
    c.execute("""
    UPDATE paper_account SET
        initial_balance = 0.0,
        current_balance = 0.0,
        total_pnl = 0.0,
        win_count = 0,
        loss_count = 0
    WHERE id = 1
    """)

    # Also check if settings has paper trading enabled and disable it if desired
    try:
        c.execute("UPDATE settings SET value = 'false' WHERE key = 'paper_trading_enabled'")
        c.execute("UPDATE settings SET value = 'false' WHERE key = 'auto_trade'")
    except Exception:
        pass

    conn.commit()
    conn.close()

    print(f"✅ Removed {trades_before} paper trades successfully.")
    print("✅ Paper account reset to clean state (Balance: $0.00, PnL: $0.00, Trades: 0).")

def main():
    for db in DATABASES:
        clean_database(db)

if __name__ == "__main__":
    main()
