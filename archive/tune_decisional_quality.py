import json
import time
import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

APPROVED_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "APTUSDT",
    "ARBUSDT", "OPUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", "RUNEUSDT", "RENDERUSDT",
    "INJUSDT", "FETUSDT", "THETAUSDT", "ALGOUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT", "ICPUSDT",
    "PYTHUSDT", "PEPEUSDT", "SHIBUSDT", "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOGEUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_local_data(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def run_tuned_decisional_audit():
    all_data = {"1h": {}, "4h": {}}
    for sym in APPROVED_COINS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    # We test 3 Quality Filters on Decisional OBs to find the perfect balance:
    # 1. Standard Enhanced (Exp >= 4.5%, Wick >= 18%)
    # 2. High-Octane Enhanced (Exp >= 6.0%, Wick >= 22%)
    # 3. God-Tier Decisional (Exp >= 6.0%, Wick >= 25%, 4H Timeframe Only)

    configs = [
        {"name": "Standard Enhanced Decisional (1H & 4H)", "tfs": ["1h", "4h"], "min_exp": 0.045, "min_wick": 0.18},
        {"name": "High-Octane Decisional (1H & 4H, Strong Impulse & Wick)", "tfs": ["1h", "4h"], "min_exp": 0.060, "min_wick": 0.22},
        {"name": "4H Prime Decisional (Only 4H High-Volume Impulse)", "tfs": ["4h"], "min_exp": 0.050, "min_wick": 0.20}
    ]

    print("=" * 90)
    print(" ⚡ TUNING DECISIONAL OB TO PERFECTION (MAX COMPOUNDING VELOCITY + SAFE DRAWDOWN)")
    print("=" * 90)

    for cfg in configs:
        trades = []
        for tf in cfg["tfs"]:
            tp_pct = 0.022 if tf == "1h" else 0.028
            sl_pct = 0.025 if tf == "1h" else 0.028
            max_hold = 24

            for sym, candles in all_data[tf].items():
                n = len(candles)
                for i in range(25, n - 35):
                    swing_low = candles[i]["low"]
                    if swing_low != min(c["low"] for c in candles[i-15:i+1]): continue

                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx <= i + 3: continue

                    total_gain = (max_high - swing_low) / swing_low
                    if total_gain < cfg["min_exp"]: continue

                    idm_low = candles[high_idx - 1]["low"]

                    best_mid = -1
                    max_bg = 0.0
                    for mid in range(i+1, high_idx):
                        bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                        fib = (candles[mid]["low"] - swing_low) / (max_high - swing_low)
                        if 0.30 <= fib <= 0.70 and bg > max_bg:
                            max_bg = bg
                            best_mid = mid

                    if best_mid == -1: continue
                    dec_c = candles[best_mid - 1]
                    dec_top = max(dec_c["open"], dec_c["close"])
                    dec_bot = dec_c["low"]
                    has_dec_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                    if not has_dec_fvg: continue

                    for t in range(high_idx + 1, min(high_idx + 35, n)):
                        if candles[t]["low"] <= dec_top:
                            tap_c = candles[t]
                            swept_idm = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                            c_range = tap_c["high"] - tap_c["low"]
                            lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                            wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                            dec_mt = (dec_top + dec_bot) / 2.0

                            if swept_idm and wick_ratio >= cfg["min_wick"] and tap_c["close"] >= dec_mt:
                                entry_p = dec_top
                                tp_p = entry_p * (1.0 + tp_pct)
                                sl_p = entry_p * (1.0 - sl_pct)

                                t_res = None
                                exit_p = entry_p
                                bars = 0
                                for m in range(t, min(t + max_hold, n)):
                                    bars += 1
                                    if candles[m]["high"] >= tp_p:
                                        t_res = "WIN"; exit_p = tp_p; break
                                    if candles[m]["close"] <= sl_p:
                                        t_res = "LOSS"; exit_p = sl_p; break
                                if not t_res:
                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                    t_res = "WIN" if fc >= entry_p else "LOSS"
                                    exit_p = fc

                                gross = (exit_p - entry_p) / entry_p
                                trades.append({
                                    "sym": sym, "tf": tf, "time": tap_c["time"],
                                    "res": t_res, "gross": gross, "bars": bars
                                })
                            break

        trades.sort(key=lambda x: x["time"])
        tot = len(trades)
        wins = sum(1 for t in trades if t["res"] == "WIN")
        losses = tot - wins
        wr = (wins / tot * 100) if tot else 0
        avg_bars = np.mean([t["bars"] for t in trades]) if trades else 0

        cap = 50.0
        vault = 0.0
        max_c = 50.0
        max_dd = 0.0
        hit_1000_idx = None
        hit_1000_date = None

        for idx, t in enumerate(trades, 1):
            pos = cap * 5.0
            net_ret = t["gross"] - 0.0014
            pnl = pos * net_ret

            if pnl > 0:
                cap += pnl * 0.85
                vault += pnl * 0.15
            else:
                cap = max(5.0, cap + pnl)

            tw = cap + vault
            if tw > max_c: max_c = tw
            dd = (max_c - tw) / max_c * 100.0
            if dd > max_dd: max_dd = dd

            if tw >= 1000.0 and hit_1000_idx is None:
                hit_1000_idx = idx
                hit_1000_date = time.strftime("%Y-%m-%d", time.gmtime(t["time"]/1000))

        print(f"\n⚙️  CONFIGURATION: {cfg['name']}")
        print(f"    Setups: {tot:4d} (Avg {tot/52:.1f}/week) | Wins: {wins:4d} ({wr:5.2f}%) | Losses: {losses:4d}")
        print(f"    Avg Duration: {avg_bars:.1f} bars (~{avg_bars*2:.1f} hours)")
        print(f"    🎉 $1,000 Hit At: Trade #{hit_1000_idx} on {hit_1000_date}")
        print(f"    Total Wealth Generated: ${cap+vault:,.2f} USDT (Vault: ${vault:,.2f})")
        print(f"    Max Portfolio Drawdown: {max_dd:5.2f}%")

if __name__ == "__main__":
    run_tuned_decisional_audit()
