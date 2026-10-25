import json
import os
import sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
TARGET_1CR = 115000.0  # ₹1 Crore INR ≈ $115,000 USDT

with open("scripts/resolved_apex_setups.json", "r") as f:
    raw_setups = json.load(f)

print(f"Loaded {len(raw_setups)} resolved setups.")

# Calculate overall baseline stats of the raw setups
outcomes_count = defaultdict(int)
trailing_profits = []
for s in raw_setups:
    outcomes_count[s["outcome"]] += 1
    if s["outcome"] == "TRAILING_SL_HIT":
        trailing_profits.append(s["locked_roi"])

print("\n--- RAW SETUPS FORENSICS ---")
for k, v in outcomes_count.items():
    print(f"  {k}: {v} ({v/len(raw_setups)*100:.1f}%)")
if trailing_profits:
    print(f"  Trailing SL Trades: {len(trailing_profits)} | Highest Locked ROI: +{max(trailing_profits):.1f}% ROI | Avg Locked ROI: +{sum(trailing_profits)/len(trailing_profits):.1f}% ROI")

# =============================================================================
# SIMULATION ENGINE
# If setups in 2-year window (5,639) finish before reaching 1 Crore, we repeat
# the cycle chronologically with timestamp offset so we can measure exact multi-year duration.
# =============================================================================

def get_chronological_stream(max_loops=15):
    """Yields setups chronologically with proper time continuity across loops."""
    start_time = raw_setups[0]["entry_time"]
    end_time = raw_setups[-1]["exit_time"]
    cycle_duration = end_time - start_time + (24 * 3600 * 1000)  # Add 1 day buffer

    for loop in range(max_loops):
        time_offset = loop * cycle_duration
        for s in raw_setups:
            yield {
                "sym": s["sym"],
                "tf": s["tf"],
                "side": s["side"],
                "entry_time": s["entry_time"] + time_offset,
                "exit_time": s["exit_time"] + time_offset,
                "outcome": s["outcome"],
                "locked_roi": s["locked_roi"],
                "peak_roi": s["peak_roi"],
                "trailing_step": s["trailing_step"],
                "roe_pct": s["roe_pct"]
            }

# =============================================================================
# MODEL 1: 10-SECTION 100% COMPOUNDING (DECA MATRIX)
# =============================================================================
def run_model_1_deca(num_sections=10):
    sections = [{"id": i+1, "balance": 50.0, "busy_until": 0, "trades": 0, "wins": 0} for i in range(num_sections)]
    
    total_trades = 0
    wins = 0
    losses = 0
    tp_hits = 0
    trailing_sl_hits = 0
    soft_sl_hits = 0
    hard_sl_hits = 0
    timeout_hits = 0
    
    highest_trailing_roe = 0.0
    trailing_roe_list = []
    
    peak_portfolio = 500.0
    max_dd = 0.0
    
    start_time = None
    target_hit_time = None
    target_hit_trade = None
    
    milestone_targets = [1000.0, 2000.0, 5000.0, 10000.0, 25000.0, 50000.0, 100000.0, TARGET_1CR]
    next_m_idx = 0
    milestones_log = []
    
    stream = get_chronological_stream()
    
    for s in stream:
        if start_time is None:
            start_time = s["entry_time"]
            
        cur_time = s["entry_time"]
        
        # Find an idle section
        idle_section = None
        for sec in sections:
            if sec["busy_until"] <= cur_time and sec["balance"] >= 2.0:
                idle_section = sec
                break
                
        if idle_section is None:
            # All 10 sections are currently busy with active trades
            continue
            
        # Execute trade on this section
        margin = idle_section["balance"]  # 100% compounding of this section
        pnl = margin * (s["roe_pct"] / 100.0)
        
        idle_section["balance"] += pnl
        if idle_section["balance"] < 1.0:
            idle_section["balance"] = 1.0  # Floor guard
            
        idle_section["busy_until"] = s["exit_time"]
        idle_section["trades"] += 1
        total_trades += 1
        
        if s["roe_pct"] > 0:
            wins += 1
            idle_section["wins"] += 1
        else:
            losses += 1
            
        # Outcomes breakdown
        out = s["outcome"]
        if out == "TP_HIT":
            tp_hits += 1
        elif out == "TRAILING_SL_HIT":
            trailing_sl_hits += 1
            trailing_roe_list.append(s["locked_roi"])
            if s["locked_roi"] > highest_trailing_roe:
                highest_trailing_roe = s["locked_roi"]
        elif out == "SOFT_SL_HIT":
            soft_sl_hits += 1
        elif out == "HARD_SL_HIT":
            hard_sl_hits += 1
        else:
            timeout_hits += 1
            
        # Total Portfolio check
        total_portfolio = sum(sec["balance"] for sec in sections)
        if total_portfolio > peak_portfolio:
            peak_portfolio = total_portfolio
        dd = (peak_portfolio - total_portfolio) / peak_portfolio * 100.0
        if dd > max_dd:
            max_dd = dd
            
        # Check milestones
        if next_m_idx < len(milestone_targets) and total_portfolio >= milestone_targets[next_m_idx]:
            days_el = (s["exit_time"] - start_time) / (86400 * 1000)
            milestones_log.append({
                "milestone": milestone_targets[next_m_idx],
                "portfolio": round(total_portfolio, 2),
                "trades": total_trades,
                "days": round(days_el, 1),
                "months": round(days_el / 30.41, 1),
                "years": round(days_el / 365.25, 2)
            })
            next_m_idx += 1
            
        if total_portfolio >= TARGET_1CR:
            target_hit_time = s["exit_time"]
            target_hit_trade = total_trades
            break
            
    days_to_1cr = round((target_hit_time - start_time) / (86400 * 1000), 1) if target_hit_time else None
    
    return {
        "model_name": "Model 1: 10-Section 100% Compounding (Deca Matrix)",
        "starting_capital": 500.0,
        "final_capital": round(sum(sec["balance"] for sec in sections), 2),
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(wins / total_trades * 100.0, 2) if total_trades else 0,
        "tp_hits": tp_hits,
        "trailing_sl_hits": trailing_sl_hits,
        "soft_sl_hits": soft_sl_hits,
        "hard_sl_hits": hard_sl_hits,
        "timeout_hits": timeout_hits,
        "highest_trailing_roi": highest_trailing_roe,
        "avg_trailing_roi": round(sum(trailing_roe_list)/len(trailing_roe_list), 2) if trailing_roe_list else 0,
        "max_drawdown_pct": round(max_dd, 2),
        "days_to_1cr": days_to_1cr,
        "months_to_1cr": round(days_to_1cr / 30.41, 1) if days_to_1cr else None,
        "years_to_1cr": round(days_to_1cr / 365.25, 2) if days_to_1cr else None,
        "milestones": milestones_log,
        "sections_breakdown": [
            {"id": sec["id"], "balance": round(sec["balance"], 2), "trades": sec["trades"], "wins": sec["wins"]}
            for sec in sections
        ]
    }

