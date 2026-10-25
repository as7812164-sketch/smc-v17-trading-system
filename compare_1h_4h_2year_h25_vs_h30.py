import os
import sys
import json
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")

CANDLE_CACHE = {}

def load_candles(sym, interval):
    key = f"{sym}_{interval}"
    if key in CANDLE_CACHE:
        return CANDLE_CACHE[key]
    fpath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        c["volume"] = float(c.get("volume", 0.0))
    CANDLE_CACHE[key] = data
    return data

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_1h = load_candles("BTCUSDT", "1h")
    return {c["time"]: c for c in btc_4h}, {c["time"]: c for c in btc_1h}

def analyze():
    print("=" * 80)
    print("🔬 2-YEAR COMPLETE TIMEFRAME AUDIT: HERMES 2.5 VS HERMES 3.0 (1H & 4H)")
    print("=" * 80)

    btc_map_4h, btc_map_1h = build_btc_map()
    
    # Harvest candidate setups by timeframe
    setups_by_tf = {"1h": [], "4h": []}

    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        max_tap_window = 28
        max_hold = 30 if tf == "4h" else 40

        for sym in TOP_22_CHAMPIONS:
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < 40:
                continue

            atr = [0.0] * n
            for k in range(1, n):
                tr = max(candles[k]["high"] - candles[k]["low"],
                         abs(candles[k]["high"] - candles[k-1]["close"]),
                         abs(candles[k]["low"] - candles[k-1]["close"]))
                atr[k] = tr if k < 14 else (atr[k-1] * 13 + tr) / 14

            for i in range(20, n - 2):
                # LONG
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        if candles[t]["low"] <= dec_top * 1.0005:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean = btc_dump < 0.020

                                            if btc_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                setups_by_tf[tf].append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                                })
                                                break

                # SHORT
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.050:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        if candles[t]["high"] >= dec_bot * 0.9995:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean_short = btc_pump < 0.020

                                            if btc_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                setups_by_tf[tf].append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                                })
                                                break

    for tf in ["1h", "4h"]:
        setups_by_tf[tf].sort(key=lambda x: x["time"])
        print(f"Total candidate setups for {tf.upper()}: {len(setups_by_tf[tf])}")

    stats = {}

    for target_tf in ["4h", "1h"]:
        setups = setups_by_tf[target_tf]
        stats[target_tf] = {}

        for engine_name in ["HERMES_2.5", "HERMES_3.0"]:
            # Run sequential compounding queue for this timeframe (2 slots: Binance + Bitget)
            slot1_busy = 0
            slot2_busy = 0
            
            executed = []
            balance = 50.0
            vault = 0.0
            peak_equity = 50.0
            max_dd = 0.0
            milestone_2k = None

            for s in setups:
                s_time = s["time"]
                if s_time >= slot1_busy:
                    target_slot = 1
                elif s_time >= slot2_busy:
                    target_slot = 2
                else:
                    continue

                sym = s["sym"]
                tf = s["tf"]
                side = s["side"]
                t = s["t_idx"]
                candles = load_candles(sym, tf)
                n = len(candles)
                
                if engine_name == "HERMES_2.5":
                    entry = s["dec_top"] if side == "LONG" else s["dec_bot"]
                    tp_p = entry * (1.0 + s["std_tp_pct"]) if side == "LONG" else entry * (1.0 - s["std_tp_pct"])
                    soft_sl_p = entry * (1.0 - s["soft_sl_pct"]) if side == "LONG" else entry * (1.0 + s["soft_sl_pct"])
                    hard_sl_p = entry * (1.0 - s["hard_sl_pct"]) if side == "LONG" else entry * (1.0 + s["hard_sl_pct"])
                else: # HERMES 3.0
                    mt = s["mt"]
                    if side == "LONG":
                        entry = mt if s["tap_low"] <= mt else (s["dec_top"] + mt) / 2.0
                        tp_p = entry * (1.0 + s["std_tp_pct"])
                        struct_sl = min(s["dec_bot"], s["tap_low"]) - 0.20 * s["atr"]
                        hard_sl_p = min(struct_sl, entry * (1.0 - s["hard_sl_pct"]))
                        hard_sl_p = max(hard_sl_p, entry * 0.962)
                        soft_sl_p = (entry + hard_sl_p) / 2.0
                    else:
                        entry = mt if s["tap_high"] >= mt else (s["dec_bot"] + mt) / 2.0
                        tp_p = entry * (1.0 - s["std_tp_pct"])
                        struct_sl = max(s["dec_top"], s["tap_high"]) + 0.20 * s["atr"]
                        hard_sl_p = max(struct_sl, entry * (1.0 + s["hard_sl_pct"]))
                        hard_sl_p = min(hard_sl_p, entry * 1.038)
                        soft_sl_p = (entry + hard_sl_p) / 2.0

                res = None
                exit_price = entry
                exit_time = s_time
                curr_sl = soft_sl_p
                be_locked = False

                for m in range(t, min(t + s["max_hold"], n)):
                    cm = candles[m]
                    m_time = cm["time"]

                    if engine_name == "HERMES_3.0":
                        btc_ts = m_time - (m_time % (3600 * 1000))
                        btc_c = btc_map_1h.get(btc_ts)
                        if btc_c:
                            btc_chg = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                            if side == "LONG" and btc_chg < -0.010 and not be_locked:
                                curr_sl = max(curr_sl, entry * 0.995)
                            elif side == "SHORT" and btc_chg > 0.010 and not be_locked:
                                curr_sl = min(curr_sl, entry * 1.005)

                    if side == "LONG":
                        if cm["high"] >= entry * 1.022 and engine_name == "HERMES_3.0":
                            curr_sl = max(curr_sl, entry * 1.012)
                            be_locked = True
                        elif cm["high"] >= entry * 1.016:
                            curr_sl = max(curr_sl, entry * 1.002)
                            be_locked = True

                        if cm["high"] >= tp_p:
                            res = "WIN"
                            exit_price = tp_p
                            exit_time = m_time
                            break
                        if cm["low"] <= hard_sl_p:
                            res = "LOSS"
                            exit_price = hard_sl_p
                            exit_time = m_time
                            break
                        if cm["close"] <= curr_sl:
                            res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                            exit_price = cm["close"]
                            exit_time = m_time
                            break
                    else:
                        if cm["low"] <= entry * 0.978 and engine_name == "HERMES_3.0":
                            curr_sl = min(curr_sl, entry * 0.988)
                            be_locked = True
                        elif cm["low"] <= entry * 0.984:
                            curr_sl = min(curr_sl, entry * 0.998)
                            be_locked = True

                        if cm["low"] <= tp_p:
                            res = "WIN"
                            exit_price = tp_p
                            exit_time = m_time
                            break
                        if cm["high"] >= hard_sl_p:
                            res = "LOSS"
                            exit_price = hard_sl_p
                            exit_time = m_time
                            break
                        if cm["close"] >= curr_sl:
                            res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                            exit_price = cm["close"]
                            exit_time = m_time
                            break

                if not res:
                    fc = candles[min(t + s["max_hold"], n - 1)]["close"]
                    res = "WIN" if (fc >= entry if side == "LONG" else fc <= entry) else "LOSS"
                    exit_price = fc
                    exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]

                if target_slot == 1:
                    slot1_busy = exit_time
                else:
                    slot2_busy = exit_time

                # Compounding stats
                pos_size = balance * 5.0
                ret = (exit_price - entry) / entry if side == "LONG" else (entry - exit_price) / entry
                pnl = pos_size * ret - (pos_size * 0.0016)
                
                if pnl > 0:
                    balance += pnl * 0.85
                    vault += pnl * 0.15
                else:
                    balance += pnl
                    if balance < 10.0:
                        balance = 10.0

                total_eq = balance + vault
                if total_eq > peak_equity:
                    peak_equity = total_eq
                dd = (peak_equity - total_eq) / peak_equity * 100.0
                if dd > max_dd:
                    max_dd = dd

                if not milestone_2k and total_eq >= 2000.0:
                    milestone_2k = {
                        "trade_num": len(executed) + 1,
                        "date": datetime.fromtimestamp(exit_time / 1000).strftime("%Y-%m-%d")
                    }

                executed.append({"res": res, "side": side, "pnl": pnl, "time": exit_time})

            wins = sum(1 for e in executed if e["res"] == "WIN")
            losses = sum(1 for e in executed if e["res"] == "LOSS")
            long_trades = sum(1 for e in executed if e["side"] == "LONG")
            long_wins = sum(1 for e in executed if e["side"] == "LONG" and e["res"] == "WIN")
            long_losses = long_trades - long_wins
            short_trades = sum(1 for e in executed if e["side"] == "SHORT")
            short_wins = sum(1 for e in executed if e["side"] == "SHORT" and e["res"] == "WIN")
            short_losses = short_trades - short_wins

            wr = (wins / len(executed) * 100) if executed else 0
            long_wr = (long_wins / long_trades * 100) if long_trades else 0
            short_wr = (short_wins / short_trades * 100) if short_trades else 0

            stats[target_tf][engine_name] = {
                "trades": len(executed),
                "wins": wins,
                "losses": losses,
                "win_rate": round(wr, 2),
                "long_trades": long_trades,
                "long_wins": long_wins,
                "long_losses": long_losses,
                "long_wr": round(long_wr, 2),
                "short_trades": short_trades,
                "short_wins": short_wins,
                "short_losses": short_losses,
                "short_wr": round(short_wr, 2),
                "max_drawdown": round(max_dd, 2),
                "milestone_2k": milestone_2k
            }
            print(f"[{target_tf.upper()}] {engine_name} -> Trades: {len(executed)} | Wins: {wins} | Losses: {losses} | WR: {wr:.2f}% | Long WR: {long_wr:.2f}% | Short WR: {short_wr:.2f}% | 2K Hit: {milestone_2k}")

    with open("timeframe_comparison_2year_results.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    analyze()
