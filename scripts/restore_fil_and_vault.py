import json
import sqlite3
import time
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import database.db as db
db.init_db()

trade_504 = {
    'id': 504,
    'symbol': 'FILUSDT',
    'side': 'BUY',
    'entry_price': 1.0774,
    'position_size_usdt': 250.0,
    'tp_price': 1.109722,
    'sl_price': 1.0774,
    'status': 'MANUAL_CLOSED',
    'entry_time': 1791703110447,
    'exit_time': 1791703153050,
    'exit_price': 1.0774,
    'pnl_usdt': 0.0,
    'pnl_pct': 0.0,
    'timeframe': '4h',
    'hard_sl_price': 1.045078,
    'vault_stashed_usdt': 0.0,
    'sentry_reasons': 'HERMES 3.0 MODEL 2A | 50% MT Deep Entry | Rejection Wick >= 18% | Break-Even Lock',
    'highest_price': 1.1067,
    'lowest_price': 1.0774,
    'mae_pct': 0.45,
    'mfe_pct': 13.6,
    'duration_str': '1m',
    'roi_pct': 0.0,
    'exchange': 'BITGET',
    'channel': 'sec_1',
    'account_id': 1,
    'mode': 'HERMES_3.0_MODEL_2A',
    'tier': 'TIER_1',
    'be_lock_pct': 0.015,
    'trail_lock_pct': 0.018,
    'autopsy_diagnosis': 'BE SHIELD',
    'be_locked': 1
}

trade_510 = {
    'id': 510,
    'symbol': 'FILUSDT',
    'side': 'LONG',
    'entry_price': 1.0774,
    'position_size_usdt': 250.0,
    'tp_price': 1.109722,
    'sl_price': 1.0774,
    'status': 'OPEN',
    'entry_time': 1791704273746,
    'exit_time': None,
    'exit_price': None,
    'pnl_usdt': None,
    'pnl_pct': None,
    'timeframe': '4h',
    'hard_sl_price': 1.045078,
    'vault_stashed_usdt': 0.0,
    'sentry_reasons': 'HERMES 3.0 MODEL 2A | 50% MT Deep Entry | Rejection Wick >= 18% | Break-Even Shield Armed',
    'highest_price': 1.1067,
    'lowest_price': 1.0774,
    'mae_pct': 0.0,
    'mfe_pct': 13.6,
    'duration_str': '',
    'roi_pct': 11.3,
    'exchange': 'BITGET',
    'channel': 'sec_1',
    'account_id': 1,
    'mode': 'HERMES_3.0_MODEL_2A',
    'tier': 'TIER_1',
    'be_lock_pct': 0.015,
    'trail_lock_pct': 0.018,
    'autopsy_diagnosis': '',
    'be_locked': 1
}

with db.get_connection() as conn:
    for t in [trade_504, trade_510]:
        conn.execute('''
        INSERT OR REPLACE INTO paper_trades (
            id, symbol, side, entry_price, position_size_usdt, tp_price, sl_price,
            hard_sl_price, status, entry_time, exit_time, exit_price, pnl_usdt, pnl_pct,
            timeframe, sentry_reasons, highest_price, lowest_price, mae_pct, mfe_pct,
            duration_str, roi_pct, exchange, channel, account_id, mode, tier,
            be_lock_pct, trail_lock_pct, autopsy_diagnosis, be_locked
        ) VALUES (
            :id, :symbol, :side, :entry_price, :position_size_usdt, :tp_price, :sl_price,
            :hard_sl_price, :status, :entry_time, :exit_time, :exit_price, :pnl_usdt, :pnl_pct,
            :timeframe, :sentry_reasons, :highest_price, :lowest_price, :mae_pct, :mfe_pct,
            :duration_str, :roi_pct, :exchange, :channel, :account_id, :mode, :tier,
            :be_lock_pct, :trail_lock_pct, :autopsy_diagnosis, :be_locked
        )
        ''', t)

    conn.execute("""
    UPDATE paper_account SET
        mode = 'HERMES_3.0_MODEL_2A',
        current_balance = 50.0,
        initial_balance = 50.0,
        total_pnl = 0.0
    WHERE id BETWEEN 1 AND 10;
    """)
    conn.commit()

db.ensure_10_sections()
print("Successfully restored Trade 504 and Trade 510 into SQLite database/smc_v17.db!")

# Export updated local_vault_backup.json
import database.cloud_vault as cv
cv.push_vault_state()
print("Updated database/local_vault_backup.json generated successfully!")
