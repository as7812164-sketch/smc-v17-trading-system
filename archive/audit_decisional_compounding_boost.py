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

def run_decisional_compounding_audit():
    print("=" * 90)
    print(" 🚀 FORENSIC AUDIT: HOW MUCH DOES DECISIONAL OB BOOST COMPOUNDING?")
    print(" Comparing 3 Models on 1-Year (365 Days) Local Dataset Across 31 Coins:")
    print(" Model 1: ONLY Extreme OB (Low Frequency Anchor)")
    print(" Model 2: ONLY Enhanced Decisional OB (High Frequency Velocity Engine)")
    print(" Model 3: DUAL-ENGINE (Decisional Velocity Scalp + Extreme Anchor)")
    print("=" * 90)

    all_data = {"1h": {}, "4h": {}}
    for sym in APPROVED_COINS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    # Targets:
    # 1H: TP = 2.2% (+11.0% ROE @ 5x), SL = 2.5% (-12.5% ROE)
    # 4H: TP = 2.8% (+14.0% ROE @ 5x), SL = 2.8% (-14.0% ROE)
    tf_params = {
        "1h": {"tp": 0.022, "sl": 0.025, "max_hold": 24},
        "4h": {"tp": 0.028, "sl": 0.028, "max_hold": 24}
    }

    extreme_trades = []
    decisional_trades = []

    for tf in ["1h", "4h"]:
        tp_pct = tf_params[tf]["tp"]
        sl_pct = tf_params[tf]["sl"]
        max_hold = tf_params[tf]["max_hold"]

        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                # 15-bar local low
                swing_low = candles[i]["low"]
                if swing_low != min(c["low"] for c in candles[i-15:i+1]): continue

                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx <= i + 3: continue

                total_gain = (max_high - swing_low) / swing_low
                if total_gain < 0.045: continue

                # Inducement low
                idm_low = candles[high_idx - 1]["low"]

                # Decisional OB (Largest candle base in 30-70% zone with FVG)
                best_mid = -1
                max_bg = 0.0
                for mid in range(i+1, high_idx):
                    bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                    fib = (candles[mid]["low"] - swing_low) / (max_high - swing_low)
                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                        max_bg = bg
                        best_mid = mid

                dec_top, dec_bot = None, None
                has_dec_fvg = False
                if best_mid != -1:
                    dec_c = candles[best_mid - 1]
                    dec_top = max(dec_c["open"], dec_c["close"])
                    dec_bot = dec_c["low"]
                    has_dec_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False

                # Extreme OB
                ext_c = candles[i]
                ext_top = max(ext_c["open"], ext_c["close"])
                ext_bot = ext_c["low"]
                has_ext_fvg = (candles[i+2]["low"] > candles[i]["high"]) if i+2 < n else False

                # Track Decisional
                if dec_top and dec_bot and has_dec_fvg:
                    for t in range(high_idx + 1, min(high_idx + 35, n)):
                        if candles[t]["low"] <= dec_top:
                            tap_c = candles[t]
                            # Check IDM Sweep
                            swept_idm = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                            c_range = tap_c["high"] - tap_c["low"]
                            lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                            wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                            dec_mt = (dec_top + dec_bot) / 2.0

                            if swept_idm and wick_ratio >= 0.18 and tap_c["close"] >= dec_mt:
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
                                decisional_trades.append({
                                    "sym": sym, "tf": tf, "time": tap_c["time"],
                                    "res": t_res, "gross": gross, "bars": bars,
                                    "type": "DECISIONAL"
                                })
                            break

                # Track Extreme
                if ext_top and ext_bot and has_ext_fvg:
                    for t in range(high_idx + 1, min(high_idx + 45, n)):
                        if candles[t]["low"] <= ext_top:
                            tap_c = candles[t]
                            c_range = tap_c["high"] - tap_c["low"]
                            lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                            wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                            ext_mt = (ext_top + ext_bot) / 2.0

                            if wick_ratio >= 0.18 and tap_c["close"] >= ext_mt:
                                entry_p = ext_top
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
                                extreme_trades.append({
                                    "sym": sym, "tf": tf, "time": tap_c["time"],
                                    "res": t_res, "gross": gross, "bars": bars,
                                    "type": "EXTREME"
                                })
                            break

    models = [
        ("MODEL 1: ONLY EXTREME OB (Anchor Reversals)", extreme_trades),
        ("MODEL 2: ONLY ENHANCED DECISIONAL OB (Velocity Engine)", decisional_trades),
        ("MODEL 3: DUAL-ENGINE (Extreme Anchor + Decisional Scalper)", extreme_trades + decisional_trades)
    ]

    for model_name, trade_list in models:
        trade_list.sort(key=lambda x: x["time"])
        tot = len(trade_list)
        wins = sum(1 for t in trade_list if t["res"] == "WIN")
        losses = tot - wins
        wr = (wins / tot * 100) if tot else 0
        avg_bars = np.mean([t["bars"] for t in trade_list]) if trade_list else 0

        cap = 50.0
        vault = 0.0
        max_c = 50.0
        max_dd = 0.0
        hit_1000_idx = None
        hit_1000_date = None

        for idx, t in enumerate(trade_list, 1):
            pos = cap * 5.0
            net_ret = t["gross"] - 0.0014 # fees + slippage
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

        print(f"\n==========================================================================================")
        print(f" 🎯 {model_name}")
        print(f"==========================================================================================")
        print(f" Total Setups in 1 Year:       {tot} trades (Avg {tot/52:.1f} trades/week)")
        print(f" Win Rate:                     {wins}/{tot} ({wr:.2f}%)")
        print(f" Average Hold Time:            {avg_bars:.1f} bars (~{avg_bars*2:.1f} hours)")
        print(f" 🏁 $1,000 Reached At:          Trade #{hit_1000_idx} (Date: {hit_1000_date})")
        print(f" Final Trading Capital:        ${cap:,.2f} USDT")
        print(f" Secured Profit Vault:         ${vault:,.2f} USDT")
        print(f" Total Net Wealth (1 Year):    ${cap + vault:,.2f} USDT")
        print(f" Max Portfolio Drawdown:       {max_dd:.2f}%")

if __name__ == "__main__":
    run_decisional_compounding_audit()
