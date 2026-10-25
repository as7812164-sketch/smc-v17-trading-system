"""
TEST FREQUENCY OPTIMIZATION AND GROWTH EXPANSION
Compares Baseline (Current strict 109 trades) vs High-Velocity Institutional Calibration.
"""
import os
import json
from datetime import datetime, timezone, timedelta

DATA_DIR = "historical_data"
IST = timezone(timedelta(hours=5, minutes=30))

files = [f for f in os.listdir(DATA_DIR) if f.endswith("_1h.json") and not "1y_audit" in f]
coins = [f.replace("_1h.json", "") for f in files]

# Load BTC
with open(os.path.join(DATA_DIR, "BTCUSDT_4h.json")) as f:
    btc_4h = json.load(f)
btc_closes = [float(c["close"]) for c in btc_4h]
k = 2.0 / 51.0
ema = [btc_closes[0]]
for p in btc_closes[1:]:
    ema.append(p * k + ema[-1] * (1.0 - k))
btc_map = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= ema[i]) for i in range(len(btc_4h))}
btc_times = sorted(btc_map.keys())

# BTC dump detection: prior candle dropped > 1.5%
btc_dump_map = {}
for i in range(1, len(btc_4h)):
    o = btc_4h[i-1]["open"]
    c = btc_4h[i-1]["close"]
    dump = (o - c) / o * 100.0 if o > 0 else 0.0
    btc_dump_map[btc_4h[i]["time"]] = dump >= 1.5

def get_btc_dump(t_ms):
    dumped = False
    for t in btc_times:
        if t <= t_ms: dumped = btc_dump_map.get(t, False)
        else: break
    return dumped

