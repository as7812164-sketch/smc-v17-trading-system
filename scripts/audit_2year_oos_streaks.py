"""
AUDIT 2-YEAR OUT-OF-SAMPLE STREAKS, ACCURACY & DRAWDOWN
=======================================================
Detailed forensic breakdown for Hermes 3.5 Single Tier:
- Max Consecutive TP / Win Streak
- Max Consecutive SL / Loss Streak
- Total TP vs Armor/BE vs Hard SL hits
- Max Drawdown % (Depth & Duration)
- In-Sample (Year 1) vs Out-of-Sample (Year 2) vs Full 2-Year
- Monthly Breakdown across Out-of-Sample Year 2
"""

import os
import sys
import json
from datetime import datetime

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from run_timeframe_experiment_hermes35 import (
    harvest_hermes35_setups, evaluate_setup_outcome,
    calculate_ema, resample_candles
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

dir_2yr = "historical_data_2year"
coins_2yr = [
    "AAVEUSDT", "ALGOUSDT", "APTUSDT", "AVAXUSDT", "BTCUSDT",
    "DOGEUSDT", "FETUSDT", "FILUSDT", "GALAUSDT", "ICPUSDT",
    "LDOUSDT", "MKRUSDT", "NEARUSDT", "OPUSDT", "PYTHUSDT",
    "RENDERUSDT", "RUNEUSDT", "SANDUSDT", "SHIBUSDT", "SUIUSDT",
    "THETAUSDT", "UNIUSDT"
]

print("📊 Loading 2-year datasets...")
raw_4h = {}
raw_1h = {}
for c in coins_2yr:
    f4 = os.path.join(dir_2yr, f"{c}_4h.json")
    f1 = os.path.join(dir_2yr, f"{c}_1h.json")
    if os.path.exists(f4):
        raw_4h[c] = json.load(open(f4, "r", encoding="utf-8"))
    if os.path.exists(f1):
        raw_1h[c] = json.load(open(f1, "r", encoding="utf-8"))

btc_4h = raw_4h.get("BTCUSDT", [])
btc_1h = raw_1h.get("BTCUSDT", [])
btc_map_4h = {c["time"]: c for c in btc_4h}
btc_map_1h = {c["time"]: c for c in btc_1h}

btc_closes = [c["close"] for c in btc_4h]
btc_ema50 = calculate_ema(btc_closes, 50)
btc_4h_ema50_map = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_ema50[i]) for i in range(len(btc_4h))}

# Harvesting 4H Setups (Primary Macro Production Engine)
print("🔍 Harvesting 4H Hermes 3.5 Setups...")
setups_4h = []
for sym, c_list in raw_4h.items():
    s = harvest_hermes35_setups(
        c_list, sym, "4H", 240,
        btc_4h_ema50_map, btc_map_4h,
        disp_threshold=0.050, tp_pct=0.028, soft_sl_pct=0.028, hard_sl_pct=0.038
    )
    setups_4h.extend(s)

setups_4h.sort(key=lambda x: x["time"])

outcomes_4h = []
for s in setups_4h:
    c_list = raw_4h.get(s["sym"], [])
    if c_list:
        out = evaluate_setup_outcome(s, c_list, btc_map_1h)
        outcomes_4h.append(out)

# Split timestamp: September 2025 (~1758800000000)
split_ts = 1758800000000

def analyze_streaks_and_dd(trades):
    max_win_streak = 0
    max_loss_streak = 0
    curr_win_streak = 0
    curr_loss_streak = 0
    
    tp_hits = 0
    armor_be_hits = 0
    sl_hits = 0
    
    monthly_data = {}
    
    bal = 50.0
    vault = 0.0
    max_eq = 50.0
    max_dd = 0.0
    m1k_trade = None
    m2k_trade = None
    
    for idx, t in enumerate(trades):
        res = t["res"]
        dt = datetime.fromtimestamp(t["entry_time"] / 1000)
        m_key = dt.strftime("%Y-%m")
        if m_key not in monthly_data:
            monthly_data[m_key] = {"wins": 0, "losses": 0, "trades": 0}
        monthly_data[m_key]["trades"] += 1
        
        if res == "WIN":
            curr_win_streak += 1
            curr_loss_streak = 0
            if curr_win_streak > max_win_streak:
                max_win_streak = curr_win_streak
            monthly_data[m_key]["wins"] += 1
            if t["pnl_pct"] >= 0.027:
                tp_hits += 1
            else:
                armor_be_hits += 1
        else:
            curr_loss_streak += 1
            curr_win_streak = 0
            if curr_loss_streak > max_loss_streak:
                max_loss_streak = curr_loss_streak
            monthly_data[m_key]["losses"] += 1
            sl_hits += 1
            
        pos_size = bal * 5.0
        pnl = (pos_size * t["pnl_pct"]) - (pos_size * 0.0016)
        if pnl > 0:
            bal += pnl * 0.85
            vault += pnl * 0.15
        else:
            bal += pnl
            if bal < 10.0: bal = 10.0
            
        tot_eq = bal + vault
        if tot_eq > max_eq:
            max_eq = tot_eq
        dd = (max_eq - tot_eq) / max_eq * 100.0 if max_eq > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
            
        if not m1k_trade and tot_eq >= 1000.0:
            m1k_trade = idx + 1
        if not m2k_trade and tot_eq >= 2000.0:
            m2k_trade = idx + 1
            
    tot = len(trades)
    wins = sum(1 for t in trades if t["res"] == "WIN")
    wr = (wins / tot * 100.0) if tot > 0 else 0.0
    
    return {
        "total": tot,
        "wins": wins,
        "losses": tot - wins,
        "win_rate": round(wr, 2),
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "tp_hits": tp_hits,
        "armor_be_hits": armor_be_hits,
        "sl_hits": sl_hits,
        "max_drawdown_pct": round(max_dd, 2),
        "m1k_trade": m1k_trade,
        "m2k_trade": m2k_trade,
        "final_equity": round(bal + vault, 2),
        "monthly": monthly_data
    }

