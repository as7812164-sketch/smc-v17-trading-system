import json
import os

with open('scripts/harvested_trades_cache.json', 'r') as f:
    trades = json.load(f)

print(f"Loaded {len(trades)} trades.")
TARGET_1CR_INR_USDT = 115000.0  # ₹1 Crore INR ≈ $115,000 USDT

def simulate_step_milestone(step_multiplier=2.0, margin_pct=0.10, profit_buffer_pct=0.0):
    capital = 500.0
    peak = capital
    max_dd = 0.0
    tier_base = 500.0
    tier_margin = tier_base * margin_pct
    tier_target = tier_base * step_multiplier

    total_executed = 0
    milestones = []
    target_hit_trade = None
    target_hit_days = None

    loop_count = 0
    start_time_ms = trades[0]["time"]

    while capital < TARGET_1CR_INR_USDT and loop_count < 20:
        for t in trades:
            total_executed += 1
            
            # Base margin + profit buffer if active
            profit_in_tier = max(0.0, capital - tier_base)
            margin = tier_margin + (profit_in_tier * profit_buffer_pct)
            # Cap margin at 20% of capital for safety
            margin = min(margin, capital * 0.20)

            pnl = margin * (t["roe_pct"] / 100.0)
            capital += pnl

            if capital > peak:
                peak = capital
            dd = (peak - capital) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

            if capital >= tier_target:
                milestones.append({
                    "stage": len(milestones) + 1,
                    "base": round(tier_base, 2),
                    "target": round(tier_target, 2),
                    "cap": round(capital, 2),
                    "trade": total_executed,
                    "days": round((t["time"] - start_time_ms) / (86400 * 1000) + (loop_count * 365), 1)
                })
                tier_base = tier_target
                tier_margin = tier_base * margin_pct
                tier_target = tier_base * step_multiplier

            if capital >= TARGET_1CR_INR_USDT and target_hit_trade is None:
                target_hit_trade = total_executed
                target_hit_days = round((t["time"] - start_time_ms) / (86400 * 1000) + (loop_count * 365), 1)
                break
        loop_count += 1

    return {
        "step_multiplier": step_multiplier,
        "margin_pct": margin_pct,
        "profit_buffer_pct": profit_buffer_pct,
        "final_capital": round(capital, 2),
        "trades_to_1cr": target_hit_trade,
        "days_to_1cr": target_hit_days,
        "years_to_1cr": round(target_hit_days / 365.25, 2) if target_hit_days else None,
        "max_dd_pct": round(max_dd, 2),
        "milestones_count": len(milestones)
    }

results = {}
# 1. Baseline Model A (2.0x Double, 10% margin)
results["Baseline_2.0x_Double"] = simulate_step_milestone(step_multiplier=2.0, margin_pct=0.10, profit_buffer_pct=0.0)

# 2. Golden Fibonacci Step (1.5x Step, 10% margin)
results["Golden_1.5x_Step"] = simulate_step_milestone(step_multiplier=1.5, margin_pct=0.10, profit_buffer_pct=0.0)

# 3. Quarterly Milestone (1.25x Step, 10% margin)
results["Quarterly_1.25x_Step"] = simulate_step_milestone(step_multiplier=1.25, margin_pct=0.10, profit_buffer_pct=0.0)

# 4. Model A + House Money / Profit Buffer (2.0x Double, 10% base + 15% of tier profit)
results["Model_A_ProfitBuffer_15pct"] = simulate_step_milestone(step_multiplier=2.0, margin_pct=0.10, profit_buffer_pct=0.15)

# 5. Golden 1.5x Step + House Money (1.5x Step, 10% base + 15% tier profit)
results["Golden_1.5x_ProfitBuffer_15pct"] = simulate_step_milestone(step_multiplier=1.5, margin_pct=0.10, profit_buffer_pct=0.15)

# 6. Moderate 12% Margin (2.0x Double, 12% margin)
results["Model_A_12pct_Margin"] = simulate_step_milestone(step_multiplier=2.0, margin_pct=0.12, profit_buffer_pct=0.0)

# 7. Golden 1.5x Step with 12% Margin
results["Golden_1.5x_12pct_Margin"] = simulate_step_milestone(step_multiplier=1.5, margin_pct=0.12, profit_buffer_pct=0.0)

print("\n" + "="*95)
print(f"{'STRATEGY MODEL':<32} | {'TRADES':<8} | {'DAYS':<8} | {'YEARS':<7} | {'MAX DD %':<9} | {'STAGES'}")
print("="*95)
for k, v in results.items():
    print(f"{k:<32} | {str(v['trades_to_1cr']):<8} | {str(v['days_to_1cr']):<8} | {str(v['years_to_1cr']):<7} | {str(v['max_dd_pct']) + '%':<9} | {v['milestones_count']}")
print("="*95)

with open('scripts/model_a_optimizations_results.json', 'w') as f:
    json.dump(results, f, indent=2)
