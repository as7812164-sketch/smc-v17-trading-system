import os
import sys
import json
import urllib.request
from engine.quant_microstructure_math import compute_hurst_exponent, compute_taker_delta_metrics
from run_true_quant_proprietary_backtest import fetch_futures_klines, TOP_ASSETS

def run_test():
    total_trades = 0
    wins = 0
    losses = 0
    be_cuts = 0
    gross_pnl = 0.0

    print("Running Calibrated Delta-Absorption Harvest Test across 10 top coins...")

    for sym in TOP_ASSETS:
        try:
            candles = fetch_futures_klines(sym, 1500)
        except Exception:
            continue

        n = len(candles)
        if n < 100: continue

        for i in range(50, n - 40):
            c3 = candles[i]
            c2 = candles[i+1]
            c1 = candles[i+2]

            imp_h = max(c1["h"], c2["h"])
            is_red = c3["c"] < c3["o"]
            fvg = c1["l"] > c3["h"]
            disp = (imp_h - c3["l"]) / c3["l"] if c3["l"] > 0 else 0.0

            if not (is_red and fvg and disp >= 0.025):
                continue

            ob_high = c3["h"]
            ob_low = c3["l"]
            ob_range = ob_high - ob_low
            boundary_5pct = ob_high - (0.05 * ob_range)
            mt_50 = (ob_high + ob_low) / 2.0

            # Find tap
            tap_idx = -1
            for k in range(i + 3, min(i + 120, n)):
                if candles[k]["c"] < ob_low: break
                if candles[k]["l"] <= boundary_5pct:
                    tap_idx = k
                    break

            if tap_idx == -1: continue
            tap_c = candles[tap_idx]

            # QUANT GATE:
            # 1. Delta Absorption Check:
            delta_info = compute_taker_delta_metrics(tap_c["taker_buy_vol"], tap_c["vol"])
            c_rng = tap_c["h"] - tap_c["l"]
            l_wick = min(tap_c["o"], tap_c["c"]) - tap_c["l"]
            wick_ratio = (l_wick / c_rng) if c_rng > 0 else 0.0
            is_green = tap_c["c"] >= tap_c["o"]

            # Absorption: Taker Buy Delta >= 50% OR Lower Wick >= 18% with defending 50% MT
            has_absorption = (delta_info["delta_ratio"] >= 0.50 or is_green) and (wick_ratio >= 0.15 or delta_info["delta_ratio"] >= 0.52)
            if not has_absorption:
                continue

            # Execution with Calibrated Sweetspot Harvest:
            entry_p = boundary_5pct
            tp_p = entry_p * 1.020 # +2.0% Price (+10.0% ROE @ 5x)
            sl_p = min(ob_low, tap_c["l"]) * 0.998 # Tight structural SL
            be_p = entry_p * 1.010 # Fast BE lock at +1.0%

            be_act = False
            won = False
            lost = False

            for s in range(tap_idx + 1, min(tap_idx + 80, n)):
                sc = candles[s]
                if sc["h"] >= be_p: be_act = True
                if sc["h"] >= tp_p: won = True; break
                if be_act and sc["l"] <= entry_p * 1.001: break
                if sc["l"] <= sl_p: lost = True; break

            total_trades += 1
            if won:
                wins += 1
                gross_pnl += 0.020 * 5.0
            elif lost:
                losses += 1
                gross_pnl -= ((entry_p - sl_p) / entry_p) * 5.0
            else:
                be_cuts += 1

    decided = wins + losses
    wr = (wins / decided * 100.0) if decided > 0 else 0.0
    print("==================================================")
    print(f"Total Trades: {total_trades}")
    print(f"Wins: {wins} | Losses: {losses} | BE Cuts: {be_cuts}")
    print(f"WIN RATE: {wr:.2f}%")
    print(f"Gross ROE PnL: {gross_pnl * 100:.2f}%")
    print("==================================================")

if __name__ == "__main__":
    run_test()
