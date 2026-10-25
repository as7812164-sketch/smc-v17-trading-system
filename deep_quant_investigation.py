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

def run_deep_quant_investigation():
    print("=" * 95)
    print(" 🔬 LEAD QUANT INVESTIGATION: THE 3 CRITICAL PILLARS TO ELEVATE STRATEGY TO 82%+")
    print(" 1. MAE / MFE Analysis (How deep do winners dip? How high do they run?)")
    print(" 2. 1-Year Coin-by-Coin Leaderboard (God-Tier Champions vs Toxic Underperformers)")
    print(" 3. Session & Hourly Liquidity Filter (London vs NY vs Asian Dead Zone)")
    print("=" * 95)

    all_data = {"1h": {}, "4h": {}}
    for sym in APPROVED_COINS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    all_signals = []

    for tf in ["1h", "4h"]:
        tp_pct = 0.022 if tf == "1h" else 0.028
        sl_pct = 0.025 if tf == "1h" else 0.028
        max_hold = 24

        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                # Bullish
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.045:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + 35, n)):
                                        if candles[t]["low"] <= dec_top * 0.9995:
                                            tap_c = candles[t]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            c_range = tap_c["high"] - tap_c["low"]
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                sl_p = entry * (1.0 - sl_pct)
                                                
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                # Track MAE & MFE
                                                max_adverse = 0.0
                                                max_favorable = 0.0
                                                
                                                for m in range(t, min(t + max_hold, n)):
                                                    bar = candles[m]
                                                    dip = (entry - bar["low"]) / entry
                                                    run = (bar["high"] - entry) / entry
                                                    if dip > max_adverse: max_adverse = dip
                                                    if run > max_favorable: max_favorable = run
                                                    
                                                    if bar["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = bar["time"]; break
                                                    if bar["close"] <= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = bar["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                    
                                                all_signals.append({
                                                    "sym": sym, "tf": tf, "side": "LONG", "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit_p": exit_p,
                                                    "gross": (exit_p - entry) / entry, "res": res,
                                                    "mae": max_adverse, "mfe": max_favorable
                                                })
                                            break

                # Bearish
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.045:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + 35, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            c_range = tap_c["high"] - tap_c["low"]
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                sl_p = entry * (1.0 + sl_pct)
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                
                                                max_adverse = 0.0
                                                max_favorable = 0.0
                                                for m in range(t, min(t + max_hold, n)):
                                                    bar = candles[m]
                                                    dip = (bar["high"] - entry) / entry
                                                    run = (entry - bar["low"]) / entry
                                                    if dip > max_adverse: max_adverse = dip
                                                    if run > max_favorable: max_favorable = run
                                                    
                                                    if bar["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = bar["time"]; break
                                                    if bar["close"] >= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = bar["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                    
                                                all_signals.append({
                                                    "sym": sym, "tf": tf, "side": "SHORT", "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit_p": exit_p,
                                                    "gross": (entry - exit_p) / entry, "res": res,
                                                    "mae": max_adverse, "mfe": max_favorable
                                                })
                                            break

    all_signals.sort(key=lambda x: x["time"])

    # 1. Realistic 1-Trade Sequential Queue
    executed_trades = []
    active_exit = 0
    for s in all_signals:
        if s["time"] >= active_exit:
            executed_trades.append(s)
            active_exit = s["exit_time"]

    print(f"\n✅ Total Sequential Trades Analyzed: {len(executed_trades)}")

    # -------------------------------------------------------------------------
    # PILLAR 1: MAE / MFE ANALYSIS
    # -------------------------------------------------------------------------
    winning_trades = [t for t in executed_trades if t["res"] == "WIN"]
    maes = [t["mae"] * 100 for t in winning_trades]
    mfes = [t["mfe"] * 100 for t in winning_trades]

    print("\n" + "=" * 90)
    print(" 📊 PILLAR 1: MAE / MFE FORENSIC ANALYSIS (WINNING TRADES ANATOMY)")
    print("=" * 90)
    print(f" Median Drawdown Before Winning (Median MAE):  {np.median(maes):.2f}%")
    print(f" 75% of Winning Trades Never Dips More Than:    {np.percentile(maes, 75):.2f}%")
    print(f" 90% of Winning Trades Never Dips More Than:    {np.percentile(maes, 90):.2f}%")
    print(f" Median Maximum Run Beyond TP (Median MFE):    {np.median(mfes):.2f}%")
    print(f" Top 25% of Trades Surged Beyond:               {np.percentile(mfes, 75):.2f}%")

    # -------------------------------------------------------------------------
    # PILLAR 2: COIN-BY-COIN 1-YEAR PERFORMANCE LEADERBOARD
    # -------------------------------------------------------------------------
    coin_stats = {}
    for t in executed_trades:
        sym = t["sym"]
        if sym not in coin_stats:
            coin_stats[sym] = {"trades": 0, "wins": 0, "net_pnl": 0.0}
        coin_stats[sym]["trades"] += 1
        if t["res"] == "WIN": coin_stats[sym]["wins"] += 1
        coin_stats[sym]["net_pnl"] += t["gross"]

    ranked_coins = []
    for sym, st in coin_stats.items():
        wr = (st["wins"] / st["trades"] * 100) if st["trades"] else 0
        ranked_coins.append((sym, st["trades"], st["wins"], wr, st["net_pnl"]))

    ranked_coins.sort(key=lambda x: (x[3], x[4]), reverse=True)

    print("\n" + "=" * 90)
    print(" 🏆 PILLAR 2: 1-YEAR COIN LEADERBOARD (TOP CHAMPIONS vs UNDERPERFORMERS)")
    print("=" * 90)
    print(" Rank | Symbol     | Trades | Wins | Win Rate | Total Net Move Gain")
    print("------|------------|--------|------|----------|--------------------")
    for r, (sym, tr, w, wr, pnl) in enumerate(ranked_coins[:12], 1):
        print(f" #{r:2d}  | {sym:10s} | {tr:4d}   | {w:4d} |  {wr:5.1f}%  | +{pnl*100:6.1f}%")
    print(" ...")
    print(" BOTTOM 5 UNDERPERFORMERS:")
    for r, (sym, tr, w, wr, pnl) in enumerate(ranked_coins[-5:], len(ranked_coins)-4):
        print(f" #{r:2d}  | {sym:10s} | {tr:4d}   | {w:4d} |  {wr:5.1f}%  | +{pnl*100:6.1f}%")

    # -------------------------------------------------------------------------
    # PILLAR 3: SESSION BREAKDOWN (UTC HOURS)
    # -------------------------------------------------------------------------
    # Asian: 00:00 - 07:00 UTC
    # London: 07:00 - 13:00 UTC
    # New York: 13:00 - 20:00 UTC
    # Off-Hours: 20:00 - 00:00 UTC

    session_stats = {"ASIAN (00-07 UTC)": [0, 0], "LONDON (07-13 UTC)": [0, 0], "NEW YORK (13-20 UTC)": [0, 0], "OFF-HOURS (20-24 UTC)": [0, 0]}
    for t in executed_trades:
        utc_hour = time.gmtime(t["time"]/1000).tm_hour
        if 0 <= utc_hour < 7: s_name = "ASIAN (00-07 UTC)"
        elif 7 <= utc_hour < 13: s_name = "LONDON (07-13 UTC)"
        elif 13 <= utc_hour < 20: s_name = "NEW YORK (13-20 UTC)"
        else: s_name = "OFF-HOURS (20-24 UTC)"

        if t["res"] == "WIN": session_stats[s_name][0] += 1
        else: session_stats[s_name][1] += 1

    print("\n" + "=" * 90)
    print(" ⏰ PILLAR 3: GLOBAL SESSION PERFORMANCE AUDIT")
    print("=" * 90)
    for s_name, (sw, sl) in session_stats.items():
        stot = sw + sl
        swr = (sw / stot * 100) if stot else 0
        print(f"  • {s_name:24s}: {stot:3d} Trades | {sw:3d} Wins / {sl:2d} Losses | Win Rate: {swr:5.2f}%")

if __name__ == "__main__":
    run_deep_quant_investigation()
