"""
LABORATORY TEST: BTC 20 EMA IMPACT ON HERMES 3.5 STRATEGY
Evaluates BTC 4H EMA20, BTC 1H EMA20, and combinations across 1-year historical dataset.
"""
import os
import json
import time

DATA_DIR = "historical_data"
files = [f for f in os.listdir(DATA_DIR) if f.endswith("_1h.json") and not "1y_audit" in f]
coins = sorted([f.replace("_1h.json", "") for f in files])

# Load BTC 4H and 1H
with open(os.path.join(DATA_DIR, "BTCUSDT_4h.json"), "r", encoding="utf-8") as f:
    btc_4h = json.load(f)
btc_4h_closes = [float(c["close"]) for c in btc_4h]

with open(os.path.join(DATA_DIR, "BTCUSDT_1h.json"), "r", encoding="utf-8") as f:
    btc_1h = json.load(f)
btc_1h_closes = [float(c["close"]) for c in btc_1h]

def calc_ema(arr, period):
    k = 2.0 / (period + 1.0)
    res = [arr[0]]
    for p in arr[1:]: res.append(p * k + res[-1] * (1.0 - k))
    return res

# Calculate BTC EMAs
btc_4h_ema20 = calc_ema(btc_4h_closes, 20)
btc_4h_ema50 = calc_ema(btc_4h_closes, 50)
btc_4h_ema200 = calc_ema(btc_4h_closes, 200)

btc_1h_ema20 = calc_ema(btc_1h_closes, 20)

btc_map_4h_ema20 = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_4h_ema20[i]) for i in range(len(btc_4h))}
btc_map_4h_ema50 = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_4h_ema50[i]) for i in range(len(btc_4h))}
btc_map_4h_ema200 = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_4h_ema200[i]) for i in range(len(btc_4h))}
btc_times_4h = sorted(btc_map_4h_ema50.keys())

btc_map_1h_ema20 = {btc_1h[i]["time"]: (btc_1h[i]["close"] >= btc_1h_ema20[i]) for i in range(len(btc_1h))}
btc_times_1h = sorted(btc_map_1h_ema20.keys())

# Pre-load candidate candles and ATR
CANDLE_CACHE = {}
for tf_str in ["4h", "1h"]:
    for sym in coins:
        path = os.path.join(DATA_DIR, f"{sym}_{tf_str}.json")
        if not os.path.exists(path): continue
        with open(path, "r", encoding="utf-8") as f:
            candles = json.load(f)
        n = len(candles)
        if n < 50: continue
        atr_series = [0.0] * n
        for k_idx in range(1, n):
            tr = max(candles[k_idx]["high"] - candles[k_idx]["low"],
                     abs(candles[k_idx]["high"] - candles[k_idx-1]["close"]),
                     abs(candles[k_idx]["low"] - candles[k_idx-1]["close"]))
            atr_series[k_idx] = tr if k_idx < 14 else (atr_series[k_idx-1] * 13 + tr) / 14
        CANDLE_CACHE[(sym, tf_str)] = (candles, atr_series)

