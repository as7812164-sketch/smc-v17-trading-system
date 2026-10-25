"""
COMPARING COMPOUNDING ARCHITECTURES ON IDENTICAL TRADES:
1. 10-Section Deca ($50 isolated per section)
2. 5-Slot Matrix ($100 per slot)
3. 3-Slot Matrix ($166 per slot)
4. Single Master Queue (1 Trade at a time, 100% of portfolio compounded)
5. Fixed Fractional Risk (5% Risk per trade on $500 portfolio)
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

btc_ema20 = calc_ema(btc_closes, 20)
btc_ema50 = calc_ema(btc_closes, 50)
btc_ema200 = calc_ema(btc_closes, 200)

# New Trend Filter: EMA20 >= EMA50 OR Close >= EMA200
btc_trend_map = {btc_4h[i]["time"]: ((btc_ema20[i] >= btc_ema50[i]) or (btc_4h[i]["close"] >= btc_ema200[i])) for i in range(len(btc_4h))}
btc_times = sorted(btc_trend_map.keys())

# Load datasets
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

# Detect candidate trades with 18h / 8h maturation and Multi-EMA BTC filter
candidate_signals = []
for (sym, tf_str), (candles, atr_series) in CANDLE_CACHE.items():
    min_mat_bars = 8 if tf_str == "4h" else 18
    n = len(candles)
    max_mat_bars = 360 if tf_str == "4h" else 720

    for i in range(20, n - 4):
        c3, c2, c1 = candles[i], candles[i+1], candles[i+2]

        # BULLISH
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
                    for tm in btc_times:
                        if tm <= tap_time: allowed = btc_trend_map[tm]
                        else: break

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

        # BEARISH
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
                    for tm in btc_times:
                        if tm <= tap_time: allowed = not btc_trend_map[tm]
                        else: break

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

# Simulate trade outcomes
trade_outcomes = []
for sig in candidate_signals:
    candles, tap_idx, side = sig["candles"], sig["tap_idx"], sig["side"]
    entry_p, hard_sl, soft_sl = sig["entry_price"], sig["hard_sl"], sig["soft_sl"]

    tp_price = round(entry_p * (1.0 + 0.0280), 8) if side == "BUY" else round(entry_p * (1.0 - 0.0280), 8)
    be_trigger = entry_p * (1.0 + 0.0160) if side == "BUY" else entry_p * (1.0 - 0.0160)
    be_sl = round(entry_p * 1.0010, 8) if side == "BUY" else round(entry_p * 0.9990, 8)
    harvest_trigger = entry_p * (1.0 + 0.0180) if side == "BUY" else entry_p * (1.0 - 0.0180)
    harvest_sl = round(entry_p * (1.0 + 0.0090), 8) if side == "BUY" else round(entry_p * (1.0 - 0.0090), 8)

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

def run_portfolio_mode(name, num_slots=10, slot_split=False, sequential=False, margin_pct=1.0):
    # Initial balance
    if sequential:
        balance = 500.0
        busy_until = 0
        executed = []
        for t in trade_outcomes:
            e_time, x_time = t["entry_time"], t["exit_time"]
            if e_time < busy_until: continue
            
            margin = balance * margin_pct
            pos_size = margin * 5.0
            fee = pos_size * 0.0016
            net_pnl = pos_size * (t["gross_pct"] / 100.0) - fee
            balance = max(10.0, balance + net_pnl)
            busy_until = x_time + (2 * 3600 * 1000)
            executed.append({**t, "net_pnl": net_pnl, "bal": balance})
        
        wins = sum(1 for x in executed if x["net_pnl"] > 0)
        tot = len(executed)
        print(f"\n[{name}]")
        print(f"  • Trades: {tot} | Win Rate: {wins/tot*100:.1f}% ({wins}W / {tot-wins}L)")
        print(f"  • Start: $500.00 | Ending Balance: ${balance:,.2f} (ROI: {(balance-500)/500*100:+,.1f}%)")
        return

    # Multi-slot mode
    slots = {i: {"balance": 500.0 / num_slots, "busy_until": 0} for i in range(num_slots)}
    sym_busy = {}
    rr_ptr = 0
    executed = []

    for t in trade_outcomes:
        sym, tf, e_time, x_time = t["symbol"], t["tf"], t["entry_time"], t["exit_time"]
        if sym_busy.get(sym, 0) > e_time: continue

        target_slots = list(range(num_slots))
        sel_slot = None
        for step in range(num_slots):
            s_id = (rr_ptr + step) % num_slots
            if slots[s_id]["busy_until"] <= e_time:
                sel_slot = s_id
                rr_ptr = (s_id + 1) % num_slots
                break
        if sel_slot is None: continue

        sec = slots[sel_slot]
        bal = sec["balance"]
        margin = bal * margin_pct
        pos_size = margin * 5.0
        fee = pos_size * 0.0016
        net_pnl = pos_size * (t["gross_pct"] / 100.0) - fee
        sec["balance"] = max(1.0, bal + net_pnl)
        sec["busy_until"] = x_time
        sym_busy[sym] = x_time + (2 * 3600 * 1000)
        executed.append({**t, "net_pnl": net_pnl})

    tot = len(executed)
    wins = sum(1 for x in executed if x["net_pnl"] > 0)
    end_eq = sum(s["balance"] for s in slots.values())
    roi = (end_eq - 500.0) / 500.0 * 100.0
    print(f"\n[{name}]")
    print(f"  • Trades: {tot} | Win Rate: {wins/tot*100:.1f}% ({wins}W / {tot-wins}L)")
    print(f"  • Start: $500.00 | Ending Equity: ${end_eq:,.2f} (ROI: {roi:+,.1f}%)")

if __name__ == "__main__":
    print("=" * 80)
    print("COMPARATIVE STUDY: WHERE DOES THE COMPOUNDING MONEY GO?")
    print("=" * 80)
    run_portfolio_mode("1. 10-Section Deca (Current: $50 each, Isolated Risk)", num_slots=10)
    run_portfolio_mode("2. 5-Slot Matrix ($100 per slot)", num_slots=5)
    run_portfolio_mode("3. 3-Slot Matrix ($166.67 per slot)", num_slots=3)
    run_portfolio_mode("4. Sequential Single Pool (1 Trade at a time, 100% Compounding)", sequential=True, margin_pct=1.0)
    run_portfolio_mode("5. Conservative Sequential Pool (1 Trade at a time, 20% Margin per trade)", sequential=True, margin_pct=0.20)
