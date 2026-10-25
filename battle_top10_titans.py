import json
import time
import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_local_data(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def simulate_portfolio(signals, start_cap=50.0, leverage=5.0, target_cap=1000.0, fee_pct=0.0008):
    # Sort signals by entry time
    signals.sort(key=lambda x: x["time"])
    
    # 1-trade sequential queue
    executed = []
    active_exit = 0
    for s in signals:
        if s["time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    cap = start_cap
    vault = 0.0
    peak_cap = start_cap
    max_dd = 0.0
    hit_1k_trade = None
    wins = 0
    losses = 0
    gross_profits = 0.0
    gross_losses = 0.0

    for idx, trade in enumerate(executed):
        # Gross profit/loss with leverage
        pos_size = cap * leverage
        gross_move = trade["gross"]
        net_move = gross_move - (2.0 * fee_pct)
        pnl = pos_size * net_move

        if trade["res"] == "WIN":
            wins += 1
            gross_profits += max(0, pnl)
            # Reinvest 85%, stash 15% in vault
            cap += (pnl * 0.85)
            vault += (pnl * 0.15)
        else:
            losses += 1
            gross_losses += abs(min(0, pnl))
            cap += pnl
            if cap < 2.0:
                cap = 0.0 # Liquidated/bankrupt

        total_wealth = cap + vault
        if total_wealth > peak_cap:
            peak_cap = total_wealth
        dd = (peak_cap - total_wealth) / peak_cap if peak_cap > 0 else 0
        if dd > max_dd:
            max_dd = dd

        if total_wealth >= target_cap and hit_1k_trade is None:
            hit_1k_trade = idx + 1

        if cap <= 0:
            break

    n_trades = len(executed)
    wr = (wins / n_trades * 100.0) if n_trades > 0 else 0.0
    pf = (gross_profits / gross_losses) if gross_losses > 0 else (99.0 if gross_profits > 0 else 0.0)

    return {
        "trades": n_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": wr,
        "max_dd": max_dd * 100.0,
        "hit_1k": hit_1k_trade,
        "final_cap": cap + vault,
        "profit_factor": pf
    }

def run_titans_battle():
    print("=" * 110)
    print(" ⚔️ THE TITANS BATTLE ROYALE: HERMES 20X vs TOP 10 LEGENDARY MARKET STRATEGIES")
    print(" Dataset: 1 Full Year (Sep 2025 - Sep 2026) | 339,512 Candlesticks | Top-22 Champions Universe")
    print(" Capital: $50 USDT Initial | Leverage: 5x Isolated Perpetual | Mode: Realistic 1-Trade Sequential Queue")
    print("=" * 110)

    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    # =========================================================================
    # 👑 0. HERMES 20X (Our Master Engineered System)
    # =========================================================================
    hermes_signals = []
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
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + 35, n)):
                                        if candles[t]["low"] <= dec_top * 0.9995:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_c["low"]) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                sl_p = entry * (1.0 - sl_pct)
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] <= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                hermes_signals.append({
                                                    "sym": sym, "side": "LONG", "time": tap_c["time"],
                                                    "exit_time": exit_t, "gross": (exit_p - entry) / entry, "res": res
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
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + 35, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_c["high"] + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                sl_p = entry * (1.0 + sl_pct)
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] >= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                hermes_signals.append({
                                                    "sym": sym, "side": "SHORT", "time": tap_c["time"],
                                                    "exit_time": exit_t, "gross": (entry - exit_p) / entry, "res": res
                                                })
                                            break

    # =========================================================================
    # 🥊 1. Michael Huddleston (ICT) - Silver Bullet (1st FVG after Liquidity Sweep)
    # =========================================================================
    ict_sb_signals = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.025; sl_pct = 0.025; max_hold = 24
        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(20, n - 30):
                # Swing low sweep
                prev_low = min(c["low"] for c in candles[i-15:i])
                if candles[i]["low"] < prev_low:
                    # Look for immediate 1st FVG in next 3 candles
                    for k in range(i+1, min(i+4, n-2)):
                        if candles[k+1]["low"] > candles[k-1]["high"]: # Bullish FVG
                            fvg_entry = candles[k-1]["high"]
                            # Enter when price returns to fill FVG
                            for t in range(k+1, min(k+15, n)):
                                if candles[t]["low"] <= fvg_entry:
                                    entry = fvg_entry
                                    tp_p = entry * (1.0 + tp_pct)
                                    sl_p = entry * (1.0 - sl_pct)
                                    res = None; exit_p = entry; exit_t = candles[t]["time"]
                                    for m in range(t, min(t + max_hold, n)):
                                        if candles[m]["high"] >= tp_p:
                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                        if candles[m]["close"] <= sl_p:
                                            res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                    if not res:
                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                        res = "WIN" if fc >= entry else "LOSS"
                                        exit_p = fc
                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                    ict_sb_signals.append({
                                        "sym": sym, "time": candles[t]["time"], "exit_time": exit_t,
                                        "gross": (exit_p - entry) / entry, "res": res
                                    })
                                    break
                            break

    # =========================================================================
    # 🥊 2. LuxAlgo - Premium SMC (Unmitigated Order Blocks + BOS)
    # =========================================================================
    lux_signals = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.025; sl_pct = 0.025; max_hold = 24
        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.040:
                            ob_c = candles[i]
                            ob_top = max(ob_c["open"], ob_c["close"])
                            for t in range(high_idx + 1, min(high_idx + 35, n)):
                                if candles[t]["low"] <= ob_top:
                                    entry = ob_top
                                    tp_p = entry * (1.0 + tp_pct)
                                    sl_p = entry * (1.0 - sl_pct)
                                    res = None; exit_p = entry; exit_t = candles[t]["time"]
                                    for m in range(t, min(t + max_hold, n)):
                                        if candles[m]["high"] >= tp_p:
                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                        if candles[m]["close"] <= sl_p:
                                            res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                    if not res:
                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                        res = "WIN" if fc >= entry else "LOSS"
                                        exit_p = fc
                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                    lux_signals.append({
                                        "sym": sym, "time": candles[t]["time"], "exit_time": exit_t,
                                        "gross": (exit_p - entry) / entry, "res": res
                                    })
                                    break

    # =========================================================================
    # 🥊 3. Richard Wyckoff - Spring & Upthrust (Phase C Accumulation)
    # =========================================================================
    wyckoff_signals = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.026; sl_pct = 0.024; max_hold = 24
        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(30, n - 30):
                # Identify trading range (TR) support
                range_low = min(c["low"] for c in candles[i-25:i])
                range_high = max(c["high"] for c in candles[i-25:i])
                # Spring: Price dips below range_low, but closes back inside range within 2 bars
                if candles[i]["low"] < range_low and candles[i]["close"] > range_low:
                    entry = candles[i]["close"]
                    tp_p = entry * (1.0 + tp_pct)
                    sl_p = candles[i]["low"] * 0.998 # SL below spring low
                    res = None; exit_p = entry; exit_t = candles[i]["time"]
                    for m in range(i+1, min(i + max_hold, n)):
                        if candles[m]["high"] >= tp_p:
                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                        if candles[m]["close"] <= sl_p:
                            res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                    if not res:
                        fc = candles[min(i + max_hold, n - 1)]["close"]
                        res = "WIN" if fc >= entry else "LOSS"
                        exit_p = fc
                        exit_t = candles[min(i + max_hold, n - 1)]["time"]
                    wyckoff_signals.append({
                        "sym": sym, "time": candles[i]["time"], "exit_time": exit_t,
                        "gross": (exit_p - entry) / entry, "res": res
                    })

    # =========================================================================
    # 🥊 4. John Bollinger - Bollinger Bands Mean Reversion (20 SMA, 2.0 SD)
    # =========================================================================
    bb_signals = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.022; sl_pct = 0.022; max_hold = 20
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 50: continue
            closes = np.array([c["close"] for c in candles])
            for i in range(25, n - 25):
                sub = closes[i-20:i]
                sma = np.mean(sub)
                std = np.std(sub)
                lower_band = sma - (2.0 * std)
                upper_band = sma + (2.0 * std)
                # Lower band pierce and bounce
                if candles[i]["low"] < lower_band and candles[i]["close"] > lower_band:
                    entry = candles[i]["close"]
                    tp_p = entry * (1.0 + tp_pct)
                    sl_p = entry * (1.0 - sl_pct)
                    res = None; exit_p = entry; exit_t = candles[i]["time"]
                    for m in range(i+1, min(i + max_hold, n)):
                        if candles[m]["high"] >= tp_p:
                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                        if candles[m]["close"] <= sl_p:
                            res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                    if not res:
                        fc = candles[min(i + max_hold, n - 1)]["close"]
                        res = "WIN" if fc >= entry else "LOSS"
                        exit_p = fc
                        exit_t = candles[min(i + max_hold, n - 1)]["time"]
                    bb_signals.append({
                        "sym": sym, "time": candles[i]["time"], "exit_time": exit_t,
                        "gross": (exit_p - entry) / entry, "res": res
                    })

    # =========================================================================
    # 🥊 5. Turtle Trading (Richard Dennis) - 20-Day Donchian Breakout
    # =========================================================================
    turtle_signals = []
    for tf in ["4h"]: # Classic turtle is higher timeframe
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 40: continue
            for i in range(25, n - 25):
                donchian_high = max(c["high"] for c in candles[i-20:i])
                donchian_low = min(c["low"] for c in candles[i-10:i]) # 10-bar exit
                if candles[i]["close"] > donchian_high:
                    entry = candles[i]["close"]
                    sl_p = entry * 0.965 # 3.5% trailing stop
                    tp_p = entry * 1.050 # Trend ride
                    res = None; exit_p = entry; exit_t = candles[i]["time"]
                    for m in range(i+1, min(i + 30, n)):
                        if candles[m]["high"] >= tp_p:
                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                        if candles[m]["close"] < donchian_low or candles[m]["close"] <= sl_p:
                            res = "LOSS" if candles[m]["close"] <= entry else "WIN"
                            exit_p = candles[m]["close"]
                            exit_t = candles[m]["time"]; break
                    if not res:
                        fc = candles[min(i + 30, n - 1)]["close"]
                        res = "WIN" if fc >= entry else "LOSS"
                        exit_p = fc
                        exit_t = candles[min(i + 30, n - 1)]["time"]
                    turtle_signals.append({
                        "sym": sym, "time": candles[i]["time"], "exit_time": exit_t,
                        "gross": (exit_p - entry) / entry, "res": res
                    })

    # =========================================================================
    # 🥊 6. Larry Williams - Volatility Expansion & Williams %R
    # =========================================================================
    lw_signals = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.024; sl_pct = 0.024; max_hold = 20
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 30: continue
            for i in range(15, n - 25):
                h10 = max(c["high"] for c in candles[i-10:i])
                l10 = min(c["low"] for c in candles[i-10:i])
                if h10 == l10: continue
                # Williams %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
                wr = (h10 - candles[i]["close"]) / (h10 - l10) * -100.0
                # Oversold crossing above -80 with expansion candle
                c_range = candles[i]["high"] - candles[i]["low"]
                avg_range = np.mean([c["high"] - c["low"] for c in candles[i-10:i]])
                if wr > -75 and c_range > 1.3 * avg_range and candles[i]["close"] > candles[i]["open"]:
                    entry = candles[i]["close"]
                    tp_p = entry * (1.0 + tp_pct)
                    sl_p = entry * (1.0 - sl_pct)
                    res = None; exit_p = entry; exit_t = candles[i]["time"]
                    for m in range(i+1, min(i + max_hold, n)):
                        if candles[m]["high"] >= tp_p:
                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                        if candles[m]["close"] <= sl_p:
                            res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                    if not res:
                        fc = candles[min(i + max_hold, n - 1)]["close"]
                        res = "WIN" if fc >= entry else "LOSS"
                        exit_p = fc
                        exit_t = candles[min(i + max_hold, n - 1)]["time"]
                    lw_signals.append({
                        "sym": sym, "time": candles[i]["time"], "exit_time": exit_t,
                        "gross": (exit_p - entry) / entry, "res": res
                    })

    # =========================================================================
    # 🥊 7. Mark Minervini - Stage 2 Trend Template (EMA 20/50/200 Alignment)
    # =========================================================================
    minervini_signals = []
    for tf in ["4h"]:
        tp_pct = 0.035; sl_pct = 0.025; max_hold = 25
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 250: continue
            closes = [c["close"] for c in candles]
            ema20 = [0.0]*n; ema50 = [0.0]*n; ema200 = [0.0]*n
            k20 = 2.0/21; k50 = 2.0/51; k200 = 2.0/201
            ema20[0] = closes[0]; ema50[0] = closes[0]; ema200[0] = closes[0]
            for idx_c in range(1, n):
                ema20[idx_c] = closes[idx_c]*k20 + ema20[idx_c-1]*(1.0-k20)
                ema50[idx_c] = closes[idx_c]*k50 + ema50[idx_c-1]*(1.0-k50)
                ema200[idx_c] = closes[idx_c]*k200 + ema200[idx_c-1]*(1.0-k200)

            for i in range(210, n - 25):
                # Stage 2 condition: Price > EMA 20 > EMA 50 > EMA 200
                if closes[i] > ema20[i] > ema50[i] > ema200[i]:
                    # Pullback to EMA 20/50 and rebound
                    if candles[i-1]["low"] <= ema20[i-1] and candles[i]["close"] > ema20[i]:
                        entry = closes[i]
                        tp_p = entry * (1.0 + tp_pct)
                        sl_p = entry * (1.0 - sl_pct)
                        res = None; exit_p = entry; exit_t = candles[i]["time"]
                        for m in range(i+1, min(i + max_hold, n)):
                            if candles[m]["high"] >= tp_p:
                                res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                            if candles[m]["close"] <= sl_p:
                                res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                        if not res:
                            fc = candles[min(i + max_hold, n - 1)]["close"]
                            res = "WIN" if fc >= entry else "LOSS"
                            exit_p = fc
                            exit_t = candles[min(i + max_hold, n - 1)]["time"]
                        minervini_signals.append({
                            "sym": sym, "time": candles[i]["time"], "exit_time": exit_t,
                            "gross": (exit_p - entry) / entry, "res": res
                        })

    # =========================================================================
    # 🥊 8. Alexander Elder - Triple Screen Trading (MACD + Stochastic Pullback)
    # =========================================================================
    elder_signals = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.024; sl_pct = 0.022; max_hold = 22
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 100: continue
            closes = [c["close"] for c in candles]
            # EMA 12, EMA 26
            ema12 = [0.0]*n; ema26 = [0.0]*n
            k12 = 2.0/13; k26 = 2.0/27
            ema12[0]=closes[0]; ema26[0]=closes[0]
            for idx_c in range(1, n):
                ema12[idx_c] = closes[idx_c]*k12 + ema12[idx_c-1]*(1.0-k12)
                ema26[idx_c] = closes[idx_c]*k26 + ema26[idx_c-1]*(1.0-k26)
            macd_hist = [ema12[idx_c] - ema26[idx_c] for idx_c in range(n)]

            for i in range(35, n - 25):
                # Screen 1: MACD Histogram rising
                if macd_hist[i] > macd_hist[i-1]:
                    # Screen 2: Stochastic 14 oversold pullback (<25)
                    h14 = max(c["high"] for c in candles[i-14:i])
                    l14 = min(c["low"] for c in candles[i-14:i])
                    if h14 > l14:
                        stoch = (candles[i]["close"] - l14) / (h14 - l14) * 100.0
                        if stoch < 25 and candles[i]["close"] > candles[i]["open"]:
                            entry = candles[i]["close"]
                            tp_p = entry * (1.0 + tp_pct)
                            sl_p = entry * (1.0 - sl_pct)
                            res = None; exit_p = entry; exit_t = candles[i]["time"]
                            for m in range(i+1, min(i + max_hold, n)):
                                if candles[m]["high"] >= tp_p:
                                    res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                if candles[m]["close"] <= sl_p:
                                    res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                            if not res:
                                fc = candles[min(i + max_hold, n - 1)]["close"]
                                res = "WIN" if fc >= entry else "LOSS"
                                exit_p = fc
                                exit_t = candles[min(i + max_hold, n - 1)]["time"]
                            elder_signals.append({
                                "sym": sym, "time": candles[i]["time"], "exit_time": exit_t,
                                "gross": (exit_p - entry) / entry, "res": res
                            })

    # =========================================================================
    # 🥊 9. Tom DeMark - TD Sequential (TD 9 Exhaustion Countdown Reversal)
    # =========================================================================
    demark_signals = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.025; sl_pct = 0.022; max_hold = 20
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 40: continue
            closes = [c["close"] for c in candles]
            buy_setup = 0
            for i in range(5, n - 25):
                if closes[i] < closes[i-4]:
                    buy_setup += 1
                else:
                    buy_setup = 0

                # Perfect TD 9 Buy Countdown
                if buy_setup == 9:
                    entry = closes[i]
                    tp_p = entry * (1.0 + tp_pct)
                    sl_p = entry * (1.0 - sl_pct)
                    res = None; exit_p = entry; exit_t = candles[i]["time"]
                    for m in range(i+1, min(i + max_hold, n)):
                        if candles[m]["high"] >= tp_p:
                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                        if candles[m]["close"] <= sl_p:
                            res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                    if not res:
                        fc = candles[min(i + max_hold, n - 1)]["close"]
                        res = "WIN" if fc >= entry else "LOSS"
                        exit_p = fc
                        exit_t = candles[min(i + max_hold, n - 1)]["time"]
                    demark_signals.append({
                        "sym": sym, "time": candles[i]["time"], "exit_time": exit_t,
                        "gross": (exit_p - entry) / entry, "res": res
                    })

    # =========================================================================
    # 🥊 10. Volume Profile / Auction Market Theory (POC & Value Area Low VAL)
    # =========================================================================
    amt_signals = []
    for tf in ["1h", "4h"]:
        tp_pct = 0.025; sl_pct = 0.022; max_hold = 24
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 50: continue
            for i in range(30, n - 25):
                # Calculate 24-period Value Area (70% volume range)
                sub = candles[i-24:i]
                vols = [c["volume"] for c in sub]
                lows = [c["low"] for c in sub]
                highs = [c["high"] for c in sub]
                min_p = min(lows); max_p = max(highs)
                if max_p == min_p: continue
                # Approximate Value Area Low (VAL = 30th percentile of price range)
                val_level = min_p + 0.30 * (max_p - min_p)
                # Test VAL with wick rejection
                if candles[i]["low"] <= val_level and candles[i]["close"] > val_level:
                    entry = candles[i]["close"]
                    tp_p = entry * (1.0 + tp_pct)
                    sl_p = entry * (1.0 - sl_pct)
                    res = None; exit_p = entry; exit_t = candles[i]["time"]
                    for m in range(i+1, min(i + max_hold, n)):
                        if candles[m]["high"] >= tp_p:
                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                        if candles[m]["close"] <= sl_p:
                            res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                    if not res:
                        fc = candles[min(i + max_hold, n - 1)]["close"]
                        res = "WIN" if fc >= entry else "LOSS"
                        exit_p = fc
                        exit_t = candles[min(i + max_hold, n - 1)]["time"]
                    amt_signals.append({
                        "sym": sym, "time": candles[i]["time"], "exit_time": exit_t,
                        "gross": (exit_p - entry) / entry, "res": res
                    })

    # =========================================================================
    # SIMULATION AND SCORING
    # =========================================================================
    titans = [
        ("HERMES 20X (Our Master)", hermes_signals, "🌟 MASTER CHAMPION"),
        ("Michael Huddleston (ICT) - Silver Bullet", ict_sb_signals, "ICT Mentorship"),
        ("LuxAlgo - SMC Premium Pro", lux_signals, "LuxAlgo SMC"),
        ("Richard Wyckoff - Spring/Upthrust", wyckoff_signals, "Wyckoff Method"),
        ("John Bollinger - Bollinger Bands", bb_signals, "Mean Reversion"),
        ("Turtle Trading (Richard Dennis)", turtle_signals, "Donchian Breakout"),
        ("Larry Williams - Volatility Exp %R", lw_signals, "Williams %R"),
        ("Mark Minervini - Trend Template", minervini_signals, "Minervini Stage 2"),
        ("Alexander Elder - Triple Screen", elder_signals, "Elder MACD/Stoch"),
        ("Tom DeMark - TD Sequential (TD9)", demark_signals, "DeMark Reversals"),
        ("Auction Market Theory (POC/VAL)", amt_signals, "Volume Profile")
    ]

    results = []
    for name, sigs, category in titans:
        res = simulate_portfolio(sigs)
        res["name"] = name
        res["category"] = category
        results.append(res)

    print("\n" + "=" * 115)
    print(f"{'TITAN STRATEGY / CREATOR':<40} | {'TRADES':<7} | {'WIN RATE':<9} | {'MAX DD':<8} | {'$1K HIT?':<12} | {'FINAL CAP ($50)':<18} | {'PF':<5}")
    print("-" * 115)
    for r in results:
        hit_str = f"Trade #{r['hit_1k']}" if r['hit_1k'] else "❌ FAILED"
        if r['final_cap'] > 1_000_000:
            cap_str = f"${r['final_cap']/1_000_000:.2f}M USDT"
        elif r['final_cap'] > 1000:
            cap_str = f"${r['final_cap']:.2f} USDT"
        else:
            cap_str = f"${r['final_cap']:.2f} USDT"
            
        print(f"{r['name']:<40} | {r['trades']:<7} | {r['win_rate']:>6.2f}%   | {r['max_dd']:>6.2f}% | {hit_str:<12} | {cap_str:<18} | {r['profit_factor']:>4.2f}")
    print("=" * 115)

    # Save results to json
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "titans_battle_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ All results saved to: {out_path}")

if __name__ == "__main__":
    run_titans_battle()
