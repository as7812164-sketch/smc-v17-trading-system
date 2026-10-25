import os
import sys
import json
import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TOP_22_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT", "NEARUSDT", "OPUSDT",
    "ARBUSDT", "APTUSDT", "TIAUSDT", "INJUSDT", "FETUSDT", "AAVEUSDT",
    "ALGOUSDT", "DOTUSDT", "MATICUSDT", "LDOUSDT"
]

def load_candles(sym, tf):
    fn = f"historical_data/{sym}_{tf}.json"
    if not os.path.exists(fn):
        return []
    with open(fn, "r") as fp:
        raw = json.load(fp)
    return [
        {
            "time": c.get("time") or c.get("open_time"),
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
            "volume": float(c.get("volume", 0))
        } for c in raw
    ]

def calc_ema(prices, period=50):
    if len(prices) < period:
        return [prices[-1]] * len(prices)
    emas = []
    k = 2.0 / (period + 1.0)
    ema = sum(prices[:period]) / period
    for i in range(len(prices)):
        if i < period:
            emas.append(ema)
        else:
            ema = prices[i] * k + ema * (1 - k)
            emas.append(ema)
    return emas

def run_hermes35_single_tier_audit():
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_closes = [c["close"] for c in btc_4h]
    btc_ema50 = calc_ema(btc_closes, 50)
    btc_map_4h = {btc_4h[i]["time"]: (btc_closes[i] >= btc_ema50[i]) for i in range(len(btc_4h))}

    results = {
        "4h": {"trades": [], "wins": 0, "losses": 0, "breakeven": 0},
        "1h": {"trades": [], "wins": 0, "losses": 0, "breakeven": 0}
    }

    tp_spot_pct = 0.1220 / 5.0   # +2.44%
    sl_spot_pct = 0.1200 / 5.0   # -2.40%
    be_spot_pct = 0.0150         # +1.50% move triggers BE

    for tf in ["4h", "1h"]:
        bars_month = 180 if tf == "4h" else 720
        min_disp = 0.050 if tf == "4h" else 0.045

        for sym in TOP_22_SYMBOLS:
            if sym == "BTCUSDT":
                continue  # BTC is the anchor filter
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < bars_month:
                continue

            c_month = candles[-bars_month:]
            nm = len(c_month)
            seen_ob = set()

            for i in range(10, nm - 20):
                # -------------------------------------------------------------
                # 1. BULLISH EXTREME OB (LONG SETUP)
                # -------------------------------------------------------------
                w_lows = [x["low"] for x in c_month[i-8:i+1]]
                if c_month[i]["low"] == min(w_lows) and c_month[i]["close"] < c_month[i]["open"]:
                    if i in seen_ob:
                        continue

                    # Judas sweep
                    p_low = min(x["low"] for x in c_month[max(0, i-5):i]) if i >= 5 else c_month[i]["low"]
                    is_judas = c_month[i]["low"] <= p_low

                    # FVG check (3-bar void)
                    has_fvg = (i + 2 < nm) and (c_month[i+2]["low"] > c_month[i]["high"])

                    # Displacement pump
                    sub = c_month[i:min(i+14, nm)]
                    highs = [x["high"] for x in sub]
                    max_h = max(highs)
                    h_idx = i + highs.index(max_h)
                    gain = (max_h - c_month[i]["low"]) / c_month[i]["low"]

                    # King BTC Trend Filter
                    t_stamp = c_month[i]["time"]
                    # Find closest BTC 4h candle
                    btc_bullish = True
                    if btc_map_4h:
                        closest_btc_t = min(btc_map_4h.keys(), key=lambda t: abs(t - t_stamp))
                        btc_bullish = btc_map_4h.get(closest_btc_t, True)

                    if gain >= min_disp and has_fvg and is_judas and btc_bullish and h_idx > i + 2:
                        seen_ob.add(i)
                        ob_high = c_month[i]["high"]
                        ob_low = c_month[i]["low"]
                        mt_50 = (ob_high + ob_low) / 2.0

                        tp_p = round(mt_50 * (1.0 + tp_spot_pct), 6)
                        sl_p = round(mt_50 * (1.0 - sl_spot_pct), 6)

                        # Look for 1st Tap at 50% MT
                        for t in range(h_idx + 1, min(h_idx + 30, nm)):
                            tap_bar = c_month[t]
                            tapped_mt = tap_bar["low"] <= mt_50 and tap_bar["low"] > sl_p
                            body_held = tap_bar["close"] >= mt_50  # 50% MT HOLD RULE!

                            if tapped_mt and body_held:
                                entry_time_str = datetime.datetime.fromtimestamp(tap_bar["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                outcome = "PENDING"
                                exit_time_str = ""
                                max_fav = 0.0

                                for k in range(t + 1, min(t + 35, nm)):
                                    bar_k = c_month[k]
                                    fav = (bar_k["high"] - mt_50) / mt_50
                                    if fav > max_fav:
                                        max_fav = fav

                                    # Target Hit
                                    if bar_k["high"] >= tp_p:
                                        outcome = "WIN"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                    # Breakeven Armor Lock
                                    elif max_fav >= be_spot_pct and bar_k["low"] <= mt_50:
                                        outcome = "BREAKEVEN"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                    # Hard SL Hit
                                    elif bar_k["low"] <= sl_p:
                                        outcome = "LOSS"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break

                                if outcome == "WIN":
                                    results[tf]["wins"] += 1
                                elif outcome == "LOSS":
                                    results[tf]["losses"] += 1
                                elif outcome == "BREAKEVEN":
                                    results[tf]["breakeven"] += 1

                                results[tf]["trades"].append({
                                    "symbol": sym, "side": "LONG", "entry": mt_50, "tp": tp_p, "sl": sl_p,
                                    "entry_time": entry_time_str, "exit_time": exit_time_str, "outcome": outcome, "disp": round(gain*100, 1)
                                })
                                break

                # -------------------------------------------------------------
                # 2. BEARISH EXTREME OB (SHORT SETUP)
                # -------------------------------------------------------------
                w_highs = [x["high"] for x in c_month[i-8:i+1]]
                if c_month[i]["high"] == max(w_highs) and c_month[i]["close"] > c_month[i]["open"]:
                    if i in seen_ob:
                        continue

                    p_high = max(x["high"] for x in c_month[max(0, i-5):i]) if i >= 5 else c_month[i]["high"]
                    is_judas = c_month[i]["high"] >= p_high

                    has_fvg = (i + 2 < nm) and (c_month[i+2]["high"] < c_month[i]["low"])

                    sub = c_month[i:min(i+14, nm)]
                    lows = [x["low"] for x in sub]
                    min_l = min(lows)
                    l_idx = i + lows.index(min_l)
                    drop = (c_month[i]["high"] - min_l) / c_month[i]["high"]

                    t_stamp = c_month[i]["time"]
                    btc_bearish = True
                    if btc_map_4h:
                        closest_btc_t = min(btc_map_4h.keys(), key=lambda t: abs(t - t_stamp))
                        btc_bearish = not btc_map_4h.get(closest_btc_t, True)

                    if drop >= min_disp and has_fvg and is_judas and btc_bearish and l_idx > i + 2:
                        seen_ob.add(i)
                        ob_high = c_month[i]["high"]
                        ob_low = c_month[i]["low"]
                        mt_50 = (ob_high + ob_low) / 2.0

                        tp_p = round(mt_50 * (1.0 - tp_spot_pct), 6)
                        sl_p = round(mt_50 * (1.0 + sl_spot_pct), 6)

                        for t in range(l_idx + 1, min(l_idx + 30, nm)):
                            tap_bar = c_month[t]
                            tapped_mt = tap_bar["high"] >= mt_50 and tap_bar["high"] < sl_p
                            body_held = tap_bar["close"] <= mt_50  # 50% MT HOLD RULE!

                            if tapped_mt and body_held:
                                entry_time_str = datetime.datetime.fromtimestamp(tap_bar["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                outcome = "PENDING"
                                exit_time_str = ""
                                max_fav = 0.0

                                for k in range(t + 1, min(t + 35, nm)):
                                    bar_k = c_month[k]
                                    fav = (mt_50 - bar_k["low"]) / mt_50
                                    if fav > max_fav:
                                        max_fav = fav

                                    if bar_k["low"] <= tp_p:
                                        outcome = "WIN"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                    elif max_fav >= be_spot_pct and bar_k["high"] >= mt_50:
                                        outcome = "BREAKEVEN"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break
                                    elif bar_k["high"] >= sl_p:
                                        outcome = "LOSS"
                                        exit_time_str = datetime.datetime.fromtimestamp(bar_k["time"]/1000 + 19800, tz=datetime.timezone.utc).strftime("%d-%b %H:%M")
                                        break

                                if outcome == "WIN":
                                    results[tf]["wins"] += 1
                                elif outcome == "LOSS":
                                    results[tf]["losses"] += 1
                                elif outcome == "BREAKEVEN":
                                    results[tf]["breakeven"] += 1

                                results[tf]["trades"].append({
                                    "symbol": sym, "side": "SHORT", "entry": mt_50, "tp": tp_p, "sl": sl_p,
                                    "entry_time": entry_time_str, "exit_time": exit_time_str, "outcome": outcome, "disp": round(drop*100, 1)
                                })
                                break

    return results

if __name__ == "__main__":
    res = run_hermes35_single_tier_audit()
    with open("hermes35_single_tier_audit.json", "w") as fp:
        json.dump(res, fp, indent=2)

    print("================================================================================")
    print("🏆 HERMES 3.5 SINGLE TIER (PURE TIER 1): 1-MONTH (30-DAY) AUDIT RESULTS")
    print("================================================================================")
    for tf in ["4h", "1h"]:
        tot = len(res[tf]["trades"])
        w = res[tf]["wins"]
        l = res[tf]["losses"]
        be = res[tf]["breakeven"]
        decided = w + l
        wr = (w / decided * 100) if decided > 0 else 0
        cap_pres = ((w + be) / tot * 100) if tot > 0 else 0
        print(f"\n[{tf.upper()} TIMEFRAME RESULTS]:")
        print(f"  Total Setups Found: {tot}")
        print(f"  Take Profit Hits (Wins): {w} 🎯")
        print(f"  Stop Loss Hits (Losses): {l} ❌")
        print(f"  Breakeven Exits ($0 Loss): {be} 🛡️")
        print(f"  Decided Win Rate (Wins vs Losses): {wr:.2f}%")
        print(f"  Capital Preservation Rate (Zero-Loss): {cap_pres:.2f}%")
        print("  Sample Trades:")
        for t in res[tf]["trades"][:4]:
            print(f"    • {t['symbol']} {t['side']} | Entry: {t['entry']} | TP: {t['tp']} | Result: {t['outcome']} ({t['entry_time']} -> {t['exit_time']})")
