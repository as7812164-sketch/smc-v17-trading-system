import json
import os
import sys

from run_full_quant_buy_1year_backtest import run_backtest

b_4h, b_all, q_4h, q_all = run_backtest()

q_all.sort(key=lambda x: x["time"])
print(f"Total Full Quant 1H+4H Signals generated: {len(q_all)}")
w_raw = sum(1 for x in q_all if x['res'] == 'WIN')
print(f"Raw Wins: {w_raw} / {len(q_all)} = {w_raw/len(q_all)*100:.2f}%\n")

for slots in [1, 2, 3, 5, 999]:
    active_positions = []
    executed = []
    for s in q_all:
        active_positions = [t for t in active_positions if t > s["time"]]
        if len(active_positions) < slots:
            active_positions.append(s["exit_time"])
            executed.append(s)
    w = sum(1 for x in executed if x['res'] == 'WIN')
    l = len(executed) - w
    wr = (w / len(executed) * 100.0) if executed else 0.0
    slot_label = f"{slots} Slot{'s' if slots > 1 else ''}" if slots < 100 else "All Signals (Unconstrained)"
    print(f"{slot_label:<30}: Executed = {len(executed):3d} | Wins = {w:3d} | Losses = {l:2d} | Win Rate = {wr:5.2f}%")