def run_experiment(mode="CURRENT_BASELINE"):
    """
    mode options:
    - 'CURRENT_BASELINE': 5% disp, 5% runway, 48b maturation, strict BTC EMA50 veto
    - 'OPTIMIZED_HIGH_FREQUENCY':
        * 1H: disp >= 3.0%, runway >= 3.0%, maturation >= 12b (12h)
        * 4H: disp >= 4.5%, runway >= 4.0%, maturation >= 8b (32h)
        * King BTC: Active Dump Shield (blocks longs during BTC dump >= 1.5%, rather than 76% binary veto)
        * 5% Boundary Entry + 0.20% Radar + Stepped Harvest intact!
    """
    candidate_signals = []

    for tf_str in ["4h", "1h"]:
        min_disp = 0.050 if mode == "CURRENT_BASELINE" else (0.045 if tf_str == "4h" else 0.030)
        min_runway = 5.0 if mode == "CURRENT_BASELINE" else (4.0 if tf_str == "4h" else 3.0)
        min_mat_bars = (12 if tf_str == "4h" else 48) if mode == "CURRENT_BASELINE" else (8 if tf_str == "4h" else 12)

        for sym in coins:
            path = os.path.join(DATA_DIR, f"{sym}_{tf_str}.json")
            if not os.path.exists(path): continue
            with open(path) as f: candles = json.load(f)
            n = len(candles)
            if n < 50: continue

            # ATR
            atr_series = [0.0] * n
            for k_idx in range(1, n):
                tr = max(candles[k_idx]["high"] - candles[k_idx]["low"],
                         abs(candles[k_idx]["high"] - candles[k_idx-1]["close"]),
                         abs(candles[k_idx]["low"] - candles[k_idx-1]["close"]))
                atr_series[k_idx] = tr if k_idx < 14 else (atr_series[k_idx-1] * 13 + tr) / 14

            max_mat_bars = 360 if tf_str == "4h" else 720
            search_start = 20

            for i in range(search_start, n - 4):
                c3 = candles[i]
                c2 = candles[i+1]
                c1 = candles[i+2]

                # BULLISH
                if c3["close"] < c3["open"] and c1["low"] > c3["high"]:
                    impulse_h = max(c2["high"], c1["high"])
                    gain = (impulse_h - c3["low"]) / c3["low"] if c3["low"] > 0 else 0.0
                    if gain >= min_disp:
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_range = ob_high - ob_low
                        mt = (ob_high + ob_low) / 2.0
                        peak_runway = max(candles[k]["high"] for k in range(i+1, min(i+25, n)))
                        runway_pct = ((peak_runway - ob_high) / ob_high * 100.0) if ob_high > 0 else 0.0
                        if runway_pct < min_runway: continue

                        eff_entry = round(ob_high - 0.05 * ob_range, 8)
                        radar_price = round(eff_entry * 1.0020, 8)

                        broken = False
                        tap_idx = None
                        idm_low = min(candles[k]["low"] for k in range(max(0, i-3), min(i+4, n)))
                        for t in range(i+3, min(i + max_mat_bars, n)):
                            curr_c = candles[t]
                            if curr_c["close"] < ob_low:
                                broken = True; break
                            bars_alive = t - (i+2)
                            idm_swept = any(candles[k]["low"] < idm_low for k in range(i+3, t+1)) or (curr_c["low"] < idm_low)
                            if bars_alive >= min_mat_bars and idm_swept:
                                if curr_c["low"] <= eff_entry * 1.0005 and curr_c["close"] >= ob_low:
                                    c_range = curr_c["high"] - curr_c["low"]
                                    l_wick = min(curr_c["open"], curr_c["close"]) - curr_c["low"]
                                    w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                    min_wick = 0.18 if mode == "CURRENT_BASELINE" else 0.14
                                    if w_ratio >= min_wick and curr_c["close"] >= mt:
                                        tap_idx = t; break

                        if not broken and tap_idx is not None:
                            tap_time = candles[tap_idx]["time"]
                            # BTC filter
                            allowed = False
                            if mode == "CURRENT_BASELINE":
                                # strict EMA50
                                for t in btc_times:
                                    if t <= tap_time: allowed = btc_map[t]
                                    else: break
                            else:
                                # Active Dump Shield: allowed if BTC did NOT dump >= 1.5%
                                allowed = not get_btc_dump(tap_time)

                            if allowed:
                                cur_atr = atr_series[tap_idx]
                                struct_sl = min(ob_low, candles[tap_idx]["low"]) - 0.20 * cur_atr
                                hard_sl = max(min(struct_sl, eff_entry * 0.9620), eff_entry * 0.9620)
                                soft_sl = (eff_entry + hard_sl) / 2.0
                                candidate_signals.append({
                                    "symbol": sym, "tf": tf_str, "side": "BUY",
                                    "entry_price": eff_entry, "radar_price": radar_price,
                                    "tap_idx": tap_idx, "entry_time": tap_time,
                                    "soft_sl": soft_sl, "hard_sl": hard_sl, "candles": candles
                                })

                # BEARISH
                if c3["close"] > c3["open"] and c1["high"] < c3["low"]:
                    impulse_l = min(c2["low"], c1["low"])
                    drop = (c3["high"] - impulse_l) / c3["high"] if c3["high"] > 0 else 0.0
                    if drop >= min_disp:
                        ob_high = c3["high"]
                        ob_low = c3["low"]
                        ob_range = ob_high - ob_low
                        mt = (ob_high + ob_low) / 2.0
                        peak_runway = min(candles[k]["low"] for k in range(i+1, min(i+25, n)))
                        runway_pct = ((ob_low - peak_runway) / ob_low * 100.0) if ob_low > 0 else 0.0
                        if runway_pct < min_runway: continue

                        eff_entry = round(ob_low + 0.05 * ob_range, 8)
                        radar_price = round(eff_entry * 0.9980, 8)

                        broken = False
                        tap_idx = None
                        idm_high = max(candles[k]["high"] for k in range(max(0, i-3), min(i+4, n)))
                        for t in range(i+3, min(i + max_mat_bars, n)):
                            curr_c = candles[t]
                            if curr_c["close"] > ob_high:
                                broken = True; break
                            bars_alive = t - (i+2)
                            idm_swept = any(candles[k]["high"] > idm_high for k in range(i+3, t+1)) or (curr_c["high"] > idm_high)
                            if bars_alive >= min_mat_bars and idm_swept:
                                if curr_c["high"] >= eff_entry * 0.9995 and curr_c["close"] <= ob_high:
                                    c_range = curr_c["high"] - curr_c["low"]
                                    u_wick = curr_c["high"] - max(curr_c["open"], curr_c["close"])
                                    w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                    min_wick = 0.18 if mode == "CURRENT_BASELINE" else 0.14
                                    if w_ratio >= min_wick and curr_c["close"] <= mt:
                                        tap_idx = t; break

                        if not broken and tap_idx is not None:
                            tap_time = candles[tap_idx]["time"]
                            allowed = False
                            if mode == "CURRENT_BASELINE":
                                for t in btc_times:
                                    if t <= tap_time: allowed = not btc_map[t]
                                    else: break
                            else:
                                allowed = True # Shorts allowed in non-extreme pump

                            if allowed:
                                cur_atr = atr_series[tap_idx]
                                struct_sl = max(ob_high, candles[tap_idx]["high"]) + 0.20 * cur_atr
                                hard_sl = min(max(struct_sl, eff_entry * 1.0380), eff_entry * 1.0380)
                                soft_sl = (eff_entry + hard_sl) / 2.0
                                candidate_signals.append({
                                    "symbol": sym, "tf": tf_str, "side": "SELL",
                                    "entry_price": eff_entry, "radar_price": radar_price,
                                    "tap_idx": tap_idx, "entry_time": tap_time,
                                    "soft_sl": soft_sl, "hard_sl": hard_sl, "candles": candles
                                })

    # Sort signals
    candidate_signals.sort(key=lambda s: s["entry_time"])

    # Simulate forward trades
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
        hard_sl = sig["hard_sl"]
        soft_sl = sig["soft_sl"]

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
            b_high = bar["high"]
            b_low = bar["low"]
            b_time = bar["time"]

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

    # Deca Compounding Simulation (Round-Robin Rotating)
    sections = {s_id: {"balance": 50.0, "busy_until": 0, "trades": 0, "wins": 0} for s_id in range(1, 11)}
    sym_busy = {}
    rr_4h = 0
    rr_1h = 0
    executed_trades = []

    for t in trade_outcomes:
        sym = t["symbol"]; tf = t["tf"]; e_time = t["entry_time"]; x_time = t["exit_time"]
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
        sec["trades"] += 1
        if net_pnl > 0: sec["wins"] += 1
        sym_busy[sym] = x_time + (2 * 3600 * 1000)

        executed_trades.append({**t, "sec_id": sel_sec, "net_pnl": net_pnl, "sec_bal": sec["balance"]})

    tot_trades = len(executed_trades)
    wins = sum(1 for t in executed_trades if t["net_pnl"] > 0)
    tp_hits = sum(1 for t in executed_trades if t["outcome"] == "TP_HIT")
    harvest_hits = sum(1 for t in executed_trades if t["outcome"] == "HARVEST_STAGE2_LOCK")
    be_hits = sum(1 for t in executed_trades if t["outcome"] == "BE_LOCK")
    losses = tot_trades - wins
    end_eq = sum(s["balance"] for s in sections.values())
    roi = (end_eq - 500.0) / 500.0 * 100.0
    wr = (wins / tot_trades * 100.0) if tot_trades else 0.0
    safe_rate = ((wins + be_hits) / tot_trades * 100.0) if tot_trades else 0.0

    print(f"\n[{mode}] RESULTS:")
    print(f"  • Total Signals Found:      {len(candidate_signals)}")
    print(f"  • Executed Trades in 10 Sec: {tot_trades} trades")
    print(f"  • Direct Win Rate:           {wr:.1f}% ({wins}W / {losses}L)")
    print(f"      - Direct TP (+14% ROE): {tp_hits}")
    print(f"      - Stage 2 Harvest (+4.5% ROE): {harvest_hits}")
    print(f"      - Break-Even Exits:     {be_hits}")
    print(f"  • Capital Safety Rate:       {safe_rate:.1f}%")
    print(f"  • Total Portfolio Start:     $500.00 USDT")
    print(f"  • Total Portfolio Ending:    ${end_eq:,.2f} USDT ({roi:+,.1f}%)")
    print(f"  • Average Trades / Month:    {tot_trades / 12:.1f} trades/month")
    return {"trades": tot_trades, "wr": wr, "end_eq": end_eq, "roi": roi}

if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING COMPARATIVE AUDIT ON 1-YEAR OOS DATA")
    print("=" * 80)
    run_experiment("CURRENT_BASELINE")
    run_experiment("OPTIMIZED_HIGH_FREQUENCY")
