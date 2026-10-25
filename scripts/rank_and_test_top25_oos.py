"""
DISCOVERY & 1-YEAR OOS TEST: TOP 25 ELITE CHAMPIONS vs TOP 22 BASELINE
======================================================================
Screens all 36 available crypto futures assets on 1-Year Out-of-Sample data:
- Identifies Top 25 coins that most strongly respect Hermes 3.5 rules
- Compares 25-Coin Universe vs Original 22-Coin Universe side-by-side
- Evaluates 100% Pure Compounding ($50 start, 5x leverage, 0 amount split)
- Strict Isolation: Does NOT touch live production engine or database!
"""

import os
import sys
import json
from datetime import datetime

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from run_timeframe_experiment_hermes35 import (
    harvest_hermes35_setups, evaluate_setup_outcome,
    calculate_ema
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

h_dir = "historical_data"
h_files = [f for f in os.listdir(h_dir) if f.endswith("_4h.json")]

print("=" * 85)
print("🔍 SCREENING ALL 36 COINS FOR HERMES 3.5 INSTITUTIONAL COMPLIANCE")
print(f"Horizon: 1-Year Continuous Out-of-Sample (Sep 2025 - Sep 2026 | 2,190 4H bars/coin)")
print("=" * 85)

raw_4h = {}
raw_1h = {}
for f in h_files:
    sym = f.replace("_4h.json", "")
    p4 = os.path.join(h_dir, f)
    p1 = os.path.join(h_dir, f"{sym}_1h.json")
    raw_4h[sym] = json.load(open(p4, "r", encoding="utf-8"))
    if os.path.exists(p1):
        raw_1h[sym] = json.load(open(p1, "r", encoding="utf-8"))

btc_4h = raw_4h.get("BTCUSDT", [])
btc_map_4h = {c["time"]: c for c in btc_4h}
btc_1h_c = raw_1h.get("BTCUSDT", btc_4h)
btc_map_1h = {c["time"]: c for c in btc_1h_c}

btc_closes = [c["close"] for c in btc_4h]
btc_ema50 = calculate_ema(btc_closes, 50)
btc_4h_ema50_map = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_ema50[i]) for i in range(len(btc_4h))}

# Step 1: Evaluate individual coin behavior under Hermes 3.5
coin_diagnostics = {}
all_harvested_by_coin = {}

for sym, c_list in raw_4h.items():
    setups = harvest_hermes35_setups(
        c_list, sym, "4H", 240,
        btc_4h_ema50_map, btc_map_4h,
        disp_threshold=0.050, tp_pct=0.028, soft_sl_pct=0.028, hard_sl_pct=0.038
    )
    all_harvested_by_coin[sym] = setups
    
    wins = 0
    losses = 0
    gross_win_pnl = 0.0
    gross_loss_pnl = 0.0
    
    for s in setups:
        out = evaluate_setup_outcome(s, c_list, btc_map_1h)
        if out["res"] == "WIN":
            wins += 1
            gross_win_pnl += out["pnl_pct"]
        else:
            losses += 1
            gross_loss_pnl += abs(out["pnl_pct"])
            
    tot = wins + losses
    wr = (wins / tot * 100.0) if tot > 0 else 0.0
    pf = (gross_win_pnl / gross_loss_pnl) if gross_loss_pnl > 0 else 99.0
    
    coin_diagnostics[sym] = {
        "trades": tot,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "profit_factor": round(pf, 2)
    }

# Rank coins: Require at least 8 trades for statistical significance, sorted by win rate and profit factor
eligible_coins = [k for k, v in coin_diagnostics.items() if v["trades"] >= 8]
sorted_coins = sorted(eligible_coins, key=lambda x: (coin_diagnostics[x]["win_rate"], coin_diagnostics[x]["profit_factor"], coin_diagnostics[x]["trades"]), reverse=True)

print(f"\n📊 Evaluated {len(coin_diagnostics)} coins. Displaying Top-Ranked Assets:")
print(f"{'RANK':<5} {'COIN':<12} {'SETUPS':<8} {'WINS':<6} {'LOSSES':<8} {'WIN RATE':<10} {'PROFIT FACTOR':<14}")
print("-" * 75)
for idx, sym in enumerate(sorted_coins[:30]):
    d = coin_diagnostics[sym]
    print(f"#{idx+1:<4} {sym:<12} {d['trades']:<8} {d['wins']:<6} {d['losses']:<8} {d['win_rate']:>5.1f}%    {d['profit_factor']:>6.2f}")

