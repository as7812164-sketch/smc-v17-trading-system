"""
===============================================================================
SMC 2.0 USER PARAMETERS AUDIT: 30-DAY TOP-22 BENCHMARK
===============================================================================
Parameters Configured by User:
- Leverage: 5x
- TP: 12.20% ROE (2.44% price move)
- SL: 12.00% ROE (2.40% price move)
- Timeframes: 1H (720 candles / 30 days) and 4H (180 candles / 30 days)
- Universe: Top-22 Binance Futures Assets
===============================================================================
"""

import os
import sys
import json

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

class SMC2UserParamDetector(SMC2ExtremeOBDetector):
    def __init__(self, tp_roe_pct: float = 12.20, sl_roe_pct: float = 12.00, leverage: float = 5.0, **kwargs):
        super().__init__(**kwargs)
        self.leverage = leverage
        self.tp_price_pct = (tp_roe_pct / 100.0) / self.leverage  # 12.2% / 5 = 2.44%
        self.sl_price_pct = (sl_roe_pct / 100.0) / self.leverage  # 12.0% / 5 = 2.40%

    def detect_setups(self, symbol, candles, interval="1h", full_scan=True):
        raw = super().detect_setups(symbol, candles, interval, full_scan)
        for s in raw:
            entry = s["entry_price"]
            side = s["side"]
            if side == "LONG":
                s["tp_price"] = round(entry * (1.0 + self.tp_price_pct), 6)
                s["sl_price"] = round(entry * (1.0 - self.sl_price_pct), 6)
            else:
                s["tp_price"] = round(entry * (1.0 - self.tp_price_pct), 6)
                s["sl_price"] = round(entry * (1.0 + self.sl_price_pct), 6)
            s["rr_ratio"] = round(self.tp_price_pct / self.sl_price_pct, 2)
        return raw


def run_benchmark(interval: str, candle_count: int):
    detector = SMC2UserParamDetector(
        tp_roe_pct=12.20,
        sl_roe_pct=12.00,
        leverage=5.0,
        min_displacement_pct=0.045,
        swing_lookback=12,
        max_tap_window=30,
        min_rr_ratio=1.0,
        be_lock_pct=0.015  # BE locks at +1.5% price move (+7.5% ROE)
    )
    simulator = SMC2Simulator(leverage=5.0, initial_balance=50.0)

    total_trades = 0
    total_wins = 0
    total_be = 0
    total_losses = 0
    coin_data = []

    print("\n" + "=" * 78)
    print(f"🏛️ SMC 2.0 30-DAY AUDIT: {interval.upper()} (TP: 12.20% ROE | SL: 12.00% ROE | 5x Lev)")
    print(f"Candles per coin: {candle_count} (~30 continuous days)")
    print("=" * 78)
    print(f"{'Coin':<12} | {'Trades':<7} | {'Win (TP)':<8} | {'BE ($0)':<7} | {'Loss (SL)':<9} | {'WinRate':<8} | {'Net PnL %':<10}")
    print("-" * 78)

    for symbol in TOP_22_COINS:
        file_path = f"historical_data/{symbol}_{interval}.json"
        if not os.path.exists(file_path):
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            candles_full = json.load(f)

        candles = candles_full[-candle_count:] if len(candles_full) >= candle_count else candles_full
        setups = detector.detect_setups(symbol, candles, interval=interval, full_scan=True)
        res = simulator.run_simulation(candles, setups)

        total_trades += res["total_trades"]
        total_wins += res["win_trades"]
        total_be += res["be_trades"]
        total_losses += res["loss_trades"]

        if res["total_trades"] > 0:
            print(f"{symbol:<12} | {res['total_trades']:<7} | {res['win_trades']:<8} | {res['be_trades']:<7} | {res['loss_trades']:<9} | {res['win_rate']:>6.1f}%  | {res['net_roi_pct']:>+8.2f}%")
        
        coin_data.append({
            "symbol": symbol,
            "trades": res["total_trades"],
            "wins": res["win_trades"],
            "be": res["be_trades"],
            "losses": res["loss_trades"],
            "win_rate": res["win_rate"],
            "roi": res["net_roi_pct"]
        })

    win_rate = (total_wins / total_trades * 100.0) if total_trades > 0 else 0.0
    preservation_rate = ((total_wins + total_be) / total_trades * 100.0) if total_trades > 0 else 0.0

    print("=" * 78)
    print(f"📊 SUMMARY FOR {interval.upper()} (30 DAYS):")
    print(f"Total Trades: {total_trades}")
    print(f"🏆 TP Hits (+12.20% ROE): {total_wins}")
    print(f"🛡️ Breakeven Exits ($0.00): {total_be}")
    print(f"🛑 SL Hits (-12.00% ROE): {total_losses}")
    print(f"🎯 Win Rate (TP Hits): {win_rate:.2f}%")
    print(f"🛡️ Capital Preservation Rate (TP + BE): {preservation_rate:.2f}%")
    print("=" * 78 + "\n")

    return {
        "interval": interval,
        "total_trades": total_trades,
        "wins": total_wins,
        "be": total_be,
        "losses": total_losses,
        "win_rate": win_rate,
        "preservation_rate": preservation_rate
    }

if __name__ == "__main__":
    res_1h = run_benchmark("1h", 720)
    res_4h = run_benchmark("4h", 180)

    # Combined Aggregation
    comb_trades = res_1h["total_trades"] + res_4h["total_trades"]
    comb_wins = res_1h["wins"] + res_4h["wins"]
    comb_be = res_1h["be"] + res_4h["be"]
    comb_losses = res_1h["losses"] + res_4h["losses"]
    comb_wr = (comb_wins / comb_trades * 100.0) if comb_trades > 0 else 0.0
    comb_pres = ((comb_wins + comb_be) / comb_trades * 100.0) if comb_trades > 0 else 0.0

    print("=" * 78)
    print("🏆 MASTER COMBINED PORTFOLIO SUMMARY (1H + 4H DUAL-TIMEFRAME - 30 DAYS):")
    print("=" * 78)
    print(f"Total Combined Trades: {comb_trades}")
    print(f"🏆 Total TP Hits (+12.20% ROE): {comb_wins}")
    print(f"🛡️ Total Zero-Loss Breakeven Exits: {comb_be}")
    print(f"🛑 Total Stop Loss Hits (-12.00% ROE): {comb_losses}")
    print(f"🎯 Master Win Rate: {comb_wr:.2f}%")
    print(f"🛡️ Total Capital Preservation Rate: {comb_pres:.2f}%")
    print("=" * 78)
