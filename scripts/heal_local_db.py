import sqlite3
import json
import os

db_path = 'database/smc_v17.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute('UPDATE paper_account SET current_balance = 119.61, total_pnl = 69.61, loss_count = 0, win_count = 12, win_streak = 3 WHERE id = 1')
    conn.execute('UPDATE paper_trades SET status = "TRAILING_SL_HIT", exit_price = 0.1837668, pnl_usdt = 0.27, pnl_pct = 1.0, roi_pct = 1.0, exit_time = 1791983078878, autopsy_diagnosis = "Self-Healed: Trailing SL Locked Profit" WHERE id = 525')
    conn.commit()
    conn.close()
    print('Local SQLite healed!')

backup_path = 'database/local_vault_backup.json'
if os.path.exists(backup_path):
    with open(backup_path, 'r', encoding='utf-8') as f:
        v = json.load(f)
    for a in v.get('accounts', []):
        if a.get('id') == 1:
            a['current_balance'] = 119.61
            a['total_pnl'] = 69.61
            a['loss_count'] = 0
            a['win_count'] = 12
    for t in v.get('paper_trades', []):
        if t.get('id') == 525:
            t['status'] = 'TRAILING_SL_HIT'
            t['exit_price'] = 0.1837668
            t['pnl_usdt'] = 0.27
            t['pnl_pct'] = 1.0
            t['roi_pct'] = 1.0
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(v, f, indent=2)
    print('Local backup JSON healed!')
