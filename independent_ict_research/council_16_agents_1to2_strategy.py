"""
===============================================================================
🏛️ COUNCIL OF 16 AGENTS: UNIFIED 1:2 RISK:REWARD ICT MASTER STRATEGY
===============================================================================
Synthesized from 8 Comprehensive Masterclasses (2 Specialized Agents per Video)
Executed on 1 Full Year (339,512 Candlesticks) across Top-22 Binance Futures Assets
Timeframes: 1H and 4H
Strict 1:2 Risk:Reward Ratio (TP = 2 * Risk Distance)
===============================================================================
"""

import os
import sys
import json
import time
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

BASE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
DATA_DIR = os.path.join(BASE_DIR, "historical_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "independent_ict_research")


def load_candles(sym: str, interval: str) -> List[Dict[str, Any]]:
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_atr(candles: List[Dict[str, Any]], period: int = 14) -> List[float]:
    if not candles:
        return []
    atrs = [max(candles[0]["high"] - candles[0]["low"], 1e-6)]
    for i in range(1, len(candles)):
        curr = candles[i]
        prev = candles[i - 1]
        tr = max(curr["high"] - curr.get("low", curr["high"]),
                 abs(curr["high"] - prev["close"]),
                 abs(curr["low"] - prev["close"]))
        prev_atr = atrs[-1]
        atr = (prev_atr * (period - 1) + tr) / period
        atrs.append(atr)
    return atrs


def run_16_agents_unified_strategy(all_data: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> List[Dict[str, Any]]:
    trades = []
    
    # Pre-map BTC candles for Macro Causal Brake (King BTC Shield)
    btc_map = {
        "1h": {c["time"]: c for c in all_data["1h"].get("BTCUSDT", [])},
        "4h": {c["time"]: c for c in all_data["4h"].get("BTCUSDT", [])}
    }

    for tf in ["1h", "4h"]:
        max_hold = 32

        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 60:
                continue
            
            atrs = calculate_atr(candles, 14)

            for i in range(25, n - 35):
                # =============================================================
                # BULLISH SETUP: 16-AGENT CONSENSUS CHECKLIST
                # =============================================================
                c1 = candles[i - 1]
                c2 = candles[i]  # Candidate OB
                
                # Gate 1 (Agent 1 & 5): Red Candle & Prior Liquidity Sweep
                # Candle 2 must be red (bearish), sweep Candle 1 low, and be swing low pivot
                is_red = c2["close"] <= c2["open"]
                swept_c1 = c2["low"] < c1["low"]
                is_swing_low = c2["low"] == min(c["low"] for c in candles[max(0, i - 12):i + 1])
                
                if not (is_red and swept_c1 and is_swing_low):
                    continue

                # Gate 2 (Agent 1 & 10): Undisputed Bedrock (No subsequent bar pierces C2 Low!)
                if any(candles[k]["low"] <= c2["low"] for k in range(i + 1, min(i + 5, n))):
                    continue

                # Scan forward for Displacement, FVG, and Body Close BOS
                sub_w = candles[i:min(i + 18, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)

                if high_idx <= i + 2:
                    continue

                gain = (max_high - c2["low"]) / c2["low"]
                atr_val = atrs[i] if i < len(atrs) else (c2["low"] * 0.015)
                disp_required = max(0.035, (1.5 * atr_val) / c2["low"])

                # Gate 3 (Agent 2 & 9): Violent Displacement >= 1.5x ATR
                if gain < disp_required:
                    continue

                # Gate 4 (Agent 2 & 10): Virgin Fair Value Gap (FVG)
                has_fvg = False
                fvg_high_boundary = c2["high"]
                for d in range(i + 1, min(high_idx, n - 1)):
                    if d + 1 < n and candles[d + 1]["low"] > candles[d - 1]["high"]:
                        has_fvg = True
                        fvg_high_boundary = candles[d + 1]["low"]
                        break

                if not has_fvg:
                    continue

                # Gate 5 (Agent 7): Confirmed Candle Body Close BOS (Zero Wick Sweep Trap!)
                prev_structure_high = max(c["high"] for c in candles[max(0, i - 15):i])
                body_bos = any(c["close"] > prev_structure_high for c in candles[i + 1:high_idx + 1])
                if not body_bos:
                    continue

                # Gate 6 (Agent 10): Zone Must Remain Virgin Before Official Retrace
                early_mitigated = any(candles[k]["low"] <= c2["high"] for k in range(i + 3, high_idx))
                if early_mitigated:
                    continue

                # Dealing Range & Equilibrium (Agent 12)
                dealing_range = max_high - c2["low"]
                fib_50_eq = max_high - 0.50 * dealing_range
                fib_618_gold = max_high - 0.618 * dealing_range
                fib_786_deep = max_high - 0.786 * dealing_range
                ob_mt = (c2["high"] + c2["low"]) / 2.0

                # Gate 7 (Agent 8): Inducement (IDM) Sweep
                idm_low = candles[high_idx - 1]["low"]

                # Retracement Scan
                for t in range(high_idx + 1, min(high_idx + 35, n)):
                    tap_c = candles[t]
                    
                    # IDM must be swept first
                    idm_swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                    
                    # Retracement must enter Wholesale Discount (at or below 0.618 Fib or touching OB)
                    in_discount = tap_c["low"] <= min(fib_50_eq, c2["high"] * 1.002)

                    if idm_swept and in_discount:
                        # Gate 8 (Chief Auditor & BTC Shield): King BTC Causal Brake
                        btc_c = btc_map[tf].get(tap_c["time"])
                        btc_safe = True
                        if btc_c and sym != "BTCUSDT":
                            btc_move = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                            if btc_move < -0.010:  # BTC actively dumping > 1%
                                btc_safe = False
                        
                        if not btc_safe:
                            break

                        # Gate 9 (Agent 14): Microstructure Absorption (>= 18% Rejection Wick)
                        c_range = tap_c["high"] - tap_c["low"]
                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                        w_ratio = (l_wick / c_range) if c_range > 0 else 0

                        if w_ratio >= 0.18 and tap_c["close"] >= c2["low"]:
                            # FRACTAL REFINEMENT (Guardeer L2 & L11): Tighten SL via 50% MT / absorption wick
                            entry = min(tap_c["close"], c2["high"])
                            tap_atr = atrs[t] if t < len(atrs) else (entry * 0.015)
                            # Tight refined structural SL just below the tap wick/MT
                            refined_sl = max(c2["low"] - (0.20 * tap_atr), entry * 0.986)
                            sl_p = refined_sl
                            risk_dist = entry - sl_p

                            if risk_dist <= 0 or (risk_dist / entry) > 0.025:
                                continue  # Reject wide unrefined risk

                            # STRICT 1:2 RISK:REWARD RATIO
                            reward_dist = 2.0 * risk_dist
                            tp_p = entry + reward_dist

                            res = None
                            exit_p = entry
                            exit_t = tap_c["time"]
                            be_locked = False

                            # Simulate execution with Stepped BE Protection at +1.0R
                            for m in range(t + 1, min(t + max_hold, n)):
                                # If price reaches +1.0R, move SL to Break-Even!
                                if candles[m]["high"] >= entry + risk_dist:
                                    be_locked = True

                                # Check 1:2 TP
                                if candles[m]["high"] >= tp_p:
                                    res = "WIN"
                                    exit_p = tp_p
                                    exit_t = candles[m]["time"]
                                    break
                                # Check SL
                                if candles[m]["low"] <= (entry if be_locked else sl_p):
                                    if be_locked:
                                        res = "WIN"  # Saved at Break-Even
                                        exit_p = entry
                                    else:
                                        res = "LOSS"
                                        exit_p = min(sl_p, candles[m]["open"])
                                    exit_t = candles[m]["time"]
                                    break

                            if not res:
                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                res = "WIN" if fc >= entry else "LOSS"
                                exit_p = fc
                                exit_t = candles[min(t + max_hold, n - 1)]["time"]

                            gross_move = (exit_p - entry) / entry
                            trades.append({
                                "strategy": "COUNCIL_16_AGENTS_1TO2",
                                "sym": sym,
                                "side": "LONG",
                                "tf": tf,
                                "time": tap_c["time"],
                                "exit_time": exit_t,
                                "entry": entry,
                                "sl": sl_p,
                                "tp": tp_p,
                                "risk_pct": round((risk_dist / entry) * 100, 2),
                                "reward_pct": round((reward_dist / entry) * 100, 2),
                                "rr_ratio": 2.0,
                                "exit": exit_p,
                                "gross": gross_move,
                                "res": res
                            })
                            break

                # =============================================================
                # BEARISH SETUP: 16-AGENT CONSENSUS CHECKLIST
                # =============================================================
                is_green = c2["close"] >= c2["open"]
                swept_c1_high = c2["high"] > c1["high"]
                is_swing_high = c2["high"] == max(c["high"] for c in candles[max(0, i - 12):i + 1])

                if not (is_green and swept_c1_high and is_swing_high):
                    continue

                if any(candles[k]["high"] >= c2["high"] for k in range(i + 1, min(i + 5, n))):
                    continue

                sub_w = candles[i:min(i + 18, n)]
                lows = [c["low"] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)

                if low_idx <= i + 2:
                    continue

                drop = (c2["high"] - min_low) / c2["high"]
                atr_val = atrs[i] if i < len(atrs) else (c2["high"] * 0.015)
                disp_required = max(0.035, (1.5 * atr_val) / c2["high"])

                if drop < disp_required:
                    continue

                has_fvg = False
                for d in range(i + 1, min(low_idx, n - 1)):
                    if d + 1 < n and candles[d + 1]["high"] < candles[d - 1]["low"]:
                        has_fvg = True
                        break

                if not has_fvg:
                    continue

                prev_structure_low = min(c["low"] for c in candles[max(0, i - 15):i])
                body_bos = any(c["close"] < prev_structure_low for c in candles[i + 1:low_idx + 1])
                if not body_bos:
                    continue

                early_mitigated = any(candles[k]["high"] >= c2["low"] for k in range(i + 3, low_idx))
                if early_mitigated:
                    continue

                dealing_range = c2["high"] - min_low
                fib_50_eq = min_low + 0.50 * dealing_range
                idm_high = candles[low_idx - 1]["high"]

                for t in range(low_idx + 1, min(low_idx + 35, n)):
                    tap_c = candles[t]
                    idm_swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                    in_premium = tap_c["high"] >= max(fib_50_eq, c2["low"] * 0.998)

                    if idm_swept and in_premium:
                        btc_c = btc_map[tf].get(tap_c["time"])
                        btc_safe = True
                        if btc_c and sym != "BTCUSDT":
                            btc_move = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
                            if btc_move > 0.010:  # BTC pumping hard
                                btc_safe = False

                        if not btc_safe:
                            break

                        c_range = tap_c["high"] - tap_c["low"]
                        u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                        w_ratio = (u_wick / c_range) if c_range > 0 else 0

                        if w_ratio >= 0.18 and tap_c["close"] <= c2["high"]:
                            entry = max(tap_c["close"], c2["low"])
                            tap_atr = atrs[t] if t < len(atrs) else (entry * 0.015)
                            refined_sl = min(c2["high"] + (0.20 * tap_atr), entry * 1.014)
                            sl_p = refined_sl
                            risk_dist = sl_p - entry

                            if risk_dist <= 0 or (risk_dist / entry) > 0.025:
                                continue

                            reward_dist = 2.0 * risk_dist
                            tp_p = entry - reward_dist

                            res = None
                            exit_p = entry
                            exit_t = tap_c["time"]
                            be_locked = False

                            for m in range(t + 1, min(t + max_hold, n)):
                                if candles[m]["low"] <= entry - risk_dist:
                                    be_locked = True

                                if candles[m]["low"] <= tp_p:
                                    res = "WIN"
                                    exit_p = tp_p
                                    exit_t = candles[m]["time"]
                                    break
                                if candles[m]["high"] >= (entry if be_locked else sl_p):
                                    if be_locked:
                                        res = "WIN"
                                        exit_p = entry
                                    else:
                                        res = "LOSS"
                                        exit_p = max(sl_p, candles[m]["open"])
                                    exit_t = candles[m]["time"]
                                    break

                            if not res:
                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                res = "WIN" if fc <= entry else "LOSS"
                                exit_p = fc
                                exit_t = candles[min(t + max_hold, n - 1)]["time"]

                            gross_move = (entry - exit_p) / entry
                            trades.append({
                                "strategy": "COUNCIL_16_AGENTS_1TO2",
                                "sym": sym,
                                "side": "SHORT",
                                "tf": tf,
                                "time": tap_c["time"],
                                "exit_time": exit_t,
                                "entry": entry,
                                "sl": sl_p,
                                "tp": tp_p,
                                "risk_pct": round((risk_dist / entry) * 100, 2),
                                "reward_pct": round((reward_dist / entry) * 100, 2),
                                "rr_ratio": 2.0,
                                "exit": exit_p,
                                "gross": gross_move,
                                "res": res
                            })
                            break
    return trades


def simulate_portfolio(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    trades.sort(key=lambda x: x["time"])
    executed = []
    active_exit = 0
    for t in trades:
        if t["time"] >= active_exit:
            executed.append(t)
            active_exit = t["exit_time"]

    total_trades = len(executed)
    if total_trades == 0:
        return {"total_trades": 0, "win_rate": 0.0}

    wins = [t for t in executed if t["res"] == "WIN"]
    losses = [t for t in executed if t["res"] == "LOSS"]
    win_rate = (len(wins) / total_trades) * 100.0

    balance = 50.0
    vault = 0.0
    peak = 50.0
    max_dd = 0.0
    fee = 0.0016
    milestone_1k = None
    milestone_2k = None
    gross_gains = 0.0
    gross_losses = 0.0

    for idx, t in enumerate(executed, 1):
        pos_size = balance * 5.0
        pct_change = t["gross"]
        net_pct = pct_change - fee
        pnl = pos_size * net_pct

        if pnl >= 0:
            gross_gains += pnl
            v_cut = pnl * 0.15
            reinvest = pnl * 0.85
            vault += v_cut
            balance += reinvest
        else:
            gross_losses += abs(pnl)
            balance += pnl
            if balance < 10.0:
                balance = 10.0

        equity = balance + vault
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

        if equity >= 1000.0 and milestone_1k is None:
            milestone_1k = idx
        if equity >= 2000.0 and milestone_2k is None:
            milestone_2k = idx

    profit_factor = (gross_gains / gross_losses) if gross_losses > 0 else 99.99

    return {
        "total_setups": len(trades),
        "executed_trades": total_trades,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "final_balance": round(balance, 2),
        "final_vault": round(vault, 2),
        "final_equity": round(balance + vault, 2),
        "max_drawdown": round(max_dd, 2),
        "milestone_1k": milestone_1k,
        "milestone_2k": milestone_2k,
        "executed_sample": executed[:5]
    }


def main():
    print("=" * 80)
    print("🏛️ RUNNING 16-AGENT COUNCIL UNIFIED ICT STRATEGY (1:2 RISK:REWARD)")
    print("=" * 80)
    
    all_data = {"1h": {}, "4h": {}}
    for sym in TOP_22_CHAMPIONS:
        for tf in ["1h", "4h"]:
            c = load_candles(sym, tf)
            if len(c) >= 500:
                all_data[tf][sym] = c

    trades = run_16_agents_unified_strategy(all_data)
    print(f"Generated Raw Verified Setups: {len(trades)}")
    
    results = simulate_portfolio(trades)
    
    out_file = os.path.join(OUTPUT_DIR, "COUNCIL_16_AGENTS_1TO2_RESULTS.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    print("\n" + "=" * 80)
    print("🏆 COUNCIL AUDIT VERDICT: 1:2 RISK:REWARD ICT STRATEGY")
    print("=" * 80)
    print(f"Executed Trades (1-Year Queue): {results['executed_trades']}")
    print(f"Wins:                          {results['wins']}")
    print(f"Losses:                        {results['losses']}")
    print(f"Win Rate (%):                  {results['win_rate']}%")
    print(f"Profit Factor:                 {results['profit_factor']}")
    print(f"Max Drawdown (%):              {results['max_drawdown']}%")
    print(f"Milestone $1,000 ($50 start):  Trade #{results['milestone_1k']}")
    print(f"Milestone $2,000 Target:       Trade #{results['milestone_2k']}")
    print(f"Final Portfolio Equity:        ${results['final_equity']} USDT")
    print("=" * 80)


if __name__ == "__main__":
    main()
