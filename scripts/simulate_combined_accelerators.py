import sys
import os
import json

# Let's test the combined optimization models:
# Optimization 1: Golden 1.5x Milestone Step (instead of 2.0x Double)
# Optimization 2: Profit-Buffer Acceleration ("House Money" margin booster)
# Optimization 3: Asymmetric Trailing (+18% to +22% ROE on Grade A+ setups)
# Optimization 4: Multi-Slot Concurrency (2 to 3 slots)

with open('scripts/harvested_trades_cache.json', 'r') as f:
    trades = json.load(f)

TARGET_1CR = 115000.0  # ₹1 Crore INR ≈ $115,000 USDT

def simulate_system(name, step_mult=2.0, base_margin_pct=0.10, profit_buf_pct=0.0, rr_boost=False, monthly_volume=58.4):
    capital = 500.0
    peak = capital
    max_dd = 0.0
    tier_base = 500.0
    tier_target = tier_base * step_mult
    
    total_trades = 0
    milestones = []
    hit_trade = None
    
    loop = 0
    while capital < TARGET_1CR and loop < 25:
        for t in trades:
            total_trades += 1
            
            # Profit in current tier
            p_tier = max(0.0, capital - tier_base)
            margin = (tier_base * base_margin_pct) + (p_tier * profit_buf_pct)
            margin = min(margin, capital * 0.20)  # Safe cap
            
            # ROE calculation
            roe = t["roe_pct"]
            if rr_boost and roe > 10.0:
                # Grade A+ momentum runner gives +18.5% instead of fixed +14.5%
                roe = roe * 1.25
                
            pnl = margin * (roe / 100.0)
            capital += pnl
            
            if capital > peak:
                peak = capital
            dd = (peak - capital) / peak * 100.0
            if dd > max_dd:
                max_dd = dd
                
            if capital >= tier_target:
                milestones.append({
                    "stage": len(milestones) + 1,
                    "reached": round(capital, 2),
                    "trade": total_trades
                })
                tier_base = tier_target
                tier_target = tier_base * step_mult
                
            if capital >= TARGET_1CR and hit_trade is None:
                hit_trade = total_trades
                break
        loop += 1
        
    months = round(hit_trade / monthly_volume, 1) if hit_trade else 0
    years = round(months / 12.0, 2)
    
    return {
        "name": name,
        "trades": hit_trade,
        "max_dd": round(max_dd, 2),
        "months": months,
        "years": years,
        "stages": len(milestones)
    }

models = [
    # Baseline
    ("1. Baseline Model A (2.0x Double, 1-Slot)", 2.0, 0.10, 0.0, False, 58.4),
    
    # Lever 1: 1.5x Golden Step
    ("2. Lever 1: Golden 1.5x Step (1-Slot)", 1.5, 0.10, 0.0, False, 58.4),
    
    # Lever 2: House Money Profit Buffer
    ("3. Lever 2: Profit-Buffer Aggression (1-Slot)", 2.0, 0.10, 0.15, False, 58.4),
    
    # Lever 3: Golden 1.5x Step + House Money Buffer
    ("4. Lever 1+2: Golden 1.5x + Profit-Buffer", 1.5, 0.10, 0.12, False, 58.4),
    
    # Lever 4: Trailing Expansion
    ("5. Lever 1+2+3: Golden 1.5x + Buffer + Trailing Boost", 1.5, 0.10, 0.12, True, 58.4),
    
    # With Concurrency (2 Parallel Slots -> 101 trades/mo)
    ("6. Golden 1.5x + 2 Concurrent Slots", 1.5, 0.10, 0.0, False, 101.3),
    
    # Supercharged: Levers 1+2+3 + 2 Concurrent Slots
    ("7. Supercharged Model A (All Levers + 2 Slots)", 1.5, 0.10, 0.12, True, 101.3),
    
    # Supercharged: Levers 1+2+3 + 3 Concurrent Slots (133 trades/mo)
    ("8. Ultra Model A (All Levers + 3 Slots)", 1.5, 0.10, 0.12, True, 133.0),
]

print("="*105)
print(f"{'MODEL DESCRIPTION':<48} | {'TRADES':<8} | {'MAX DD %':<9} | {'MONTHS':<8} | {'CALENDAR TIME'}")
print("="*105)
for m in models:
    res = simulate_system(m[0], m[1], m[2], m[3], m[4], m[5])
    print(f"{res['name']:<48} | {str(res['trades']):<8} | {str(res['max_dd']) + '%':<9} | {str(res['months']) + ' mo':<8} | {str(res['years']) + ' Years'}")
print("="*105)
