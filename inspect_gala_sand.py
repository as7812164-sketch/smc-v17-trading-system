import sqlite3
import json

conn = sqlite3.connect("database/smc_v17.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT * FROM paper_trades WHERE symbol IN ('GALAUSDT', 'SANDUSDT') ORDER BY exit_time DESC LIMIT 4").fetchall()
for r in rows:
    t = dict(r)
    ep = t.get("entry_price")
    xp = t.get("exit_price")
    tp = t.get("tp_price")
    sl = t.get("sl_price")
    raw_move_pct = ((ep - xp) / ep * 100) if ep else 0 # For short
    lev = 5
    calc_roe = raw_move_pct * lev
    print(f"ID: {t['id']} | {t['symbol']} | Side: {t['side']} | TF: {t['timeframe']}")
    print(f"Entry: {ep} | Exit: {xp} | TP: {tp} | SL: {sl}")
    print(f"Raw Move Pct: {raw_move_pct:.2f}% | Calc ROE (5x): {calc_roe:.2f}% | DB pnl_pct: {t.get('pnl_pct')}% | DB roi_pct: {t.get('roi_pct')}%")
    print(f"Position Size: ${t.get('position_size_usdt')} | PnL USDT: ${t.get('pnl_usdt')}")
    print(f"Duration: {t.get('duration_str')} | Status: {t.get('status')}")
    print(f"Sentry / Reasons: {t.get('sentry_reasons')}")
    print("-" * 50)
