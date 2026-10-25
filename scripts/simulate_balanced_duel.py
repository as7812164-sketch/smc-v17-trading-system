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

def get_chronological_stream(max_loops=15):
    start_time = raw_setups[0]["entry_time"]
    end_time = raw_setups[-1]["exit_time"]
    cycle_duration = end_time - start_time + (24 * 3600 * 1000)

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
# MODEL 1A: 10-SECTION 100% COMPOUNDING (BALANCED ROUND-ROBIN)
# All 10 sections compound independently; setups distributed to longest-idle section.
# =============================================================================
def run_model_1_balanced():
    sections = [{"id": i+1, "balance": 50.0, "busy_until": 0, "trades": 0, "wins": 0} for i in range(10)]
    
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
        
        # Find idle sections and pick the one with lowest trade count / longest idle
        idle_sections = [sec for sec in sections if sec["busy_until"] <= cur_time and sec["balance"] >= 2.0]
        if not idle_sections:
            continue
            
        # Pick section with fewest trades so all 10 sections grow equally
        idle_sections.sort(key=lambda x: (x["trades"], x["busy_until"]))
        idle_section = idle_sections[0]
            
        margin = idle_section["balance"]
        pnl = margin * (s["roe_pct"] / 100.0)
        
        idle_section["balance"] += pnl
        if idle_section["balance"] < 1.0:
            idle_section["balance"] = 1.0
            
        idle_section["busy_until"] = s["exit_time"]
        idle_section["trades"] += 1
        total_trades += 1
        
        if s["roe_pct"] > 0:
            wins += 1
            idle_section["wins"] += 1
        else:
            losses += 1
            
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
            
        total_portfolio = sum(sec["balance"] for sec in sections)
        if total_portfolio > peak_portfolio:
            peak_portfolio = total_portfolio
        dd = (peak_portfolio - total_portfolio) / peak_portfolio * 100.0
        if dd > max_dd:
            max_dd = dd
            
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
        "model_name": "Model 1 (Balanced): 10-Section 100% Compounding",
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
# MODEL 1B: 10-SECTION 100% COMPOUNDING (4H SECTIONS 1-5 + 1H SECTIONS 6-10)
# =============================================================================
def run_model_1_split():
    sections = [{"id": i+1, "balance": 50.0, "busy_until": 0, "trades": 0, "wins": 0} for i in range(10)]
    
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
        
        # If 4H setup -> Sections 1-5. If 1H setup -> Sections 6-10
        if s["tf"] == "4h":
            eligible = sections[:5]
        else:
            eligible = sections[5:]
            
        idle_sections = [sec for sec in eligible if sec["busy_until"] <= cur_time and sec["balance"] >= 2.0]
        if not idle_sections:
            continue
            
        idle_sections.sort(key=lambda x: (x["trades"], x["busy_until"]))
        idle_section = idle_sections[0]
            
        margin = idle_section["balance"]
        pnl = margin * (s["roe_pct"] / 100.0)
        
        idle_section["balance"] += pnl
        if idle_section["balance"] < 1.0:
            idle_section["balance"] = 1.0
            
        idle_section["busy_until"] = s["exit_time"]
        idle_section["trades"] += 1
        total_trades += 1
        
        if s["roe_pct"] > 0:
            wins += 1
            idle_section["wins"] += 1
        else:
            losses += 1
            
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
            
        total_portfolio = sum(sec["balance"] for sec in sections)
        if total_portfolio > peak_portfolio:
            peak_portfolio = total_portfolio
        dd = (peak_portfolio - total_portfolio) / peak_portfolio * 100.0
        if dd > max_dd:
            max_dd = dd
            
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
        "model_name": "Model 1 (4H/1H Split): 10-Section 100% Compounding",
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
# MODEL 2: STEP-DOUBLE 10% PER SIGNAL (5 CONCURRENT SIGNALS)
# =============================================================================
def run_model_2(max_concurrent_signals=5):
    capital = 500.0
    tier_base = 500.0
    tier_target = 1000.0
    tier_margin = tier_base * 0.10
    
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
    
    active_positions = []
    milestones_log = []
    
    stream = get_chronological_stream()
    
    for s in stream:
        if start_time is None:
            start_time = s["entry_time"]
            
        cur_time = s["entry_time"]
        
        still_active = []
        for pos in sorted(active_positions, key=lambda x: x["exit_time"]):
            if pos["exit_time"] <= cur_time:
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
                    
                if capital > peak_portfolio:
                    peak_portfolio = capital
                dd = (peak_portfolio - capital) / peak_portfolio * 100.0
                if dd > max_dd:
                    max_dd = dd
                    
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
            
        if len(active_positions) >= max_concurrent_signals:
            continue
            
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

m1_bal = run_model_1_balanced()
m1_split = run_model_1_split()
m2_5 = run_model_2(max_concurrent_signals=5)
m2_10 = run_model_2(max_concurrent_signals=10)

all_results = {
    "m1_balanced": m1_bal,
    "m1_split": m1_split,
    "m2_5": m2_5,
    "m2_10": m2_10
}

with open("scripts/full_duel_breakdown.json", "w") as f:
    json.dump(all_results, f, indent=2)

print("\n" + "="*115)
print(f"{'MODEL NAME':<45} | {'TRADES':<7} | {'WIN RATE':<9} | {'MAX DD %':<9} | {'DAYS':<7} | {'MONTHS':<8} | {'YEARS'}")
print("="*115)
for k, v in all_results.items():
    print(f"{v['model_name']:<45} | {v['total_trades']:<7} | {str(v['win_rate_pct'])+'%':<9} | {str(v['max_drawdown_pct'])+'%':<9} | {str(v['days_to_1cr']):<7} | {str(v['months_to_1cr'])+' mo':<8} | {str(v['years_to_1cr'])+' Yrs'}")
print("="*115)

for k, v in all_results.items():
    print(f"\n>>> FORENSICS FOR: {v['model_name']}")
    print(f"  TP Hits (+15% ROE): {v['tp_hits']} ({v['tp_hits']/v['total_trades']*100:.1f}%)")
    print(f"  Trailing SL Hits: {v['trailing_sl_hits']} ({v['trailing_sl_hits']/v['total_trades']*100:.1f}%)")
    print(f"    Highest Trailing Locked ROI: +{v['highest_trailing_roi']:.1f}% ROI | Avg Trailing ROI: +{v['avg_trailing_roi']:.1f}% ROI")
    print(f"  Soft SL Hits (-7.5% ROE): {v['soft_sl_hits']} ({v['soft_sl_hits']/v['total_trades']*100:.1f}%)")
    print(f"  Hard SL Hits (-15.0% ROE): {v['hard_sl_hits']} ({v['hard_sl_hits']/v['total_trades']*100:.1f}%)")
