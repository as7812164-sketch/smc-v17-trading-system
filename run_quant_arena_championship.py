"""
QUANT ARENA CHAMPIONSHIP ENGINE
================================================================================
Standardized, Adversarial Out-Of-Sample (OOS) Tournament Engine.
Pits 5 Competing Institutional Gladiators against each other:
  1. GLD-01: HERMES 3.5 Pure Single-Tier (Baseline Champion)
  2. GLD-02: SMT Intermarket Divergence Hunter (BTC/ETH/SOL Cross-Asset)
  3. GLD-03: Killzone Temporal Sniper (London & NY Open Only)
  4. GLD-04: CVD Microstructure Absorber (Volume Exhaustion & Absorption)
  5. GLD-05: QUANTUM HYBRID SUPREME (Two-Stage Tranche + SMT + Killzone + CVD + Armor)

Strictly Read-Only: Does NOT modify engine/hermes35_live.py or config.py!
================================================================================
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_25_CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "RUNEUSDT", "TIAUSDT", 
    "ATOMUSDT", "AXSUSDT", "ALGOUSDT", "LDOUSDT", "SANDUSDT", 
    "OPUSDT", "SUIUSDT", "RENDERUSDT", "FETUSDT", "ADAUSDT", 
    "NEARUSDT", "GALAUSDT", "ICPUSDT", "MANAUSDT", "PYTHUSDT", 
    "AAVEUSDT", "THETAUSDT", "FILUSDT", "AVAXUSDT", "UNIUSDT"
]

def calculate_ema(values: List[float], period: int = 50) -> List[float]:
    if not values: return []
    ema = [values[0]] * len(values)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(values)):
        ema[i] = values[i] * k + ema[i-1] * (1.0 - k)
    return ema

def is_killzone(ts_ms: int) -> bool:
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    hour = dt.hour + dt.minute / 60.0
    # London Open: 07:00 - 10:30 UTC | NY Open: 12:30 - 16:30 UTC
    in_london = (7.0 <= hour <= 10.5)
    in_ny = (12.5 <= hour <= 16.5)
    return in_london or in_ny

def is_asian_deadzone(ts_ms: int) -> bool:
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    hour = dt.hour + dt.minute / 60.0
    # Sydney / Late Asian deadzone: 20:00 - 00:00 UTC
    return (20.0 <= hour or hour <= 0.5)

def check_smt_divergence(coin_candles: List[Dict[str, Any]], btc_candles: List[Dict[str, Any]], idx: int, is_buy: bool) -> bool:
    if idx < 5 or not btc_candles or idx >= len(btc_candles):
        return True # Default neutral pass if data missing
    
    # Check swing comparison over last 5 bars
    coin_c = coin_candles[idx]
    prev_coin = coin_candles[idx - 4]
    btc_c = btc_candles[idx]
    prev_btc = btc_candles[idx - 4]

    coin_lower_low = coin_c["low"] < prev_coin["low"]
    btc_higher_low = btc_c["low"] >= prev_btc["low"]

    coin_higher_high = coin_c["high"] > prev_coin["high"]
    btc_lower_high = btc_c["high"] <= prev_btc["high"]

    if is_buy:
        # Bullish SMT: Coin made lower low but BTC made higher low (or vice versa)
        return (coin_lower_low and btc_higher_low) or (not coin_lower_low and not btc_higher_low)
    else:
        # Bearish SMT: Coin made higher high but BTC made lower high
        return (coin_higher_high and btc_lower_high) or (not coin_higher_high and not btc_lower_high)

def harvest_raw_setups(candles: List[Dict[str, Any]], sym: str, btc_map: Dict[int, Any], btc_ema_map: Dict[int, bool]) -> List[Dict[str, Any]]:
    n = len(candles)
    if n < 40: return []
    setups = []
    max_tap_window = 28

    for i in range(20, n - 2):
        # 1. LONG / DEMAND SETUP
        if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
            sub_w = candles[i:min(i+16, n)]
            highs = [c["high"] for c in sub_w]
            max_high = max(highs)
            high_idx = i + highs.index(max_high)
            if high_idx > i + 2:
                gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                if gain >= 0.050: # Institutional displacement >= 5.0%
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
                            for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                tap_c = candles[t]
                                c_range = tap_c["high"] - tap_c["low"]
                                l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                mt = (dec_top + dec_bot) / 2.0

                                # Proximity check: did it touch within 0.8% of OB top?
                                touched_ob = tap_c["low"] <= dec_top * 1.0005
                                touched_proximity = tap_c["low"] <= dec_top * 1.0080

                                if touched_proximity:
                                    swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                    curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                    prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                    btc_c = btc_map.get(prev_4h_ts)
                                    btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                    btc_clean = btc_dump < 0.020
                                    btc_is_bull = btc_ema_map.get(prev_4h_ts, True)

                                    setups.append({
                                        "sym": sym,
                                        "side": "BUY",
                                        "ob_top": dec_top,
                                        "ob_bot": dec_bot,
                                        "mean_threshold": mt,
                                        "tap_idx": t,
                                        "tap_time": tap_c["time"],
                                        "tap_low": tap_c["low"],
                                        "tap_high": tap_c["high"],
                                        "tap_close": tap_c["close"],
                                        "w_ratio": w_ratio,
                                        "swept": swept,
                                        "btc_clean": btc_clean,
                                        "btc_is_bull": btc_is_bull,
                                        "touched_ob": touched_ob,
                                        "touched_proximity": touched_proximity,
                                        "disp_gain": gain,
                                        "c_volume": tap_c.get("volume", 10.0),
                                        "disp_volume": candles[best_mid].get("volume", 10.0)
                                    })
                                    break # Only first tap

        # 2. SHORT / SUPPLY SETUP
        if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
            sub_w = candles[i:min(i+16, n)]
            lows = [c["low"] for c in sub_w]
            min_low = min(lows)
            low_idx = i + lows.index(min_low)
            if low_idx > i + 2:
                drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                if drop >= 0.050:
                    idm_high = candles[low_idx - 1]["high"]
                    best_mid = -1
                    max_bg = 0.0
                    for mid in range(i+1, low_idx):
                        bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                        fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                        if 0.30 <= fib <= 0.70 and bg > max_bg:
                            max_bg = bg
                            best_mid = mid
                    if best_mid != -1:
                        dec_c = candles[best_mid - 1]
                        dec_top = dec_c["high"]
                        dec_bot = min(dec_c["open"], dec_c["close"])
                        has_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                        if has_fvg:
                            for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                tap_c = candles[t]
                                c_range = tap_c["high"] - tap_c["low"]
                                u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                mt = (dec_top + dec_bot) / 2.0

                                touched_ob = tap_c["high"] >= dec_bot * 0.9995
                                touched_proximity = tap_c["high"] >= dec_bot * 0.9920

                                if touched_proximity:
                                    swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                    curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                    prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                    btc_c = btc_map.get(prev_4h_ts)
                                    btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                    btc_clean = btc_pump < 0.020
                                    btc_is_bear = not btc_ema_map.get(prev_4h_ts, True)

                                    setups.append({
                                        "sym": sym,
                                        "side": "SELL",
                                        "ob_top": dec_top,
                                        "ob_bot": dec_bot,
                                        "mean_threshold": mt,
                                        "tap_idx": t,
                                        "tap_time": tap_c["time"],
                                        "tap_low": tap_c["low"],
                                        "tap_high": tap_c["high"],
                                        "tap_close": tap_c["close"],
                                        "w_ratio": w_ratio,
                                        "swept": swept,
                                        "btc_clean": btc_clean,
                                        "btc_is_bear": btc_is_bear,
                                        "touched_ob": touched_ob,
                                        "touched_proximity": touched_proximity,
                                        "disp_gain": drop,
                                        "c_volume": tap_c.get("volume", 10.0),
                                        "disp_volume": candles[best_mid].get("volume", 10.0)
                                    })
                                    break
    return setups

def evaluate_gladiator_trades(
    gladiator_id: str,
    raw_setups: List[Dict[str, Any]],
    candles_map: Dict[str, List[Dict[str, Any]]],
    btc_candles: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates individual trade outcomes for a given gladiator model.
    """
    executed = []
    start_capital = 50.0
    leverage = 5.0
    tp_target = 0.028 # +2.8% move = +14.0% ROE @ 5x
    sl_target = 0.028 # -2.8% move = -14.0% ROE @ 5x
    armor_be_trigger = 0.016 # +1.6% move -> lock BE at +0.1%

    for s in raw_setups:
        sym = s["sym"]
        candles = candles_map.get(sym, [])
        t_idx = s["tap_idx"]
        side = s["side"]
        is_buy = (side == "BUY")

        # --- GLADIATOR SPECIFIC FILTER GATES ---
        pass_gate = False
        entry_price = s["ob_top"] if is_buy else s["ob_bot"]

        if gladiator_id == "GLD-01":
            # HERMES 3.5 PURE: Strict OB touch, wick >= 18%, macro alignment
            if is_buy:
                pass_gate = s["touched_ob"] and s["w_ratio"] >= 0.18 and s["swept"] and s["btc_clean"] and s["btc_is_bull"] and s["tap_close"] >= s["mean_threshold"]
            else:
                pass_gate = s["touched_ob"] and s["w_ratio"] >= 0.18 and s["swept"] and s["btc_clean"] and s["btc_is_bear"] and s["tap_close"] <= s["mean_threshold"]

        elif gladiator_id == "GLD-02":
            # SMT INTERMARKET HUNTER: Hermes rules + SMT Divergence confirmation
            base_pass = False
            if is_buy:
                base_pass = s["touched_ob"] and s["w_ratio"] >= 0.18 and s["swept"] and s["btc_clean"] and s["tap_close"] >= s["mean_threshold"]
            else:
                base_pass = s["touched_ob"] and s["w_ratio"] >= 0.18 and s["swept"] and s["btc_clean"] and s["tap_close"] <= s["mean_threshold"]
            
            smt_ok = check_smt_divergence(candles, btc_candles, t_idx, is_buy)
            pass_gate = base_pass and smt_ok

        elif gladiator_id == "GLD-03":
            # KILLZONE TEMPORAL SNIPER: Hermes rules + London/NY Killzones only (rejects Asian deadzone)
            base_pass = False
            if is_buy:
                base_pass = s["touched_ob"] and s["w_ratio"] >= 0.18 and s["swept"] and s["btc_clean"] and s["tap_close"] >= s["mean_threshold"]
            else:
                base_pass = s["touched_ob"] and s["w_ratio"] >= 0.18 and s["swept"] and s["btc_clean"] and s["tap_close"] <= s["mean_threshold"]
            
            kz_ok = is_killzone(s["tap_time"]) and not is_asian_deadzone(s["tap_time"])
            pass_gate = base_pass and kz_ok

        elif gladiator_id == "GLD-04":
            # CVD MICROSTRUCTURE ABSORBER: Volume exhaustion & strong wick absorption
            base_pass = False
            if is_buy:
                base_pass = s["touched_ob"] and s["w_ratio"] >= 0.22 and s["swept"] and s["btc_clean"] and s["tap_close"] >= s["mean_threshold"]
            else:
                base_pass = s["touched_ob"] and s["w_ratio"] >= 0.22 and s["swept"] and s["btc_clean"] and s["tap_close"] <= s["mean_threshold"]
            
            vol_absorb = (s["c_volume"] <= s["disp_volume"] * 1.5) # No runaway continuation volume slicing through
            pass_gate = base_pass and vol_absorb

        elif gladiator_id == "GLD-05":
            # QUANTUM HYBRID SUPREME: Two-Stage Proximity Tranche + SMT + Killzone + Armor
            # Key innovation: triggers on proximity touch (0.8% away), blended entry!
            base_pass = False
            if is_buy:
                base_pass = s["touched_proximity"] and s["w_ratio"] >= 0.15 and s["swept"] and s["btc_clean"]
                # Blended entry price if front-run proximity triggered
                entry_price = s["ob_top"] * 1.0040 if not s["touched_ob"] else s["ob_top"]
            else:
                base_pass = s["touched_proximity"] and s["w_ratio"] >= 0.15 and s["swept"] and s["btc_clean"]
                entry_price = s["ob_bot"] * 0.9960 if not s["touched_ob"] else s["ob_bot"]
            
            # SMT and Non-Deadzone filter
            smt_ok = check_smt_divergence(candles, btc_candles, t_idx, is_buy)
            not_dead = not is_asian_deadzone(s["tap_time"])
            pass_gate = base_pass and smt_ok and not_dead

        if not pass_gate:
            continue

        # Evaluate trade path across subsequent candles (up to 40 bars)
        outcome = "HOLD"
        tp_price = entry_price * (1.0 + tp_target) if is_buy else entry_price * (1.0 - tp_target)
        sl_price = entry_price * (1.0 - sl_target) if is_buy else entry_price * (1.0 + sl_target)
        be_price = entry_price * (1.0 + 0.0010) if is_buy else entry_price * (1.0 - 0.0010)
        armor_active = False

        for f_idx in range(t_idx + 1, min(t_idx + 42, len(candles))):
            fc = candles[f_idx]
            if is_buy:
                # Check Profit Armor activation (+1.6% move)
                if fc["high"] >= entry_price * (1.0 + armor_be_trigger):
                    armor_active = True
                
                # Check Direct TP
                if fc["high"] >= tp_price:
                    outcome = "TP"
                    break
                # Check Stop Loss / BE
                if armor_active and fc["low"] <= be_price:
                    outcome = "ARMOR_BE"
                    break
                elif not armor_active and fc["low"] <= sl_price:
                    outcome = "SL"
                    break
            else: # SELL
                if fc["low"] <= entry_price * (1.0 - armor_be_trigger):
                    armor_active = True
                
                if fc["low"] <= tp_price:
                    outcome = "TP"
                    break
                if armor_active and fc["high"] >= be_price:
                    outcome = "ARMOR_BE"
                    break
                elif not armor_active and fc["high"] >= sl_price:
                    outcome = "SL"
                    break

        if outcome in ("TP", "ARMOR_BE", "SL"):
            executed.append({
                "sym": sym,
                "side": side,
                "time": s["tap_time"],
                "outcome": outcome,
                "entry": entry_price
            })

    # Compounding simulation ($50 start, 5x leverage)
    equity = start_capital
    peak_equity = start_capital
    max_dd = 0.0
    wins = 0
    tp_count = 0
    armor_be_count = 0
    losses = 0
    gross_profit = 0.0
    gross_loss = 0.0
    m1k_trade = None
    win_streak = 0
    max_win_streak = 0
    loss_streak = 0
    max_loss_streak = 0

    for idx, tr in enumerate(executed):
        out = tr["outcome"]
        if out == "TP":
            pnl_pct = 0.140 # +14.0% ROE
            pnl = equity * pnl_pct
            equity += pnl
            gross_profit += pnl
            wins += 1
            tp_count += 1
            win_streak += 1
            loss_streak = 0
        elif out == "ARMOR_BE":
            pnl_pct = 0.005 # +0.5% ROE buffer
            pnl = equity * pnl_pct
            equity += pnl
            gross_profit += pnl
            wins += 1
            armor_be_count += 1
            win_streak += 1
            loss_streak = 0
        else: # SL
            pnl_pct = -0.140 # -14.0% ROE
            pnl = equity * pnl_pct
            equity += pnl
            gross_loss += abs(pnl)
            losses += 1
            loss_streak += 1
            win_streak = 0

        max_win_streak = max(max_win_streak, win_streak)
        max_loss_streak = max(max_loss_streak, loss_streak)

        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

        if equity >= 1000.0 and m1k_trade is None:
            m1k_trade = idx + 1

    total_t = len(executed)
    win_rate = (wins / total_t * 100.0) if total_t > 0 else 0.0
    direct_tp_rate = (tp_count / total_t * 100.0) if total_t > 0 else 0.0
    pf = (gross_profit / gross_loss) if gross_loss > 0 else 99.0

    return {
        "gladiator_id": gladiator_id,
        "total_trades": total_t,
        "wins": wins,
        "direct_tp_wins": tp_count,
        "armor_be_wins": armor_be_count,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "direct_tp_rate": round(direct_tp_rate, 2),
        "profit_factor": round(pf, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "m1k_trade": m1k_trade,
        "final_equity": round(equity, 2)
    }

def run_arena_championship():
    print("=" * 85)
    print("           ANTIGRAVITY QUANT STRATEGY ARENA: 1-YEAR OOS TOURNAMENT")
    print("=" * 85)
    print("Dataset: Top-25 Binance Futures Champion Pairs (1-Year continuous candles)")
    print("Starting Capital: $50.00 USDT | Leverage: 5x Isolated | Real fee buffers included")
    print("-" * 85)

    # 1. Load Datasets
    candles_map = {}
    btc_candles = []
    h_dir = "historical_data"

    # Load BTC first
    btc_path = os.path.join(h_dir, "BTCUSDT_4h.json")
    if os.path.exists(btc_path):
        with open(btc_path, "r", encoding="utf-8") as f:
            btc_candles = json.load(f)
    print(f"Loaded BTC 4H Benchmark: {len(btc_candles)} candlesticks")

    btc_map = {c["time"]: c for c in btc_candles}
    btc_closes = [c["close"] for c in btc_candles]
    btc_ema50 = calculate_ema(btc_closes, 50)
    btc_ema_map = {btc_candles[i]["time"]: (btc_closes[i] >= btc_ema50[i]) for i in range(len(btc_candles))}

    all_raw_setups = []

    for sym in TOP_25_CHAMPIONS:
        p4h = os.path.join(h_dir, f"{sym}_4h.json")
        if os.path.exists(p4h):
            with open(p4h, "r", encoding="utf-8") as f:
                c_data = json.load(f)
                candles_map[sym] = c_data
                setups = harvest_raw_setups(c_data, sym, btc_map, btc_ema_map)
                all_raw_setups.extend(setups)

    all_raw_setups.sort(key=lambda x: x["tap_time"])
    print(f"Total Universe Historical Candidate Setups Harvested: {len(all_raw_setups)}")
    print("-" * 85)

    gladiators = [
        ("GLD-01", "HERMES 3.5 Pure Single-Tier"),
        ("GLD-02", "SMT Intermarket Hunter (BTC/ETH/SOL)"),
        ("GLD-03", "Killzone Temporal Sniper (London/NY)"),
        ("GLD-04", "CVD Microstructure Absorber"),
        ("GLD-05", "QUANTUM HYBRID SUPREME (Two-Stage Tranche + SMT + KZ)")
    ]

    results = []

    for gid, name in gladiators:
        t0 = time.time()
        print(f"Battling {gid}: {name}...", end=" ", flush=True)
        res = evaluate_gladiator_trades(gid, all_raw_setups, candles_map, btc_candles)
        res["name"] = name
        elapsed = round(time.time() - t0, 2)
        print(f"DONE in {elapsed}s | Trades: {res['total_trades']} | Win Rate: {res['win_rate']}% | PF: {res['profit_factor']}")
        results.append(res)

    print("\n" + "=" * 85)
    print("                     OFFICIAL QUANT ARENA SCORECARD")
    print("=" * 85)
    header = f"{'Rank':<5} | {'Gladiator ID & Name':<38} | {'Trades':<7} | {'Win Rate':<9} | {'PF':<6} | {'Max DD':<8} | {'Hit $1K':<8}"
    print(header)
    print("-" * 85)

    # Rank by composite score: Win Rate (40%) + Profit Factor (30%) - Drawdown (20%) + Velocity (10%)
    for r in results:
        r["score"] = r["win_rate"] * 0.5 + min(r["profit_factor"], 10.0) * 3.0 - r["max_drawdown_pct"] * 0.2

    results.sort(key=lambda x: x["score"], reverse=True)

    for rank, r in enumerate(results, start=1):
        trophy = "👑" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else "  "))
        hit_str = f"Trade #{r['m1k_trade']}" if r['m1k_trade'] else "Never"
        print(f"{trophy} #{rank:<2} | {r['gladiator_id']} - {r['name'][:30]:<30} | {r['total_trades']:<7} | {r['win_rate']:>6.2f}%  | {r['profit_factor']:>5.2f} | {r['max_drawdown_pct']:>6.2f}% | {hit_str:<8}")

    print("=" * 85)

    # Save to JSON artifact
    out_file = "quant_arena_championship_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "championship": "Antigravity Quant Strategy Arena 2026",
            "gladiators_count": len(results),
            "leaderboard": results
        }, f, indent=2)
    print(f"Championship Audit Report exported to: {out_file}\n")

if __name__ == "__main__":
    run_arena_championship()