def test_btc_filter(name, btc_mode="4H_EMA20", min_mat_1h=48, min_mat_4h=12):
    candidate_signals = []

    for (sym, tf_str), (candles, atr_series) in CANDLE_CACHE.items():
        min_mat_bars = min_mat_4h if tf_str == "4h" else min_mat_1h
        n = len(candles)
        max_mat_bars = 360 if tf_str == "4h" else 720

        for i in range(20, n - 4):
            c3, c2, c1 = candles[i], candles[i+1], candles[i+2]

            # BULLISH OB
            if c3["close"] < c3["open"] and c1["low"] > c3["high"]:
                gain = (max(c2["high"], c1["high"]) - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                if gain >= 0.050:
                    ob_high, ob_low = c3["high"], c3["low"]
                    ob_range = ob_high - ob_low
                    mt = (ob_high + ob_low) / 2.0
                    peak_runway = max(candles[k]["high"] for k in range(i+1, min(i+25, n)))
                    runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0
                    if runway_pct < 5.0: continue

                    eff_entry = round(ob_high - 0.05 * ob_range, 8)
                    broken = False
                    tap_idx = None
                    idm_low = min(candles[k]["low"] for k in range(max(0, i-3), min(i+4, n)))
                    has_swept_idm = False

                    for t in range(i+3, min(i + max_mat_bars, n)):
                        curr_c = candles[t]
                        if curr_c["close"] < ob_low: broken = True; break
                        if curr_c["low"] < idm_low: has_swept_idm = True
                        bars_alive = t - (i+2)
                        if bars_alive >= min_mat_bars and has_swept_idm:
                            if curr_c["low"] <= eff_entry * 1.0005 and curr_c["close"] >= ob_low:
                                c_range = curr_c["high"] - curr_c["low"]
                                l_wick = min(curr_c["open"], curr_c["close"]) - curr_c["low"]
                                w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                if w_ratio >= 0.18 and curr_c["close"] >= mt:
                                    tap_idx = t; break

                    if not broken and tap_idx is not None:
                        tap_time = candles[tap_idx]["time"]
                        allowed = True
                        if btc_mode == "4H_EMA20":
                            for t in btc_times_4h:
                                if t <= tap_time: allowed = btc_map_4h_ema20[t]
                                else: break
                        elif btc_mode == "4H_EMA50":
                            for t in btc_times_4h:
                                if t <= tap_time: allowed = btc_map_4h_ema50[t]
                                else: break
                        elif btc_mode == "4H_EMA200":
                            for t in btc_times_4h:
                                if t <= tap_time: allowed = btc_map_4h_ema200[t]
                                else: break
                        elif btc_mode == "1H_EMA20":
                            for t in btc_times_1h:
                                if t <= tap_time: allowed = btc_map_1h_ema20[t]
                                else: break
                        elif btc_mode == "NONE":
                            allowed = True

                        if allowed:
                            cur_atr = atr_series[tap_idx]
                            struct_sl = min(ob_low, candles[tap_idx]["low"]) - 0.20 * cur_atr
                            hard_sl = max(min(struct_sl, eff_entry * 0.9620), eff_entry * 0.9620)
                            soft_sl = (eff_entry + hard_sl) / 2.0
                            candidate_signals.append({
                                "symbol": sym, "tf": tf_str, "side": "BUY",
                                "entry_price": eff_entry, "tap_idx": tap_idx, "entry_time": tap_time,
                                "soft_sl": soft_sl, "hard_sl": hard_sl, "candles": candles
                            })

            # BEARISH OB
            if c3["close"] > c3["open"] and c1["high"] < c3["low"]:
                drop = (c3["high"] - min(c2["low"], c1["low"])) / c3["high"] if c3["high"] > 0 else 0.0
                if drop >= 0.050:
                    ob_high, ob_low = c3["high"], c3["low"]
                    ob_range = ob_high - ob_low
                    mt = (ob_high + ob_low) / 2.0
                    peak_runway = min(candles[k]["low"] for k in range(i+1, min(i+25, n)))
                    runway_pct = ((ob_low - peak_runway) / ob_low * 100.0) if ob_low > 0 else 0.0
                    if runway_pct < 5.0: continue

                    eff_entry = round(ob_low + 0.05 * ob_range, 8)
                    broken = False
                    tap_idx = None
                    idm_high = max(candles[k]["high"] for k in range(max(0, i-3), min(i+4, n)))
                    has_swept_idm = False

                    for t in range(i+3, min(i + max_mat_bars, n)):
                        curr_c = candles[t]
                        if curr_c["close"] > ob_high: broken = True; break
                        if curr_c["high"] > idm_high: has_swept_idm = True
                        bars_alive = t - (i+2)
                        if bars_alive >= min_mat_bars and has_swept_idm:
                            if curr_c["high"] >= eff_entry * 0.9995 and curr_c["close"] <= ob_high:
                                c_range = curr_c["high"] - curr_c["low"]
                                u_wick = curr_c["high"] - max(curr_c["open"], curr_c["close"])
                                w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                if w_ratio >= 0.18 and curr_c["close"] <= mt:
                                    tap_idx = t; break

                    if not broken and tap_idx is not None:
                        tap_time = candles[tap_idx]["time"]
                        allowed = True
                        if btc_mode == "4H_EMA20":
                            for t in btc_times_4h:
                                if t <= tap_time: allowed = not btc_map_4h_ema20[t]
                                else: break
                        elif btc_mode == "4H_EMA50":
                            for t in btc_times_4h:
                                if t <= tap_time: allowed = not btc_map_4h_ema50[t]
                                else: break
                        elif btc_mode == "4H_EMA200":
                            for t in btc_times_4h:
                                if t <= tap_time: allowed = not btc_map_4h_ema200[t]
                                else: break
                        elif btc_mode == "1H_EMA20":
                            for t in btc_times_1h:
                                if t <= tap_time: allowed = not btc_map_1h_ema20[t]
                                else: break
                        elif btc_mode == "NONE":
                            allowed = True

                        if allowed:
                            cur_atr = atr_series[tap_idx]
                            struct_sl = max(ob_high, candles[tap_idx]["high"]) + 0.20 * cur_atr
                            hard_sl = min(max(struct_sl, eff_entry * 1.0380), eff_entry * 1.0380)
                            soft_sl = (eff_entry + hard_sl) / 2.0
                            candidate_signals.append({
                                "symbol": sym, "tf": tf_str, "side": "SELL",
                                "entry_price": eff_entry, "tap_idx": tap_idx, "entry_time": tap_time,
                                "soft_sl": soft_sl, "hard_sl": hard_sl, "candles": candles
                            })

    candidate_signals.sort(key=lambda s: s["entry_time"])

    # Simulate trades
    tp_move_pct = 0.0280
    stage1_be_pct = 0.0160
    stage2_h_pct = 0.0180
    harvest_lock = 0.0090

    trade_outcomes = []
    for sig in candidate_signals:
        candles, tap_idx, side = sig["candles"], sig["tap_idx"], sig["side"]
        entry_p, hard_sl, soft_sl = sig["entry_price"], sig["hard_sl"], sig["soft_sl"]

        tp_price = round(entry_p * (1.0 + tp_move_pct), 8) if side == "BUY" else round(entry_p * (1.0 - tp_move_pct), 8)
        be_trigger = entry_p * (1.0 + stage1_be_pct) if side == "BUY" else entry_p * (1.0 - stage1_be_pct)
        be_sl = round(entry_p * 1.0010, 8) if side == "BUY" else round(entry_p * 0.9990, 8)
        harvest_trigger = entry_p * (1.0 + stage2_h_pct) if side == "BUY" else entry_p * (1.0 - stage2_h_pct)
        harvest_sl = round(entry_p * (1.0 + harvest_lock), 8) if side == "BUY" else round(entry_p * (1.0 - harvest_lock), 8)

        current_sl = soft_sl
        outcome = None
        exit_p = entry_p
        exit_time = candles[tap_idx]["time"]

        for k in range(tap_idx, min(tap_idx + 180, len(candles))):
            bar = candles[k]
            b_high, b_low, b_time = bar["high"], bar["low"], bar["time"]

            if side == "BUY":
                if b_high >= harvest_trigger:
                    if harvest_sl > current_sl: current_sl = harvest_sl
                elif b_high >= be_trigger:
                    if be_sl > current_sl: current_sl = be_sl

                if b_high >= tp_price: outcome = "TP_HIT"; exit_p = tp_price; exit_time = b_time; break
                elif b_low <= current_sl:
                    outcome = "HARVEST_STAGE2_LOCK" if current_sl == harvest_sl else ("BE_LOCK" if current_sl == be_sl else "SL_HIT")
                    exit_p = current_sl; exit_time = b_time; break
                elif b_low <= hard_sl: outcome = "SL_HIT"; exit_p = hard_sl; exit_time = b_time; break
            else:
                if b_low <= harvest_trigger:
                    if harvest_sl < current_sl: current_sl = harvest_sl
                elif b_low <= be_trigger:
                    if be_sl < current_sl: current_sl = be_sl

                if b_low <= tp_price: outcome = "TP_HIT"; exit_p = tp_price; exit_time = b_time; break
                elif b_high >= current_sl:
                    outcome = "HARVEST_STAGE2_LOCK" if current_sl == harvest_sl else ("BE_LOCK" if current_sl == be_sl else "SL_HIT")
                    exit_p = current_sl; exit_time = b_time; break
                elif b_high >= hard_sl: outcome = "SL_HIT"; exit_p = hard_sl; exit_time = b_time; break

        if outcome is None:
            last_c = candles[min(tap_idx + 180, len(candles) - 1)]
            exit_p = last_c["close"]; exit_time = last_c["time"]; outcome = "TIME_CLOSE"

        gross_pct = ((exit_p - entry_p) / entry_p * 100.0) if side == "BUY" else ((entry_p - exit_p) / entry_p * 100.0)
        trade_outcomes.append({**sig, "outcome": outcome, "exit_price": exit_p, "exit_time": exit_time, "gross_pct": gross_pct})

    # Deca Compounding (Round-Robin Rotating)
    sections = {s_id: {"balance": 50.0, "busy_until": 0} for s_id in range(1, 11)}
    sym_busy = {}
    rr_4h = 0
    rr_1h = 0
    executed_trades = []

    for t in trade_outcomes:
        sym, tf, e_time, x_time = t["symbol"], t["tf"], t["entry_time"], t["exit_time"]
        if sym_busy.get(sym, 0) > e_time: continue

        target_ids = [1, 2, 3, 4, 5] if tf == "4h" else [6, 7, 8, 9, 10]
        start_ptr = rr_4h if tf == "4h" else rr_1h
        sel_sec = None
        for step in range(len(target_ids)):
            s_id = target_ids[(start_ptr + step) % len(target_ids)]
            if sections[s_id]["busy_until"] <= e_time:
                sel_sec = s_id
                if tf == "4h": rr_4h = (start_ptr + step + 1) % len(target_ids)
                else: rr_1h = (start_ptr + step + 1) % len(target_ids)
                break
        if sel_sec is None: continue

        sec = sections[sel_sec]
        bal = sec["balance"]
        pos_size = bal * 5.0
        fee = pos_size * 0.0016
        net_pnl = pos_size * (t["gross_pct"] / 100.0) - fee
        sec["balance"] = round(max(1.0, bal + net_pnl), 2)
        sec["busy_until"] = x_time
        sym_busy[sym] = x_time + (2 * 3600 * 1000)
        executed_trades.append({**t, "net_pnl": net_pnl, "sec_id": sel_sec})

    tot = len(executed_trades)
    wins = sum(1 for t in executed_trades if t["net_pnl"] > 0)
    tp_hits = sum(1 for t in executed_trades if t["outcome"] == "TP_HIT")
    harvest_hits = sum(1 for t in executed_trades if t["outcome"] == "HARVEST_STAGE2_LOCK")
    be_hits = sum(1 for t in executed_trades if t["outcome"] == "BE_LOCK")
    losses = tot - wins
    end_eq = sum(s["balance"] for s in sections.values())
    roi = (end_eq - 500.0) / 500.0 * 100.0
    wr = (wins / tot * 100.0) if tot else 0.0
    safe = ((wins + be_hits) / tot * 100.0) if tot else 0.0

    print(f"\n{name}", flush=True)
    print(f"  • Total Trades: {tot} ({tot/12:.1f}/month) | Win Rate: {wr:.1f}% ({wins}W / {losses}L)", flush=True)
    print(f"  • Capital Safety: {safe:.1f}% (Wins + BE: {wins + be_hits} protected / {tot})", flush=True)
    print(f"  • Direct TP (+14%): {tp_hits} | Harvest (+4.5%): {harvest_hits} | Break-Even (+0.1%): {be_hits}", flush=True)
    print(f"  • Portfolio Start: $500.00 | Ending Equity: ${end_eq:,.2f} ({roi:+,.1f}%)", flush=True)
    return {"name": name, "trades": tot, "wr": wr, "safe": safe, "end_eq": end_eq, "roi": roi, "tp": tp_hits, "harvest": harvest_hits, "be": be_hits}

if __name__ == "__main__":
    t0 = time.time()
    print("=" * 80, flush=True)
    print("BTC 20 EMA LAB: AUDITING VARIOUS BTC EMA CALIBRATIONS (1 FULL YEAR OOS)", flush=True)
    print("=" * 80, flush=True)

    # 1. Baseline: 4H EMA50 (Current Engine)
    test_btc_filter("[Benchmark] BTC 4H EMA50 (Current Baseline - Maturation 48h)", btc_mode="4H_EMA50", min_mat_1h=48)

    # 2. BTC 4H EMA20 (Fast 4H Trend) with 48h Maturation
    test_btc_filter("[Test 1] BTC 4H EMA20 (Fast 4H Trend - Maturation 48h)", btc_mode="4H_EMA20", min_mat_1h=48)

    # 3. BTC 4H EMA20 with 24h Maturation
    test_btc_filter("[Test 2] BTC 4H EMA20 (Fast 4H Trend - Maturation 24h)", btc_mode="4H_EMA20", min_mat_1h=24)

    # 4. BTC 4H EMA20 with 18h Maturation
    test_btc_filter("[Test 3] BTC 4H EMA20 (Fast 4H Trend - Maturation 18h)", btc_mode="4H_EMA20", min_mat_1h=18)

    # 5. BTC 1H EMA20 (Intraday Momentum on 1H) with 18h Maturation
    test_btc_filter("[Test 4] BTC 1H EMA20 (Intraday Responsive - Maturation 18h)", btc_mode="1H_EMA20", min_mat_1h=18)

    # 6. Comparison: BTC 4H EMA200 (Macro Anchor - Maturation 18h)
    test_btc_filter("[Test 5] BTC 4H EMA200 (Macro Anchor - Maturation 18h)", btc_mode="4H_EMA200", min_mat_1h=18)

    print(f"\nAudit completed in {time.time() - t0:.2f} seconds.", flush=True)
