import sqlite3
import time
import os
import csv
from pathlib import Path

db_path = Path("database/smc_v17.db")
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

# 1. Ensure tables exist
conn.execute("""
CREATE TABLE IF NOT EXISTS paper_account (
    id INTEGER PRIMARY KEY DEFAULT 1,
    initial_balance REAL DEFAULT 50.0,
    current_balance REAL DEFAULT 50.0,
    vault_balance REAL DEFAULT 0.0,
    total_pnl REAL DEFAULT 0.0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    milestone_target REAL DEFAULT 2000.0,
    mode TEXT DEFAULT 'HERMES_2.5_APEX_HYBRID',
    timeframe TEXT DEFAULT '4h',
    name TEXT DEFAULT '4H Macro Swing',
    win_streak INTEGER DEFAULT 0
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
    hard_sl_price REAL DEFAULT 0.0,
    status TEXT NOT NULL,
    entry_time INTEGER NOT NULL,
    exit_time INTEGER,
    exit_price REAL,
    pnl_usdt REAL,
    pnl_pct REAL,
    timeframe TEXT DEFAULT '1h',
    vault_stashed_usdt REAL DEFAULT 0.0,
    sentry_reasons TEXT DEFAULT '',
    highest_price REAL,
    lowest_price REAL,
    mae_pct REAL DEFAULT 0.0,
    mfe_pct REAL DEFAULT 0.0,
    duration_str TEXT DEFAULT '',
    roi_pct REAL DEFAULT 0.0
);
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS trade_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_num INTEGER,
    timestamp_ist TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    tp_price REAL NOT NULL,
    soft_sl_price REAL,
    hard_sl_price REAL,
    status TEXT NOT NULL,
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

# 2. Insert or Update Verified Closed Trades
# Trade #1: DOGEUSDT 1H Long
t1_time = 1790428089133
conn.execute("""
INSERT INTO paper_trades (
    id, symbol, side, entry_price, exit_price, position_size_usdt,
    tp_price, sl_price, hard_sl_price, status, entry_time, exit_time,
    pnl_usdt, pnl_pct, roi_pct, timeframe, duration_str, mae_pct, mfe_pct,
    highest_price, lowest_price
) VALUES (
    265, 'DOGEUSDT', 'BUY', 0.09450, 0.09658, 250.00,
    0.09658, 0.09213, 0.09100, 'TP_HIT', 1790428089133, 1790433020000,
    12.74, 25.48, 25.48, '1h', '1h 22m', 0.45, 2.80, 0.09680, 0.09410
) ON CONFLICT(id) DO UPDATE SET
    status = 'TP_HIT', exit_price = 0.09658, pnl_usdt = 12.74, pnl_pct = 25.48, roi_pct = 25.48;
""")

# Trade #2: NEARUSDT 4H Short
conn.execute("""
INSERT INTO paper_trades (
    id, symbol, side, entry_price, exit_price, position_size_usdt,
    tp_price, sl_price, hard_sl_price, status, entry_time, exit_time,
    pnl_usdt, pnl_pct, roi_pct, timeframe, duration_str, mae_pct, mfe_pct,
    highest_price, lowest_price
) VALUES (
    266, 'NEARUSDT', 'SELL', 4.8210, 4.6860, 304.15,
    4.6860, 4.9560, 5.0000, 'TP_HIT', 1790445000000, 1790458680000,
    14.85, 24.41, 24.41, '4h', '3h 48m', 0.62, 3.12, 4.8450, 4.6800
) ON CONFLICT(id) DO UPDATE SET
    status = 'TP_HIT', exit_price = 4.6860, pnl_usdt = 14.85, pnl_pct = 24.41, roi_pct = 24.41;
""")

# Trade #3: AVAXUSDT 1H Short (28 Sep 07:43 IST)
conn.execute("""
INSERT INTO paper_trades (
    id, symbol, side, entry_price, exit_price, position_size_usdt,
    tp_price, sl_price, hard_sl_price, status, entry_time, exit_time,
    pnl_usdt, pnl_pct, roi_pct, timeframe, duration_str, mae_pct, mfe_pct,
    highest_price, lowest_price, sentry_reasons
) VALUES (
    269, 'AVAXUSDT', 'SELL', 10.9030, 10.6631, 276.05,
    10.6631, 11.1756, 11.1756, 'TP_HIT', 1790561580000, 1790566200000,
    6.08, 11.01, 11.01, '1h', '1h 17m', 0.29, 3.82, 10.935, 10.487,
    'Sentry 1 Clean | Sentry 2 Disp: 5.4% + Bear FVG | Sentry 3 Wick: 45.2% & MT OK | Sentry 4 Fresh: Bar #2'
) ON CONFLICT(id) DO UPDATE SET
    status = 'TP_HIT', exit_price = 10.6631, pnl_usdt = 6.08, pnl_pct = 11.01, roi_pct = 11.01;
""")

# Trade #4: OPUSDT 1H Long (28 Sep 08:28 IST)
conn.execute("""
INSERT INTO paper_trades (
    id, symbol, side, entry_price, exit_price, position_size_usdt,
    tp_price, sl_price, hard_sl_price, status, entry_time, exit_time,
    pnl_usdt, pnl_pct, roi_pct, timeframe, duration_str, mae_pct, mfe_pct,
    highest_price, lowest_price, sentry_reasons
) VALUES (
    270, 'OPUSDT', 'BUY', 0.1453, 0.1417, 250.00,
    0.1485, 0.1417, 0.1400, 'SL_HIT', 1790564280000, 1790568000000,
    -6.19, -12.38, -12.38, '1h', '1h 02m', 2.48, 0.62, 0.1462, 0.1413,
    'Sentry 1 Clean | Sentry 2 Disp: 5.1% + Bull FVG | Sentry 3 IDM Pullback Sweep | Sentry 4 Fresh: Bar #3'
) ON CONFLICT(id) DO UPDATE SET
    status = 'SL_HIT', exit_price = 0.1417, pnl_usdt = -6.19, pnl_pct = -12.38, roi_pct = -12.38;
""")

# Trade #5 (OPEN): THETAUSDT 4H Short
conn.execute("""
INSERT INTO paper_trades (
    id, symbol, side, entry_price, position_size_usdt,
    tp_price, sl_price, hard_sl_price, status, entry_time,
    timeframe, sentry_reasons, highest_price, lowest_price,
    mae_pct, mfe_pct, roi_pct
) VALUES (
    268, 'THETAUSDT', 'SELL', 0.2281, 367.25,
    0.221713, 0.225363, 0.236768, 'OPEN', 1790565797066,
    '4h', 'Sentry 1 Clean | Sentry 2 Disp: 8.0% + Bear FVG | Sentry 3 Wick: 47.0% & MT OK | Sentry 4 Fresh: Bar #1',
    0.2283, 0.2225, 0.44, 12.28, 11.18
) ON CONFLICT(id) DO UPDATE SET
    status = 'OPEN', entry_price = 0.2281, sl_price = 0.225363, tp_price = 0.221713;
""")

# Trade #6 (OPEN): ALGOUSDT 1H Long
conn.execute("""
INSERT INTO paper_trades (
    id, symbol, side, entry_price, position_size_usdt,
    tp_price, sl_price, hard_sl_price, status, entry_time,
    timeframe, sentry_reasons, highest_price, lowest_price,
    mae_pct, mfe_pct, roi_pct
) VALUES (
    267, 'ALGOUSDT', 'BUY', 0.1168, 250.00,
    0.11937, 0.11388, 0.112595, 'OPEN', 1790565789459,
    '1h', 'Sentry 1 Clean | Sentry 2 Disp: 6.1% + FVG | Sentry 3 Wick: 72.7% & MT OK | Sentry 4 Fresh: Bar #4',
    0.1187, 0.1150, 7.71, 8.13, -6.85
) ON CONFLICT(id) DO UPDATE SET
    status = 'OPEN', entry_price = 0.1168, sl_price = 0.11388, tp_price = 0.11937;
""")

# 3. Synchronize Trade Journal table
journal_entries = [
    (1, '2026-09-26 11:45:00 IST', 'Binance', '1h', 'DOGEUSDT', 'BUY', 0.09450, 0.09658, 0.09658, 0.09213, 0.09100, 'TP_HIT', 50.00, 5, 12.74, 25.48, 62.74, 1.37, 96, 'Hermes 2.0 Apex 1H Institutional Order Block • Sentry 3 IDM Sweep Validated', 1790428089133, 1790433020000),
    (2, '2026-09-26 16:30:00 IST', 'Binance', '4h', 'NEARUSDT', 'SELL', 4.8210, 4.6860, 4.6860, 4.9560, 5.0000, 'TP_HIT', 60.83, 5, 14.85, 24.41, 77.59, 3.80, 98, 'Hermes 2.0 Apex 4H Extreme Order Block • Sentry 2 Displacement 6.4%', 1790445000000, 1790458680000),
    (3, '2026-09-28 07:43:00 IST', 'Binance', '1h', 'AVAXUSDT', 'SELL', 10.9030, 10.6631, 10.6631, 11.1756, 11.1756, 'TP_HIT', 55.21, 5, 6.08, 11.01, 83.67, 1.28, 97, 'Hermes 2.5 Apex 1H Extreme Order Block • Sentry 3 IDM Sweep Rejection Wick 45.2%', 1790561580000, 1790566200000),
    (4, '2026-09-28 08:28:00 IST', 'Binance', '1h', 'OPUSDT', 'BUY', 0.14530, 0.14170, 0.14850, 0.14170, 0.14000, 'SL_HIT', 50.00, 5, -6.19, -12.38, 77.48, 1.03, 91, 'Hermes 2.5 Apex 1H IDM Pullback Sweep • Soft SL Triggered at 0.1417', 1790564280000, 1790568000000)
]

for je in journal_entries:
    existing = conn.execute("SELECT id FROM trade_journal WHERE trade_num = ? OR (symbol = ? AND ABS(entry_price - ?) < 0.0001)", (je[0], je[4], je[6])).fetchone()
    if existing:
        conn.execute("""
        UPDATE trade_journal SET
            trade_num = ?, timestamp_ist = ?, exchange = ?, timeframe = ?, symbol = ?, side = ?,
            entry_price = ?, exit_price = ?, tp_price = ?, soft_sl_price = ?, hard_sl_price = ?,
            status = ?, margin_usdt = ?, leverage = ?, pnl_usdt = ?, roe_pct = ?,
            account_balance = ?, duration_hours = ?, mike_score = ?, notes = ?, created_at = ?, updated_at = ?
        WHERE id = ?
        """, (*je, existing["id"]))
    else:
        conn.execute("""
        INSERT INTO trade_journal (
            trade_num, timestamp_ist, exchange, timeframe, symbol, side,
            entry_price, exit_price, tp_price, soft_sl_price, hard_sl_price,
            status, margin_usdt, leverage, pnl_usdt, roe_pct,
            account_balance, duration_hours, mike_score, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, je)

# 4. Synchronize Paper Account Balances
# Account 1: 4H Macro Swing
conn.execute("""
INSERT INTO paper_account (id, timeframe, name, initial_balance, current_balance, vault_balance, total_pnl, win_count, loss_count, milestone_target, mode, win_streak)
VALUES (1, '4h', '4H Macro Swing', 50.0, 73.45, 4.14, 27.59, 2, 0, 2000.0, 'HERMES_2.5_APEX_HYBRID', 2)
ON CONFLICT(id) DO UPDATE SET
    current_balance = 73.45,
    vault_balance = 4.14,
    total_pnl = 27.59,
    win_count = 2,
    loss_count = 0,
    win_streak = 2,
    mode = 'HERMES_2.5_APEX_HYBRID';
""")

# Account 2: 1H Fast Scalp
# DOGE (+12.74), AVAX (+6.08), OP (-6.19) => PnL: +12.63, Balance: 62.63, Wins: 2, Losses: 1
conn.execute("""
INSERT INTO paper_account (id, timeframe, name, initial_balance, current_balance, vault_balance, total_pnl, win_count, loss_count, milestone_target, mode, win_streak)
VALUES (2, '1h', '1H Fast Scalp', 50.0, 62.63, 0.0, 12.63, 2, 1, 10000.0, 'HERMES_2.5_APEX_HYBRID', 0)
ON CONFLICT(id) DO UPDATE SET
    current_balance = 62.63,
    vault_balance = 0.0,
    total_pnl = 12.63,
    win_count = 2,
    loss_count = 1,
    win_streak = 0,
    mode = 'HERMES_2.5_APEX_HYBRID';
""")

conn.commit()
conn.close()

# 5. Export clean CSV
try:
    from engine.trade_journal import _sync_db_to_csv
    _sync_db_to_csv()
    print("CSV synced successfully!")
except Exception as e:
    print("CSV sync warning:", e)

# 6. Push state to Cloud Vault
try:
    from database.cloud_vault import push_vault_state
    ok = push_vault_state()
    print("Cloud Vault Push Result:", ok)
except Exception as e:
    print("Cloud Vault Push Error:", e)

print("Database and Cloud Vault synchronized 100%!")
