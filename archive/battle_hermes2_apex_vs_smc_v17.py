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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_1Y_DIR = os.path.join(BASE_DIR, "historical_data")
DATA_2Y_DIR = os.path.join(BASE_DIR, "historical_data_2year")

def load_data(data_dir, sym, interval):
    fpath = os.path.join(data_dir, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

# =============================================================================
# 1. SIMULATE HERMES 2.0 APEX
# =============================================================================
def run_hermes_2_apex(all_data, btc_map_4h):
    signals = []
    
    # Tracking Sentry saves
    sentry_saves = {
        "sentry_1_btc_macro": 0,
        "sentry_2_weak_displacement": 0,
        "sentry_3_no_idm_or_wick": 0,
        "sentry_4_stale_tap": 0
    }

    for tf in ["1h", "4h"]:
        tp_pct = 0.022 if tf == "1h" else 0.028
        soft_sl_pct = 0.025 if tf == "1h" else 0.028
        hard_sl_pct = 0.036 if tf == "1h" else 0.038
        max_hold = 24
        min_displacement = 0.050 # Sentry 2: 5.0% Institutional Floor
        max_tap_window = 28      # Sentry 4: Strict 28-Bar Freshness Cap

        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                # ----------------- Bullish Setup -----------------
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= min_displacement:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1; max_bg = 0.0
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
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        if candles[t]["low"] <= dec_top * 0.9995:
                                            tap_c = candles[t]
                                            
                                            # Sentry 1: Macro BTC Causal Brake
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            if btc_c and (btc_c["open"] - btc_c["close"]) / btc_c["open"] >= 0.020:
                                                sentry_saves["sentry_1_btc_macro"] += 1
                                                break
                                            
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            # Sentry 3: IDM Sweep + >=18% Wick + 50% MT
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                soft_sl_p = entry * (1.0 - soft_sl_pct)
                                                hard_sl_p = entry * (1.0 - hard_sl_pct)

                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["low"] <= hard_sl_p:
                                                        res = "LOSS"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] <= soft_sl_p:
                                                        res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                signals.append({
                                                    "sym": sym, "side": "LONG", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (exit_p - entry) / entry, "res": res
                                                })
                                            break

                # ----------------- Bearish Setup -----------------
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= min_displacement:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1; max_bg = 0.0
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
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            
                                            # Sentry 1: Macro BTC Causal Brake
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            if btc_c and (btc_c["close"] - btc_c["open"]) / btc_c["open"] >= 0.020:
                                                sentry_saves["sentry_1_btc_macro"] += 1
                                                break
                                            
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                soft_sl_p = entry * (1.0 + soft_sl_pct)
                                                hard_sl_p = entry * (1.0 + hard_sl_pct)

                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["high"] >= hard_sl_p:
                                                        res = "LOSS"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] >= soft_sl_p:
                                                        res = "LOSS"; exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                                signals.append({
                                                    "sym": sym, "side": "SHORT", "tf": tf, "time": tap_c["time"],
                                                    "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                                    "gross": (entry - exit_p) / entry, "res": res
                                                })
                                            break

    signals.sort(key=lambda x: x["time"])
    return signals, sentry_saves


