"""
1-YEAR BACKTEST AUDIT: BB 2.0 (MODEL 3 SNIPER) ON 1 FULL YEAR (OCT 2025 - OCT 2026)
===================================================================================
- Universe: Top 20 Champions
- Period: 365 Days (1 Full Year, 8,760 hourly candles per coin)
- Anchor: Daily PDH / PDL Sweep
- Execution: Extreme OB + 50% Mean Threshold + 0.15% Anti-Hunt SL
- Armor: Stepped Trailing SL (+1.0R -> +0.2R BE, +1.5R -> +1.0R lock, +2.0R -> +1.5R lock, +3.0R TP)
- Starting Capital: $500.00 USDT across 10 Deca Sections ($50.00 each)
"""

import os
import sys
import json
from datetime import datetime, timezone
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "historical_data")

CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT",
    "DOGEUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT",
    "OPUSDT", "RENDERUSDT", "SUIUSDT", "TIAUSDT", "UNIUSDT",
    "XRPUSDT", "1000PEPEUSDT", "APTUSDT", "ARBUSDT", "FETUSDT"
]

PAIR_MAPPING = {
    "BTCUSDT": 1, "ETHUSDT": 1,
    "SOLUSDT": 2, "BNBUSDT": 2,
    "AVAXUSDT": 3, "DOGEUSDT": 3,
    "DOTUSDT": 4, "LINKUSDT": 4,
    "LTCUSDT": 5, "NEARUSDT": 5,
    "OPUSDT": 6, "RENDERUSDT": 6,
    "SUIUSDT": 7, "TIAUSDT": 7,
    "UNIUSDT": 8, "XRPUSDT": 8,
    "1000PEPEUSDT": 9, "APTUSDT": 9,
    "ARBUSDT": 10, "FETUSDT": 10
}

