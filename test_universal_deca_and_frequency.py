"""
TEST UNIVERSAL DECA ALLOCATION + TIME-FRAME EXPANSION
Tests unlocking full utilization of all 10 sections and optimal frequency calibrations.
"""
import os
import json
import time

DATA_DIR = "historical_data"
files = [f for f in os.listdir(DATA_DIR) if f.endswith("_1h.json") and not "1y_audit" in f]
coins = sorted([f.replace("_1h.json", "") for f in files])

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

# Load datasets and synthesize 2H
CANDLE_CACHE = {}
for sym in coins:
    # 4H
    p4 = os.path.join(DATA_DIR, f"{sym}_4h.json")
    if os.path.exists(p4):
        with open(p4) as f: c4 = json.load(f)
        if len(c4) >= 50:
            atr = [0.0] * len(c4)
            for k in range(1, len(c4)):
                tr = max(c4[k]["high"]-c4[k]["low"], abs(c4[k]["high"]-c4[k-1]["close"]), abs(c4[k]["low"]-c4[k-1]["close"]))
                atr[k] = tr if k < 14 else (atr[k-1]*13 + tr) / 14
            CANDLE_CACHE[(sym, "4h")] = (c4, atr)

    # 1H
    p1 = os.path.join(DATA_DIR, f"{sym}_1h.json")
    if os.path.exists(p1):
        with open(p1) as f: c1 = json.load(f)
        if len(c1) >= 50:
            atr = [0.0] * len(c1)
            for k in range(1, len(c1)):
                tr = max(c1[k]["high"]-c1[k]["low"], abs(c1[k]["high"]-c1[k-1]["close"]), abs(c1[k]["low"]-c1[k-1]["close"]))
                atr[k] = tr if k < 14 else (atr[k-1]*13 + tr) / 14
            CANDLE_CACHE[(sym, "1h")] = (c1, atr)

            # Synthesize 2H candles
            c2 = []
            for idx in range(0, len(c1) - 1, 2):
                bar1, bar2 = c1[idx], c1[idx+1]
                c2.append({
                    "time": bar1["time"],
                    "open": bar1["open"],
                    "high": max(bar1["high"], bar2["high"]),
                    "low": min(bar1["low"], bar2["low"]),
                    "close": bar2["close"],
                    "volume": bar1.get("volume", 0) + bar2.get("volume", 0)
                })
            if len(c2) >= 50:
                atr2 = [0.0] * len(c2)
                for k in range(1, len(c2)):
                    tr = max(c2[k]["high"]-c2[k]["low"], abs(c2[k]["high"]-c2[k-1]["close"]), abs(c2[k]["low"]-c2[k-1]["close"]))
                    atr2[k] = tr if k < 14 else (atr2[k-1]*13 + tr) / 14
                CANDLE_CACHE[(sym, "2h")] = (c2, atr2)

print(f"Loaded {len(CANDLE_CACHE)} pair-timeframe datasets (including 2H resampled).", flush=True)

def simulate_engine(name, timeframes=["4h", "1h"], min_mat={"4h": 12, "2h": 12, "1h": 24}, btc_mode="EMA50", universal_sections=False):
    candidate_signals = []

    for (sym, tf_str), (candles, atr_series) in CANDLE_CACHE.items():
        if tf_str not in timeframes: continue
        min_mat_bars = min_mat.get(tf_str, 12)
        n = len(candles)
        max_mat_bars = 720 if tf_str == "1h" else 360

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

    # Portfolio Deca Compounding
    sections = {s_id: {"balance": 50.0, "busy_until": 0} for s_id in range(1, 11)}
    sym_busy = {}
    rr_ptr = 0
    executed_trades = []

    for t in trade_outcomes:
        sym, tf, e_time, x_time = t["symbol"], t["tf"], t["entry_time"], t["exit_time"]
        if sym_busy.get(sym, 0) > e_time: continue

        if universal_sections:
            target_ids = list(range(1, 11))
        else:
            target_ids = [1, 2, 3, 4, 5] if tf == "4h" else [6, 7, 8, 9, 10]

        sel_sec = None
        for step in range(len(target_ids)):
            s_id = target_ids[(rr_ptr + step) % len(target_ids)]
            if sections[s_id]["busy_until"] <= e_time:
                sel_sec = s_id
                rr_ptr = (rr_ptr + step + 1) % len(target_ids)
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
    print(f"  • Executed Trades: {tot} ({tot/12:.1f}/mo) | WinRate: {wr:.1f}% ({wins}W / {losses}L) | Safety: {safe:.1f}%", flush=True)
    print(f"  • Direct TP (+14%): {tp_hits} | Harvest (+4.5%): {harvest_hits} | Break-Even (+0.1%): {be_hits}", flush=True)
    print(f"  • Portfolio Start: $500.00 | Ending: ${end_eq:,.2f} ({roi:+,.1f}%)", flush=True)

if __name__ == "__main__":
    t0 = time.time()
    print("=" * 80, flush=True)
    print("DECA ALLOCATION & MULTI-TIMEFRAME COMPREHENSIVE EXPERIMENT", flush=True)
    print("=" * 80, flush=True)
    
    simulate_engine("Option 1: Baseline (Isolated 4H/1H, Maturation 48h/12b, BTC EMA50)",
                    timeframes=["4h", "1h"], min_mat={"4h": 12, "1h": 48}, btc_mode="EMA50", universal_sections=False)

    simulate_engine("Option 2: Universal Sections (Any Section can take 4H/1H, Maturation 24h 1H, BTC EMA50)",
                    timeframes=["4h", "1h"], min_mat={"4h": 12, "1h": 24}, btc_mode="EMA50", universal_sections=True)

    simulate_engine("Option 3: Universal Sections + Maturation 18h 1H + BTC EMA50",
                    timeframes=["4h", "1h"], min_mat={"4h": 12, "1h": 18}, btc_mode="EMA50", universal_sections=True)

    simulate_engine("Option 4: Universal Sections + Multi-TF (4H + 2H + 1H) + BTC EMA50",
                    timeframes=["4h", "2h", "1h"], min_mat={"4h": 12, "2h": 12, "1h": 18}, btc_mode="EMA50", universal_sections=True)

    simulate_engine("Option 5: Universal Sections + Multi-TF (4H + 2H + 1H) + BTC EMA200",
                    timeframes=["4h", "2h", "1h"], min_mat={"4h": 12, "2h": 12, "1h": 18}, btc_mode="EMA200", universal_sections=True)

    print(f"\nSimulation completed in {time.time() - t0:.2f} seconds.", flush=True)