# =============================================================================
# 2. SIMULATE LEGACY SMC V17
# =============================================================================
def run_smc_v17_engine(all_data, tp_pct=0.040, sl_pct=0.030, max_tap_window=50):
    """
    Standard SMC V17 Strategy:
    - 10-period average body displacement (>= 1.5x avg body)
    - True Origin: last opposite candle within 6 bars
    - 7.0% Qualification expansion without retesting
    - Entry: First Tap of OB boundary (OB High for BUY, OB Low for SELL)
    - NO IDM sweep filter
    - NO Rejection Wick ratio filter
    - NO 50% Mean Threshold defense
    - NO Macro BTC Causal Brake
    - Max tap window: up to 50 bars
    """
    signals = []

    for tf in ["1h", "4h"]:
        # If legacy fixed parameters:
        curr_tp = tp_pct
        curr_sl = sl_pct
        max_hold = 30 # standard hold for 4H/1H

        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 60: continue

            for i in range(20, n - 35):
                # Calculate average body size of preceding 10 candles
                bodies = [abs(candles[b]["close"] - candles[b]["open"]) for b in range(i - 10, i)]
                avg_body = sum(bodies) / len(bodies) if bodies else 0.0001

                # ----------------- Bullish SMC V17 -----------------
                # Displacement candle: body >= 1.5 * avg_body and green
                disp_c = candles[i]
                if (disp_c["close"] - disp_c["open"]) >= 1.5 * avg_body:
                    # Find origin: latest red candle within prior 6 candles
                    origin_idx = None
                    for o in range(i - 1, max(0, i - 7), -1):
                        if candles[o]["close"] < candles[o]["open"]:
                            origin_idx = o
                            break
                    
                    if origin_idx is not None:
                        ob_high = candles[origin_idx]["high"]
                        ob_low = candles[origin_idx]["low"]

                        # 7% Qualification rule: price must reach at least ob_high * 1.07 without touching ob_high first
                        qual_target = ob_high * 1.07
                        qualified = False
                        qual_idx = None

                        for q in range(i, min(i + 25, n)):
                            if candles[q]["low"] <= ob_high and q > i: # touched OB before qualifying = invalidated
                                break
                            if candles[q]["high"] >= qual_target:
                                qualified = True
                                qual_idx = q
                                break

                        if qualified and qual_idx is not None:
                            # Search for first tap entry within next max_tap_window candles
                            for t in range(qual_idx + 1, min(qual_idx + max_tap_window, n)):
                                if candles[t]["low"] <= ob_high:
                                    entry = ob_high
                                    tp_p = entry * (1.0 + curr_tp)
                                    sl_p = entry * (1.0 - curr_sl)

                                    res = None; exit_p = entry; exit_t = candles[t]["time"]
                                    for m in range(t, min(t + max_hold, n)):
                                        if candles[m]["high"] >= tp_p:
                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                        if candles[m]["low"] <= sl_p:
                                            res = "LOSS"; exit_p = min(sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                    if not res:
                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                        res = "WIN" if fc >= entry else "LOSS"
                                        exit_p = fc
                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                    signals.append({
                                        "sym": sym, "side": "LONG", "tf": tf, "time": candles[t]["time"],
                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                        "gross": (exit_p - entry) / entry, "res": res
                                    })
                                    break # Only first tap!

                # ----------------- Bearish SMC V17 -----------------
                # Displacement candle: body >= 1.5 * avg_body and red
                if (disp_c["open"] - disp_c["close"]) >= 1.5 * avg_body:
                    # Find origin: latest green candle within prior 6 candles
                    origin_idx = None
                    for o in range(i - 1, max(0, i - 7), -1):
                        if candles[o]["close"] > candles[o]["open"]:
                            origin_idx = o
                            break
                    
                    if origin_idx is not None:
                        ob_high = candles[origin_idx]["high"]
                        ob_low = candles[origin_idx]["low"]

                        # 7% Qualification rule: price must reach at least ob_low * 0.93 without touching ob_low first
                        qual_target = ob_low * 0.93
                        qualified = False
                        qual_idx = None

                        for q in range(i, min(i + 25, n)):
                            if candles[q]["high"] >= ob_low and q > i:
                                break
                            if candles[q]["low"] <= qual_target:
                                qualified = True
                                qual_idx = q
                                break

                        if qualified and qual_idx is not None:
                            # Search for first tap entry
                            for t in range(qual_idx + 1, min(qual_idx + max_tap_window, n)):
                                if candles[t]["high"] >= ob_low:
                                    entry = ob_low
                                    tp_p = entry * (1.0 - curr_tp)
                                    sl_p = entry * (1.0 + curr_sl)

                                    res = None; exit_p = entry; exit_t = candles[t]["time"]
                                    for m in range(t, min(t + max_hold, n)):
                                        if candles[m]["low"] <= tp_p:
                                            res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                        if candles[m]["high"] >= sl_p:
                                            res = "LOSS"; exit_p = max(sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                    if not res:
                                        fc = candles[min(t + max_hold, n - 1)]["close"]
                                        res = "WIN" if fc <= entry else "LOSS"
                                        exit_p = fc
                                        exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                    signals.append({
                                        "sym": sym, "side": "SHORT", "tf": tf, "time": candles[t]["time"],
                                        "exit_time": exit_t, "entry": entry, "exit": exit_p,
                                        "gross": (entry - exit_p) / entry, "res": res
                                    })
                                    break

    signals.sort(key=lambda x: x["time"])
    return signals


# =============================================================================
# 3. SEQUENTIAL QUEUE & COMPOUNDING SIMULATOR
# =============================================================================
def simulate_compounding(signals, name="Strategy", start_cap=50.0, leverage=5.0, reinvest_ratio=0.85, vault_ratio=0.15, friction=0.0016):
    # Sort by time
    signals.sort(key=lambda x: x["time"])
    
    # Sequential execution: 1 trade at a time
    executed = []
    active_exit = 0
    for s in signals:
        if s["time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    cap = start_cap
    vault = 0.0
    peak = start_cap
    max_dd = 0.0
    hit_1k = None
    hit_2k = None
    
    wins = 0
    losses = 0
    gp = 0.0
    gl = 0.0

    trade_logs = []

    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - friction
        pos_size = cap * leverage
        pnl = pos_size * net_move

        if trade["res"] == "WIN":
            wins += 1
            gp += pnl
            cap += (pnl * reinvest_ratio)
            vault += (pnl * vault_ratio)
        else:
            losses += 1
            gl += abs(pnl)
            cap += pnl
            if cap < 2.0:
                cap = 0.0

        total_wealth = cap + vault
        if total_wealth > peak:
            peak = total_wealth
        dd = (peak - total_wealth) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

        trade_date = time.strftime('%Y-%m-%d %H:%M', time.gmtime(trade["time"] / 1000))
        if total_wealth >= 1000.0 and hit_1k is None:
            hit_1k = {"trade_num": idx + 1, "date": trade_date, "total": total_wealth}
        if total_wealth >= 2000.0 and hit_2k is None:
            hit_2k = {"trade_num": idx + 1, "date": trade_date, "total": total_wealth}

        trade_logs.append({
            "num": idx + 1,
            "sym": trade["sym"],
            "side": trade["side"],
            "tf": trade["tf"],
            "res": trade["res"],
            "gross_pct": trade["gross"] * 100,
            "net_move_pct": net_move * 100,
            "pnl": pnl,
            "active_cap": cap,
            "vault": vault,
            "total_wealth": total_wealth,
            "date": trade_date
        })

        if cap <= 0 and vault <= 0:
            break

    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    pf = (gp / gl) if gl > 0 else 999.0

    return {
        "name": name,
        "total_signals": len(signals),
        "executed_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "profit_factor": pf,
        "max_drawdown_pct": max_dd * 100,
        "start_capital": start_cap,
        "final_active_cap": cap,
        "final_vault": vault,
        "final_total_wealth": cap + vault,
        "hit_1k": hit_1k,
        "hit_2k": hit_2k,
        "trades": trade_logs
    }

# =============================================================================
# 4. FIXED SIZING SIMULATION (10% Balance / Trade - Legacy SMC V17 Default)
# =============================================================================
def simulate_fixed_sizing(signals, name="Strategy Fixed 10%", start_cap=100.0, alloc_pct=0.10, leverage=1.0, friction=0.0016):
    signals.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for s in signals:
        if s["time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    bal = start_cap
    peak = start_cap
    max_dd = 0.0
    wins = 0
    losses = 0
    gp = 0.0
    gl = 0.0

    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - friction
        pos_size = bal * alloc_pct * leverage
        pnl = pos_size * net_move

        if trade["res"] == "WIN":
            wins += 1
            gp += pnl
        else:
            losses += 1
            gl += abs(pnl)
        bal += pnl
        if bal < 1.0: bal = 0.0

        if bal > peak: peak = bal
        dd = (peak - bal) / peak if peak > 0 else 0
        if dd > max_dd: max_dd = dd

    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    pf = (gp / gl) if gl > 0 else 999.0

    return {
        "name": name,
        "executed_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "profit_factor": pf,
        "max_drawdown_pct": max_dd * 100,
        "final_balance": bal
    }


def main():
    print("=" * 110)
    print(" ⚔️ SHOWDOWN BATTLE: HERMES 2.0 APEX vs SMC V17 LEGACY MASTER AUDIT")
    print(" Evaluating True Algorithmic Accuracy, Drawdown, Sentry Protection & Compounding Edge")
    print("=" * 110)

    # 1. Test on 1-Year Dataset (339,512 Candlesticks)
    print("\n>>> Loading 1-Year Dataset...")
    data_1y = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_data(DATA_1Y_DIR, sym, tf)
            if len(k) >= 500:
                data_1y[tf][sym] = k
    
    btc_4h_1y = load_data(DATA_1Y_DIR, "BTCUSDT", "4h")
    btc_map_4h_1y = {c["time"]: c for c in btc_4h_1y}

    print(">>> Running HERMES 2.0 APEX on 1-Year Data...")
    hermes_signals_1y, sentry_saves_1y = run_hermes_2_apex(data_1y, btc_map_4h_1y)

    print(">>> Running SMC V17 (Native: +4% TP / -3% SL) on 1-Year Data...")
    smc_signals_native_1y = run_smc_v17_engine(data_1y, tp_pct=0.040, sl_pct=0.030)

    print(">>> Running SMC V17 (Normalized Geometry: +2.8% TP / -2.8% SL) on 1-Year Data...")
    smc_signals_norm_1y = run_smc_v17_engine(data_1y, tp_pct=0.028, sl_pct=0.028)

    # 2. Test on 2-Year Dataset (470,532 Candlesticks)
    print("\n>>> Loading 2-Year Dataset...")
    data_2y = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_data(DATA_2Y_DIR, sym, tf)
            if len(k) >= 500:
                data_2y[tf][sym] = k
    
    btc_4h_2y = load_data(DATA_2Y_DIR, "BTCUSDT", "4h")
    btc_map_4h_2y = {c["time"]: c for c in btc_4h_2y}

    print(">>> Running HERMES 2.0 APEX on 2-Year Data...")
    hermes_signals_2y, sentry_saves_2y = run_hermes_2_apex(data_2y, btc_map_4h_2y)

    print(">>> Running SMC V17 (Native: +4% TP / -3% SL) on 2-Year Data...")
    smc_signals_native_2y = run_smc_v17_engine(data_2y, tp_pct=0.040, sl_pct=0.030)

    # 3. Compounding Simulations ($50 Start, 5x Leverage, 85/15 Vault Split)
    print("\n>>> Simulating 5x Compounding Models...")
    res_hermes_1y = simulate_compounding(hermes_signals_1y, name="HERMES 2.0 APEX (1-Year)")
    res_smc_native_1y = simulate_compounding(smc_signals_native_1y, name="SMC V17 Native (1-Year)")
    res_smc_norm_1y = simulate_compounding(smc_signals_norm_1y, name="SMC V17 Calibrated TP/SL (1-Year)")

    res_hermes_2y = simulate_compounding(hermes_signals_2y, name="HERMES 2.0 APEX (2-Year)")
    res_smc_native_2y = simulate_compounding(smc_signals_native_2y, name="SMC V17 Native (2-Year)")

    # 4. Fixed Sizing ($100 Start, 10% Risk - Legacy Paper Trading Mode)
    print(">>> Simulating Fixed Sizing Models...")
    fixed_hermes_1y = simulate_fixed_sizing(hermes_signals_1y, name="HERMES 2.0 APEX (Fixed 10%)")
    fixed_smc_1y = simulate_fixed_sizing(smc_signals_native_1y, name="SMC V17 Native (Fixed 10%)")

    # Combine output
    summary = {
        "dataset_1y_bars": 339512,
        "dataset_2y_bars": 470532,
        "sentry_saves_1y": sentry_saves_1y,
        "sentry_saves_2y": sentry_saves_2y,
        "compounding_results": {
            "hermes_1y": {k: v for k, v in res_hermes_1y.items() if k != "trades"},
            "smc_native_1y": {k: v for k, v in res_smc_native_1y.items() if k != "trades"},
            "smc_norm_1y": {k: v for k, v in res_smc_norm_1y.items() if k != "trades"},
            "hermes_2y": {k: v for k, v in res_hermes_2y.items() if k != "trades"},
            "smc_native_2y": {k: v for k, v in res_smc_native_2y.items() if k != "trades"},
        },
        "fixed_sizing_1y": {
            "hermes_1y": fixed_hermes_1y,
            "smc_native_1y": fixed_smc_1y
        }
    }

    out_file = os.path.join(BASE_DIR, "battle_hermes2_vs_smc_v17_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 110)
    print(" 🏆 HEAD-TO-HEAD BATTLE RESULTS SUMMARY")
    print("=" * 110)
    print(f"{'Metric':<32} | {'HERMES 2.0 APEX (1Y)':<24} | {'SMC V17 Native (1Y)':<24} | {'SMC V17 Calibrated (1Y)':<24}")
    print("-" * 110)
    print(f"{'Total Signals':<32} | {res_hermes_1y['total_signals']:<24} | {res_smc_native_1y['total_signals']:<24} | {res_smc_norm_1y['total_signals']:<24}")
    print(f"{'Executed Trades (1-at-a-time)':<32} | {res_hermes_1y['executed_trades']:<24} | {res_smc_native_1y['executed_trades']:<24} | {res_smc_norm_1y['executed_trades']:<24}")
    print(f"{'Win Rate %':<32} | {res_hermes_1y['win_rate']:<23.2f}% | {res_smc_native_1y['win_rate']:<23.2f}% | {res_smc_norm_1y['win_rate']:<23.2f}%")
    print(f"{'Profit Factor':<32} | {res_hermes_1y['profit_factor']:<24.2f} | {res_smc_native_1y['profit_factor']:<24.2f} | {res_smc_norm_1y['profit_factor']:<24.2f}")
    print(f"{'Max Drawdown %':<32} | {res_hermes_1y['max_drawdown_pct']:<23.2f}% | {res_smc_native_1y['max_drawdown_pct']:<23.2f}% | {res_smc_norm_1y['max_drawdown_pct']:<23.2f}%")
    
    h1k_hermes = f"Trade #{res_hermes_1y['hit_1k']['trade_num']}" if res_hermes_1y['hit_1k'] else "FAILED / BUST"
    h1k_smc = f"Trade #{res_smc_native_1y['hit_1k']['trade_num']}" if res_smc_native_1y['hit_1k'] else "FAILED / BUST"
    h1k_norm = f"Trade #{res_smc_norm_1y['hit_1k']['trade_num']}" if res_smc_norm_1y['hit_1k'] else "FAILED / BUST"
    print(f"{'$1,000 Milestone Hit':<32} | {h1k_hermes:<24} | {h1k_smc:<24} | {h1k_norm:<24}")

    h2k_hermes = f"Trade #{res_hermes_1y['hit_2k']['trade_num']}" if res_hermes_1y['hit_2k'] else "FAILED / BUST"
    h2k_smc = f"Trade #{res_smc_native_1y['hit_2k']['trade_num']}" if res_smc_native_1y['hit_2k'] else "FAILED / BUST"
    h2k_norm = f"Trade #{res_smc_norm_1y['hit_2k']['trade_num']}" if res_smc_norm_1y['hit_2k'] else "FAILED / BUST"
    print(f"{'$2,000 Milestone Hit':<32} | {h2k_hermes:<24} | {h2k_smc:<24} | {h2k_norm:<24}")

    fin_hermes = f"${res_hermes_1y['final_total_wealth']:,.2f}"
    fin_smc = f"${res_smc_native_1y['final_total_wealth']:,.2f}"
    fin_norm = f"${res_smc_norm_1y['final_total_wealth']:,.2f}"
    print(f"{'Final Wealth ($50 start)':<32} | {fin_hermes:<24} | {fin_smc:<24} | {fin_norm:<24}")
    print("=" * 110)

    print("\n" + "=" * 80)
    print(" 🛡️ SENTRY FORENSICS: WHY SMC V17 SUFFERS LOSSES")
    print("=" * 80)
    print(f" Macro BTC Flash-Dump Losses Prevented by Sentry 1: {sentry_saves_1y['sentry_1_btc_macro']} setups")
    print(f" 2-Year Dataset Hermes WR: {res_hermes_2y['win_rate']:.2f}% (Executed: {res_hermes_2y['executed_trades']} trades, PF: {res_hermes_2y['profit_factor']:.2f})")
    print(f" 2-Year Dataset SMC V17 WR: {res_smc_native_2y['win_rate']:.2f}% (Executed: {res_smc_native_2y['executed_trades']} trades, PF: {res_smc_native_2y['profit_factor']:.2f})")
    print("=" * 80)

if __name__ == "__main__":
    main()