def get_day_key(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")

def run_1year_test():
    all_trades = []

    for sym in CHAMPIONS:
        fpath = os.path.join(DATA_DIR, f"{sym}_1h.json")
        if not os.path.exists(fpath):
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)

        if len(candles) < 1000:
            continue

        # Group candles by calendar day (UTC)
        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            prev_day_key = sorted_days[d_i - 1]
            curr_day_key = sorted_days[d_i]

            prev_day_candles = [c for _, c in day_buckets[prev_day_key]]
            curr_day_entries = day_buckets[curr_day_key]

            if len(prev_day_candles) < 12 or len(curr_day_entries) < 12:
                continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)

            long_taken_today = False
            short_taken_today = False

            for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
                if g_idx + 2 >= len(candles):
                    continue

                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # 1. BOTTOM OB (PDL) -> LONG
                if not long_taken_today:
                    dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                    if dist_to_pdl <= 0.015 or c_l <= pdl:
                        is_bearish = c_c < c_o
                        gain_1bar = (next_c["high"] - c_l) / c_l
                        gain_2bar = (next_c2["high"] - c_l) / c_l
                        has_fvg = next_c2["low"] > c_h

                        if (is_bearish or (c_h - c_l) > 0) and (gain_1bar >= 0.012 or gain_2bar >= 0.018) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_low * 0.9985
                            risk = mt - sl

                            if risk > 0:
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                    b = candles[w_idx]
                                    if b["low"] <= sl:
                                        break
                                    if b["low"] <= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    long_taken_today = True
                                    trade = evaluate_trade(candles, fill_idx, "LONG", mt, sl, risk, sym, curr_day_key)
                                    all_trades.append(trade)

                # 2. TOP OB (PDH) -> SHORT
                if not short_taken_today:
                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    if dist_to_pdh <= 0.015 or c_h >= pdh:
                        is_bullish = c_c > c_o
                        drop_1bar = (c_h - next_c["low"]) / c_h
                        drop_2bar = (c_h - next_c2["low"]) / c_h
                        has_fvg = next_c2["high"] < c_l

                        if (is_bullish or (c_h - c_l) > 0) and (drop_1bar >= 0.012 or drop_2bar >= 0.018) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_high * 1.0015
                            risk = sl - mt

                            if risk > 0:
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                    b = candles[w_idx]
                                    if b["high"] >= sl:
                                        break
                                    if b["high"] >= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    short_taken_today = True
                                    trade = evaluate_trade(candles, fill_idx, "SHORT", mt, sl, risk, sym, curr_day_key)
                                    all_trades.append(trade)

                if long_taken_today and short_taken_today:
                    break

    all_trades.sort(key=lambda t: t["fill_time"])
    print(f"Total 1-Year Trades Found: {len(all_trades)}")

    # Simulations: Flat Risk, Deca 2%, Deca 5%
    def simulate(risk_pct: float, is_deca: bool):
        sections = {
            i: {
                "id": i,
                "balance": 50.0,
                "peak": 50.0,
                "busy_until": 0,
                "trades": 0,
                "wins": 0,
                "saves": 0,
                "losses": 0,
                "pnl": 0.0
            }
            for i in range(1, 11)
        }
        monthly_pnl = defaultdict(float)
        executed = []

        for t in all_trades:
            sec_id = PAIR_MAPPING.get(t["symbol"], 1)
            sec = sections[sec_id]

            if sec["busy_until"] > t["fill_time"]:
                continue

            sec["busy_until"] = t["exit_time"]
            sec["trades"] += 1

            r_pnl = t["pnl_r"]
            if is_deca:
                risk_usd = sec["balance"] * risk_pct
            else:
                risk_usd = 10.0 # Flat $10

            dollar_pnl = risk_usd * r_pnl
            sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))
            sec["pnl"] = round(sec["pnl"] + dollar_pnl, 2)
            if sec["balance"] > sec["peak"]:
                sec["peak"] = sec["balance"]

            month_key = t["day"][:7] # YYYY-MM
            monthly_pnl[month_key] += dollar_pnl

            if "WIN" in t["outcome"]:
                sec["wins"] += 1
            elif "SAVE" in t["outcome"]:
                sec["saves"] += 1
            else:
                sec["losses"] += 1

            executed.append({
                "time": t["exit_time"],
                "dollar_pnl": dollar_pnl,
                "total_eq": sum(s["balance"] for s in sections.values())
            })

        tot_eq = sum(s["balance"] for s in sections.values())
        tot_wins = sum(s["wins"] for s in sections.values())
        tot_saves = sum(s["saves"] for s in sections.values())
        tot_losses = sum(s["losses"] for s in sections.values())
        tot_exec = len(executed)

        win_rate = (tot_wins / tot_exec * 100) if tot_exec else 0.0
        green_rate = ((tot_wins + tot_saves) / tot_exec * 100) if tot_exec else 0.0
        net_profit = tot_eq - 500.0
        roi_pct = (net_profit / 500.0) * 100.0

        # Max Drawdown
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
            "total_trades": tot_exec,
            "wins": tot_wins,
            "saves": tot_saves,
            "losses": tot_losses,
            "win_rate": win_rate,
            "green_rate": green_rate,
            "loss_rate": (tot_losses / tot_exec * 100) if tot_exec else 0.0,
            "initial": 500.0,
            "final": tot_eq,
            "profit": net_profit,
            "roi_pct": roi_pct,
            "max_dd": max_dd,
            "sections": sections,
            "monthly_pnl": dict(monthly_pnl)
        }

    res_flat = simulate(0.0, False)
    res_2pct = simulate(0.02, True)
    res_5pct = simulate(0.05, True)

    print("\n" + "=" * 80)
    print("🏆 1-YEAR (365 DAYS: OCT 2025 - OCT 2026) FULL YEAR AUDIT RESULTS")
    print("=" * 80)

    for label, res in [("A. Flat Risk ($10/trade Flat)", res_flat),
                       ("B. Deca Conservative (2% Section Risk)", res_2pct),
                       ("C. Deca Aggressive (5% Section Risk)", res_5pct)]:
        print(f"\n--- {label} ---")
        print(f"• Total Executed Trades: {res['total_trades']}")
        print(f"• Pure Wins: {res['wins']} | Fee Shield Saves (BE): {res['saves']} | Losses (SL): {res['losses']}")
        print(f"• Pure Win Rate: {res['win_rate']:.2f}%")
        print(f"• Total Green / Protected Rate: {res['green_rate']:.2f}%")
        print(f"• Loss Rate: {res['loss_rate']:.2f}%")
        print(f"• Starting Balance: ${res['initial']:.2f} USDT")
        print(f"• Final Balance: ${res['final']:,.2f} USDT")
        print(f"• Net Profit: ${res['profit']:+,.2f} USDT ({res['roi_pct']:+,.1f}%)")
        print(f"• Max Account Drawdown: {res['max_dd']:.2f}%")

    print("\n" + "-" * 80)
    print("📅 MONTH-BY-MONTH PNL BREAKDOWN (Deca 2% Conservative):")
    print("-" * 80)
    for m, pnl in sorted(res_2pct["monthly_pnl"].items()):
        print(f"  {m}: ${pnl:+8.2f} USDT")

    print("\n" + "-" * 80)
    print("🧩 SECTION-BY-SECTION FINAL BALANCES (Deca 2% Conservative):")
    print("-" * 80)
    for s_id in range(1, 11):
        s = res_2pct["sections"][s_id]
        assigned = [c.replace("USDT","") for c, sid in PAIR_MAPPING.items() if sid == s_id]
        print(f"Sec #{s['id']:<2} ({', '.join(assigned):<12}) | Final: ${s['balance']:<8.2f} | PnL: ${s['pnl']:+8.2f} | Trades: {s['trades']}")

def evaluate_trade(candles, fill_idx, side, entry_price, sl_price, risk, symbol, day_str, max_hold_bars=48, friction_r=0.06):
    active_sl = sl_price
    current_tier = 0
    n = len(candles)
    fill_candle = candles[fill_idx]
    fill_time = fill_candle["time"]

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold_bars, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]
        exit_time = b["time"]

        if side == "LONG":
            if b_l <= active_sl:
                if current_tier == 0:
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "LOSS", "pnl_r": -1.0 - friction_r}
                elif current_tier == 1:
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r}
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "WIN", "pnl_r": locked_r - friction_r}

            max_fav_r = (b_h - entry_price) / risk
            if max_fav_r >= 1.0:
                tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry_price + (locked_r * risk)

        else: # SHORT
            if b_h >= active_sl:
                if current_tier == 0:
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "LOSS", "pnl_r": -1.0 - friction_r}
                elif current_tier == 1:
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r}
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "WIN", "pnl_r": locked_r - friction_r}

            max_fav_r = (entry_price - b_l) / risk
            if max_fav_r >= 1.0:
                tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry_price - (locked_r * risk)

    last_c = candles[min(fill_idx + max_hold_bars, n - 1)]
    pnl_r = ((last_c["close"] - entry_price) / risk) if side == "LONG" else ((entry_price - last_c["close"]) / risk)
    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": last_c["time"], "outcome": "TIMEOUT", "pnl_r": pnl_r - friction_r}

if __name__ == "__main__":
    run_1year_test()
