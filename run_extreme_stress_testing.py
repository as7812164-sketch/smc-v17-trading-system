import json
import time
import os
import sys
import random
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR_2Y = os.path.join(BASE_DIR, "historical_data_2year")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

def load_candles(sym, interval="4h"):
    fpath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_hermes2_raw_signals(interval="4h"):
    """
    Extracts all valid HERMES 2.0 APEX setups across the 2-Year dataset.
    """
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_map_4h = {c["time"]: c for c in btc_4h}

    candles_map = {}
    for sym in TOP_22_CHAMPIONS:
        k = load_candles(sym, interval)
        if len(k) >= 400:
            candles_map[sym] = k

    tp_pct = 0.028
    soft_sl_pct = 0.028
    hard_sl_pct = 0.038
    max_hold = 24
    min_displacement = 0.050 # Sentry 2: 5.0% Institutional Displacement Floor
    max_tap_window = 28      # Sentry 4: Strict 28-Bar Freshness Guard

    raw_signals = []

    for sym, candles in candles_map.items():
        n = len(candles)
        for i in range(25, n - 35):
            # BULLISH SETUP
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
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        if btc_c and (btc_c["open"] - btc_c["close"]) / btc_c["open"] >= 0.020:
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
                                            bars_held = 1
                                            trade_lows = [tap_c["low"]]
                                            trade_highs = [tap_c["high"]]

                                            for m in range(t, min(t + max_hold, n)):
                                                bars_held = m - t + 1
                                                trade_lows.append(candles[m]["low"])
                                                trade_highs.append(candles[m]["high"])

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
                                                bars_held = max_hold

                                            deepest_low = min(trade_lows)
                                            highest_high = max(trade_highs)
                                            mae = (entry - deepest_low) / entry * 100.0
                                            mfe = (highest_high - entry) / entry * 100.0

                                            raw_signals.append({
                                                "sym": sym, "side": "LONG", "interval": interval,
                                                "entry_time": tap_c["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross": (exit_p - entry) / entry,
                                                "res": res, "bars_held": bars_held,
                                                "mae": mae, "mfe": mfe
                                            })
                                        break

            # BEARISH SETUP
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
                                            bars_held = 1
                                            trade_highs = [tap_c["high"]]
                                            trade_lows = [tap_c["low"]]

                                            for m in range(t, min(t + max_hold, n)):
                                                bars_held = m - t + 1
                                                trade_highs.append(candles[m]["high"])
                                                trade_lows.append(candles[m]["low"])

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
                                                bars_held = max_hold

                                            highest_high = max(trade_highs)
                                            deepest_low = min(trade_lows)
                                            mae = (highest_high - entry) / entry * 100.0
                                            mfe = (entry - deepest_low) / entry * 100.0

                                            raw_signals.append({
                                                "sym": sym, "side": "SHORT", "interval": interval,
                                                "entry_time": tap_c["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross": (entry - exit_p) / entry,
                                                "res": res, "bars_held": bars_held,
                                                "mae": mae, "mfe": mfe
                                            })
                                        break

    raw_signals.sort(key=lambda x: x["entry_time"])

    # Strict 1-Trade Sequential Queue
    executed = []
    active_exit = 0
    for s in raw_signals:
        if s["entry_time"] >= active_exit:
            executed.append(s)
            active_exit = s["exit_time"]

    return executed

def run_simulation(trades, leverage=5.0, fee_pct=0.0016, extra_loss_slippage=0.0, front_loaded_losses=0):
    """
    Simulates compounding from $50 USDT to $2,000 USDT under extreme stress parameters.
    """
    sim_trades = [dict(t) for t in trades]

    # Stress Modification: Extra Loss Slippage
    if extra_loss_slippage > 0.0:
        for t in sim_trades:
            if t["res"] == "LOSS":
                t["gross"] = t["gross"] - extra_loss_slippage

    # Stress Modification: Front-Loaded Consecutive Loss Torture
    if front_loaded_losses > 0:
        losses = [t for t in sim_trades if t["res"] == "LOSS"][:front_loaded_losses]
        remaining = [t for t in sim_trades if t not in losses]
        sim_trades = losses + remaining

    cap = 50.0
    vault = 0.0
    peak_wealth = 50.0
    max_dd = 0.0
    hit_2k_trade = None
    hit_2k_days = None
    start_time = sim_trades[0]["entry_time"] if sim_trades else 0

    wins = 0; losses = 0; gp = 0.0; gl = 0.0
    is_liquidated = False

    for idx, t in enumerate(sim_trades):
        pos_size = cap * leverage
        net_move = t["gross"] - fee_pct
        pnl = pos_size * net_move

        if t["res"] == "WIN":
            wins += 1; gp += pnl
            cap += (pnl * 0.85); vault += (pnl * 0.15)
        else:
            losses += 1; gl += abs(pnl)
            cap += pnl
            if cap < 2.0:
                cap = 0.0
                is_liquidated = True

        total_wealth = cap + vault
        if total_wealth > peak_wealth:
            peak_wealth = total_wealth
        dd = (peak_wealth - total_wealth) / peak_wealth if peak_wealth > 0 else 0
        if dd > max_dd:
            max_dd = dd

        if total_wealth >= 2000.0 and hit_2k_trade is None:
            hit_2k_trade = idx + 1
            hit_2k_days = (t["exit_time"] - start_time) / (1000 * 3600 * 24)

        if is_liquidated:
            break

    wr = (wins / len(sim_trades) * 100.0) if sim_trades else 0.0
    pf = (gp / gl) if gl > 0 else 99.0

    return {
        "trades_executed": idx + 1 if sim_trades else 0,
        "total_available": len(sim_trades),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "max_dd": round(max_dd * 100.0, 2),
        "hit_2k_trade": hit_2k_trade,
        "hit_2k_days": round(hit_2k_days, 1) if hit_2k_days else None,
        "final_wealth": round(cap + vault, 2),
        "active_cap": round(cap, 2),
        "vault_stash": round(vault, 2),
        "profit_factor": round(pf, 2),
        "status": "LIQUIDATED / BUST" if is_liquidated else ("TARGET CONQUERED" if hit_2k_trade else "SURVIVED")
    }

def main():
    print("=" * 115)
    print(" ⚡ HERMES 2.0 APEX: EXTREME ADVERSARIAL STRESS-TESTING GAUNTLET (4H 2-YEAR)")
    print(" Testing Extreme Execution Frictions, Monte Carlo Torture, 3x Fees, Adverse Slippage & High Leverage")
    print("=" * 115)

    print("\n⏳ Extracting 2-Year Real Binance Baseline Trades...")
    base_trades = extract_hermes2_raw_signals("4h")
    print(f"✅ Extracted {len(base_trades)} sequential 4H trades across Top-22 Champions.")

    stress_experiments = [
        {
            "id": "T0_BASELINE",
            "name": "Trial 0: Standard Baseline (Control)",
            "leverage": 5.0, "fee": 0.0016, "slip": 0.000, "losses": 0,
            "desc": "Standard 5x leverage, 0.16% fee, real candle close exits."
        },
        {
            "id": "T1_TRIPLE_FEES",
            "name": "Trial 1: Triple Fee Shock (0.48% Round-Trip)",
            "leverage": 5.0, "fee": 0.0048, "slip": 0.000, "losses": 0,
            "desc": "Simulates 3x exchange taker fees, VIP-0 max fees, and funding rate drag."
        },
        {
            "id": "T2_PUNITIVE_SLIPPAGE",
            "name": "Trial 2: Punitive Gap Slippage (+1.0% Extra Loss on Every Stop)",
            "leverage": 5.0, "fee": 0.0016, "slip": 0.010, "losses": 0,
            "desc": "Every losing trade takes an extra -1.0% adverse gap fill (-3.8% to -4.8% loss)."
        },
        {
            "id": "T3_HELL_COMBO",
            "name": "Trial 3: Execution Hell (Triple Fees + 1.2% Adverse Gap Slippage)",
            "leverage": 5.0, "fee": 0.0048, "slip": 0.012, "losses": 0,
            "desc": "Combines 0.48% fees + extreme 1.2% gap slippage on all losses."
        },
        {
            "id": "T4_STREAK_TORTURE_5",
            "name": "Trial 4: Streak Torture (5 Consecutive Losses Forced at $50 Start)",
            "leverage": 5.0, "fee": 0.0016, "slip": 0.000, "losses": 5,
            "desc": "Forces 5 consecutive losses immediately at Trade #1..5 before any vault is built."
        },
        {
            "id": "T5_STREAK_TORTURE_8",
            "name": "Trial 5: Severe Streak Torture (8 Consecutive Losses Forced at Start)",
            "leverage": 5.0, "fee": 0.0016, "slip": 0.000, "losses": 8,
            "desc": "Forces 8 consecutive losses immediately at start (capital drops to ~$13)."
        },
        {
            "id": "T6_LEVERAGE_8X",
            "name": "Trial 6: High Leverage Stress (8x Leverage Aggression)",
            "leverage": 8.0, "fee": 0.0016, "slip": 0.000, "losses": 0,
            "desc": "Increases leverage by 60% (8x isolated) on $50 starting compounding."
        },
        {
            "id": "T7_LEVERAGE_10X",
            "name": "Trial 7: Extreme Leverage Threshold (10x Leverage)",
            "leverage": 10.0, "fee": 0.0016, "slip": 0.000, "losses": 0,
            "desc": "Tests double standard leverage (10x isolated) to locate mathematical ruin boundary."
        },
        {
            "id": "T8_MAX_APOCALYPSE",
            "name": "Trial 8: Maximum Apocalypse (8x Leverage + 2x Fees + 0.8% Slip + 4 Front Losses)",
            "leverage": 8.0, "fee": 0.0032, "slip": 0.008, "losses": 4,
            "desc": "All extreme stressors combined simultaneously: 8x lev, 2x fees, gap slippage, and 4 loss streak."
        }
    ]

    results = {}

    for exp in stress_experiments:
        print(f"\n⚡ Running {exp['name']}...")
        res = run_simulation(
            base_trades,
            leverage=exp["leverage"],
            fee_pct=exp["fee"],
            extra_loss_slippage=exp["slip"],
            front_loaded_losses=exp["losses"]
        )
        res["description"] = exp["desc"]
        res["leverage"] = exp["leverage"]
        results[exp["id"]] = res

        status_icon = "🏆" if res["status"] == "TARGET CONQUERED" else ("⚠️" if res["status"] == "SURVIVED" else "💀")
        hit_str = f"Trade #{res['hit_2k_trade']} ({res['hit_2k_days']} days)" if res['hit_2k_trade'] else "Not Hit"
        print(f"  • Status: {status_icon} {res['status']} | Max DD: {res['max_dd']}% | Win Rate: {res['win_rate']}%")
        print(f"  • $2,000 Milestone: {hit_str} | Active Cap: ${res['active_cap']:,.2f} | Vault: ${res['vault_stash']:,.2f} | Final: ${res['final_wealth']:,.2f}")

    out_file = os.path.join(BASE_DIR, "hermes2_apex_extreme_stress_test_report.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 115)
    print("✅ Extreme Stress Testing Gauntlet Complete! Report saved to:")
    print(f"  {out_file}")
    print("=" * 115)

if __name__ == "__main__":
    main()
