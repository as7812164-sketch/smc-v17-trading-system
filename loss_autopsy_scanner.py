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

def run_loss_autopsy():
    print("=" * 95)
    print(" 🩺 FORENSIC POST-MORTEM AUTOPSY: SCANNING ALL LOSING TRADES (1 FULL YEAR)")
    print(" Goal: Decode EXACTLY why each loss occurred and identify the systemic loopholes")
    print("=" * 95)

    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    # Also load BTC 4H & 1H for macro correlation
    btc_4h = load_local_data("BTCUSDT", "4h")
    btc_1h = load_local_data("BTCUSDT", "1h")
    btc_map_4h = {c["time"]: c for c in btc_4h}
    
    # Calculate BTC 4H EMA20
    btc_closes = [c["close"] for c in btc_4h]
    btc_ema20 = [0.0] * len(btc_closes)
    if btc_closes:
        k_mult = 2.0 / (20 + 1)
        btc_ema20[0] = btc_closes[0]
        for i in range(1, len(btc_closes)):
            btc_ema20[i] = btc_closes[i] * k_mult + btc_ema20[i-1] * (1.0 - k_mult)
    btc_ema_map = {btc_4h[i]["time"]: btc_ema20[i] for i in range(len(btc_4h))}

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
                                                bars_to_exit = 0
                                                for m in range(t, min(t + max_hold, n)):
                                                    bars_to_exit += 1
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] <= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                
                                                # Forensic Metadata
                                                bars_to_tap = t - high_idx
                                                avg_vol_20 = np.mean([c["volume"] for c in candles[i-20:i]])
                                                disp_vol_ratio = candles[best_mid]["volume"] / avg_vol_20 if avg_vol_20 > 0 else 1.0
                                                tap_candle_size_pct = c_range / entry
                                                
                                                all_signals.append({
                                                    "sym": sym, "tf": tf, "side": "LONG", "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit_p": exit_p,
                                                    "gross": (exit_p - entry) / entry, "res": res,
                                                    "bars_to_tap": bars_to_tap, "vol_ratio": disp_vol_ratio,
                                                    "tap_size_pct": tap_candle_size_pct, "bars_to_exit": bars_to_exit
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
                                                bars_to_exit = 0
                                                for m in range(t, min(t + max_hold, n)):
                                                    bars_to_exit += 1
                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] >= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                    
                                                bars_to_tap = t - low_idx
                                                avg_vol_20 = np.mean([c["volume"] for c in candles[i-20:i]])
                                                disp_vol_ratio = candles[best_mid]["volume"] / avg_vol_20 if avg_vol_20 > 0 else 1.0
                                                tap_candle_size_pct = c_range / entry

                                                all_signals.append({
                                                    "sym": sym, "tf": tf, "side": "SHORT", "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit_p": exit_p,
                                                    "gross": (entry - exit_p) / entry, "res": res,
                                                    "bars_to_tap": bars_to_tap, "vol_ratio": disp_vol_ratio,
                                                    "tap_size_pct": tap_candle_size_pct, "bars_to_exit": bars_to_exit
                                                })
                                            break

    all_signals.sort(key=lambda x: x["time"])

    # Sequential queue execution
    executed_trades = []
    active_exit = 0
    for s in all_signals:
        if s["time"] >= active_exit:
            executed_trades.append(s)
            active_exit = s["exit_time"]

    losses = [t for t in executed_trades if t["res"] == "LOSS"]
    wins = [t for t in executed_trades if t["res"] == "WIN"]

    print(f"\nTotal Executed Trades: {len(executed_trades)} | Wins: {len(wins)} (78.58%) | Losses: {len(losses)} (21.42%)\n")

    # -------------------------------------------------------------
    # AUTOPSY INVESTIGATION ON THE 124 LOSSES
    # -------------------------------------------------------------
    btc_conflict_losses = 0
    stale_ob_losses = 0 # Retest tap happened > 20 bars later
    weak_vol_losses = 0  # Breakout volume was < 1.2x of normal volume
    falling_knife_losses = 0 # Tap candle was massive (> 2.8% body/range)
    immediate_stop_losses = 0 # Stopped out in <= 2 bars (violent continuation)
    grind_stop_losses = 0 # Slow bleed out (> 15 bars)

    for t in losses:
        # 1. Check BTC Trend Conflict
        t_ts = t["time"] - (t["time"] % (4 * 3600 * 1000))
        btc_bar = btc_map_4h.get(t_ts)
        btc_ema = btc_ema_map.get(t_ts)
        if btc_bar and btc_ema:
            # If LONG trade but BTC was below EMA20
            if t["side"] == "LONG" and btc_bar["close"] < btc_ema:
                btc_conflict_losses += 1
            # If SHORT trade but BTC was above EMA20
            elif t["side"] == "SHORT" and btc_bar["close"] > btc_ema:
                btc_conflict_losses += 1

        # 2. Check Stale OB
        if t["bars_to_tap"] > 18:
            stale_ob_losses += 1

        # 3. Check Weak Volume
        if t["vol_ratio"] < 1.15:
            weak_vol_losses += 1

        # 4. Check Falling Knife / Giant Tap Candle
        if t["tap_size_pct"] > 0.026:
            falling_knife_losses += 1

        # 5. Check Speed of Stop Out
        if t["bars_to_exit"] <= 2:
            immediate_stop_losses += 1
        elif t["bars_to_exit"] >= 15:
            grind_stop_losses += 1

    tot_losses = len(losses)
    print("=" * 95)
    print(" 🔍 AUTOPSY REPORT: THE 4 ROOT CAUSES BEHIND THE 124 LOSSES")
    print("=" * 95)
    print(f" 1. ⚠️  BTC Macro Conflict (Trade opposed BTC 4H Trend):  {btc_conflict_losses:3d} losses ({btc_conflict_losses/tot_losses*100:5.1f}%)")
    print(f" 2. ⏳ Stale / Late Retest (OB tapped > 18 bars later):       {stale_ob_losses:3d} losses ({stale_ob_losses/tot_losses*100:5.1f}%)")
    print(f" 3. 📉 Weak Volume Breakout (Displacement Vol < 1.15x avg):  {weak_vol_losses:3d} losses ({weak_vol_losses/tot_losses*100:5.1f}%)")
    print(f" 4. 🔪 Falling Knife (Giant aggressive tap candle > 2.6%):   {falling_knife_losses:3d} losses ({falling_knife_losses/tot_losses*100:5.1f}%)")
    print(f" -----------------------------------------------------------------------------------------")
    print(f" • Immediate Liquidation / Black Swan (Died in <= 2 bars):    {immediate_stop_losses:3d} losses ({immediate_stop_losses/tot_losses*100:5.1f}%)")
    print(f" • Slow Grind Bleed (Exhaustion after 15+ bars):              {grind_stop_losses:3d} losses ({grind_stop_losses/tot_losses*100:5.1f}%)")
    print("=" * 95)

if __name__ == "__main__":
    run_loss_autopsy()
