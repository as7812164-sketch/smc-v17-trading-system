"""
TEST SMART FREQUENCY BOOST WITHOUT SACRIFICING WIN RATE (OPTIMIZED FAST ENGINE)
Tests surgical institutional calibrations to unlock 2x-3x more high-probability trades.
"""
import os
import json
import time

DATA_DIR = "historical_data"
files = [f for f in os.listdir(DATA_DIR) if f.endswith("_1h.json") and not "1y_audit" in f]
coins = sorted([f.replace("_1h.json", "") for f in files])

print("Pre-loading historical datasets into memory cache...", flush=True)
with open(os.path.join(DATA_DIR, "BTCUSDT_4h.json"), "r", encoding="utf-8") as f:
    btc_4h = json.load(f)
btc_closes = [float(c["close"]) for c in btc_4h]

def calc_ema(arr, period):
    k = 2.0 / (period + 1.0)
    res = [arr[0]]
    for p in arr[1:]: res.append(p * k + res[-1] * (1.0 - k))
    return res

btc_ema50 = calc_ema(btc_closes, 50)
btc_ema200 = calc_ema(btc_closes, 200)

btc_map_ema50 = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_ema50[i]) for i in range(len(btc_4h))}
btc_map_ema200 = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_ema200[i]) for i in range(len(btc_4h))}
btc_times = sorted(btc_map_ema50.keys())

# Pre-load all candles and pre-calculate ATR(14)
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

print(f"Loaded {len(CANDLE_CACHE)} pair-timeframe datasets successfully.\n", flush=True)