# Select Top 25 Elite Champions
TOP_25_ELITE = sorted_coins[:25]

# Original 22 Baseline Coins
ORIGINAL_22 = [
    "AAVEUSDT", "ALGOUSDT", "APTUSDT", "AVAXUSDT", "BTCUSDT",
    "DOGEUSDT", "FETUSDT", "FILUSDT", "GALAUSDT", "ICPUSDT",
    "LDOUSDT", "MKRUSDT", "NEARUSDT", "OPUSDT", "PYTHUSDT",
    "RENDERUSDT", "RUNEUSDT", "SANDUSDT", "SHIBUSDT", "SUIUSDT",
    "THETAUSDT", "UNIUSDT"
]

print("\n" + "=" * 85)
print("🏆 SELECTED TOP 25 ELITE CHAMPIONS FOR HERMES 3.5:")
print(", ".join(TOP_25_ELITE))
print("=" * 85)

# Step 2: Compounding Simulation Engine (100% Pure Compounding)
def simulate_portfolio(coin_list, max_slots=5):
    combined_setups = []
    for sym in coin_list:
        combined_setups.extend(all_harvested_by_coin.get(sym, []))
    combined_setups.sort(key=lambda x: x["time"])
    
    slots_busy_until = [0] * max_slots
    executed = []
    bal = 50.0
    max_bal = 50.0
    max_dd = 0.0
    m1k_trade = None
    m2k_trade = None
    
    curr_win_streak = 0
    max_win_streak = 0
    curr_loss_streak = 0
    max_loss_streak = 0
    
    tp_hits = 0
    armor_be_hits = 0
    sl_hits = 0
    
    for s in combined_setups:
        s_time = s["time"]
        c_list = raw_4h.get(s["sym"], [])
        if not c_list: continue
        
        free_slot = -1
        for idx in range(max_slots):
            if s_time >= slots_busy_until[idx]:
                free_slot = idx
                break
        if free_slot == -1:
            continue
            
        out = evaluate_setup_outcome(s, c_list, btc_map_1h)
        slots_busy_until[free_slot] = out["exit_time"]
        
        # 100% Pure Compounding
        margin = bal
        pos_size = margin * 5.0
        pnl = (pos_size * out["pnl_pct"]) - (pos_size * 0.0016)
        
        res = out["res"]
        if res == "WIN":
            curr_win_streak += 1
            curr_loss_streak = 0
            if curr_win_streak > max_win_streak: max_win_streak = curr_win_streak
            if out["pnl_pct"] >= 0.027:
                tp_hits += 1
            else:
                armor_be_hits += 1
            bal += pnl
        else:
            curr_loss_streak += 1
            curr_win_streak = 0
            if curr_loss_streak > max_loss_streak: max_loss_streak = curr_loss_streak
            sl_hits += 1
            bal += pnl
            if bal < 5.0: bal = 5.0
            
        if bal > max_bal: max_bal = bal
        dd = ((max_bal - bal) / max_bal * 100.0) if max_bal > 0 else 0.0
        if dd > max_dd: max_dd = dd
        
        if not m1k_trade and bal >= 1000.0:
            m1k_trade = len(executed) + 1
        if not m2k_trade and bal >= 2000.0:
            m2k_trade = len(executed) + 1
            
        executed.append({
            "sym": out["sym"],
            "res": res,
            "pnl": round(pnl, 2),
            "bal": round(bal, 2),
            "dur_h": round(out["dur_h"], 1)
        })
        
    tot = len(executed)
    wins = sum(1 for e in executed if e["res"] == "WIN")
    losses = tot - wins
    wr = (wins / tot * 100.0) if tot > 0 else 0.0
    
    gross_win = sum(e["pnl"] for e in executed if e["pnl"] > 0)
    gross_loss = abs(sum(e["pnl"] for e in executed if e["pnl"] < 0))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
    avg_dur = sum(e["dur_h"] for e in executed) / tot if tot > 0 else 0.0
    
    return {
        "universe_coins": len(coin_list),
        "total_setups": len(combined_setups),
        "executed_trades": tot,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "profit_factor": round(pf, 2),
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "tp_hits": tp_hits,
        "armor_be_hits": armor_be_hits,
        "sl_hits": sl_hits,
        "max_drawdown_pct": round(max_dd, 2),
        "avg_duration_h": round(avg_dur, 1),
        "m1k_trade": m1k_trade,
        "m2k_trade": m2k_trade,
        "final_equity": round(bal, 2)
    }

