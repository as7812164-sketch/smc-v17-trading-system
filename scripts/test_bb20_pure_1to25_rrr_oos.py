"""
PURE 1:2.5 RRR AUDIT (NO TRAILING SL): BB 2.0 (APRIL 1, 2026 - OCTOBER 14, 2026)
================================================================================
- Scope: 6-Month Pure OOS
- Capital: $500.00 across 10 Deca Sections ($50 each)
- Strategy: BB 2.0 Model 3 (PDH/PDL Sweep + 50% MT Retest + 0.15% Anti-Hunt SL)
- Target: Fixed 1:2.5 RRR (TP = +2.5R, SL = -1.0R)
- Trailing SL: 100% REMOVED (Zero BE lock, zero trailing)
"""

import os
import sys
import json
from datetime import datetime, timezone
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "historical_data")

CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT",
    "DOGEUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT",
    "OPUSDT", "RENDERUSDT", "SUIUSDT", "TIAUSDT", "UNIUSDT",
    "XRPUSDT", "1000PEPEUSDT", "APTUSDT", "ARBUSDT", "FETUSDT"
]

PAIR_MAPPING = {
    "BTCUSDT": 1, "ETHUSDT": 1, "SOLUSDT": 2, "BNBUSDT": 2,
    "AVAXUSDT": 3, "DOGEUSDT": 3, "DOTUSDT": 4, "LINKUSDT": 4,
    "LTCUSDT": 5, "NEARUSDT": 5, "OPUSDT": 6, "RENDERUSDT": 6,
    "SUIUSDT": 7, "TIAUSDT": 7, "UNIUSDT": 8, "XRPUSDT": 8,
    "1000PEPEUSDT": 9, "APTUSDT": 9, "ARBUSDT": 10, "FETUSDT": 10
}

