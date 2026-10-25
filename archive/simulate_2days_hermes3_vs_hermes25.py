import asyncio
import json
import sys
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed
from engine.hermes2_apex_live import TOP_22_CHAMPIONS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
START_2DAY_MS = int(datetime(2026, 9, 29, 0, 0, 0, tzinfo=IST).timestamp() * 1000)
END_2DAY_MS = int(datetime(2026, 9, 30, 23, 59, 59, tzinfo=IST).timestamp() * 1000)

async def run_2day_simulation():
    print("=" * 80)
    print("🥊 2-DAY LIVE HEAD-TO-HEAD BATTLE: HERMES 2.5 VS HERMES 3.0")
    print(f"Period: 29-Sep-2026 00:00 IST to 30-Sep-2026 23:59 IST (Last 48 Hours)")
    print("=" * 80)

    # 1. Fetch candles for all 22 champions
    candle_store = {}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["4h", "1h"]:
            k = await binance_feed.fetch_klines(sym, interval=tf, limit=80)
            candle_store[f"{sym}_{tf}"] = k

    btc_4h = candle_store.get("BTCUSDT_4h", [])
    btc_map_4h = {c["time"]: c for c in btc_4h}
    btc_1h = candle_store.get("BTCUSDT_1h", [])
    btc_map_1h = {c["time"]: c for c in btc_1h}

    # Harvest all candidate setups that triggered in these 2 days
    candidate_setups = []

    for sym in TOP_22_CHAMPIONS:
        for tf in ["4h", "1h"]:
            candles = candle_store.get(f"{sym}_{tf}", [])
            n = len(candles)
            if n < 30:
                continue
            min_disp = 0.050 if tf == "4h" else 0.035
            std_tp_pct = 0.028 if tf == "4h" else 0.022
            soft_sl_pct = 0.028 if tf == "4h" else 0.022
            hard_sl_pct = 0.038 if tf == "4h" else 0.032

            for i in range(15, n - 2):
                # LONG
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= min_disp:
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
                                    for t in range(high_idx + 1, min(high_idx + 28, n)):
                                        tap_c = candles[t]
                                        if tap_c["low"] <= dec_top * 1.0005:
                                            tap_time = tap_c["time"]
                                            if START_2DAY_MS <= tap_time <= END_2DAY_MS:
                                                c_range = tap_c["high"] - tap_c["low"]
                                                swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                                l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0
                                                
                                                curr_4h = tap_time - (tap_time % (4 * 3600 * 1000))
                                                prev_4h = curr_4h - 4 * 3600 * 1000
                                                b_c = btc_map_4h.get(prev_4h)
                                                b_dump = (b_c["open"] - b_c["close"]) / b_c["open"] if b_c else 0.0
                                                b_clean = b_dump < 0.020

                                                if b_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                    candidate_setups.append({
                                                        "sym": sym, "tf": tf, "side": "LONG", "time": tap_time,
                                                        "t_idx": t, "candles": candles, "dec_top": dec_top, "dec_bot": dec_bot,
                                                        "mt": mt, "tap_c": tap_c, "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                        "hard_sl_pct": hard_sl_pct, "w_ratio": w_ratio, "gain": gain
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
                        if drop >= min_disp:
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
                                    for t in range(low_idx + 1, min(low_idx + 28, n)):
                                        tap_c = candles[t]
                                        if tap_c["high"] >= dec_bot * 0.9995:
                                            tap_time = tap_c["time"]
                                            if START_2DAY_MS <= tap_time <= END_2DAY_MS:
                                                c_range = tap_c["high"] - tap_c["low"]
                                                swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                                u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                                w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0

                                                curr_4h = tap_time - (tap_time % (4 * 3600 * 1000))
                                                prev_4h = curr_4h - 4 * 3600 * 1000
                                                b_c = btc_map_4h.get(prev_4h)
                                                b_pump = (b_c["close"] - b_c["open"]) / b_c["open"] if b_c else 0.0
                                                b_clean_short = b_pump < 0.020

                                                if b_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                    candidate_setups.append({
                                                        "sym": sym, "tf": tf, "side": "SHORT", "time": tap_time,
                                                        "t_idx": t, "candles": candles, "dec_top": dec_top, "dec_bot": dec_bot,
                                                        "mt": mt, "tap_c": tap_c, "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                        "hard_sl_pct": hard_sl_pct, "w_ratio": w_ratio, "gain": drop
                                                    })
                                                    break

    candidate_setups.sort(key=lambda x: x["time"])
    print(f"Total Unique Triggered Setups in 48h: {len(candidate_setups)}")

    for engine_name in ["HERMES_2.5_APEX_HYBRID", "HERMES_3.0_QUANTUM"]:
        print(f"\n=======================================================")
        print(f"🚀 ENGINE: {engine_name}")
        print(f"=======================================================")
        
        # 4 Concurrent Quad Compounding slots
        slots_busy_until = {
            "binance_4h": 0,
            "binance_1h": 0,
            "bitget_4h": 0,
            "bitget_1h": 0
        }
        
        executed_trades = []
        
        for s in candidate_setups:
            sym = s["sym"]
            tf = s["tf"]
            side = s["side"]
            s_time = s["time"]
            candles = s["candles"]
            t = s["t_idx"]
            n = len(candles)
            tap_c = s["tap_c"]
            mt = s["mt"]
            time_ist = datetime.fromtimestamp(s_time/1000, tz=IST).strftime("%d-%b %I:%M %p")

            # Route to available slot
            target_slot = None
            if tf == "4h":
                if s_time >= slots_busy_until["binance_4h"]:
                    target_slot = "binance_4h"
                elif s_time >= slots_busy_until["bitget_4h"]:
                    target_slot = "bitget_4h"
            else:
                if s_time >= slots_busy_until["binance_1h"]:
                    target_slot = "binance_1h"
                elif s_time >= slots_busy_until["bitget_1h"]:
                    target_slot = "bitget_1h"

            if not target_slot:
                continue

            if engine_name == "HERMES_2.5_APEX_HYBRID":
                entry = s["dec_top"] if side == "LONG" else s["dec_bot"]
                tp = entry * (1.0 + s["std_tp_pct"]) if side == "LONG" else entry * (1.0 - s["std_tp_pct"])
                sl = entry * (1.0 - s["soft_sl_pct"]) if side == "LONG" else entry * (1.0 + s["soft_sl_pct"])
                hard_sl = entry * (1.0 - s["hard_sl_pct"]) if side == "LONG" else entry * (1.0 + s["hard_sl_pct"])
            else: # HERMES 3.0 QUANTUM
                if side == "LONG":
                    # Mean Threshold 50% discount entry
                    entry = mt if tap_c["low"] <= mt else (s["dec_top"] + mt) / 2.0
                    tp = entry * (1.0 + s["std_tp_pct"])
                    hard_sl = min(s["dec_bot"] - 0.003 * entry, entry * (1.0 - s["hard_sl_pct"]))
                    sl = (entry + hard_sl) / 2.0
                else:
                    entry = mt if tap_c["high"] >= mt else (s["dec_bot"] + mt) / 2.0
                    tp = entry * (1.0 - s["std_tp_pct"])
                    hard_sl = max(s["dec_top"] + 0.003 * entry, entry * (1.0 + s["hard_sl_pct"]))
                    sl = (entry + hard_sl) / 2.0

            outcome = "OPEN"
            exit_price = entry
            exit_time = s_time
            current_sl = sl
            be_locked = False

            for m in range(t + 1, min(t + 35, n)):
                cm = candles[m]
                m_time = cm["time"]

                # In-trade BTC emergency shield in Hermes 3.0
                if engine_name == "HERMES_3.0_QUANTUM":
                    btc_ts = m_time - (m_time % (3600 * 1000))
                    btc_c = btc_map_1h.get(btc_ts)
                    if btc_c:
                        btc_chg = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                        if side == "LONG" and btc_chg < -0.010:
                            current_sl = max(current_sl, entry * 0.995)
                        elif side == "SHORT" and btc_chg > 0.010:
                            current_sl = min(current_sl, entry * 1.005)

                if side == "LONG":
                    if cm["high"] >= entry * 1.022 and engine_name == "HERMES_3.0_QUANTUM":
                        current_sl = max(current_sl, entry * 1.012)
                        be_locked = True
                    elif cm["high"] >= entry * 1.016:
                        current_sl = max(current_sl, entry * 1.002)
                        be_locked = True

                    if cm["high"] >= tp:
                        outcome = "TP_HIT"
                        exit_price = tp
                        exit_time = m_time
                        break
                    if cm["low"] <= hard_sl:
                        outcome = "SL_HIT"
                        exit_price = hard_sl
                        exit_time = m_time
                        break
                    if cm["close"] <= current_sl:
                        outcome = "BE_PROFIT" if be_locked and current_sl > entry else "SOFT_SL"
                        exit_price = cm["close"]
                        exit_time = m_time
                        break
                else:
                    if cm["low"] <= entry * 0.978 and engine_name == "HERMES_3.0_QUANTUM":
                        current_sl = min(current_sl, entry * 0.988)
                        be_locked = True
                    elif cm["low"] <= entry * 0.984:
                        current_sl = min(current_sl, entry * 0.998)
                        be_locked = True

                    if cm["low"] <= tp:
                        outcome = "TP_HIT"
                        exit_price = tp
                        exit_time = m_time
                        break
                    if cm["high"] >= hard_sl:
                        outcome = "SL_HIT"
                        exit_price = hard_sl
                        exit_time = m_time
                        break
                    if cm["close"] >= current_sl:
                        outcome = "BE_PROFIT" if be_locked and current_sl < entry else "SOFT_SL"
                        exit_price = cm["close"]
                        exit_time = m_time
                        break

            if outcome == "OPEN":
                last_c = candles[min(t + 35, n - 1)]
                exit_price = last_c["close"]
                exit_time = last_c["time"]
                outcome = "TIME_EXIT"

            slots_busy_until[target_slot] = exit_time

            # PnL with $50 margin @ 5x leverage ($250 size)
            pos = 250.0
            if side == "LONG":
                ret_pct = (exit_price - entry) / entry * 100.0
            else:
                ret_pct = (entry - exit_price) / entry * 100.0
            pnl = pos * (ret_pct / 100.0) - (pos * 0.0016)
            roe = ret_pct * 5.0

            executed_trades.append({
                "sym": sym, "tf": tf, "side": side, "slot": target_slot,
                "time": time_ist, "entry": entry, "exit": exit_price,
                "outcome": outcome, "pnl": pnl, "roe": roe
            })
            print(f"• [{target_slot.upper()}] {time_ist} | {sym:8s} {side:5s} ({tf.upper()}) | Entry: {entry:.5f} | Exit: {exit_price:.5f} | Status: {outcome:10s} | PnL: ${pnl:+6.2f} (ROE: {roe:+5.1f}%)")

        wins = sum(1 for t in executed_trades if t["pnl"] > 0)
        losses = sum(1 for t in executed_trades if t["pnl"] <= 0)
        tot_pnl = sum(t["pnl"] for t in executed_trades)
        wr = (wins / len(executed_trades) * 100) if executed_trades else 0.0
        print(f"\n📊 Summary for {engine_name}:")
        print(f"Total Trades Taken: {len(executed_trades)} | Wins: {wins} | Losses: {losses} | Win Rate: {wr:.1f}%")
        print(f"Total Net PnL (at $50 starting margin): ${tot_pnl:+.2f} USDT")

    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(run_2day_simulation())
