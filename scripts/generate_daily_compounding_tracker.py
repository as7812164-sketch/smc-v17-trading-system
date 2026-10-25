import sqlite3
import json
import datetime
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("DECA COMPOUNDING DAILY TRACKER & AUDIT")
print("Baseline: $500.00 USDT (Day 1: 10 Sections @ $50.00 each)")
print("=" * 80)

import urllib.request
import ssl

ctx = ssl._create_unverified_context()
url = "https://nexuspro-terminal.onrender.com/api/trade/history?limit=100"
req = urllib.request.Request(url, headers={"User-Agent": "Verifier"})
with urllib.request.urlopen(req, context=ctx) as r:
    hist = json.loads(r.read().decode("utf-8"))

trades = hist.get("trades", [])
print(f"Total Closed Trades on Terminal: {len(trades)}")

# Group trades by date (IST / UTC)
daily_stats = {}

for row in trades:
    t = dict(row)
    close_val = t["close_time"]
    if close_val > 1e11:
        close_val /= 1000.0
    dt_utc = datetime.datetime.fromtimestamp(close_val, datetime.timezone.utc)
    # Convert to IST (UTC + 5:30)
    dt_ist = dt_utc + datetime.timedelta(hours=5, minutes=30)
    day_str = dt_ist.strftime("%d %b %Y")

    if day_str not in daily_stats:
        daily_stats[day_str] = {
            "date": day_str,
            "raw_date": dt_ist.strftime("%Y-%m-%d"),
            "sec_macro_pnl": 0.0, # Sections 1-5 (4H Macro)
            "sec_intra_pnl": 0.0, # Sections 6-10 (1H Intraday)
            "total_day_pnl": 0.0,
            "trades_count": 0,
            "wins": 0,
            "saves": 0,
            "losses": 0,
            "trades_list": []
        }

    pnl = float(t["realized_pnl"])
    sec_id = int(t["section_id"])
    daily_stats[day_str]["total_day_pnl"] += pnl
    daily_stats[day_str]["trades_count"] += 1
    
    if sec_id <= 5:
        daily_stats[day_str]["sec_macro_pnl"] += pnl
    else:
        daily_stats[day_str]["sec_intra_pnl"] += pnl

    if pnl > 0.5:
        daily_stats[day_str]["wins"] += 1
    elif pnl >= 0.0:
        daily_stats[day_str]["saves"] += 1
    else:
        daily_stats[day_str]["losses"] += 1

    daily_stats[day_str]["trades_list"].append(t)

# Sort days chronologically
sorted_days = sorted(daily_stats.values(), key=lambda x: x["raw_date"])

running_portfolio = 500.0
running_macro_portfolio = 250.0 # Sections 1-5 ($50 x 5 = $250)
running_intra_portfolio = 250.0 # Sections 6-10 ($50 x 5 = $250)

print("\n--- Daily Progression Table ---")
for d in sorted_days:
    day_pnl = d["total_day_pnl"]
    macro_pnl = d["sec_macro_pnl"]
    intra_pnl = d["sec_intra_pnl"]
    
    start_port = running_portfolio
    running_portfolio += day_pnl
    running_macro_portfolio += macro_pnl
    running_intra_portfolio += intra_pnl
    
    day_roi = (day_pnl / start_port) * 100.0
    cum_roi = ((running_portfolio - 500.0) / 500.0) * 100.0
    
    d["day_start"] = round(start_port, 2)
    d["day_end"] = round(running_portfolio, 2)
    d["day_pnl"] = round(day_pnl, 2)
    d["day_roi"] = round(day_roi, 2)
    d["cum_roi"] = round(cum_roi, 2)
    d["macro_end"] = round(running_macro_portfolio, 2)
    d["intra_end"] = round(running_intra_portfolio, 2)
    
    print(f"Date: {d['date']} | Start: ${d['day_start']:.2f} | Day PnL: ${d['day_pnl']:+.2f} ({d['day_roi']:+.2f}%) | End: ${d['day_end']:.2f} (Cum ROI: {d['cum_roi']:+.2f}%) | Macro: ${d['macro_end']:.2f} | Intra: ${d['intra_end']:.2f} | Trades: {d['trades_count']} (W:{d['wins']} S:{d['saves']} L:{d['losses']})")

# Also check open positions to add current unrealized equity for TODAY
pos_url = "https://nexuspro-terminal.onrender.com/api/trade/positions"
req_pos = urllib.request.Request(pos_url, headers={"User-Agent": "Verifier"})
with urllib.request.urlopen(req_pos, context=ctx) as r:
    pos_data = json.loads(r.read().decode("utf-8"))

open_pos = pos_data.get("positions", [])
u_pnl = sum(float(p.get("unrealized_pnl", 0.0)) for p in open_pos)

print(f"\nCurrent Open Positions Unrealized PnL: ${u_pnl:+.2f}")
print(f"Current Live Total Equity (with open trades): ${running_portfolio + u_pnl:.2f} USDT")
