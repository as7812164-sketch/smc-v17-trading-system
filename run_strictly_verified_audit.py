import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load all signals from the 1-year data
from simulate_4compounding_100trades import long_signals, short_signals

print(f"Total available raw signals: {len(long_signals)} Longs | {len(short_signals)} Shorts")

# Combine and sort all signals chronologically
all_signals = long_signals + short_signals
all_signals.sort(key=lambda x: x["time"])

fee_rate = 0.0016 # 0.08% maker/taker roundtrip + buffer

# =============================================================================
# MODEL 1: STRICT CHRONOLOGICAL SEQUENTIAL (1 TRADE AT A TIME, ZERO OVERLAP)
# $50 Start | 100% Capital Deployed on every trade at 5x leverage
# Trade N+1 ONLY opens after Trade N has closed!
# =============================================================================
seq_executed = []
active_exit_time = 0

for s in all_signals:
    if s["time"] >= active_exit_time:
        seq_executed.append(s)
        active_exit_time = s["exit_time"]
    if len(seq_executed) >= 100:
        break

print(f"\nModel 1: Strict Sequential (Zero Overlap): {len(seq_executed)} Trades")

cap_seq = 50.0
peak_seq = 50.0
max_dd_seq = 0.0
wins_seq = 0
losses_seq = 0

ladder_seq = []
for idx, t in enumerate(seq_executed):
    net_move = t["gross"] - fee_rate
    pos_size = cap_seq * 5.0 # 100% DEPLOYED AT 5X
    pnl = pos_size * net_move
    
    is_win = (t["res"] == "WIN")
    if is_win:
        wins_seq += 1
    else:
        losses_seq += 1
        
    cap_seq += pnl
    if cap_seq < 2.0: cap_seq = 2.0
    
    if cap_seq > peak_seq: peak_seq = cap_seq
    dd = (peak_seq - cap_seq) / peak_seq * 100.0 if peak_seq > 0 else 0.0
    if dd > max_dd_seq: max_dd_seq = dd
    
    ladder_seq.append({
        "num": idx + 1, "side": t["side"], "sym": t["sym"], "res": t["res"],
        "pnl": round(pnl, 2), "balance": round(cap_seq, 2)
    })

wr_seq = (wins_seq / len(seq_executed) * 100.0) if seq_executed else 0.0

# =============================================================================
# MODEL 2: 4 INDEPENDENT SUB-ACCOUNTS (2 SHORTS + 2 LONGS)
# Each account starts with $50.00 ($200 Total Capital)
# Each account runs its own 100% sequential compounding with zero self-overlap!
# =============================================================================
acc_exit = [0, 0, 0, 0] # 0,1: Short | 2,3: Long
acc_trades = [[], [], [], []]
acc_caps = [50.0, 50.0, 50.0, 50.0]

for s in all_signals:
    if s["side"] == "SHORT":
        # Check which short account is free
        if s["time"] >= acc_exit[0]:
            acc_trades[0].append(s)
            acc_exit[0] = s["exit_time"]
        elif s["time"] >= acc_exit[1]:
            acc_trades[1].append(s)
            acc_exit[1] = s["exit_time"]
    else:
        # Check which long account is free
        if s["time"] >= acc_exit[2]:
            acc_trades[2].append(s)
            acc_exit[2] = s["exit_time"]
        elif s["time"] >= acc_exit[3]:
            acc_trades[3].append(s)
            acc_exit[3] = s["exit_time"]
            
    total_acc_trades = sum(len(x) for x in acc_trades)
    if total_acc_trades >= 100:
        break

# Truncate to exactly 100 trades across the 4 accounts
merged_4acc = []
for i in range(4):
    for t in acc_trades[i]:
        merged_4acc.append((i, t))
merged_4acc.sort(key=lambda x: x[1]["time"])
merged_4acc = merged_4acc[:100]

# Simulate 100% compounding per account
acc_wins = [0, 0, 0, 0]
acc_losses = [0, 0, 0, 0]
for acc_id, t in merged_4acc:
    net_move = t["gross"] - fee_rate
    pos = acc_caps[acc_id] * 5.0
    pnl = pos * net_move
    acc_caps[acc_id] += pnl
    if acc_caps[acc_id] < 2.0: acc_caps[acc_id] = 2.0
    if t["res"] == "WIN":
        acc_wins[acc_id] += 1
    else:
        acc_losses[acc_id] += 1