# =============================================================================
# MODEL 2: STEP-DOUBLE 10% PER SIGNAL (WITH MULTI-SIGNAL CONCURRENCY)
# =============================================================================
def run_model_2_step_double(max_concurrent_signals=5):
    capital = 500.0
    tier_base = 500.0
    tier_target = 1000.0
    tier_margin = tier_base * 0.10  # 10% per signal
    
    total_trades = 0
    wins = 0
    losses = 0
    tp_hits = 0
    trailing_sl_hits = 0
    soft_sl_hits = 0
    hard_sl_hits = 0
    timeout_hits = 0
    
    highest_trailing_roe = 0.0
    trailing_roe_list = []
    
    peak_portfolio = 500.0
    max_dd = 0.0
    
    start_time = None
    target_hit_time = None
    target_hit_trade = None
    
    # Active open positions: list of dicts {"exit_time": ms, "margin": $, "roe_pct": %, "trade_info": s}
    active_positions = []
    
    milestone_targets = [1000.0, 2000.0, 4000.0, 8000.0, 16000.0, 32000.0, 64000.0, TARGET_1CR]
    next_m_idx = 0
    milestones_log = []
    
    stream = get_chronological_stream()
    
    for s in stream:
        if start_time is None:
            start_time = s["entry_time"]
            
        cur_time = s["entry_time"]
        
        # 1. Close any active positions that exited before cur_time
        still_active = []
        for pos in sorted(active_positions, key=lambda x: x["exit_time"]):
            if pos["exit_time"] <= cur_time:
                # Resolve trade
                pnl = pos["margin"] * (pos["roe_pct"] / 100.0)
                capital += pnl
                total_trades += 1
                
                if pos["roe_pct"] > 0:
                    wins += 1
                else:
                    losses += 1
                    
                out = pos["outcome"]
                if out == "TP_HIT":
                    tp_hits += 1
                elif out == "TRAILING_SL_HIT":
                    trailing_sl_hits += 1
                    trailing_roe_list.append(pos["locked_roi"])
                    if pos["locked_roi"] > highest_trailing_roe:
                        highest_trailing_roe = pos["locked_roi"]
                elif out == "SOFT_SL_HIT":
                    soft_sl_hits += 1
                elif out == "HARD_SL_HIT":
                    hard_sl_hits += 1
                else:
                    timeout_hits += 1
                    
                # Track peak & DD
                if capital > peak_portfolio:
                    peak_portfolio = capital
                dd = (peak_portfolio - capital) / peak_portfolio * 100.0
                if dd > max_dd:
                    max_dd = dd
                    
                # Check Milestone 2x double!
                if capital >= tier_target:
                    days_el = (pos["exit_time"] - start_time) / (86400 * 1000)
                    milestones_log.append({
                        "from_cap": tier_base,
                        "to_cap": tier_target,
                        "capital_reached": round(capital, 2),
                        "trades": total_trades,
                        "days": round(days_el, 1),
                        "months": round(days_el / 30.41, 1),
                        "years": round(days_el / 365.25, 2),
                        "margin_used": tier_margin
                    })
                    tier_base = tier_target
                    tier_margin = tier_base * 0.10
                    tier_target = tier_base * 2.0
                    
                if capital >= TARGET_1CR and target_hit_time is None:
                    target_hit_time = pos["exit_time"]
                    target_hit_trade = total_trades
                    break
            else:
                still_active.append(pos)
                
        active_positions = still_active
        if target_hit_time is not None:
            break
            
        # 2. Check if we can open a new position
        if len(active_positions) >= max_concurrent_signals:
            continue
            
        # Margin required
        req_margin = tier_margin
        used_margin = sum(p["margin"] for p in active_positions)
        free_capital = capital - used_margin
        
        if free_capital >= req_margin:
            active_positions.append({
                "exit_time": s["exit_time"],
                "margin": req_margin,
                "roe_pct": s["roe_pct"],
                "outcome": s["outcome"],
                "locked_roi": s["locked_roi"]
            })

    days_to_1cr = round((target_hit_time - start_time) / (86400 * 1000), 1) if target_hit_time else None
    
    return {
        "model_name": f"Model 2: Step-Double 10% (Max {max_concurrent_signals} Concurrent Signals)",
        "starting_capital": 500.0,
        "final_capital": round(capital, 2),
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(wins / total_trades * 100.0, 2) if total_trades else 0,
        "tp_hits": tp_hits,
        "trailing_sl_hits": trailing_sl_hits,
        "soft_sl_hits": soft_sl_hits,
        "hard_sl_hits": hard_sl_hits,
        "timeout_hits": timeout_hits,
        "highest_trailing_roi": highest_trailing_roe,
        "avg_trailing_roi": round(sum(trailing_roe_list)/len(trailing_roe_list), 2) if trailing_roe_list else 0,
        "max_drawdown_pct": round(max_dd, 2),
        "days_to_1cr": days_to_1cr,
        "months_to_1cr": round(days_to_1cr / 30.41, 1) if days_to_1cr else None,
        "years_to_1cr": round(days_to_1cr / 365.25, 2) if days_to_1cr else None,
        "milestones": milestones_log
    }

