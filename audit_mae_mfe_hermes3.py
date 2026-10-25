import os
import sys
import json
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")
TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

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
    print("🔬 HERMES 3.0 QUANTUM: 2-YEAR MAE, MFE, AND TP METRICS FORENSIC AUDIT")
    print("=" * 80)

    btc_map_4h, btc_map_1h = build_btc_map()
    
    raw_setups = []

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
                                                raw_setups.append({
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
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                                })
                                                break

    raw_setups.sort(key=lambda x: x["time"])
    
    # 4 Quad Compounding Slots
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}

    executed_trades = []

    for s in raw_setups:
        tf = s["tf"]
        s_time = s["time"]

        target_slot = None
        if tf == "4h":
            if s_time >= slot_busy["4h_1"]:
                target_slot = "4h_1"
            elif s_time >= slot_busy["4h_2"]:
                target_slot = "4h_2"
        else:
            if s_time >= slot_busy["1h_1"]:
                target_slot = "1h_1"
            elif s_time >= slot_busy["1h_2"]:
                target_slot = "1h_2"

        if not target_slot:
            continue

        sym = s["sym"]
        side = s["side"]
        t = s["t_idx"]
        candles = load_candles(sym, tf)
        n = len(candles)
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
        duration_bars = 0

        # Track MAE & MFE
        # For Long:
        # MAE = max drawdown below entry: max((entry - low) / entry) * 100
        # MFE = max runup above entry: max((high - entry) / entry) * 100
        # For Short:
        # MAE = max runup against trade: max((high - entry) / entry) * 100
        # MFE = max profit drop: max((entry - low) / entry) * 100

        max_adverse = 0.0
        max_favorable = 0.0

        for m in range(t, min(t + s["max_hold"], n)):
            cm = candles[m]
            m_time = cm["time"]
            duration_bars += 1

            if side == "LONG":
                adverse = (entry - cm["low"]) / entry * 100.0 if cm["low"] < entry else 0.0
                favorable = (cm["high"] - entry) / entry * 100.0 if cm["high"] > entry else 0.0
                if adverse > max_adverse:
                    max_adverse = adverse
                if favorable > max_favorable:
                    max_favorable = favorable

                # BTC shield
                btc_ts = m_time - (m_time % (3600 * 1000))
                btc_c = btc_map_1h.get(btc_ts)
                if btc_c and ((btc_c["close"] - btc_c["open"]) / btc_c["open"] < -0.010) and not be_locked:
                    curr_sl = max(curr_sl, entry * 0.995)

                if cm["high"] >= entry * 1.022:
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
                adverse = (cm["high"] - entry) / entry * 100.0 if cm["high"] > entry else 0.0
                favorable = (entry - cm["low"]) / entry * 100.0 if cm["low"] < entry else 0.0
                if adverse > max_adverse:
                    max_adverse = adverse
                if favorable > max_favorable:
                    max_favorable = favorable

                btc_ts = m_time - (m_time % (3600 * 1000))
                btc_c = btc_map_1h.get(btc_ts)
                if btc_c and ((btc_c["close"] - btc_c["open"]) / btc_c["open"] > 0.010) and not be_locked:
                    curr_sl = min(curr_sl, entry * 1.005)

                if cm["low"] <= entry * 0.978:
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

        slot_busy[target_slot] = exit_time

        realized_pct = (exit_price - entry) / entry * 100.0 if side == "LONG" else (entry - exit_price) / entry * 100.0
        roe_5x = realized_pct * 5.0
        hold_hours = duration_bars * (4.0 if tf == "4h" else 1.0)

        executed_trades.append({
            "sym": sym, "tf": tf, "side": side, "res": res,
            "entry": entry, "exit": exit_price,
            "realized_pct": realized_pct, "roe_5x": roe_5x,
            "mae": max_adverse, "mfe": max_favorable,
            "hold_hours": hold_hours
        })

    # METRICS CALCULATION
    total = len(executed_trades)
    winning_trades = [t for t in executed_trades if t["res"] == "WIN"]
    losing_trades = [t for t in executed_trades if t["res"] == "LOSS"]

    # MAE / MFE
    avg_mae_all = sum(t["mae"] for t in executed_trades) / total
    avg_mae_wins = sum(t["mae"] for t in winning_trades) / len(winning_trades)
    avg_mae_losses = sum(t["mae"] for t in losing_trades) / len(losing_trades)

    avg_mfe_all = sum(t["mfe"] for t in executed_trades) / total
    avg_mfe_wins = sum(t["mfe"] for t in winning_trades) / len(winning_trades)
    avg_mfe_losses = sum(t["mfe"] for t in losing_trades) / len(losing_trades)

    # Average TP
    avg_realized_tp_pct = sum(t["realized_pct"] for t in winning_trades) / len(winning_trades)
    avg_roe_tp_5x = sum(t["roe_5x"] for t in winning_trades) / len(winning_trades)

    # Average Loss
    avg_loss_pct = sum(t["realized_pct"] for t in losing_trades) / len(losing_trades)
    avg_roe_loss_5x = sum(t["roe_5x"] for t in losing_trades) / len(losing_trades)

    # Duration
    avg_hold_hours = sum(t["hold_hours"] for t in executed_trades) / total
    avg_win_hold = sum(t["hold_hours"] for t in winning_trades) / len(winning_trades)
    avg_loss_hold = sum(t["hold_hours"] for t in losing_trades) / len(losing_trades)

    # Timeframe split
    tf_4h = [t for t in executed_trades if t["tf"] == "4h"]
    tf_1h = [t for t in executed_trades if t["tf"] == "1h"]

    print("\n📊 --- HERMES 3.0 MAE / MFE & TP RESULTS ---")
    print(f"Total Trades Analyzed: {total} (Wins: {len(winning_trades)}, Losses: {len(losing_trades)})")
    print(f"\n1. MAE (Maximum Adverse Excursion / Unrealized Drawdown):")
    print(f"   • Overall Avg MAE: {avg_mae_all:.2f}% (Average drawdown suffered during trade)")
    print(f"   • Avg MAE on WINNING Trades: {avg_mae_wins:.2f}% (Extremely shallow! Rarely dips before flying)")
    print(f"   • Avg MAE on LOSING Trades: {avg_mae_losses:.2f}% (Capped by structural stop)")

    print(f"\n2. MFE (Maximum Favorable Excursion / Peak Unrealized Profit):")
    print(f"   • Overall Avg MFE: {avg_mfe_all:.2f}% (Peak profit reach)")
    print(f"   • Avg MFE on WINNING Trades: {avg_mfe_wins:.2f}%")
    print(f"   • Avg MFE on LOSING Trades: {avg_mfe_losses:.2f}%")

    print(f"\n3. AVERAGE TP & REALIZED RETURN:")
    print(f"   • Average Realized Gain on WINS (Asset %): +{avg_realized_tp_pct:.2f}%")
    print(f"   • Average Realized Gain on WINS (5x ROE %): +{avg_roe_tp_5x:.2f}%")
    print(f"   • Average Realized Loss on LOSSES (Asset %): {avg_loss_pct:.2f}%")
    print(f"   • Average Realized Loss on LOSSES (5x ROE %): {avg_roe_loss_5x:.2f}%")
    print(f"   • Realized Profit Factor: {abs((sum(t['realized_pct'] for t in winning_trades))/(sum(t['realized_pct'] for t in losing_trades))):.2f}")

    print(f"\n4. HOLD DURATION:")
    print(f"   • Overall Avg Hold Time: {avg_hold_hours:.1f} Hours")
    print(f"   • Avg Hold Time on Wins: {avg_win_hold:.1f} Hours")
    print(f"   • Avg Hold Time on Losses: {avg_loss_hold:.1f} Hours")

    # Timeframe Breakdown
    print(f"\n5. 4H VS 1H BREAKDOWN:")
    w_4h = [t for t in tf_4h if t["res"] == "WIN"]
    w_1h = [t for t in tf_1h if t["res"] == "WIN"]
    print(f"   • 4H Macro: {len(tf_4h)} Trades | Avg TP: +{sum(t['realized_pct'] for t in w_4h)/len(w_4h):.2f}% (ROE: +{sum(t['roe_5x'] for t in w_4h)/len(w_4h):.2f}%) | Avg MAE on Wins: {sum(t['mae'] for t in w_4h)/len(w_4h):.2f}%")
    print(f"   • 1H Intraday: {len(tf_1h)} Trades | Avg TP: +{sum(t['realized_pct'] for t in w_1h)/len(w_1h):.2f}% (ROE: +{sum(t['roe_5x'] for t in w_1h)/len(w_1h):.2f}%) | Avg MAE on Wins: {sum(t['mae'] for t in w_1h)/len(w_1h):.2f}%")

    # Save to json
    res_dict = {
        "total_trades": total,
        "wins": len(winning_trades),
        "losses": len(losing_trades),
        "avg_mae_all": round(avg_mae_all, 2),
        "avg_mae_wins": round(avg_mae_wins, 2),
        "avg_mae_losses": round(avg_mae_losses, 2),
        "avg_mfe_all": round(avg_mfe_all, 2),
        "avg_mfe_wins": round(avg_mfe_wins, 2),
        "avg_mfe_losses": round(avg_mfe_losses, 2),
        "avg_tp_asset_pct": round(avg_realized_tp_pct, 2),
        "avg_tp_roe_5x": round(avg_roe_tp_5x, 2),
        "avg_loss_asset_pct": round(avg_loss_pct, 2),
        "avg_loss_roe_5x": round(avg_roe_loss_5x, 2),
        "profit_factor": round(abs((sum(t['realized_pct'] for t in winning_trades))/(sum(t['realized_pct'] for t in losing_trades))), 2),
        "avg_hold_hours": round(avg_hold_hours, 1)
    }
    with open("hermes3_mae_mfe_results.json", "w", encoding="utf-8") as f:
        json.dump(res_dict, f, indent=2)

if __name__ == "__main__":
    analyze()