print("\n⚙️ Simulating 1-Year OOS on Original 22 Coins Baseline...")
res_22 = simulate_portfolio(ORIGINAL_22, max_slots=5)

print("⚙️ Simulating 1-Year OOS on Newly Optimized Top 25 Elite Champions...")
res_25 = simulate_portfolio(TOP_25_ELITE, max_slots=5)

results = {
    "test_meta": {
        "title": "TOP 25 ELITE CHAMPIONS vs ORIGINAL 22 BASELINE (1-YEAR OOS)",
        "horizon": "September 2025 - September 2026",
        "starting_capital": 50.0,
        "leverage": "5x Isolated",
        "compounding": "100% Pure Compounding (Zero Split)",
        "top_25_coins": TOP_25_ELITE,
        "original_22_coins": ORIGINAL_22,
        "timestamp": datetime.utcnow().isoformat()
    },
    "original_22_baseline": res_22,
    "top_25_elite_champions": res_25
}

with open("top25_vs_top22_oos_duel_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 85)
print("📊 1-YEAR OUT-OF-SAMPLE HEAD-TO-HEAD COMPARISON: TOP 22 vs TOP 25")
print("=" * 85)
print(f"{'METRIC':<30} {'ORIGINAL 22 COINS':<26} {'TOP 25 ELITE CHAMPIONS':<28}")
print("-" * 85)
print(f"{'Universe Size':<30} {res_22['universe_coins']:<26} {res_25['universe_coins']:<28}")
print(f"{'Total Harvested Setups':<30} {res_22['total_setups']:<26} {res_25['total_setups']:<28}")
print(f"{'Executed Trades (5 Slots)':<30} {res_22['executed_trades']:<26} {res_25['executed_trades']:<28}")
print(f"{'OOS Win Rate (Accuracy)':<30} {res_22['win_rate']:>5.2f}% ({res_22['wins']}W/{res_22['losses']}L)     {res_25['win_rate']:>5.2f}% ({res_25['wins']}W/{res_25['losses']}L)")
print(f"{'Profit Factor':<30} {res_22['profit_factor']:<26.2f} {res_25['profit_factor']:<28.2f}")
print(f"{'Max Consecutive Win Streak':<30} {res_22['max_win_streak']:<26} {res_25['max_win_streak']:<28}")
print(f"{'Max Consecutive Loss Streak':<30} {res_22['max_loss_streak']:<26} {res_25['max_loss_streak']:<28}")
print(f"{'Direct TP Hits (+2.8%)':<30} {res_22['tp_hits']:<26} {res_25['tp_hits']:<28}")
print(f"{'Profit Armor / BE Locks':<30} {res_22['armor_be_hits']:<26} {res_25['armor_be_hits']:<28}")
print(f"{'Hard SL Hits':<30} {res_22['sl_hits']:<26} {res_25['sl_hits']:<28}")
print(f"{'Max Portfolio Drawdown':<30} {res_22['max_drawdown_pct']:>5.2f}%                    {res_25['max_drawdown_pct']:>5.2f}%")
print(f"{'$1,000 Milestone Speed':<30} Trade #{res_22['m1k_trade']:<20} Trade #{res_25['m1k_trade']:<20}")
print(f"{'$2,000 Milestone Speed':<30} Trade #{res_22['m2k_trade']:<20} Trade #{res_25['m2k_trade']:<20}")
print(f"{'Avg Duration (Hours)':<30} {res_22['avg_duration_h']:<24.1f}h {res_25['avg_duration_h']:<26.1f}h")
print("=" * 85)
print("✅ Results saved to top25_vs_top22_oos_duel_results.json")
