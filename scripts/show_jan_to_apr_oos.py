import json

with open('scripts/audit_1year_bb30_vs_bb35_results.json', 'r') as f:
    data = json.load(f)

months = ['2026-01', '2026-02', '2026-03', '2026-04']
target_items = [item for item in data.get('monthly_summary', []) if item.get('month') in months]

print("=" * 80)
print("BB 3.5 OUT-OF-SAMPLE (OOS) FORENSIC AUDIT: JAN 2026 TO APR 2026 (4 MONTHS)")
print("Baseline: $500.00 USDT Initial Sectional Compounding Matrix (10 Sections @ $50)")
print("=" * 80)

total_trades_bb35 = 0
total_wins_bb35 = 0
total_saves_bb35 = 0
total_losses_bb35 = 0

total_trades_bb30 = 0
total_wins_bb30 = 0
total_saves_bb30 = 0
total_losses_bb30 = 0

for item in target_items:
    m = item['month']
    b35 = item['bb35']
    b30 = item['bb30']
    
    total_trades_bb35 += b35['total_trades']
    total_wins_bb35 += b35['wins']
    total_saves_bb35 += b35['saves']
    total_losses_bb35 += b35['losses']

    total_trades_bb30 += b30['total_trades']
    total_wins_bb30 += b30['wins']
    total_saves_bb30 += b30['saves']
    total_losses_bb30 += b30['losses']
    
    print(f"\n>>> MONTH: {m}")
    print(f"  [BB 3.5] Final Equity: ${b35['final_equity']:.2f} | Net PnL: ${b35['net_pnl']:+.2f} ({b35['roi_pct']:+.2f}%) | Max DD: {b35['max_dd']:.2f}%")
    print(f"           Trades: {b35['total_trades']} | Wins: {b35['wins']} | Saves: {b35['saves']} | Losses: {b35['losses']}")
    print(f"           Pure Win Rate: {b35['win_rate']:.2f}% | Green/Protected Rate: {b35['green_rate']:.2f}% | Loss Rate: {b35['loss_rate']:.2f}%")
    print(f"  [BB 3.0] Final Equity: ${b30['final_equity']:.2f} | Net PnL: ${b30['net_pnl']:+.2f} ({b30['roi_pct']:+.2f}%) | Max DD: {b30['max_dd']:.2f}%")
    print(f"           Trades: {b30['total_trades']} | Wins: {b30['wins']} | Saves: {b30['saves']} | Losses: {b30['losses']}")
    print(f"           Pure Win Rate: {b30['win_rate']:.2f}% | Green/Protected Rate: {b30['green_rate']:.2f}% | Loss Rate: {b30['loss_rate']:.2f}%")

print("\n" + "=" * 80)
print("4-MONTH AGGREGATE TOTALS (JAN - APR 2026)")
print("=" * 80)

pure_wr_35 = (total_wins_bb35 / total_trades_bb35) * 100 if total_trades_bb35 else 0
green_rate_35 = ((total_wins_bb35 + total_saves_bb35) / total_trades_bb35) * 100 if total_trades_bb35 else 0
loss_rate_35 = (total_losses_bb35 / total_trades_bb35) * 100 if total_trades_bb35 else 0

pure_wr_30 = (total_wins_bb30 / total_trades_bb30) * 100 if total_trades_bb30 else 0
green_rate_30 = ((total_wins_bb30 + total_saves_bb30) / total_trades_bb30) * 100 if total_trades_bb30 else 0
loss_rate_30 = (total_losses_bb30 / total_trades_bb30) * 100 if total_trades_bb30 else 0

print(f"BB 3.5 Total Trades: {total_trades_bb35}")
print(f"BB 3.5 Wins: {total_wins_bb35} | Saves: {total_saves_bb35} | Losses: {total_losses_bb35}")
print(f"BB 3.5 Pure Win Rate: {pure_wr_35:.2f}%")
print(f"BB 3.5 Green / Capital Protected Rate: {green_rate_35:.2f}% (Wins + Fee Shield Saves)")
print(f"BB 3.5 Stop Loss Rate: {loss_rate_35:.2f}%")

print("-" * 50)
print(f"BB 3.0 Total Trades: {total_trades_bb30}")
print(f"BB 3.0 Wins: {total_wins_bb30} | Saves: {total_saves_bb30} | Losses: {total_losses_bb30}")
print(f"BB 3.0 Pure Win Rate: {pure_wr_30:.2f}%")
print(f"BB 3.0 Green / Capital Protected Rate: {green_rate_30:.2f}%")
print(f"BB 3.0 Stop Loss Rate: {loss_rate_30:.2f}%")
