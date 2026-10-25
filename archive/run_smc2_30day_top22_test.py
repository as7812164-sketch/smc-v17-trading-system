"""
===============================================================================
SMC 2.0 EXPERIMENTAL: 30-DAY TOP-22 COIN BENCHMARK AUDIT
===============================================================================
Runs a continuous 30-day simulation of the SMC 2.0 Institutional Extreme OB
strategy across the Top-22 Binance Futures assets (720 candles per coin on 1H).
===============================================================================
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from engine.smc2_experimental import SMC2ExtremeOBDetector, SMC2Simulator

TOP_22_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "AVAXUSDT",
    "LINKUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "FETUSDT", "PEPEUSDT",
    "SHIBUSDT", "TIAUSDT", "RENDERUSDT", "ADAUSDT", "XRPUSDT", "INJUSDT",
    "ARBUSDT", "OPUSDT", "AAVEUSDT", "PYTHUSDT"
]

def run_30day_top22_audit(timeframe: str = "1h", candle_count: int = 720):
    detector = SMC2ExtremeOBDetector(
        min_displacement_pct=0.045,  # 4.5% displacement threshold for 1-month intraday
        swing_lookback=12,
        max_tap_window=30,
        min_rr_ratio=2.5,
        be_lock_pct=0.015,
        hard_sl_buffer_pct=0.004
    )

    all_coin_results = []
    total_setups = 0
    total_trades = 0
    total_wins = 0
    total_be = 0
    total_losses = 0

    portfolio_balance = 50.0
    initial_balance = 50.0

    print("=" * 75)
    print(f"🏛️ RUNNING SMC 2.0 30-DAY BACKTEST ACROSS TOP-22 COINS ({timeframe.upper()})")
    print(f"Data Window: Last {candle_count} candles (~30 Days continuous)")
    print("=" * 75)
    print(f"{'Coin':<12} | {'Trades':<7} | {'Win (TP)':<8} | {'BE ($0)':<7} | {'Loss':<6} | {'WinRate':<8} | {'Net PnL %':<10}")
    print("-" * 75)

    for symbol in TOP_22_COINS:
        file_path = f"historical_data/{symbol}_{timeframe}.json"
        if not os.path.exists(file_path):
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            candles_full = json.load(f)

        # Slice the last 30 days (720 candles for 1h, 180 for 4h)
        candles = candles_full[-candle_count:] if len(candles_full) >= candle_count else candles_full

        setups = detector.detect_setups(symbol, candles, interval=timeframe, full_scan=True)
        simulator = SMC2Simulator(leverage=5.0, initial_balance=50.0)
        res = simulator.run_simulation(candles, setups)

        total_setups += len(setups)
        total_trades += res["total_trades"]
        total_wins += res["win_trades"]
        total_be += res["be_trades"]
        total_losses += res["loss_trades"]

        win_rate = res["win_rate"]
        net_roi = res["net_roi_pct"]

        print(f"{symbol:<12} | {res['total_trades']:<7} | {res['win_trades']:<8} | {res['be_trades']:<7} | {res['loss_trades']:<6} | {win_rate:>6.1f}%  | {net_roi:>+8.2f}%")

        all_coin_results.append({
            "symbol": symbol,
            "setups": len(setups),
            "trades": res["total_trades"],
            "wins": res["win_trades"],
            "be": res["be_trades"],
            "losses": res["loss_trades"],
            "win_rate": win_rate,
            "roi": net_roi,
            "final_bal": res["final_balance"],
            "trade_list": res["trades"]
        })

    # Portfolio waterfall sequential compounding simulation across all generated setups chronologically
    all_trades_chronological = []
    for r in all_coin_results:
        all_trades_chronological.extend(r["trade_list"])

    # Calculate overall win rate
    overall_win_rate = (total_wins / total_trades * 100.0) if total_trades > 0 else 0.0
    overall_preservation_rate = ((total_wins + total_be) / total_trades * 100.0) if total_trades > 0 else 0.0

    print("=" * 75)
    print("📊 30-DAY TOP-22 PORTFOLIO AGGREGATE SUMMARY:")
    print("=" * 75)
    print(f"Total Institutional Extreme OB Setups Detected: {total_setups}")
    print(f"Total Executed & Completed Trades: {total_trades}")
    print(f"🏆 Total Take-Profit (TP) Hits: {total_wins}")
    print(f"🛡️ Total Zero-Loss Breakeven (BE) Exits: {total_be}")
    print(f"🛑 Total Stop-Loss (SL) Hits: {total_losses}")
    print(f"🎯 Pure Win Rate (TP Only): {overall_win_rate:.2f}%")
    print(f"🛡️ Capital Preservation Rate (TP + BE): {overall_preservation_rate:.2f}%")
    print("=" * 75)

    return {
        "total_trades": total_trades,
        "total_wins": total_wins,
        "total_be": total_be,
        "total_losses": total_losses,
        "win_rate": overall_win_rate,
        "preservation_rate": overall_preservation_rate,
        "coin_results": all_coin_results
    }

if __name__ == "__main__":
    tf = sys.argv[1] if len(sys.argv) > 1 else "1h"
    cnt = 720 if tf == "1h" else 180
    run_30day_top22_audit(timeframe=tf, candle_count=cnt)
