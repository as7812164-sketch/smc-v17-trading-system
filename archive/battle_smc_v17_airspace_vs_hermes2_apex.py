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
# 1. CONTENDER 1: SMC V17 WITH 3% AIRSPACE FILTER (3-OB STACK, 2ND OB ENTRY)
# =============================================================================
def run_smc_v17_airspace(all_data, min_airspace_pct=3.0, tp_pct=0.040, sl_pct=0.030):
    """
    SMC V17 with 3% Airspace Filter:
    - Identifies active unmitigated Order Blocks
    - Requires at least 3 stacked Order Blocks
    - Enters exclusively on the 2nd (Middle) OB
    - Airspace Gap: Clean distance between Middle OB and 1st OB must be >= min_airspace_pct (3.0%)
    - First tap entry on Middle OB boundary
    """
    signals = []

    for tf in ["1h", "4h"]:
        curr_tp = tp_pct if tf == "4h" else (tp_pct * 0.75) # 4% on 4H, 3% on 1H
        curr_sl = sl_pct if tf == "4h" else (sl_pct * 0.85)
        max_hold = 30

        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 100: continue

            detected_buy_obs = []
            detected_sell_obs = []

            # Pre-detect valid SMC OBs with >= 1.5x body displacement and >= 2.5% expansion
            for i in range(15, n - 20):
                c = candles[i]
                # Preceding 10 candle avg body
                bodies = [abs(candles[b]["close"] - candles[b]["open"]) for b in range(max(0, i - 10), i)]
                avg_b = sum(bodies) / len(bodies) if bodies else 0.0001

                # Bullish OB
                if (c["close"] - c["open"]) >= 1.5 * avg_b:
                    # Find origin red candle
                    origin_o = None
                    for o in range(i - 1, max(0, i - 7), -1):
                        if candles[o]["close"] < candles[o]["open"]:
                            origin_o = o; break
                    if origin_o is not None:
                        ob_h = candles[origin_o]["high"]
                        ob_l = candles[origin_o]["low"]
                        # Check expansion
                        max_r = max([candles[i+k]["high"] for k in range(1, min(10, n - i))])
                        if (max_r - ob_h) / ob_h >= 0.030: # 3% impulse
                            detected_buy_obs.append({
                                "bar_idx": origin_o,
                                "time": candles[origin_o]["time"],
                                "ob_high": ob_h,
                                "ob_low": ob_l,
                                "mitigated": False
                            })

                # Bearish OB
                if (c["open"] - c["close"]) >= 1.5 * avg_b:
                    origin_o = None
                    for o in range(i - 1, max(0, i - 7), -1):
                        if candles[o]["close"] > candles[o]["open"]:
                            origin_o = o; break
                    if origin_o is not None:
                        ob_h = candles[origin_o]["high"]
                        ob_l = candles[origin_o]["low"]
                        min_d = min([candles[i+k]["low"] for k in range(1, min(10, n - i))])
                        if (ob_l - min_d) / ob_l >= 0.030:
                            detected_sell_obs.append({
                                "bar_idx": origin_o,
                                "time": candles[origin_o]["time"],
                                "ob_high": ob_h,
                                "ob_low": ob_l,
                                "mitigated": False
                            })

            # Simulate forward tap execution
            # 1. Bullish setups
            for bar_idx in range(40, n - 20):
                curr_bar = candles[bar_idx]
                active_obs = [ob for ob in detected_buy_obs if ob["bar_idx"] < bar_idx - 2 and not ob["mitigated"]]
                if len(active_obs) >= 3:
                    # Sort active OBs by price: Top #1 -> Middle #2 -> Bottom #3
                    active_obs.sort(key=lambda x: x["ob_high"], reverse=True)
                    top_ob = active_obs[0]
                    middle_ob = active_obs[1]

                    entry_p = middle_ob["ob_high"]

                    # First tap on Middle OB
                    if curr_bar["low"] <= entry_p and curr_bar["open"] > entry_p:
                        middle_ob["mitigated"] = True

                        # Airspace Gap Calculation: clean distance between Middle OB High and Top OB Low
                        airspace_pct = ((top_ob["ob_low"] - entry_p) / entry_p) * 100.0

                        # Filter: Airspace must be >= 3.0%
                        if airspace_pct >= min_airspace_pct:
                            tp_p = entry_p * (1.0 + curr_tp)
                            sl_p = entry_p * (1.0 - curr_sl)

                            res = None; exit_p = entry_p; exit_t = curr_bar["time"]
                            for m in range(bar_idx + 1, min(bar_idx + max_hold, n)):
                                if candles[m]["high"] >= tp_p:
                                    res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                if candles[m]["low"] <= sl_p:
                                    res = "LOSS"; exit_p = min(sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                            if not res:
                                fc = candles[min(bar_idx + max_hold, n - 1)]["close"]
                                res = "WIN" if fc >= entry_p else "LOSS"
                                exit_p = fc
                                exit_t = candles[min(bar_idx + max_hold, n - 1)]["time"]

                            signals.append({
                                "sym": sym, "side": "LONG", "tf": tf, "time": curr_bar["time"],
                                "exit_time": exit_t, "entry": entry_p, "exit": exit_p,
                                "gross": (exit_p - entry_p) / entry_p, "res": res,
                                "airspace": airspace_pct
                            })

            # 2. Bearish setups
            for bar_idx in range(40, n - 20):
                curr_bar = candles[bar_idx]
                active_obs = [ob for ob in detected_sell_obs if ob["bar_idx"] < bar_idx - 2 and not ob["mitigated"]]
                if len(active_obs) >= 3:
                    # Sort active OBs by price: Bottom #1 (closest to price) -> Middle #2 -> Top #3
                    active_obs.sort(key=lambda x: x["ob_low"])
                    bottom_ob = active_obs[0]
                    middle_ob = active_obs[1]

                    entry_p = middle_ob["ob_low"]

                    if curr_bar["high"] >= entry_p and curr_bar["open"] < entry_p:
                        middle_ob["mitigated"] = True

                        # Airspace Gap: clean distance between Middle OB Low and Bottom OB High
                        airspace_pct = ((entry_p - bottom_ob["ob_high"]) / entry_p) * 100.0

                        if airspace_pct >= min_airspace_pct:
                            tp_p = entry_p * (1.0 - curr_tp)
                            sl_p = entry_p * (1.0 + curr_sl)

                            res = None; exit_p = entry_p; exit_t = curr_bar["time"]
                            for m in range(bar_idx + 1, min(bar_idx + max_hold, n)):
                                if candles[m]["low"] <= tp_p:
                                    res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                if candles[m]["high"] >= sl_p:
                                    res = "LOSS"; exit_p = max(sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                            if not res:
                                fc = candles[min(bar_idx + max_hold, n - 1)]["close"]
                                res = "WIN" if fc <= entry_p else "LOSS"
                                exit_p = fc
                                exit_t = candles[min(bar_idx + max_hold, n - 1)]["time"]

                            signals.append({
                                "sym": sym, "side": "SHORT", "tf": tf, "time": curr_bar["time"],
                                "exit_time": exit_t, "entry": entry_p, "exit": exit_p,
                                "gross": (entry_p - exit_p) / entry_p, "res": res,
                                "airspace": airspace_pct
                            })

    signals.sort(key=lambda x: x["time"])
    return signals

# =============================================================================
# 2. CONTENDER 2: HERMES 2.0 APEX (4-SENTRY INSTITUTIONAL ENGINE)
# =============================================================================
def run_hermes_2_apex(all_data, btc_map_4h):
    signals = []
    sentry_saves = {"sentry_1_btc_macro": 0}

    for tf in ["1h", "4h"]:
        tp_pct = 0.022 if tf == "1h" else 0.028
        soft_sl_pct = 0.025 if tf == "1h" else 0.028
        hard_sl_pct = 0.036 if tf == "1h" else 0.038
        max_hold = 24
        min_displacement = 0.050
        max_tap_window = 28

        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                # Bullish Setup
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

                # Bearish Setup
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
# 3. SEQUENTIAL COMPOUNDING ENGINE ($50 Start, 5x Leverage, 85/15 Vault Split)
# =============================================================================
def simulate_compounding(signals, name="Strategy", start_cap=50.0, leverage=5.0, reinvest_ratio=0.85, vault_ratio=0.15, friction=0.0016):
    signals.sort(key=lambda x: x["time"])
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
    
    wins = 0; losses = 0; gp = 0.0; gl = 0.0

    for idx, trade in enumerate(executed):
        net_move = trade["gross"] - friction
        pos_size = cap * leverage
        pnl = pos_size * net_move

        if trade["res"] == "WIN":
            wins += 1; gp += pnl
            cap += (pnl * reinvest_ratio)
            vault += (pnl * vault_ratio)
        else:
            losses += 1; gl += abs(pnl)
            cap += pnl
            if cap < 2.0: cap = 0.0

        total_wealth = cap + vault
        if total_wealth > peak: peak = total_wealth
        dd = (peak - total_wealth) / peak if peak > 0 else 0
        if dd > max_dd: max_dd = dd

        trade_date = time.strftime('%Y-%m-%d %H:%M', time.gmtime(trade["time"] / 1000))
        if total_wealth >= 1000.0 and hit_1k is None:
            hit_1k = {"trade_num": idx + 1, "date": trade_date, "total": total_wealth}
        if total_wealth >= 2000.0 and hit_2k is None:
            hit_2k = {"trade_num": idx + 1, "date": trade_date, "total": total_wealth}

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
        "hit_2k": hit_2k
    }

def main():
    print("=" * 115)
    print(" ⚔️ SHOWDOWN: SMC V17 (3% AIRSPACE) vs HERMES 2.0 APEX")
    print(" Head-to-Head Quantitative Audit across 1-Year (339K bars) & 2-Year (470K bars)")
    print("=" * 115)

    # 1. Load 1-Year Data
    data_1y = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_data(DATA_1Y_DIR, sym, tf)
            if len(k) >= 500: data_1y[tf][sym] = k
    btc_4h_1y = load_data(DATA_1Y_DIR, "BTCUSDT", "4h")
    btc_map_4h_1y = {c["time"]: c for c in btc_4h_1y}

    # 2. Run 1-Year Simulations
    print(">>> Running HERMES 2.0 APEX on 1-Year Data...")
    hermes_sig_1y, sentry_saves_1y = run_hermes_2_apex(data_1y, btc_map_4h_1y)

    print(">>> Running SMC V17 with 3% Airspace (Native +4% TP / -3% SL) on 1-Year Data...")
    smc_airspace_native_1y = run_smc_v17_airspace(data_1y, min_airspace_pct=3.0, tp_pct=0.040, sl_pct=0.030)

    print(">>> Running SMC V17 with 3% Airspace (Calibrated +2.8% TP / -2.8% SL) on 1-Year Data...")
    smc_airspace_cal_1y = run_smc_v17_airspace(data_1y, min_airspace_pct=3.0, tp_pct=0.028, sl_pct=0.028)

    res_hermes_1y = simulate_compounding(hermes_sig_1y, name="HERMES 2.0 APEX (1Y)")
    res_smc_air_native_1y = simulate_compounding(smc_airspace_native_1y, name="SMC V17 3% Airspace Native (1Y)")
    res_smc_air_cal_1y = simulate_compounding(smc_airspace_cal_1y, name="SMC V17 3% Airspace Calibrated (1Y)")

    # 3. Load 2-Year Data
    data_2y = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            k = load_data(DATA_2Y_DIR, sym, tf)
            if len(k) >= 500: data_2y[tf][sym] = k
    btc_4h_2y = load_data(DATA_2Y_DIR, "BTCUSDT", "4h")
    btc_map_4h_2y = {c["time"]: c for c in btc_4h_2y}

    print("\n>>> Running HERMES 2.0 APEX on 2-Year Data...")
    hermes_sig_2y, sentry_saves_2y = run_hermes_2_apex(data_2y, btc_map_4h_2y)

    print(">>> Running SMC V17 with 3% Airspace on 2-Year Data...")
    smc_airspace_native_2y = run_smc_v17_airspace(data_2y, min_airspace_pct=3.0, tp_pct=0.040, sl_pct=0.030)

    res_hermes_2y = simulate_compounding(hermes_sig_2y, name="HERMES 2.0 APEX (2Y)")
    res_smc_air_native_2y = simulate_compounding(smc_airspace_native_2y, name="SMC V17 3% Airspace Native (2Y)")

    # Save to JSON
    results = {
        "1y_results": {
            "hermes": res_hermes_1y,
            "smc_airspace_native": res_smc_air_native_1y,
            "smc_airspace_calibrated": res_smc_air_cal_1y
        },
        "2y_results": {
            "hermes": res_hermes_2y,
            "smc_airspace_native": res_smc_air_native_2y
        }
    }

    out_file = os.path.join(BASE_DIR, "battle_smc_v17_airspace_vs_hermes2_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Print Report
    print("\n" + "=" * 115)
    print(" 🏆 HEAD-TO-HEAD SCORECARD: SMC V17 (3% AIRSPACE) vs HERMES 2.0 APEX")
    print("=" * 115)
    print(f"{'Performance Dimension':<30} | {'HERMES 2.0 APEX (1Y)':<24} | {'SMC V17 (3% Airspace)':<26} | {'SMC V17 Airspace Cal':<22}")
    print("-" * 115)
    print(f"{'Total Signals':<30} | {res_hermes_1y['total_signals']:<24} | {res_smc_air_native_1y['total_signals']:<26} | {res_smc_air_cal_1y['total_signals']:<22}")
    print(f"{'Executed Trades (1-by-1)':<30} | {res_hermes_1y['executed_trades']:<24} | {res_smc_air_native_1y['executed_trades']:<26} | {res_smc_air_cal_1y['executed_trades']:<22}")
    print(f"{'Win Rate % (Accuracy)':<30} | {res_hermes_1y['win_rate']:<23.2f}% | {res_smc_air_native_1y['win_rate']:<25.2f}% | {res_smc_air_cal_1y['win_rate']:<21.2f}%")
    print(f"{'Profit Factor':<30} | {res_hermes_1y['profit_factor']:<24.2f} | {res_smc_air_native_1y['profit_factor']:<26.2f} | {res_smc_air_cal_1y['profit_factor']:<22.2f}")
    print(f"{'Max Drawdown %':<30} | {res_hermes_1y['max_drawdown_pct']:<23.2f}% | {res_smc_air_native_1y['max_drawdown_pct']:<25.2f}% | {res_smc_air_cal_1y['max_drawdown_pct']:<21.2f}%")
    
    h1_hermes = f"Trade #{res_hermes_1y['hit_1k']['trade_num']}" if res_hermes_1y['hit_1k'] else "FAILED"
    h1_air = f"Trade #{res_smc_air_native_1y['hit_1k']['trade_num']}" if res_smc_air_native_1y['hit_1k'] else "FAILED"
    h1_cal = f"Trade #{res_smc_air_cal_1y['hit_1k']['trade_num']}" if res_smc_air_cal_1y['hit_1k'] else "FAILED"
    print(f"{'$1,000 Milestone':<30} | {h1_hermes:<24} | {h1_air:<26} | {h1_cal:<22}")

    h2_hermes = f"Trade #{res_hermes_1y['hit_2k']['trade_num']}" if res_hermes_1y['hit_2k'] else "FAILED"
    h2_air = f"Trade #{res_smc_air_native_1y['hit_2k']['trade_num']}" if res_smc_air_native_1y['hit_2k'] else "FAILED"
    h2_cal = f"Trade #{res_smc_air_cal_1y['hit_2k']['trade_num']}" if res_smc_air_cal_1y['hit_2k'] else "FAILED"
    print(f"{'$2,000 Milestone':<30} | {h2_hermes:<24} | {h2_air:<26} | {h2_cal:<22}")

    print("-" * 115)
    print(f"{'2-Year Multi-Cycle Win Rate':<30} | {res_hermes_2y['win_rate']:<23.2f}% | {res_smc_air_native_2y['win_rate']:<25.2f}% | {'N/A':<22}")
    print(f"{'2-Year Max Drawdown %':<30} | {res_hermes_2y['max_drawdown_pct']:<23.2f}% | {res_smc_air_native_2y['max_drawdown_pct']:<25.2f}% | {'N/A':<22}")
    print("=" * 115)

if __name__ == "__main__":
    main()