print("\n" + "="*80)
print("RUNNING 100% REAL SIMULATION DUEL: MODEL 1 vs MODEL 2")
print("="*80)

res_m1 = run_model_1_deca(10)
res_m2_5 = run_model_2_step_double(max_concurrent_signals=5)
res_m2_10 = run_model_2_step_double(max_concurrent_signals=10)

duel_results = {
    "model_1_deca": res_m1,
    "model_2_step_double_5slots": res_m2_5,
    "model_2_step_double_10slots": res_m2_10
}

with open("scripts/exact_duel_real_results.json", "w") as f:
    json.dump(duel_results, f, indent=2)

print("\n--- EXACT DUEL SUMMARY RESULTS ---")
for key, r in duel_results.items():
    print(f"\n=================================================================")
    print(f"MODEL: {r['model_name']}")
    print(f"=================================================================")
    print(f"  Starting Capital: ${r['starting_capital']} -> Final: ${r['final_capital']}")
    print(f"  Total Trades to ₹1 Crore: {r['total_trades']}")
    print(f"  Win Rate: {r['win_rate_pct']}% ({r['wins']} Wins / {r['losses']} Losses)")
    print(f"  TP Hits (+15% ROE): {r['tp_hits']} ({r['tp_hits']/r['total_trades']*100:.1f}%)")
    print(f"  Trailing SL Hits: {r['trailing_sl_hits']} ({r['trailing_sl_hits']/r['total_trades']*100:.1f}%)")
    print(f"    -> Highest Trailing Locked ROI: +{r['highest_trailing_roi']:.1f}% ROI")
    print(f"    -> Average Trailing Locked ROI: +{r['avg_trailing_roi']:.1f}% ROI")
    print(f"  Soft SL Hits (-7.5% ROE): {r['soft_sl_hits']} ({r['soft_sl_hits']/r['total_trades']*100:.1f}%)")
    print(f"  Hard SL Hits (-15.0% ROE): {r['hard_sl_hits']} ({r['hard_sl_hits']/r['total_trades']*100:.1f}%)")
    print(f"  Max Drawdown: {r['max_drawdown_pct']}%")
    print(f"  TIME TO ₹1 CRORE: {r['days_to_1cr']} Days | {r['months_to_1cr']} Months | {r['years_to_1cr']} Years")
    print("\n  MILESTONES REACHED:")
    for m in r['milestones']:
        if 'milestone' in m:
            print(f"    Target: ${m['milestone']:<8} | Reached: ${m['portfolio']:<9} | Trades: {m['trades']:<5} | Days: {m['days']:<6} ({m['months']} mo)")
        else:
            print(f"    Tier: ${m['from_cap']} -> ${m['to_cap']:<6} | Reached: ${m['capital_reached']:<9} | Trades: {m['trades']:<5} | Days: {m['days']:<6} ({m['months']} mo) | Margin: ${m['margin_used']}")

