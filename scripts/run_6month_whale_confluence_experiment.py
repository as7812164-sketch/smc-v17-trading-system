"""
6-MONTH EXPERIMENT: BB 2.0 BASELINE VS WHALE CONFLUENCE MODEL
============================================================
Period: April 1, 2026 to October 14, 2026 (Recent 6.5 Months OOS)
Starting Capital: $500.00 USDT across 10 Deca Sections ($50 each)

Compares:
1. Standard BB 2.0 Model 3 (Baseline)
2. Whale-Enhanced BB 2.0 (Liquidity Piercing Depth + Absorption Wick >=20% + Stopping Volume Climax >=1.2x)
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

from scripts.test_1year_bb20_model3_full import evaluate_trade, get_day_key

def run_experiment(apply_whale_filter: bool):
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

            # 6-Month Pure OOS Filter
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
                c_vol = c.get("volume", 0.0)
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # Calculate 10-bar moving average volume
                past_10_vol = [candles[max(0, g_idx - k)]["volume"] for k in range(1, 11)]
                avg_vol = sum(past_10_vol) / len(past_10_vol) if past_10_vol else 1.0

                # Candle range and wicks
                candle_range = max(1e-8, c_h - c_l)
                lower_wick = max(0.0, min(c_o, c_c) - c_l)
                upper_wick = max(0.0, c_h - max(c_o, c_c))
                lower_wick_ratio = lower_wick / candle_range
                upper_wick_ratio = upper_wick / candle_range

                # Long at PDL
                if not long_taken:
                    dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                    basic_pdl_cond = (dist_to_pdl <= 0.015 or c_l <= pdl)
                    basic_disp = ((c_c < c_o or (c_h - c_l) > 0) and 
                                  ((next_c["high"] - c_l) / c_l >= 0.012 or (next_c2["high"] - c_l) / c_l >= 0.018) and 
                                  next_c2["low"] > c_h)

                    if basic_pdl_cond and basic_disp:
                        pass_filter = True
                        if apply_whale_filter:
                            # 1. Liquidity Depth: Must pierce or be within 0.3% of PDL
                            pierce_ok = (c_l <= pdl * 1.002)
                            # 2. Absorption Wick: Lower rejection wick >= 20%
                            wick_ok = (lower_wick_ratio >= 0.20 or next_c["close"] > next_c["open"])
                            # 3. Volume Climax: Sweep or displacement volume >= 1.15x average
                            vol_ok = (c_vol >= 1.15 * avg_vol or next_c.get("volume", 0) >= 1.15 * avg_vol)

                            if not (pierce_ok and wick_ok and vol_ok):
                                pass_filter = False

                        if pass_filter:
                            mt = (c_h + c_l) / 2.0
                            sl = c_l * 0.9985
                            risk = mt - sl
                            if risk > 0:
                                for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                    if candles[w_idx]["low"] <= sl:
                                        break
                                    if candles[w_idx]["low"] <= mt:
                                        long_taken = True
                                        all_trades.append(evaluate_trade(candles, w_idx, "LONG", mt, sl, risk, sym, curr_day))
                                        break

                # Short at PDH
                if not short_taken:
                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    basic_pdh_cond = (dist_to_pdh <= 0.015 or c_h >= pdh)
                    basic_disp = ((c_c > c_o or (c_h - c_l) > 0) and 
                                  ((c_h - next_c["low"]) / c_h >= 0.012 or (c_h - next_c2["low"]) / c_h >= 0.018) and 
                                  next_c2["high"] < c_l)

                    if basic_pdh_cond and basic_disp:
                        pass_filter = True
                        if apply_whale_filter:
                            # 1. Liquidity Depth: Must pierce or be within 0.3% of PDH
                            pierce_ok = (c_h >= pdh * 0.998)
                            # 2. Absorption Wick: Upper rejection wick >= 20%
                            wick_ok = (upper_wick_ratio >= 0.20 or next_c["close"] < next_c["open"])
                            # 3. Volume Climax: Sweep or displacement volume >= 1.15x average
                            vol_ok = (c_vol >= 1.15 * avg_vol or next_c.get("volume", 0) >= 1.15 * avg_vol)

                            if not (pierce_ok and wick_ok and vol_ok):
                                pass_filter = False

                        if pass_filter:
                            mt = (c_h + c_l) / 2.0
                            sl = c_h * 1.0015
                            risk = sl - mt
                            if risk > 0:
                                for w_idx in range(g_idx + 2, min(g_idx + 24, len(candles))):
                                    if candles[w_idx]["high"] >= sl:
                                        break
                                    if candles[w_idx]["high"] >= mt:
                                        short_taken = True
                                        all_trades.append(evaluate_trade(candles, w_idx, "SHORT", mt, sl, risk, sym, curr_day))
                                        break

                if long_taken and short_taken:
                    break

    all_trades.sort(key=lambda t: t["fill_time"])
    return all_trades

def simulate_portfolio(trades, risk_pct: float, is_flat: bool = False):
    sections = {i: {"id": i, "balance": 50.0, "peak": 50.0, "busy_until": 0, "trades": 0, "wins": 0, "saves": 0, "losses": 0, "pnl": 0.0} for i in range(1, 11)}
    executed = []

    for t in trades:
        sec_id = PAIR_MAPPING.get(t["symbol"], 1)
        sec = sections[sec_id]
        if sec["busy_until"] > t["fill_time"]:
            continue
        sec["busy_until"] = t["exit_time"]
        sec["trades"] += 1

        r_pnl = t["pnl_r"]
        risk_usd = 10.0 if is_flat else (sec["balance"] * risk_pct)
        dollar_pnl = risk_usd * r_pnl

        sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))
        sec["pnl"] = round(sec["pnl"] + dollar_pnl, 2)
        if sec["balance"] > sec["peak"]:
            sec["peak"] = sec["balance"]

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
    loss_rate = (tot_losses / tot_exec * 100) if tot_exec else 0.0
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
        "saves": tot_saves,
        "losses": tot_losses,
        "win_rate": win_rate,
        "green_rate": green_rate,
        "loss_rate": loss_rate,
        "final_balance": tot_eq,
        "net_profit": net_profit,
        "roi_pct": roi_pct,
        "max_dd": max_dd,
        "sections": sections
    }

def main():
    print("=" * 80)
    print("🔬 6-MONTH EXPERIMENT: BASELINE BB 2.0 VS WHALE CONFLUENCE MODEL")
    print("• Period: April 1, 2026 to October 14, 2026")
    print("• Starting Capital: $500.00 across 10 Deca Sections ($50 each)")
    print("=" * 80)

    print("\n[1/2] Running Baseline BB 2.0 Model 3...")
    base_trades = run_experiment(apply_whale_filter=False)
    base_cons = simulate_portfolio(base_trades, risk_pct=0.02)
    base_aggr = simulate_portfolio(base_trades, risk_pct=0.05)

    print("\n[2/2] Running Whale Confluence Enhanced Model...")
    whale_trades = run_experiment(apply_whale_filter=True)
    whale_cons = simulate_portfolio(whale_trades, risk_pct=0.02)
    whale_aggr = simulate_portfolio(whale_trades, risk_pct=0.05)

    print("\n" + "=" * 80)
    print("🏆 SIDE-BY-SIDE 6-MONTH EXPERIMENTAL AUDIT COMPARISON")
    print("=" * 80)

    print(f"\n{'Metric':<30} | {'Baseline BB 2.0':<22} | {'Whale Confluence Model':<22}")
    print("-" * 80)
    print(f"{'Total Trades Executed':<30} | {base_cons['trades']:<22} | {whale_cons['trades']:<22}")
    print(f"{'Pure Win Rate (%)':<30} | {base_cons['win_rate']:.2f}%{'':<16} | {whale_cons['win_rate']:.2f}%{'':<16}")
    print(f"{'Fee Shield Saves (%)':<30} | {(base_cons['saves']/base_cons['trades']*100):.2f}%{'':<16} | {(whale_cons['saves']/whale_cons['trades']*100):.2f}%{'':<16}")
    print(f"{'Loss Rate (%)':<30} | {base_cons['loss_rate']:.2f}%{'':<16} | {whale_cons['loss_rate']:.2f}%{'':<16}")
    print(f"{'Total Green/Safe Rate (%)':<30} | {base_cons['green_rate']:.2f}%{'':<16} | {whale_cons['green_rate']:.2f}%{'':<16}")
    print("-" * 80)
    print(f"{'Conservative (2% Risk)':<30} | {'':<22} | {'':<22}")
    print(f"  • Final Balance (USDT)       | ${base_cons['final_balance']:,.2f}{'':<12} | ${whale_cons['final_balance']:,.2f}{'':<12}")
    print(f"  • Net ROI (%)                | +{base_cons['roi_pct']:.1f}%{'':<15} | +{whale_cons['roi_pct']:.1f}%{'':<15}")
    print(f"  • Max Drawdown (%)           | {base_cons['max_dd']:.2f}%{'':<16} | {whale_cons['max_dd']:.2f}%{'':<16}")
    print("-" * 80)
    print(f"{'Aggressive (5% Risk)':<30} | {'':<22} | {'':<22}")
    print(f"  • Final Balance (USDT)       | ${base_aggr['final_balance']:,.2f}{'':<12} | ${whale_aggr['final_balance']:,.2f}{'':<12}")
    print(f"  • Net ROI (%)                | +{base_aggr['roi_pct']:.1f}%{'':<15} | +{whale_aggr['roi_pct']:.1f}%{'':<15}")
    print(f"  • Max Drawdown (%)           | {base_aggr['max_dd']:.2f}%{'':<16} | {whale_aggr['max_dd']:.2f}%{'':<16}")
    print("=" * 80)

if __name__ == "__main__":
    main()
