import time
import sys
from datetime import datetime, timezone, timedelta
from database.db import get_connection

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
today_str = datetime.now(IST).strftime('%Y-%m-%d')
start_of_day_ms = int(datetime.strptime(today_str, '%Y-%m-%d').replace(tzinfo=IST).timestamp() * 1000)

with get_connection() as conn:
    accs = [dict(r) for r in conn.execute('SELECT id, name, timeframe, current_balance, total_pnl, win_count, loss_count, win_streak, mode FROM paper_account ORDER BY id').fetchall()]
    print('=== 10 COMPOUNDING SECTIONS STATUS ===')
    total_balance = sum(a['current_balance'] for a in accs)
    total_pnl = sum(a['total_pnl'] for a in accs)
    total_wins = sum(a['win_count'] for a in accs)
    total_losses = sum(a['loss_count'] for a in accs)
    print(f'Total Portfolio Balance: ${total_balance:.2f} USDT | Total P&L: ${total_pnl:+.2f} USDT | Wins: {total_wins} | Losses: {total_losses}')
    for a in accs:
        print(f"  • #{a['id']} {a['name']} ({a['timeframe'].upper()}): Balance ${a['current_balance']:.2f} | PnL: ${a['total_pnl']:+.2f} | W:{a['win_count']}/L:{a['loss_count']} | Streak: {a['win_streak']}")

    open_trades = [dict(r) for r in conn.execute("SELECT * FROM paper_trades WHERE status = 'OPEN'").fetchall()]
    print(f"\n=== OPEN POSITIONS ({len(open_trades)}) ===")
    for t in open_trades:
        entry_time_str = datetime.fromtimestamp(t['entry_time']/1000, tz=IST).strftime('%Y-%m-%d %H:%M:%S IST') if t.get('entry_time') else "N/A"
        print(f"  • Trade #{t['id']}: {t['symbol']} ({str(t.get('timeframe','')).upper()} {t['side']})")
        print(f"    - Entry Price: {t['entry_price']} | Mark/High: {t.get('highest_price')} | Low: {t.get('lowest_price')}")
        print(f"    - TP: {t['tp_price']} | SL: {t['sl_price']} | Hard SL: {t.get('hard_sl_price')}")
        print(f"    - Position Size: ${t['position_size_usdt']} | Section #{t.get('account_id')} ({t.get('channel')})")
        print(f"    - Entry Time: {entry_time_str} | Mode: {t.get('mode')}")
        print(f"    - Sentry Reasons: {t.get('sentry_reasons')}")

    today_trades = [dict(r) for r in conn.execute("SELECT * FROM paper_trades WHERE entry_time >= ? OR exit_time >= ? ORDER BY id DESC", (start_of_day_ms, start_of_day_ms)).fetchall()]
    print(f"\n=== TRADES EXECUTED TODAY ({today_str}) ({len(today_trades)}) ===")
    for t in today_trades:
        entry_str = datetime.fromtimestamp(t['entry_time']/1000, tz=IST).strftime('%H:%M:%S') if t.get('entry_time') else "N/A"
        exit_str = datetime.fromtimestamp(t['exit_time']/1000, tz=IST).strftime('%H:%M:%S') if t.get('exit_time') else "OPEN"
        print(f"  • #{t['id']}: {t['symbol']} ({t.get('timeframe','').upper()} {t['side']}) | Entry: {t['entry_price']} | Exit: {t.get('exit_price','N/A')} | Status: {t['status']} | PnL: ${t.get('pnl_usdt', 0.0)} ({t.get('pnl_pct', 0.0)}%) | Time: {entry_str} -> {exit_str} | Reason: {t.get('sentry_reasons','')[:60]}")

    recent = [dict(r) for r in conn.execute("SELECT * FROM paper_trades ORDER BY id DESC LIMIT 10").fetchall()]
    print(f"\n=== LAST 10 TRADES IN SYSTEM ===")
    for t in recent:
        entry_str = datetime.fromtimestamp(t['entry_time']/1000, tz=IST).strftime('%Y-%m-%d %H:%M') if t.get('entry_time') else "N/A"
        print(f"  • #{t['id']}: {t['symbol']} ({str(t.get('timeframe','')).upper()} {t['side']}) | Entry: {t['entry_price']} | Exit: {t.get('exit_price','-')} | Status: {t['status']} | PnL: ${t.get('pnl_usdt', 0.0)} ({t.get('pnl_pct', 0.0)}%) | Entry Time: {entry_str}")
