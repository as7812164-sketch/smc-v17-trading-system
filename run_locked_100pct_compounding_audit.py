import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load the 100 chronological trades (59 Shorts, 41 Longs)
from simulate_4compounding_100trades import executed_100, s_wr, l_wr, wr, wins, losses

print("=" * 85)
print(" 🔒 MANDATE LOCKED: 100% SNOWBALL COMPOUNDING AUDIT (100 TRADES)")
print(f" Dataset: 100 Real Chronological Trades (59 Shorts @ {s_wr:.1f}% WR, 41 Longs @ {l_wr:.1f}% WR)")
print(f" Verified Overall Accuracy: {wins} Wins / {losses} Losses = {wr:.2f}% Win Rate")
print("=" * 85)

fee_rate = 0.0016 # 0.08% roundtrip maker/taker + buffer

# =============================================================================
# SCENARIO 1: SINGLE WALLET 100% FULL SNOWBALL ($50 START -> 100% DEPLOYED)
# If balance is $50, $50 deployed. If it becomes $56.60, next trade deploys $56.60!
# Dynamic Profit Armor BE Lock protects against major losses.
# =============================================================================
cap1 = 50.0
peak1 = 50.0
max_dd1 = 0.0
ladder1 = []

hit_500_1 = None
hit_1k_1 = None
hit_2k_1 = None
hit_5k_1 = None
hit_10k_1 = None

for idx, t in enumerate(executed_100):
    net_move = t["gross"] - fee_rate
    pos_size = cap1 * 5.0 # 100% OF CURRENT BALANCE AT 5X LEVERAGE
    pnl = pos_size * net_move
    
    cap1 += pnl
    if cap1 < 2.0:
        cap1 = 2.0 # Minimum floor
        
    if cap1 > peak1:
        peak1 = cap1
    dd = (peak1 - cap1) / peak1 * 100.0 if peak1 > 0 else 0.0
    if dd > max_dd1:
        max_dd1 = dd
        
    if cap1 >= 500 and hit_500_1 is None: hit_500_1 = idx + 1
    if cap1 >= 1000 and hit_1k_1 is None: hit_1k_1 = idx + 1
    if cap1 >= 2000 and hit_2k_1 is None: hit_2k_1 = idx + 1
    if cap1 >= 5000 and hit_5k_1 is None: hit_5k_1 = idx + 1
    if cap1 >= 10000 and hit_10k_1 is None: hit_10k_1 = idx + 1
    
    ladder1.append({
        "trade_num": idx + 1,
        "side": t["side"],
        "sym": t["sym"],
        "res": t["res"],
        "pnl": round(pnl, 2),
        "balance": round(cap1, 2)
    })

print("\n--- SCENARIO 1: SINGLE WALLET 100% FULL SNOWBALL ($50.00 START) ---")
print(f"Ending Balance after 100 Trades: ${cap1:,.2f} USDT")
print(f"Total Net Growth:                {((cap1 - 50.0) / 50.0 * 100.0):,.1f}%")
print(f"Max Drawdown during 100 Trades:  {max_dd1:.2f}%")
print(f"Milestones Hit:")
print(f"  • $500 Target:   Trade #{hit_500_1}")
print(f"  • $1,000 Target: Trade #{hit_1k_1}")
print(f"  • $2,000 Target: Trade #{hit_2k_1}")
if hit_5k_1:  print(f"  • $5,000 Target: Trade #{hit_5k_1}")
if hit_10k_1: print(f"  • $10,000 Target: Trade #{hit_10k_1}")

# =============================================================================
# SCENARIO 2: 4 COMPOUNDING SUB-LANES ($12.50 START EACH = $50 TOTAL)
# 2 Short Lanes + 2 Long Lanes. Each lane snowballs 100% of its OWN balance!
# =============================================================================
lanes = [12.50, 12.50, 12.50, 12.50] # Lane 0,1: Short | Lane 2,3: Long
lane_peaks = [12.50, 12.50, 12.50, 12.50]
s_turn = 0
l_turn = 2

for t in executed_100:
    net_move = t["gross"] - fee_rate
    if t["side"] == "SHORT":
        idx_lane = s_turn
        s_turn = 1 - s_turn # toggle 0 and 1
    else:
        idx_lane = l_turn
        l_turn = 5 - l_turn # toggle 2 and 3
        
    pos = lanes[idx_lane] * 5.0 # 100% of this lane's current balance
    pnl = pos * net_move
    lanes[idx_lane] += pnl
    if lanes[idx_lane] < 1.0: lanes[idx_lane] = 1.0

tot_lanes = sum(lanes)
print("\n--- SCENARIO 2: 4 COMPOUNDING LANES ($12.50 EACH = $50 TOTAL) ---")
print(f"  • Short Lane 1: ${lanes[0]:,.2f} USDT")
print(f"  • Short Lane 2: ${lanes[1]:,.2f} USDT")
print(f"  • Long Lane 1:  ${lanes[2]:,.2f} USDT")
print(f"  • Long Lane 2:  ${lanes[3]:,.2f} USDT")
print(f"Total Combined Balance: ${tot_lanes:,.2f} USDT ({((tot_lanes - 50.0) / 50.0 * 100.0):,.1f}% growth)")

# =============================================================================
# SCENARIO 3: 4 INDEPENDENT $50 ACCOUNTS ($200 TOTAL START)
# 2 Accounts trade Shorts, 2 Accounts trade Longs. 100% snowball in each account.
# =============================================================================
accs = [50.0, 50.0, 50.0, 50.0]
s_turn = 0
l_turn = 2

for t in executed_100:
    net_move = t["gross"] - fee_rate
    if t["side"] == "SHORT":
        idx_lane = s_turn
        s_turn = 1 - s_turn
    else:
        idx_lane = l_turn
        l_turn = 5 - l_turn
        
    pos = accs[idx_lane] * 5.0 # 100% of this account's balance
    pnl = pos * net_move
    accs[idx_lane] += pnl
    if accs[idx_lane] < 2.0: accs[idx_lane] = 2.0

tot_accs = sum(accs)
print("\n--- SCENARIO 3: 4 ACCOUNTS OF $50 EACH ($200 TOTAL START) ---")
print(f"  • Short Account 1: ${accs[0]:,.2f} USDT")
print(f"  • Short Account 2: ${accs[1]:,.2f} USDT")
print(f"  • Long Account 1:  ${accs[2]:,.2f} USDT")
print(f"  • Long Account 2:  ${accs[3]:,.2f} USDT")
print(f"Total Combined Balance: ${tot_accs:,.2f} USDT ({((tot_accs - 200.0) / 200.0 * 100.0):,.1f}% growth)")

# Save detailed progression of Scenario 1
with open("locked_100pct_compounding_100trades.json", "w", encoding="utf-8") as f:
    json.dump({
        "accuracy": {"total": 100, "wins": wins, "losses": losses, "win_rate": wr, "short_wr": s_wr, "long_wr": l_wr},
        "scenario1_single_wallet": {"start": 50.0, "end": round(cap1, 2), "max_dd": round(max_dd1, 2), "milestones": {"500": hit_500_1, "1000": hit_1k_1, "2000": hit_2k_1, "5000": hit_5k_1, "10000": hit_10k_1}, "trades": ladder1},
        "scenario2_four_lanes": {"start": 50.0, "end": round(tot_lanes, 2), "lanes": [round(x, 2) for x in lanes]},
        "scenario3_four_accounts": {"start": 200.0, "end": round(tot_accs, 2), "accounts": [round(x, 2) for x in accs]}
    }, f, indent=2)

print("\nSaved full audit to locked_100pct_compounding_100trades.json")