def run_smart_test(name, min_mat_1h=48, min_mat_4h=12, btc_mode="EMA50", min_disp=0.050, min_runway=5.0):
    candidate_signals = []

    for (sym, tf_str), (candles, atr_series) in CANDLE_CACHE.items():
        min_mat_bars = min_mat_4h if tf_str == "4h" else min_mat_1h
        n = len(candles)
        max_mat_bars = 360 if tf_str == "4h" else 720
        search_start = 20

        for i in range(search_start, n - 4):
            c3, c2, c1 = candles[i], candles[i+1], candles[i+2]

            # BULLISH OB
            if c3["close"] < c3["open"] and c1["low"] > c3["high"]:
                impulse_h = max(c2["high"], c1["high"])
                gain = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                if gain >= min_disp:
                    ob_high, ob_low = c3["high"], c3["low"]
                    ob_range = ob_high - ob_low
                    mt = (ob_high + ob_low) / 2.0
                    peak_runway = max(candles[k]["high"] for k in range(i+1, min(i+25, n)))
                    runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0
                    if runway_pct < min_runway: continue

                    eff_entry = round(ob_high - 0.05 * ob_range, 8)
                    broken = False
                    tap_idx = None
                    idm_low = min(candles[k]["low"] for k in range(max(0, i-3), min(i+4, n)))
                    has_swept_idm = False

                    for t in range(i+3, min(i + max_mat_bars, n)):
                        curr_c = candles[t]
                        if curr_c["close"] < ob_low:
                            broken = True
                            break
                        if curr_c["low"] < idm_low:
                            has_swept_idm = True
                        bars_alive = t - (i+2)
                        if bars_alive >= min_mat_bars and has_swept_idm:
                            if curr_c["low"] <= eff_entry * 1.0005 and curr_c["close"] >= ob_low:
                                c_range = curr_c["high"] - curr_c["low"]
                                l_wick = min(curr_c["open"], curr_c["close"]) - curr_c["low"]
                                w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                if w_ratio >= 0.18 and curr_c["close"] >= mt:
                                    tap_idx = t
                                    break

                    if not broken and tap_idx is not None:
                        tap_time = candles[tap_idx]["time"]
                        allowed = True
                        if btc_mode == "EMA50":
                            for t in btc_times:
                                if t <= tap_time: allowed = btc_map_ema50[t]
                                else: break
                        elif btc_mode == "EMA200":
                            for t in btc_times:
                                if t <= tap_time: allowed = btc_map_ema200[t]
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
                impulse_l = min(c2["low"], c1["low"])
                drop = (c3["high"] - impulse_l) / c3["high"] if c3["high"] > 0 else 0.0
                if drop >= min_disp:
                    ob_high, ob_low = c3["high"], c3["low"]
                    ob_range = ob_high - ob_low
                    mt = (ob_high + ob_low) / 2.0
                    peak_runway = min(candles[k]["low"] for k in range(i+1, min(i+25, n)))
                    runway_pct = ((ob_low - peak_runway) / ob_low * 100.0) if ob_low > 0 else 0.0
                    if runway_pct < min_runway: continue

                    eff_entry = round(ob_low + 0.05 * ob_range, 8)
                    broken = False
                    tap_idx = None
                    idm_high = max(candles[k]["high"] for k in range(max(0, i-3), min(i+4, n)))
                    has_swept_idm = False

                    for t in range(i+3, min(i + max_mat_bars, n)):
                        curr_c = candles[t]
                        if curr_c["close"] > ob_high:
                            broken = True
                            break
                        if curr_c["high"] > idm_high:
                            has_swept_idm = True
                        bars_alive = t - (i+2)
                        if bars_alive >= min_mat_bars and has_swept_idm:
                            if curr_c["high"] >= eff_entry * 0.9995 and curr_c["close"] <= ob_high:
                                c_range = curr_c["high"] - curr_c["low"]
                                u_wick = curr_c["high"] - max(curr_c["open"], curr_c["close"])
                                w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                if w_ratio >= 0.18 and curr_c["close"] <= mt:
                                    tap_idx = t
                                    break

                    if not broken and tap_idx is not None:
                        tap_time = candles[tap_idx]["time"]
                        allowed = True
                        if btc_mode == "EMA50":
                            for t in btc_times:
                                if t <= tap_time: allowed = not btc_map_ema50[t]
                                else: break
                        elif btc_mode == "EMA200":
                            for t in btc_times:
                                if t <= tap_time: allowed = not btc_map_ema200[t]
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
        candles = sig["candles"]
        tap_idx = sig["tap_idx"]
        side = sig["side"]
        entry_p = sig["entry_price"]
        hard_sl, soft_sl = sig["hard_sl"], sig["soft_sl"]

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

                if b_high >= tp_price:
                    outcome = "TP_HIT"; exit_p = tp_price; exit_time = b_time; break
                elif b_low <= current_sl:
                    outcome = "HARVEST_STAGE2_LOCK" if current_sl == harvest_sl else ("BE_LOCK" if current_sl == be_sl else "SL_HIT")
                    exit_p = current_sl; exit_time = b_time; break
                elif b_low <= hard_sl:
                    outcome = "SL_HIT"; exit_p = hard_sl; exit_time = b_time; break
            else:
                if b_low <= harvest_trigger:
                    if harvest_sl < current_sl: current_sl = harvest_sl
                elif b_low <= be_trigger:
                    if be_sl < current_sl: current_sl = be_sl

                if b_low <= tp_price:
                    outcome = "TP_HIT"; exit_p = tp_price; exit_time = b_time; break
                elif b_high >= current_sl:
                    outcome = "HARVEST_STAGE2_LOCK" if current_sl == harvest_sl else ("BE_LOCK" if current_sl == be_sl else "SL_HIT")
                    exit_p = current_sl; exit_time = b_time; break
                elif b_high >= hard_sl:
                    outcome = "SL_HIT"; exit_p = hard_sl; exit_time = b_time; break

        if outcome is None:
            last_c = candles[min(tap_idx + 180, len(candles) - 1)]
            exit_p = last_c["close"]; exit_time = last_c["time"]; outcome = "TIME_CLOSE"

        gross_pct = ((exit_p - entry_p) / entry_p * 100.0) if side == "BUY" else ((entry_p - exit_p) / entry_p * 100.0)
        trade_outcomes.append({
            **sig, "outcome": outcome, "exit_price": exit_p, "exit_time": exit_time, "gross_pct": gross_pct
        })

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

    print(f"\n[{name}]", flush=True)
    print(f"  • Trades: {tot} ({tot/12:.1f}/mo) | WinRate: {wr:.1f}% ({wins}W / {losses}L) | Safety: {safe:.1f}%", flush=True)
    print(f"  • Direct TP: {tp_hits} | Harvest +4.5%: {harvest_hits} | Break-Even: {be_hits}", flush=True)
    print(f"  • Portfolio Start: $500.00 | Ending: ${end_eq:,.2f} ({roi:+,.1f}%)", flush=True)
    return {"name": name, "trades": tot, "wr": wr, "safe": safe, "end_eq": end_eq, "roi": roi, "tp": tp_hits, "harvest": harvest_hits, "be": be_hits}

if __name__ == "__main__":
    t0 = time.time()
    print("=" * 80, flush=True)
    print("TESTING TARGETED CALIBRATIONS FOR FREQUENCY & GROWTH", flush=True)
    print("=" * 80, flush=True)
    run_smart_test("1. Baseline (Current: 48h 1H / 12b 4H, BTC EMA50)", min_mat_1h=48, min_mat_4h=12, btc_mode="EMA50")
    run_smart_test("2. 1H Maturation to 24h (1 Day), BTC EMA50", min_mat_1h=24, min_mat_4h=12, btc_mode="EMA50")
    run_smart_test("3. 1H Maturation to 18h, BTC EMA50", min_mat_1h=18, min_mat_4h=8, btc_mode="EMA50")
    run_smart_test("4. 1H Maturation 24h + BTC EMA200 (Macro Anchor)", min_mat_1h=24, min_mat_4h=12, btc_mode="EMA200")
    run_smart_test("5. Pure SMC Autonomy (No BTC Veto, 24h 1H)", min_mat_1h=24, min_mat_4h=12, btc_mode="NONE")
    run_smart_test("6. Pure SMC Autonomy (No BTC Veto, 18h 1H)", min_mat_1h=18, min_mat_4h=8, btc_mode="NONE")
    print(f"\nExecution finished in {time.time() - t0:.2f} seconds.", flush=True)
