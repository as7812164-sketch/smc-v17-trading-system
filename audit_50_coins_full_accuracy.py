import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Load candidate discovery results if available
cand_path = "candidate_coins_discovery_results.json"
cand_data = []
if os.path.exists(cand_path):
    with open(cand_path, "r", encoding="utf-8") as f:
        cand_data = json.load(f)

# Sort candidates by win rate descending
cand_data.sort(key=lambda x: (x.get("win_rate", 0), x.get("total_trades", 0)), reverse=True)

print("=" * 80)
print("🏆 CANDIDATE COINS OUTSIDE TOP-22 (DISCOVERY AUDIT RESULTS)")
print("=" * 80)
print(f"{'Symbol':<10} | {'Trades':<8} | {'Wins':<6} | {'Loss':<6} | {'Win Rate':<10} | {'Net PnL':<10} | {'Avg MFE'}")
print("-" * 80)

total_c_trades = 0
total_c_wins = 0
total_c_losses = 0
total_c_pnl = 0.0

for c in cand_data:
    trades = c.get("total_trades", 0)
    wins = c.get("wins", 0)
    losses = c.get("losses", 0)
    wr = c.get("win_rate", 0.0)
    pnl = c.get("net_pnl", 0.0)
    mfe = c.get("avg_mfe", 0.0)
    total_c_trades += trades
    total_c_wins += wins
    total_c_losses += losses
    total_c_pnl += pnl
    print(f"{c['symbol']:<10} | {trades:<8} | {wins:<6} | {losses:<6} | {wr:<9.1f}% | ${pnl:<9.2f} | +{mfe:.1f}%")

c_overall_wr = (total_c_wins / total_c_trades * 100.0) if total_c_trades > 0 else 0.0
print("-" * 80)
print(f"TOTAL CANDIDATES: {len(cand_data)} coins | Trades: {total_c_trades} | {total_c_wins}W / {total_c_losses}L | Win Rate: {c_overall_wr:.2f}% | Net PnL: ${total_c_pnl:.2f}")
print("=" * 80)

# Check 1-year master test results if available
y1_path = "hermes25_1year_test_results.json"
if os.path.exists(y1_path):
    print("\n" + "=" * 80)
    print("🏆 1-YEAR MASTER AUDIT (TOP-22 CHAMPIONS BASELINE)")
    print("=" * 80)
    with open(y1_path, "r", encoding="utf-8") as f:
        y1_data = json.load(f)
    print("1-Year Baseline Summary:", json.dumps(y1_data.get("summary", {}), indent=2))
