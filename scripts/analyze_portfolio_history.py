import sqlite3
import pandas as pd
import json

conn = sqlite3.connect("database/smc_v17.db")
c = conn.cursor()

# Get all column names
c.execute("PRAGMA table_info(paper_trades)")
columns = [col[1] for col in c.fetchall()]

# Fetch all trades
c.execute("SELECT * FROM paper_trades ORDER BY id ASC")
rows = c.fetchall()

trades = [dict(zip(columns, row)) for row in rows]
print(f"Total trades in DB: {len(trades)}")

# Separate closed vs open
closed_trades = [t for t in trades if t['status'] not in ('OPEN', 'PENDING')]
open_trades = [t for t in trades if t['status'] == 'OPEN']

print(f"Closed trades: {len(closed_trades)}")
print(f"Open trades: {len(open_trades)}")

# Analyze closed trades
wins = []
losses = []
breakevens = []

for t in closed_trades:
    pnl = t.get('pnl_usdt')
    roi = t.get('roi_pct') or t.get('pnl_pct') or 0.0
    
    # If pnl_usdt is None, try calculating from roi
    if pnl is None:
        size = t.get('position_size_usdt') or 50.0
        pnl = (size / 5.0) * (roi / 100.0) # approx on margin
    
    t['computed_pnl'] = pnl
    t['computed_roi'] = roi
    
    if roi > 0.5:
        wins.append(t)
    elif roi < -0.5:
        losses.append(t)
    else:
        breakevens.append(t)

print(f"\n--- Performance Breakdown ---")
print(f"Wins: {len(wins)}")
print(f"Losses: {len(losses)}")
print(f"Break-evens: {len(breakevens)}")

total_decided = len(wins) + len(losses)
win_rate = (len(wins) / total_decided * 100.0) if total_decided > 0 else 0.0
overall_win_rate = (len(wins) / len(closed_trades) * 100.0) if len(closed_trades) > 0 else 0.0

print(f"Win Rate (excluding BE): {win_rate:.2f}%")
print(f"Overall Win Rate (including BE): {overall_win_rate:.2f}%")

total_profit = sum(t['computed_pnl'] for t in wins if t['computed_pnl'] is not None)
total_loss = sum(abs(t['computed_pnl']) for t in losses if t['computed_pnl'] is not None)
net_pnl = total_profit - total_loss
profit_factor = (total_profit / total_loss) if total_loss > 0 else 999.0

print(f"Total Win Profit: +${total_profit:.2f}")
print(f"Total Loss Amount: -${total_loss:.2f}")
print(f"Net Realized PnL: +${net_pnl:.2f}")
print(f"Profit Factor: {profit_factor:.2f}")

# Longest winning streak
streaks = []
current_streak = 0
for t in closed_trades:
    roi = t.get('computed_roi', 0.0)
    if roi > 0.5 or roi >= 0.0: # count BE / wins as non-losing streak
        current_streak += 1
    else:
        streaks.append(current_streak)
        current_streak = 0
streaks.append(current_streak)
max_win_streak = max(streaks) if streaks else 0
print(f"Max Consecutive Non-Losing Streak: {max_win_streak} trades")

# Group by coin
coin_perf = {}
for t in closed_trades:
    sym = t.get('symbol', 'UNKNOWN')
    if sym not in coin_perf:
        coin_perf[sym] = {'wins': 0, 'losses': 0, 'be': 0, 'pnl': 0.0}
    roi = t.get('computed_roi', 0.0)
    pnl = t.get('computed_pnl', 0.0) or 0.0
    if roi > 0.5:
        coin_perf[sym]['wins'] += 1
    elif roi < -0.5:
        coin_perf[sym]['losses'] += 1
    else:
        coin_perf[sym]['be'] += 1
    coin_perf[sym]['pnl'] += pnl

print("\n--- Top Performing Coins ---")
sorted_coins = sorted(coin_perf.items(), key=lambda x: x[1]['pnl'], reverse=True)
for sym, stats in sorted_coins[:10]:
    total_c = stats['wins'] + stats['losses'] + stats['be']
    wr = (stats['wins'] / (stats['wins'] + stats['losses']) * 100) if (stats['wins'] + stats['losses']) > 0 else 0
    print(f"  {sym:12s}: {stats['wins']}W - {stats['losses']}L - {stats['be']}BE | PnL: +${stats['pnl']:.2f} | Win Rate: {wr:.1f}%")

# Recent 15 closed trades detailed view
print("\n--- Recent 15 Closed Trades Forensic List ---")
for t in closed_trades[-15:]:
    sym = t.get('symbol')
    side = t.get('side')
    entry = t.get('entry_price')
    exit_p = t.get('exit_price')
    roi = t.get('computed_roi')
    pnl = t.get('computed_pnl')
    status = t.get('status')
    sec = t.get('section_id') or t.get('account_id')
    mae = t.get('mae_pct')
    mfe = t.get('mfe_pct')
    print(f"  ID {t['id']:3d} | {sym:10s} {side:5s} | In: {entry} -> Out: {exit_p} | ROI: {roi:+.2f}% | PnL: {pnl:+.2f} USDT | Status: {status} | Sec: {sec}")