full_report = analyze_streaks_and_dd(outcomes_4h)
is_report = analyze_streaks_and_dd([t for t in outcomes_4h if t["entry_time"] < split_ts])
oos_report = analyze_streaks_and_dd([t for t in outcomes_4h if t["entry_time"] >= split_ts])

# Also check 3H for user completeness
print("🔄 Resampling 22 coins from 1H to 3H...")
raw_3h = {}
for sym, c_list in raw_1h.items():
    raw_3h[sym] = resample_candles(c_list, 180)

setups_3h = []
for sym, c_list in raw_3h.items():
    s = harvest_hermes35_setups(
        c_list, sym, "3H", 180,
        btc_4h_ema50_map, btc_map_4h,
        disp_threshold=0.050, tp_pct=0.028, soft_sl_pct=0.028, hard_sl_pct=0.038
    )
    setups_3h.extend(s)
setups_3h.sort(key=lambda x: x["time"])

outcomes_3h = []
for s in setups_3h:
    c_list = raw_3h.get(s["sym"], [])
    if c_list:
        out = evaluate_setup_outcome(s, c_list, btc_map_1h)
        outcomes_3h.append(out)

full_report_3h = analyze_streaks_and_dd(outcomes_3h)
oos_report_3h = analyze_streaks_and_dd([t for t in outcomes_3h if t["entry_time"] >= split_ts])

summary_data = {
    "4H": {
        "full": full_report,
        "in_sample": is_report,
        "out_of_sample": oos_report
    },
    "3H": {
        "full": full_report_3h,
        "out_of_sample": oos_report_3h
    }
}

with open("audit_2year_streaks_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary_data, f, indent=2)

print("\n" + "=" * 80)
print("📈 HERMES 3.5: 2-YEAR OUT-OF-SAMPLE (OOS) DEEP AUDIT RESULTS")
print("=" * 80)
print("\n[4H (240m) PRODUCTION MACRO ENGINE]")
print(f"Total OOS Trades: {oos_report['total']}")
print(f"OOS Accuracy (Win Rate): {oos_report['win_rate']}% ({oos_report['wins']} Wins / {oos_report['losses']} Losses)")
print(f"Lagatar TP Hit (Max Win Streak): {oos_report['max_win_streak']} trades in a row! 🔥")
print(f"Lagatar SL Hit (Max Loss Streak): {oos_report['max_loss_streak']} trades in a row! 🛡️")
print(f"Full Target TP Hits: {oos_report['tp_hits']} ({oos_report['tp_hits']/oos_report['total']*100:.1f}%)")
print(f"Profit Armor / BE Locks: {oos_report['armor_be_hits']} ({oos_report['armor_be_hits']/oos_report['total']*100:.1f}%)")
print(f"Hard SL Hits: {oos_report['sl_hits']} ({oos_report['sl_hits']/oos_report['total']*100:.1f}%)")
print(f"Max Portfolio Drawdown: {oos_report['max_drawdown_pct']}%")
print(f"$1,000 Milestone Reached: Trade #{oos_report['m1k_trade']}")
print(f"$2,000 Milestone Reached: Trade #{oos_report['m2k_trade']}")

print("\n[OOS MONTH-BY-MONTH ACCURACY BREAKDOWN (YEAR 2)]")
for m, data in sorted(oos_report["monthly"].items()):
    wr = (data["wins"] / data["trades"] * 100.0) if data["trades"] > 0 else 0
    print(f"  {m}: {data['trades']:2d} Trades | {data['wins']:2d} Wins / {data['losses']:2d} Losses | Accuracy: {wr:5.1f}%")

print("\n" + "-" * 80)
print("[3H (180m) ULTRA-ACCURACY COMPARISON]")
print(f"OOS Total: {oos_report_3h['total']} | Accuracy: {oos_report_3h['win_rate']}% ({oos_report_3h['wins']}W / {oos_report_3h['losses']}L)")
print(f"Lagatar TP Hit (Max Win Streak): {oos_report_3h['max_win_streak']} trades in a row! 🔥")
print(f"Lagatar SL Hit (Max Loss Streak): {oos_report_3h['max_loss_streak']} trades in a row! 🛡️")
print(f"Max Drawdown: {oos_report_3h['max_drawdown_pct']}% | M1K: Trade #{oos_report_3h['m1k_trade']} | M2K: Trade #{oos_report_3h['m2k_trade']}")
print("=" * 80)
