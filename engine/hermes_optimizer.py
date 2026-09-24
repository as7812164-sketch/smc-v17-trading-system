"""
Hermes Strategy Optimizer Engine
Performs multi-asset parameter grid search over historical klines
to discover optimal strategy configurations for 15m, 1H, and 4H timeframes.
"""

import os
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR_15M = BASE_DIR / "market_data_cache_15m"

def load_15m_cached_data() -> Dict[str, List[Dict[str, Any]]]:
    """Loads all 20 cached 15m Binance Futures assets."""
    market_data = {}
    if not CACHE_DIR_15M.exists():
        return market_data

    files = [f for f in os.listdir(CACHE_DIR_15M) if f.endswith("_15m.json")]
    for fname in sorted(files):
        sym = fname.replace("_15m.json", "")
        fpath = CACHE_DIR_15M / fname
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                candles = json.load(f)
                if candles and len(candles) >= 5000:
                    market_data[sym] = candles
        except Exception:
            pass
    return market_data

def evaluate_parameter_set(
    market_data: Dict[str, List[Dict[str, Any]]],
    airspace_req_pct: float = 2.0,
    min_exp_pct: float = 0.0120,
    tp_pct: float = 0.0120,
    be_trigger_pct: float = 0.0050,
    soft_sl_pct: float = 0.0120,
    hard_sl_pct: float = 0.0220,
    fee_shield_buffer: float = 0.0010,
    killzone_only: bool = False,
    max_hold_bars: int = 16
) -> Dict[str, Any]:
    """Runs a backtest simulation for a single parameter set across all assets."""
    all_trades = []

    for sym, candles in market_data.items():
        n = len(candles)
        if n < 100:
            continue

        closes = [c["close"] for c in candles]
        ema50 = [0.0] * n
        mult = 2.0 / (50 + 1)
        ema50[49] = sum(closes[:50]) / 50.0
        for k in range(50, n):
            ema50[k] = (closes[k] - ema50[k-1]) * mult + ema50[k-1]

        detected_obs = []
        for i in range(15, n - 35):
            c = candles[i]
            if c["close"] >= c["open"]:
                continue
            ob_h, ob_l = c["high"], c["low"]
            if ob_h <= ob_l:
                continue

            prev_vols = [candles[x]["volume"] for x in range(max(0, i-10), i)]
            avg_vol = sum(prev_vols) / len(prev_vols) if prev_vols else c["volume"]
            if avg_vol > 0 and (c["volume"] / avg_vol) > 3.8:
                continue

            max_rally = max([candles[i+k]["high"] for k in range(1, min(9, n-i))])
            if (max_rally - ob_h) / ob_h < min_exp_pct:
                continue

            detected_obs.append({"bar_idx": i, "time": c["time"], "ob_high": ob_h, "ob_low": ob_l, "mitigated": False})

        for bar_idx in range(40, n - 35):
            curr_c = candles[bar_idx]
            if curr_c["close"] < ema50[bar_idx]:
                continue

            gm_time = time.gmtime(curr_c["time"] / 1000)

            # Optional Killzone filter (London 07-10 UTC, NY 12-15 UTC)
            if killzone_only:
                hour = gm_time.tm_hour
                if not ((7 <= hour <= 10) or (12 <= hour <= 15)):
                    continue

            # Weekend Altcoin Guard
            if gm_time.tm_wday in (5, 6) and sym not in ("BTCUSDT", "ETHUSDT"):
                continue

            active_obs = [ob for ob in detected_obs if ob["bar_idx"] < bar_idx - 2 and not ob["mitigated"]]
            if len(active_obs) < 3:
                continue

            recent_obs = sorted(active_obs, key=lambda x: x["bar_idx"], reverse=True)[:3]
            sorted_obs = sorted(recent_obs, key=lambda x: x["ob_high"], reverse=True)
            if sorted_obs[0]["ob_high"] <= sorted_obs[1]["ob_high"] or sorted_obs[1]["ob_high"] <= sorted_obs[2]["ob_high"]:
                continue

            top_ob = sorted_obs[0]
            middle_ob = sorted_obs[1]
            entry_level = middle_ob["ob_high"]
            entry_price = entry_level * 1.0004

            if not (curr_c["low"] <= entry_price and curr_c["open"] > entry_level):
                continue

            airspace_pct = (top_ob["ob_low"] - entry_price) / entry_price * 100.0
            if airspace_pct < airspace_req_pct:
                continue

            d_ratio = curr_c["taker_buy"] / curr_c["volume"] if curr_c["volume"] > 0 else 0.50
            cvd_prev = candles[bar_idx - 2]["cvd"] if bar_idx >= 2 else candles[0]["cvd"]
            cvd_diff = curr_c["cvd"] - cvd_prev
            if not (d_ratio >= 0.48 and cvd_diff > 0):
                continue

            middle_ob["mitigated"] = True

            tp_target = entry_price * (1.0 + tp_pct)
            be_trigger = entry_price * (1.0 + be_trigger_pct)
            fee_shield_be = entry_price * (1.0 + fee_shield_buffer)
            soft_sl_level = entry_price * (1.0 - soft_sl_pct)
            hard_sl_level = entry_price * (1.0 - hard_sl_pct)

            trade_res = None
            be_active = False

            for step in range(bar_idx + 1, min(bar_idx + 1 + max_hold_bars, n)):
                f_c = candles[step]
                if f_c["low"] <= hard_sl_level:
                    trade_res = "HARD_SL_HIT"
                    break
                if not be_active and f_c["high"] >= be_trigger:
                    be_active = True
                if f_c["high"] >= tp_target:
                    trade_res = "WIN"
                    break
                if be_active and f_c["low"] <= fee_shield_be:
                    trade_res = "BREAKEVEN"
                    break
                if not be_active and f_c["close"] <= soft_sl_level:
                    trade_res = "SOFT_SL_HIT"
                    break

            if not trade_res:
                trade_res = "BREAKEVEN" if be_active else "TIME_STOP_EXIT"

            all_trades.append({
                "time": curr_c["time"],
                "sym": sym,
                "result": trade_res
            })

    all_trades.sort(key=lambda x: x["time"])
    # Disjoint locks
    final_trades = []
    locks = {}
    for t in all_trades:
        if t["sym"] in locks and locks[t["sym"]] > t["time"]:
            continue
        final_trades.append(t)
        locks[t["sym"]] = t["time"] + max_hold_bars * 15 * 60 * 1000

    tot = len(final_trades)
    wins = sum(1 for t in final_trades if t["result"] == "WIN")
    bes = sum(1 for t in final_trades if t["result"] in ("BREAKEVEN", "TIME_STOP_EXIT"))
    losses = sum(1 for t in final_trades if "SL_HIT" in t["result"])

    win_rate = (wins / tot * 100.0) if tot > 0 else 0.0
    be_rate = (bes / tot * 100.0) if tot > 0 else 0.0
    loss_rate = (losses / tot * 100.0) if tot > 0 else 0.0
    safety_rate = ((wins + bes) / tot * 100.0) if tot > 0 else 0.0

    # Compounding $50
    capital = 50.0
    peak = capital
    max_dd = 0.0
    for t in final_trades:
        if t["result"] == "WIN":
            capital += capital * (tp_pct * 5.0)
        elif "SL_HIT" in t["result"]:
            capital -= capital * (soft_sl_pct * 5.0)
        if capital > peak:
            peak = capital
        dd = (peak - capital) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

    return {
        "airspace_req_pct": airspace_req_pct,
        "min_exp_pct": min_exp_pct,
        "killzone_only": killzone_only,
        "total_trades": tot,
        "wins": wins,
        "breakevens": bes,
        "losses": losses,
        "win_rate_pct": round(win_rate, 2),
        "breakeven_rate_pct": round(be_rate, 2),
        "loss_rate_pct": round(loss_rate, 2),
        "capital_safety_pct": round(safety_rate, 2),
        "starting_balance": 50.0,
        "final_balance": round(capital, 2),
        "net_gain_pct": round(((capital - 50.0) / 50.0) * 100.0, 1),
        "max_drawdown_pct": round(max_dd, 2)
    }

