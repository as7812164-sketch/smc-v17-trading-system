import json
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

with open('hermes35_30day_master_audit.json', 'r') as f:
    data = json.load(f)

trades = data.get('trades', [])
slots = {
    '4h_1': 'Section A (4H Macro Alpha)',
    '4h_2': 'Section B (4H Macro Beta)',
    '1h_1': 'Section C (1H Tactical Alpha)',
    '1h_2': 'Section D (1H Tactical Beta)'
}

stats = {}

for s_key, s_name in slots.items():
    s_trades = [t for t in trades if t['slot'] == s_key]
    s_trades.sort(key=lambda x: x['entry_time'])
    
    tp_count = sum(1 for t in s_trades if t['outcome'] == 'TP_HIT')
    be_count = sum(1 for t in s_trades if t['outcome'] == 'BE_EXIT')
    sl_count = sum(1 for t in s_trades if t['outcome'] == 'SL_HIT')
    total = len(s_trades)
    
    decisive_wr = (tp_count / (tp_count + sl_count) * 100) if (tp_count + sl_count) > 0 else 0
    cap_pres = ((tp_count + be_count) / total * 100) if total > 0 else 0
    
    total_profit = sum(t['pnl_usdt'] for t in s_trades if t['pnl_usdt'] > 0)
    total_loss = abs(sum(t['pnl_usdt'] for t in s_trades if t['pnl_usdt'] < 0))
    pf = (total_profit / total_loss) if total_loss > 0 else 999.0
    
    durations = []
    gaps = []
    
    for i, t in enumerate(s_trades):
        # Calculate real duration
        dur_h = max(1.0, (t['exit_time'] - t['entry_time']) / (3600 * 1000))
        durations.append(dur_h)
        if i < len(s_trades) - 1:
            nxt = s_trades[i+1]
            gap_h = max(0.0, (nxt['entry_time'] - t['exit_time']) / (3600 * 1000))
            gaps.append(gap_h)
            
    avg_dur = sum(durations) / len(durations) if durations else 0
    avg_gap = sum(gaps) / len(gaps) if gaps else 0
    
    final_bal = s_trades[-1]['account_balance'] if s_trades else 50.0
    net_pnl = final_bal - 50.0
    
    stats[s_key] = {
        'name': s_name,
        'total': total,
        'tp': tp_count,
        'be': be_count,
        'sl': sl_count,
        'decisive_wr': decisive_wr,
        'cap_pres': cap_pres,
        'start_bal': 50.0,
        'final_bal': final_bal,
        'net_pnl': net_pnl,
        'pf': pf,
        'avg_dur': avg_dur,
        'avg_gap': avg_gap,
        'trades': s_trades
    }

print("=== 4-SECTION COMPREHENSIVE SUMMARY ===")
for s_key, st in stats.items():
    print(f"{st['name']} ({s_key}):")
    print(f"  Trades Executed: {st['total']} | TP: {st['tp']} | BE: {st['be']} | SL: {st['sl']}")
    print(f"  Decisive Win Rate (TP vs SL): {st['decisive_wr']:.2f}% | Capital Preservation: {st['cap_pres']:.2f}%")
    print(f"  Compounding Growth: $50.00 -> ${st['final_bal']:,.2f} (Net Realized: +${st['net_pnl']:,.2f} USDT)")
    print(f"  Average Position Hold: {st['avg_dur']:.1f} hours | Avg Wait to Next Trade: {st['avg_gap']:.1f} hours | Profit Factor: {st['pf']:.2f}")
    print()

# Output chronologically sample trades for each section
print("\n=== SAMPLE TRADE SEQUENCES WITH EXACT DATE, TIME, DURATION, AND GAPS ===")
for s_key, st in stats.items():
    print(f"\n--- {st['name']} ({s_key}) - First 5 Trades Timeline ---")
    for i in range(min(5, len(st['trades']))):
        t = st['trades'][i]
        dur_h = max(1.0, (t['exit_time'] - t['entry_time']) / (3600 * 1000))
        gap_str = "N/A"
        if i < len(st['trades']) - 1:
            nxt = st['trades'][i+1]
            gap_h = max(0.0, (nxt['entry_time'] - t['exit_time']) / (3600 * 1000))
            gap_str = f"{gap_h:.1f}h"
        print(f"Trade #{t['trade_id']} | {t['symbol']} {t['side']} | Entry: {t['entry_date']} | Exit: {t['exit_date']} | Open Duration: {dur_h:.1f}h | Gap To Next Trade: {gap_str} | Result: {t['outcome']} (+${t['pnl_usdt']}) | Balance: ${t['account_balance']}")
