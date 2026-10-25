"""
Compounding simulation: 10 isolated sections ($50 start per section = $500 total).
Compares Hermes 3.5 (50% MT) vs Boundary + 15m OF on 1H and 4H chronological setups.
"""
import os
import json

from run_experiment_boundary_orderflow_vs_50mt import (
    load_15m_data, resample_15m_to_higher_tf, calculate_ema
)

def simulate_isolated_deca(trades):
    # 10 sections, each starts at $50.00
    sections = [50.0] * 10
    sec_idx = 0
    
    # Sort trades by timestamp
    trades.sort(key=lambda x: x["time"])
    
    for t in trades:
        balance = sections[sec_idx]
        outcome = t["outcome"]
        
        # 5x leverage, 100% section margin
        if outcome == "WIN":
            # +14.0% ROE -> profit = balance * 0.14
            sections[sec_idx] += balance * 0.140
        elif outcome == "LOSS":
            # -14.0% ROE -> loss = balance * 0.14
            sections[sec_idx] -= balance * 0.140
        elif outcome == "BREAKEVEN":
            # +0.50% net after fee buffer
            sections[sec_idx] += balance * 0.005
            
        sec_idx = (sec_idx + 1) % 10
        
    total_equity = sum(sections)
    return total_equity, sections

# Let's inspect the compounding across 1H
print("Compounding calculation helper ready.")
