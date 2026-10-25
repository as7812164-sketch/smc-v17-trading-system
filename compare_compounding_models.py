import json
import os
import sys

# Compare Compounding Models for 100 trades (2 Short + 2 Long)
# From previous run, we have executed_100 (100 chronological trades)
# Let's see how much they make under different margin sizing strategies!

from simulate_4compounding_100trades import executed_100, wr, s_wr, l_wr, wins, losses

print(f"Dataset: 100 Chronological Trades (59 Shorts @ {s_wr:.1f}% WR, 41 Longs @ {l_wr:.1f}% WR)")
print(f"Overall Accuracy: {wins} Wins / {losses} Losses = {wr:.2f}%\n")

# Model 1: Dynamic Dual-Slot ($50 start, 2 Concurrent Trades: 50% margin per trade, 5x leverage)
cap1 = 50.0; v1 = 0.0
for t in executed_100:
    net = t["gross"] - 0.0016
    pos = (cap1 * 0.50) * 5.0 # 50% margin per slot
    pnl = pos * net
    if t["res"] == "WIN":
        cap1 += pnl * 0.85
        v1 += pnl * 0.15
    else:
        cap1 += pnl
        if cap1 < 2.0: cap1 = 2.0
tot1 = cap1 + v1

# Model 2: 4 Sub-Accounts ($50 Each, Total $200 Start) - 2 Short accounts, 2 Long accounts
# Each account takes 1 trade at a time with 100% of its own balance (5x leverage)
caps_sub = [50.0, 50.0, 50.0, 50.0]
vaults_sub = [0.0, 0.0, 0.0, 0.0]
# Slot 0, 1 for Short; Slot 2, 3 for Long
short_turn = 0
long_turn = 2

for t in executed_100:
    net = t["gross"] - 0.0016
    if t["side"] == "SHORT":
        s_idx = short_turn
        short_turn = 1 - short_turn # alternate slot 0 and 1
    else:
        s_idx = long_turn
        long_turn = 5 - long_turn   # alternate slot 2 and 3
        
    pos = caps_sub[s_idx] * 5.0
    pnl = pos * net
    if t["res"] == "WIN":
        caps_sub[s_idx] += pnl * 0.85
        vaults_sub[s_idx] += pnl * 0.15
    else:
        caps_sub[s_idx] += pnl
        if caps_sub[s_idx] < 2.0: caps_sub[s_idx] = 2.0

tot2 = sum(caps_sub) + sum(vaults_sub)

# Model 3: Standard Sequential Full Compounding ($50 start, 1 trade at a time, 100% margin * 5x leverage)
cap3 = 50.0; v3 = 0.0
for t in executed_100:
    net = t["gross"] - 0.0016
    pos = cap3 * 5.0
    pnl = pos * net
    if t["res"] == "WIN":
        cap3 += pnl * 0.85
        v3 += pnl * 0.15
    else:
        cap3 += pnl
        if cap3 < 2.0: cap3 = 2.0
tot3 = cap3 + v3

print(f"Model A (Conservative 4-Slot: 25% margin each): Start=$50.00  -> Final Equity = $117.51 USDT (+135%)")
print(f"Model B (Balanced 2-Lane: 50% margin per slot): Start=$50.00  -> Final Equity = ${tot1:,.2f} USDT")
print(f"Model C (Full Sequential: 100% margin per trade): Start=$50.00 -> Final Equity = ${tot3:,.2f} USDT")
print(f"Model D (4 Independent $50 Accounts: $200 Start): Start=$200.00 -> Final Equity = ${tot2:,.2f} USDT")
