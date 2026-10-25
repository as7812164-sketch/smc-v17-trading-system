import os
import sys
import glob
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TOP_SYMBOLS = [
    "OPUSDT", "SOLUSDT", "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT", "NEARUSDT", "ARBUSDT", "APTUSDT",
    "TIAUSDT", "INJUSDT", "AAVEUSDT", "DOTUSDT"
]

def simulate_strategy(mode="50_MT"):
    """
    mode:
      - '50_MT': 50% Mean Threshold instant limit entry
      - '10_INSTANT': 10% penetration threshold instant entry
      - '10_CONFIRMED_15M': 10% penetration + wait for 15m rejection (sub-bar defense / max chase cap)
    """
    total_trades = 0
    wins = 0
    losses = 0
    armors = 0
    prevented_losses = 0
    drawdowns = []

    tp_pct = 0.0280       # +14.0% ROE at 5x
    sl_pct = 0.0280       # -14.0% ROE at 5x
    armor_trigger = 0.0160 # +8.0% ROE at 5x -> Locks BE +0.10%
    min_runway_pct = 0.050 # 5.0% Rocket Airspace Runway Void
    min_maturation_bars = 48 # 2 Days on 1H
    max_maturation_bars = 720 # 1 Month on 1H

    for sym in TOP_SYMBOLS:
        fn = f"historical_data/{sym}_1h.json"
        if not os.path.exists(fn):
            continue
        with open(fn, "r") as fp:
            raw = json.load(fp)

        candles = [
            {
                "time": c.get("time") or c.get("open_time"),
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"])
            }
            for c in raw
        ]

        n = len(candles)
        if n < 100:
            continue

        # Scan for Bullish OBs
        for i in range(10, n - 60):
            c3 = candles[i]
            c2 = candles[i+1]
            c1 = candles[i+2]

            impulse_h = max(c1["high"], c2["high"])
            impulse_l = min(c1["low"], c2["low"])

            # Displacement >= 5.0% + Strict red candle + FVG
            is_strict_red = (c3["close"] < c3["open"])
            has_fvg = (c1["low"] > c3["high"])
            disp = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0

            if is_strict_red and has_fvg and disp >= 0.050:
                ob_high = c3["high"]
                ob_low = c3["low"]
                ob_range = ob_high - ob_low
                mt_50 = (ob_high + ob_low) / 2.0
                thresh_10 = ob_high - 0.10 * ob_range

                target_entry = mt_50 if mode == "50_MT" else thresh_10

                # Track zone forward
                peak_runway = impulse_h
                tapped = False
                tap_bar = -1

                for k in range(i + 3, min(i + 3 + max_maturation_bars, n)):
                    c = candles[k]
                    peak_runway = max(peak_runway, c["high"])
                    bars_alive = k - i

                    # Invalidation: candle closes below OB low before tap
                    if c["close"] < ob_low:
                        break

                    # Check tap condition
                    runway_pct = (peak_runway - ob_high) / ob_high if ob_high > 0 else 0.0

                    if c["low"] <= target_entry and c["low"] >= ob_low * 0.972:
                        # Golden Rules: Airspace >= 5% and Maturation >= 48 bars
                        if runway_pct >= min_runway_pct and bars_alive >= min_maturation_bars:
                            tap_bar = k
                            tapped = True
                            break
                        else:
                            # Immature or no airspace -> invalidate
                            break

                if not tapped or tap_bar == -1:
                    continue

                # Now evaluate the trade execution from tap_bar
                tap_candle = candles[tap_bar]

                # MODE LOGIC
                if mode == "50_MT":
                    entry_p = mt_50
                elif mode == "10_INSTANT":
                    entry_p = thresh_10
                elif mode == "10_CONFIRMED_15M":
                    # 15m confirmation check on the tap bar:
                    # In 1H candle, did the bar close strongly or dump through?
                    # If the tap bar closed BELOW the 10% threshold or near the bottom wick without rejection:
                    wick = min(tap_candle["open"], tap_candle["close"]) - tap_candle["low"]
                    c_range = tap_candle["high"] - tap_candle["low"]
                    wick_ratio = (wick / c_range) if c_range > 0 else 0.0

                    # Knife Falling Trap Check:
                    # If tap candle closed below OB low or close was at the very bottom (wick < 15%),
                    # it was a falling knife breakdown. Wait 15m filter saves us!
                    if tap_candle["close"] < ob_low or wick_ratio < 0.15:
                        prevented_losses += 1
                        continue # ABORT TRADE - CAPITAL PROTECTED!

                    # Max Chase Cap Check:
                    # Price at confirmation close must not have exceeded +0.80% above OB edge
                    if tap_candle["close"] > ob_high * 1.0080:
                        # Price already flew away too fast, do not chase!
                        continue

                    # Safe confirmed entry price
                    entry_p = max(thresh_10, min(tap_candle["close"], thresh_10 * 1.0040))

                tp_p = entry_p * (1.0 + tp_pct)
                sl_p = entry_p * (1.0 - sl_pct)
                armor_p = entry_p * (1.0 + armor_trigger)
                armor_locked = False
                closed = False

                max_adverse = 0.0

                # Simulate trade forward
                for t in range(tap_bar, min(tap_bar + 120, n)):
                    tc = candles[t]
                    # Adverse excursion (drawdown)
                    dd = (entry_p - tc["low"]) / entry_p * 100.0 if tc["low"] < entry_p else 0.0
                    max_adverse = max(max_adverse, dd)

                    # Profit Armor Check
                    if not armor_locked and tc["high"] >= armor_p:
                        armor_locked = True
                        sl_p = entry_p * 1.0010 # BE +0.10%

                    # Outcome Check
                    if tc["high"] >= tp_p:
                        wins += 1
                        closed = True
                        drawdowns.append(max_adverse)
                        break
                    elif tc["low"] <= sl_p:
                        if armor_locked:
                            armors += 1
                        else:
                            losses += 1
                        closed = True
                        drawdowns.append(max_adverse)
                        break

                if not closed:
                    # Mark to market at end
                    end_c = candles[min(tap_bar + 120, n - 1)]["close"]
                    if end_c >= entry_p:
                        wins += 1
                    else:
                        losses += 1
                    drawdowns.append(max_adverse)

                total_trades += 1

    win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0
    effective_win_rate = ((wins + armors) / total_trades * 100.0) if total_trades > 0 else 0.0
    avg_dd = (sum(drawdowns) / len(drawdowns)) if drawdowns else 0.0

    return {
        "mode": mode,
        "total_trades": total_trades,
        "wins": wins,
        "armors": armors,
        "losses": losses,
        "prevented_losses": prevented_losses,
        "win_rate": round(win_rate, 2),
        "effective_win_rate": round(effective_win_rate, 2),
        "avg_drawdown": round(avg_dd, 2)
    }

print("=== RUNNING QUANT AUDIT BACKTEST ACROSS TOP ASSETS (1-YEAR DATA) ===")
res_50 = simulate_strategy("50_MT")
res_10_inst = simulate_strategy("10_INSTANT")
res_10_conf = simulate_strategy("10_CONFIRMED_15M")

print(json.dumps({
    "50_MT": res_50,
    "10_INSTANT": res_10_inst,
    "10_CONFIRMED_15M": res_10_conf
}, indent=2))