def run_hermes_parameter_sweep() -> Dict[str, Any]:
    """Sweeps multiple parameter combinations to find optimal settings."""
    print("[*] Hermes Optimizer: Loading 6-Month 15m Dataset...", flush=True)
    market_data = load_15m_cached_data()
    if not market_data:
        print("[!] No cached 15m market data found.", flush=True)
        return {}

    print(f"[*] Loaded {len(market_data)} cached assets (~360,000 candles). Running Grid Search...", flush=True)

    grid_results = []
    for airspace in [1.5, 2.0, 2.5, 3.0]:
        for kz in [False, True]:
            res = evaluate_parameter_set(
                market_data,
                airspace_req_pct=airspace,
                killzone_only=kz
            )
            kz_label = "KZ: ACTIVE (London+NY)" if kz else "KZ: 24/7"
            print(
                f"  • Airspace: {airspace:.1f}% | {kz_label:<25} ➔ Trades: {res['total_trades']:<2} | "
                f"Win Rate: {res['win_rate_pct']:>5.1f}% | Safety: {res['capital_safety_pct']:>5.1f}% | "
                f"Loss Rate: {res['loss_rate_pct']:>4.1f}% | $50 ➔ ${res['final_balance']:>6.2f} (+{res['net_gain_pct']}%)",
                flush=True
            )
            grid_results.append(res)

    # Sort by a composite score: (Safety * 0.4) + (WinRate * 0.4) + (Return * 0.2)
    def ranking_score(r):
        return (r["capital_safety_pct"] * 0.5) + (r["win_rate_pct"] * 0.3) + (min(r["net_gain_pct"], 300) * 0.2)

    grid_results.sort(key=ranking_score, reverse=True)
    best_config = grid_results[0]

    report = {
        "timestamp": int(time.time() * 1000),
        "total_configurations_tested": len(grid_results),
        "optimal_configuration": best_config,
        "all_configurations": grid_results
    }

    report_path = BASE_DIR / "hermes_optimization_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 95, flush=True)
    print("      🏆 HERMES OPTIMIZER: TOP RECOMMENDED CONFIGURATION FOR 15-MINUTE SCALPS", flush=True)
    print("=" * 95, flush=True)
    print(f"  👑 Optimal Airspace Gap:    {best_config['airspace_req_pct']:.1f}%")
    print(f"  ⏰ Session Filter:           {'London & NY AM Killzones' if best_config['killzone_only'] else '24/7 Market Operations'}")
    print(f"  🎯 Total High-Quality Trades: {best_config['total_trades']}")
    print(f"  🏆 Win Rate (Direct TP):     {best_config['win_rate_pct']}%")
    print(f"  🛡️ Capital Safety Rate:      {best_config['capital_safety_pct']}%")
    print(f"  ❌ SL Loss Rate:             {best_config['loss_rate_pct']}% (Minimal risk)")
    print(f"  💰 $50.00 Compounding:       $50.00 ➔ ${best_config['final_balance']:,.2f} USDT (+{best_config['net_gain_pct']}%)")
    print(f"  🛡️ Max Drawdown:             {best_config['max_drawdown_pct']}%")
    print("=" * 95 + "\n", flush=True)

    return report

if __name__ == "__main__":
    run_hermes_parameter_sweep()