tot_4acc_wins = sum(acc_wins)
tot_4acc_loss = sum(acc_losses)
tot_4acc_wr = tot_4acc_wins / len(merged_4acc) * 100.0
tot_4acc_balance = sum(acc_caps)

# =============================================================================
# MODEL 3: SINGLE $50 SPLIT INTO 4 COMPOUNDING LANES ($12.50 EACH)
# Same as Model 2, but starting with $12.50 per lane ($50 total)
# =============================================================================
lane_caps = [12.50, 12.50, 12.50, 12.50]
for acc_id, t in merged_4acc:
    net_move = t["gross"] - fee_rate
    pos = lane_caps[acc_id] * 5.0
    pnl = pos * net_move
    lane_caps[acc_id] += pnl
    if lane_caps[acc_id] < 1.0: lane_caps[acc_id] = 1.0

tot_4lane_balance = sum(lane_caps)

print("=" * 85)
print(" 🔬 RE-AUDITED FORENSIC RESULTS (STRICT TIMELINE VERIFIED, ZERO OVERLAP)")
print("=" * 85)

print("\n--- MODEL 1: STRICT 1-WALLET SEQUENTIAL ($50 START -> 100% REINVESTED) ---")
print(f"Total Trades:      {len(seq_executed)}")
print(f"Accuracy:          {wins_seq} Wins / {losses_seq} Losses = {wr_seq:.2f}% Win Rate")
print(f"Starting Capital:  $50.00 USDT")
print(f"Final Balance:     ${cap_seq:,.2f} USDT")
print(f"Total Growth:      {((cap_seq - 50.0) / 50.0 * 100.0):,.1f}%")
print(f"Max Drawdown:      {max_dd_seq:.2f}%")

print("\n--- MODEL 2: 4 ACCOUNTS OF $50 EACH ($200 TOTAL START) ---")
print(f"Total Trades:      {len(merged_4acc)}")
print(f"Accuracy:          {tot_4acc_wins} Wins / {tot_4acc_loss} Losses = {tot_4acc_wr:.2f}% Win Rate")
print(f"Starting Capital:  $200.00 USDT ($50 x 4 accounts)")
print(f"Final Balance:     ${tot_4acc_balance:,.2f} USDT")
print(f"  • Short Acc 1:   ${acc_caps[0]:,.2f} ({acc_wins[0]}W / {acc_losses[0]}L)")
print(f"  • Short Acc 2:   ${acc_caps[1]:,.2f} ({acc_wins[1]}W / {acc_losses[1]}L)")
print(f"  • Long Acc 1:    ${acc_caps[2]:,.2f} ({acc_wins[2]}W / {acc_losses[2]}L)")
print(f"  • Long Acc 2:    ${acc_caps[3]:,.2f} ({acc_wins[3]}W / {acc_losses[3]}L)")
print(f"Total Growth:      {((tot_4acc_balance - 200.0) / 200.0 * 100.0):,.1f}%")

print("\n--- MODEL 3: $50 DIVIDED INTO 4 LANES ($12.50 START EACH) ---")
print(f"Starting Capital:  $50.00 USDT ($12.50 x 4 lanes)")
print(f"Final Balance:     ${tot_4lane_balance:,.2f} USDT")
print(f"  • Short Lane 1:  ${lane_caps[0]:,.2f}")
print(f"  • Short Lane 2:  ${lane_caps[1]:,.2f}")
print(f"  • Long Lane 1:   ${lane_caps[2]:,.2f}")
print(f"  • Long Lane 2:   ${lane_caps[3]:,.2f}")
print(f"Total Growth:      {((tot_4lane_balance - 50.0) / 50.0 * 100.0):,.1f}%")

# Save to json
with open("rechecked_compounding_100trades.json", "w", encoding="utf-8") as f:
    json.dump({
        "model1_seq": {"trades": len(seq_executed), "wins": wins_seq, "losses": losses_seq, "wr": wr_seq, "end_bal": round(cap_seq, 2), "max_dd": round(max_dd_seq, 2), "ladder": ladder_seq[:25]},
        "model2_4acc": {"start": 200.0, "end_bal": round(tot_4acc_balance, 2), "wr": tot_4acc_wr, "caps": [round(x, 2) for x in acc_caps]},
        "model3_4lanes": {"start": 50.0, "end_bal": round(tot_4lane_balance, 2), "wr": tot_4acc_wr, "caps": [round(x, 2) for x in lane_caps]}
    }, f, indent=2)

print("\nSaved re-audited results to rechecked_compounding_100trades.json")
