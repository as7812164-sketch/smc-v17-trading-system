"""
Simulate exact Deca Matrix Compounding ($500 starting equity, 10 sections @ $50 each)
for Model A (50% MT) vs Model B (Boundary + 15m OF) on 1H and 4H setups.
"""
import os
import sys
import json

from run_experiment_boundary_orderflow_vs_50mt import (
    load_15m_data, resample_15m_to_higher_tf, calculate_ema
)

def run_deca_compounding_sim():
    data_15m = load_15m_data()
    btc_15m = data_15m.get("BTCUSDT", [])
    btc_4h = resample_15m_to_higher_tf(btc_15m, 4)
    btc_closes_4h = [c["close"] for c in btc_4h]
    btc_ema50_4h = calculate_ema(btc_closes_4h, 50)
    btc_4h_ema50_map = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_ema50_4h[i]) for i in range(len(btc_4h))}

    tp_spot_pct = 0.0280    # +14.0% ROE at 5x
    sl_spot_pct = 0.0280    # -14.0% ROE at 5x
    armor_spot_pct = 0.0160 # +8.0% ROE at 5x -> Locks BE +0.10%
    be_lock_pct = 0.0010

    for target_tf_hours in [4, 1]:
        tf_name = f"{target_tf_hours}H"
        all_setups = []

        for sym, c15_list in data_15m.items():
            c_high_tf = resample_15m_to_higher_tf(c15_list, target_tf_hours)
            n_htf = len(c_high_tf)
            if n_htf < 30: continue
            
            for i in range(15, n_htf - 10):
                # Bullish OB
                if c_high_tf[i]["low"] == min(c["low"] for c in c_high_tf[max(0, i-10):i+1]):
                    sub = c_high_tf[i:min(i+16, n_htf)]
                    highs = [c["high"] for c in sub]
                    max_h = max(highs)
                    h_idx = i + highs.index(max_h)
                    if h_idx > i + 2:
                        gain = (max_h - c_high_tf[i]["low"]) / c_high_tf[i]["low"]
                        if gain >= 0.050:
                            has_fvg = (c_high_tf[i+2]["low"] > c_high_tf[i]["high"]) if i+2 < n_htf else False
                            if not has_fvg and i+3 < n_htf:
                                has_fvg = (c_high_tf[i+3]["low"] > c_high_tf[i+1]["high"])
                            if has_fvg:
                                all_setups.append({
                                    "sym": sym, "tf": tf_name, "side": "BUY",
                                    "ob_high": c_high_tf[i]["high"], "ob_low": c_high_tf[i]["low"],
                                    "mt": (c_high_tf[i]["high"] + c_high_tf[i]["low"]) / 2.0,
                                    "h_idx_time": c_high_tf[h_idx]["time"], "c15_list": c15_list
                                })
                # Bearish OB
                if c_high_tf[i]["high"] == max(c["high"] for c in c_high_tf[max(0, i-10):i+1]):
                    sub = c_high_tf[i:min(i+16, n_htf)]
                    lows = [c["low"] for c in sub]
                    min_l = min(lows)
                    l_idx = i + lows.index(min_l)
                    if l_idx > i + 2:
                        drop = (c_high_tf[i]["high"] - min_l) / c_high_tf[i]["high"]
                        if drop >= 0.050:
                            has_fvg = (c_high_tf[i+2]["high"] < c_high_tf[i]["low"]) if i+2 < n_htf else False
                            if not has_fvg and i+3 < n_htf:
                                has_fvg = (c_high_tf[i+3]["high"] < c_high_tf[i+1]["low"])
                            if has_fvg:
                                all_setups.append({
                                    "sym": sym, "tf": tf_name, "side": "SELL",
                                    "ob_high": c_high_tf[i]["high"], "ob_low": c_high_tf[i]["low"],
                                    "mt": (c_high_tf[i]["high"] + c_high_tf[i]["low"]) / 2.0,
                                    "h_idx_time": c_high_tf[l_idx]["time"], "c15_list": c15_list
                                })

        all_setups.sort(key=lambda x: x["h_idx_time"])
        
        trades_a = []
        trades_b = []

        for s in all_setups:
            c15 = s["c15_list"]
            h_time = s["h_idx_time"]
            side = s["side"]
            ob_high = s["ob_high"]
            ob_low = s["ob_low"]
            mt = s["mt"]

            start_15m_idx = None
            for idx, c in enumerate(c15):
                if c["time"] >= h_time:
                    start_15m_idx = idx
                    break
            if start_15m_idx is None or start_15m_idx + 10 >= len(c15):
                continue

            search_window = c15[start_15m_idx : min(start_15m_idx + 180, len(c15))]
            b_idx = None
            mt_idx = None
            for idx, c in enumerate(search_window):
                if side == "BUY":
                    if b_idx is None and c["low"] <= ob_high: b_idx = idx
                    if mt_idx is None and c["low"] <= mt: mt_idx = idx
                else:
                    if b_idx is None and c["high"] >= ob_low: b_idx = idx
                    if mt_idx is None and c["high"] >= mt: mt_idx = idx

            # Evaluate Model A
            if mt_idx is not None:
                tap_time = search_window[mt_idx]["time"]
                curr_4h_start = tap_time - (tap_time % (4 * 3600 * 1000))
                prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                btc_is_bull = btc_4h_ema50_map.get(prev_4h_ts, True)
                if (side == "BUY" and btc_is_bull) or (side == "SELL" and not btc_is_bull):
                    entry = mt
                    tp = entry * (1.0 + tp_spot_pct) if side == "BUY" else entry * (1.0 - tp_spot_pct)
                    sl = entry * (1.0 - sl_spot_pct) if side == "BUY" else entry * (1.0 + sl_spot_pct)
                    armor = entry * (1.0 + armor_spot_pct) if side == "BUY" else entry * (1.0 - armor_spot_pct)
                    be = entry * (1.0 + be_lock_pct) if side == "BUY" else entry * (1.0 - be_lock_pct)
                    locked = False
                    outcome = "LOSS"
                    exit_time = search_window[-1]["time"]
                    for c in search_window[mt_idx + 1:]:
                        if side == "BUY":
                            if not locked and c["high"] >= armor:
                                locked = True; sl = be
                            if c["high"] >= tp:
                                outcome = "WIN"; exit_time = c["time"]; break
                            elif c["low"] <= sl:
                                outcome = "BREAKEVEN" if locked else "LOSS"
                                exit_time = c["time"]; break
                        else:
                            if not locked and c["low"] <= armor:
                                locked = True; sl = be
                            if c["low"] <= tp:
                                outcome = "WIN"; exit_time = c["time"]; break
                            elif c["high"] >= sl:
                                outcome = "BREAKEVEN" if locked else "LOSS"
                                exit_time = c["time"]; break
                    trades_a.append({"time": tap_time, "exit_time": exit_time, "outcome": outcome})

            # Evaluate Model B
            if b_idx is not None:
                tap_15m = search_window[b_idx]
                next_15m = search_window[b_idx + 1] if b_idx + 1 < len(search_window) else tap_15m
                delta_tap = float(tap_15m.get("delta", 0.0))
                delta_next = float(next_15m.get("delta", 0.0))
                vol_tap = float(tap_15m.get("volume", 1.0)) or 1.0
                tbuy_ratio = float(tap_15m.get("taker_buy", 0.0)) / vol_tap
                of_ok = (delta_tap > 0 or delta_next > 0 or tbuy_ratio >= 0.51) if side == "BUY" else (delta_tap < 0 or delta_next < 0 or tbuy_ratio <= 0.49)
                if of_ok:
                    entry = ob_high if side == "BUY" else ob_low
                    tp = entry * (1.0 + tp_spot_pct) if side == "BUY" else entry * (1.0 - tp_spot_pct)
                    sl = entry * (1.0 - sl_spot_pct) if side == "BUY" else entry * (1.0 + sl_spot_pct)
                    armor = entry * (1.0 + armor_spot_pct) if side == "BUY" else entry * (1.0 - armor_spot_pct)
                    be = entry * (1.0 + be_lock_pct) if side == "BUY" else entry * (1.0 - be_lock_pct)
                    locked = False
                    outcome = "LOSS"
                    exit_time = search_window[-1]["time"]
                    for c in search_window[b_idx + 1:]:
                        if side == "BUY":
                            if not locked and c["high"] >= armor:
                                locked = True; sl = be
                            if c["high"] >= tp:
                                outcome = "WIN"; exit_time = c["time"]; break
                            elif c["low"] <= sl:
                                outcome = "BREAKEVEN" if locked else "LOSS"
                                exit_time = c["time"]; break
                        else:
                            if not locked and c["low"] <= armor:
                                locked = True; sl = be
                            if c["low"] <= tp:
                                outcome = "WIN"; exit_time = c["time"]; break
                            elif c["high"] >= sl:
                                outcome = "BREAKEVEN" if locked else "LOSS"
                                exit_time = c["time"]; break
                    trades_b.append({"time": search_window[b_idx]["time"], "exit_time": exit_time, "outcome": outcome})

        def run_isolated_deca(trade_list):
            trade_list.sort(key=lambda x: x["time"])
            # 5 sections for this timeframe (as in production: 5 sections for 4H, 5 for 1H)
            sections = [50.0] * 5
            sec_idx = 0
            for t in trade_list:
                bal = sections[sec_idx]
                if t["outcome"] == "WIN":
                    sections[sec_idx] += bal * 0.140 # +14% ROE
                elif t["outcome"] == "LOSS":
                    sections[sec_idx] = max(1.0, sections[sec_idx] - bal * 0.140) # -14% ROE
                elif t["outcome"] == "BREAKEVEN":
                    sections[sec_idx] += bal * 0.005 # +0.50% net
                sec_idx = (sec_idx + 1) % 5
            return sum(sections), sections

        eq_a, sec_a = run_isolated_deca(trades_a)
        eq_b, sec_b = run_isolated_deca(trades_b)
        print(f"\n=======================================================")
        print(f"💰 {tf_name} TIMEFRAME DECA COMPOUNDING SIMULATION ($250 START)")
        print(f"=======================================================")
        print(f"MODEL A (50% MT):          Final Equity = ${eq_a:.2f} (from $250.00) across {len(trades_a)} trades")
        print(f"MODEL B (BOUNDARY + 15M OF): Final Equity = ${eq_b:.2f} (from $250.00) across {len(trades_b)} trades")

if __name__ == "__main__":
    run_deca_compounding_sim()