def get_day_key(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")

def evaluate_pure_rrr(candles, fill_idx, side, entry, sl, rrr_multiple, sym, day_str):
    risk_price = abs(entry - sl)
    if risk_price <= 0:
        return None

    # Target based on user RRR multiple (e.g. 2.0, 2.5, 3.0)
    tp_price = entry + (rrr_multiple * risk_price) if side == "LONG" else entry - (rrr_multiple * risk_price)
    fill_time = candles[fill_idx]["time"]

    for i in range(fill_idx, min(fill_idx + 120, len(candles))):
        c = candles[i]
        c_h = c["high"]
        c_l = c["low"]

        if side == "LONG":
            sl_hit = c_l <= sl
            tp_hit = c_h >= tp_price

            if sl_hit and tp_hit:
                # Conservative: assume SL hit first if both in same candle
                return {"symbol": sym, "day": day_str, "side": side, "fill_time": fill_time, "exit_time": c["time"], "pnl_r": -1.0, "outcome": "LOSS"}
            elif tp_hit:
                return {"symbol": sym, "day": day_str, "side": side, "fill_time": fill_time, "exit_time": c["time"], "pnl_r": rrr_multiple, "outcome": "WIN_TP"}
            elif sl_hit:
                return {"symbol": sym, "day": day_str, "side": side, "fill_time": fill_time, "exit_time": c["time"], "pnl_r": -1.0, "outcome": "LOSS"}

        else: # SHORT
            sl_hit = c_h >= sl
            tp_hit = c_l <= tp_price

            if sl_hit and tp_hit:
                return {"symbol": sym, "day": day_str, "side": side, "fill_time": fill_time, "exit_time": c["time"], "pnl_r": -1.0, "outcome": "LOSS"}
            elif tp_hit:
                return {"symbol": sym, "day": day_str, "side": side, "fill_time": fill_time, "exit_time": c["time"], "pnl_r": rrr_multiple, "outcome": "WIN_TP"}
            elif sl_hit:
                return {"symbol": sym, "day": day_str, "side": side, "fill_time": fill_time, "exit_time": c["time"], "pnl_r": -1.0, "outcome": "LOSS"}

    last_c = candles[min(fill_idx + 120, len(candles) - 1)]
    pnl_r = ((last_c["close"] - entry) / risk_price) if side == "LONG" else ((entry - last_c["close"]) / risk_price)
    pnl_r = max(-1.0, min(rrr_multiple, pnl_r))
    return {
        "symbol": sym, "day": day_str, "side": side,
        "fill_time": fill_time, "exit_time": last_c["time"],
        "pnl_r": pnl_r,
        "outcome": "TIMEOUT_WIN" if pnl_r > 0 else "TIMEOUT_LOSS"
    }

def run_bb20_scan(rrr_multiple: float):
    all_trades = []

    for sym in CHAMPIONS:
        fpath = os.path.join(DATA_DIR, f"{sym}_1h.json")
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)
        if len(candles) < 1000:
            continue

        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            curr_day = sorted_days[d_i]
            prev_day = sorted_days[d_i - 1]

            if curr_day < "2026-04-01":
                continue

            prev_day_candles = [c for _, c in day_buckets[prev_day]]
            curr_day_entries = day_buckets[curr_day]

            if len(prev_day_candles) < 12 or len(curr_day_entries) < 12:
                continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)

            long_taken = False
            short_taken = False

            for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
                if g_idx + 2 >= len(candles):
                    continue
                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # LONG at PDL
                if not long_taken:
                    dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                    basic_pdl = (dist_to_pdl <= 0.015 or c_l <= pdl)
                    basic_disp = ((c_c < c_o or (c_h - c_l) > 0) and 
                                  ((next_c["high"] - c_l) / c_l >= 0.012 or (next_c2["high"] - c_l) / c_l >= 0.018) and 
                                  next_c2["low"] > c_h)

                    if basic_pdl and basic_disp:
                        mt = (c_h + c_l) / 2.0
                        sl = c_l * 0.9985
                        risk = mt - sl
                        if risk > 0:
                            for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                if candles[w_idx]["low"] <= sl:
                                    break
                                if candles[w_idx]["low"] <= mt:
                                    long_taken = True
                                    res = evaluate_pure_rrr(candles, w_idx, "LONG", mt, sl, rrr_multiple, sym, curr_day)
                                    if res: all_trades.append(res)
                                    break

                # SHORT at PDH
                if not short_taken:
                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    basic_pdh = (dist_to_pdh <= 0.015 or c_h >= pdh)
                    basic_disp = ((c_c > c_o or (c_h - c_l) > 0) and 
                                  ((c_h - next_c["low"]) / c_h >= 0.012 or (c_h - next_c2["low"]) / c_h >= 0.018) and 
                                  next_c2["high"] < c_l)

                    if basic_pdh and basic_disp:
                        mt = (c_h + c_l) / 2.0
                        sl = c_h * 1.0015
                        risk = sl - mt
                        if risk > 0:
                            for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                if candles[w_idx]["high"] >= sl:
                                    break
                                if candles[w_idx]["high"] >= mt:
                                    short_taken = True
                                    res = evaluate_pure_rrr(candles, w_idx, "SHORT", mt, sl, rrr_multiple, sym, curr_day)
                                    if res: all_trades.append(res)
                                    break

                if long_taken and short_taken:
                    break

    all_trades.sort(key=lambda t: t["fill_time"])
    return all_trades

def simulate_portfolio(trades, risk_pct: float):
    sections = {}
    for i in range(1, 11):
        coins = [c for c, sid in PAIR_MAPPING.items() if sid == i]
        sections[i] = {"id": i, "assigned_coins": coins, "balance": 50.0, "peak": 50.0, "busy_until": 0, "trades": 0, "wins": 0, "losses": 0, "pnl": 0.0}
    monthly_pnl = defaultdict(float)
    executed = []

    for t in trades:
        sec_id = PAIR_MAPPING.get(t["symbol"], 1)
        sec = sections[sec_id]
        if sec["busy_until"] > t["fill_time"]:
            continue
        sec["busy_until"] = t["exit_time"]
        sec["trades"] += 1

        r_pnl = t["pnl_r"]
        risk_usd = sec["balance"] * risk_pct
        dollar_pnl = risk_usd * r_pnl

        sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))
        sec["pnl"] = round(sec["pnl"] + dollar_pnl, 2)
        if sec["balance"] > sec["peak"]:
            sec["peak"] = sec["balance"]

        m_key = t["day"][:7]
        monthly_pnl[m_key] += dollar_pnl

        if t["pnl_r"] > 0:
            sec["wins"] += 1
        else:
            sec["losses"] += 1

        executed.append({
            "time": t["exit_time"],
            "dollar_pnl": dollar_pnl,
            "total_eq": sum(s["balance"] for s in sections.values())
        })

    tot_eq = sum(s["balance"] for s in sections.values())
    tot_wins = sum(s["wins"] for s in sections.values())
    tot_losses = sum(s["losses"] for s in sections.values())
    tot_exec = len(executed)

    win_rate = (tot_wins / tot_exec * 100) if tot_exec else 0.0
    net_profit = tot_eq - 500.0
    roi_pct = (net_profit / 500.0) * 100.0

    peak = 500.0
    max_dd = 0.0
    for rec in executed:
        eq = rec["total_eq"]
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

    return {
        "trades": tot_exec,
        "wins": tot_wins,
        "losses": tot_losses,
        "win_rate": win_rate,
        "final_balance": tot_eq,
        "net_profit": net_profit,
        "roi_pct": roi_pct,
        "max_dd": max_dd,
        "monthly_pnl": monthly_pnl,
        "sections": sections
    }

def main():
    rrr_list = [2.0, 2.5, 3.0]

    print("=" * 100)
    print("🎯 RRR SENSITIVITY AUDIT: BB 2.0 (NO TRAILING SL) ON 6-MONTH OOS DATA")
    print("• Period: April 1, 2026 to October 14, 2026")
    print("• Starting Capital: $500.00 across 10 Deca Sections ($50 each)")
    print("• Testing RRR multiples: 1:2.0 vs 1:2.5 vs 1:3.0 (Zero Trailing SL)")
    print("=" * 100)

    results = []

    for rrr in rrr_list:
        print(f"\n👉 Simulating Fixed 1:{rrr:.1f} RRR Target...")
        trades = run_bb20_scan(rrr_multiple=rrr)
        res_cons = simulate_portfolio(trades, risk_pct=0.02)
        res_aggr = simulate_portfolio(trades, risk_pct=0.05)
        results.append({
            "rrr": f"1:{rrr:.1f}",
            "trades": res_cons["trades"],
            "wins": res_cons["wins"],
            "losses": res_cons["losses"],
            "win_rate": res_cons["win_rate"],
            "cons_final": res_cons["final_balance"],
            "cons_roi": res_cons["roi_pct"],
            "cons_dd": res_cons["max_dd"],
            "aggr_final": res_aggr["final_balance"],
            "aggr_roi": res_aggr["roi_pct"],
            "aggr_dd": res_aggr["max_dd"],
            "sections": res_cons["sections"],
            "monthly_pnl": res_aggr["monthly_pnl"]
        })

    print("\n" + "=" * 100)
    print("🏆 SIDE-BY-SIDE RRR COMPARISON TABLE (1:2.0 vs 1:2.5 vs 1:3.0)")
    print("=" * 100)
    print(f"{'RRR Target':<12} | {'Trades':<8} | {'Win Rate':<10} | {'Cons (2%) Final':<16} | {'Aggr (5%) Final':<17} | {'Max DD'}")
    print("-" * 100)

    for r in results:
        print(f"{r['rrr']:<12} | {r['trades']:<8} | {r['win_rate']:<6.1f}%   | ${r['cons_final']:<14.2f}  | ${r['aggr_final']:<15.2f} | {r['cons_dd']:.2f}%")

    print("=" * 100)

    # Detailed Section Breakdown for 1:2.5 RRR
    r_25 = results[1]
    print(f"\n🧩 SECTION-BY-SECTION BALANCES FOR 1:2.5 RRR (CONSERVATIVE 2% MODE):")
    print("-" * 100)
    for s_id in sorted(r_25["sections"].keys()):
        sec = r_25["sections"][s_id]
        print(f"  Sec #{s_id:<2} ({', '.join(sec['assigned_coins'][:2]):<16}) | Final: ${sec['balance']:<8.2f} | PnL: ${sec['pnl']:+8.2f} | Trades: {sec['trades']:<3} (Wins: {sec['wins']}, Losses: {sec['losses']})")

    print("\n📅 MONTH-BY-MONTH PNL FOR 1:2.5 RRR (5% AGGRESSIVE COMPOUNDING):")
    print("-" * 100)
    for m in sorted(r_25["monthly_pnl"].keys()):
        print(f"  {m}: ${r_25['monthly_pnl'][m]:+11.2f} USDT")

if __name__ == "__main__":
    main()
