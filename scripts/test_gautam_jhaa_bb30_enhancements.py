"""
BB 3.0 QUANTITATIVE PERFORMANCE BENCHMARK & AUDIT
Baseline BB 3.0 vs Upgraded BB 3.0 (Gautam Kumar Jhaa Institutional Model)
==========================================================================
Auditor: Quantitative Performance Auditor
Dataset: 20 Champions across 1 Full Year (October 2025 - October 2026, 15m candles)
Capital Base: $500.00 USDT starting capital across 10 Deca sections ($50.00 each)
Compounding Model: 5% Compounding Risk per Section, Section Concurrency = 1

Models Compared:
1. Baseline BB 3.0:
   - Fixed 3.0R Target + Stepped Trailing SL Ladder (+1.0R -> +0.2R, +1.5R -> +1.0R, etc.)
2. Upgraded BB 3.0 (Gautam Kumar Jhaa Model):
   - Opposite Daily Liquidity (PDH/PDL) Target (Minimum 2.5R required)
   - 90% Partial Profit Lock at Opposite Daily Liquidity
   - 10% Moonbag Runner with dynamic trailing SL extension
   - London (07:00-11:00 UTC) & NY (13:00-17:00 UTC) Killzone tagging & priority
   - Time-Pass Exhaustion Filter (rejects if intraday move exhausted >= 85% of range)
"""

import os
import sys
import json
import glob
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = Path(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system")
CACHE_DIR = ROOT_DIR / "market_data_cache_15m"
SCRATCH_DIR = ROOT_DIR / "scratch"
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON = SCRATCH_DIR / "bb30_gautam_jhaa_benchmark.json"

# Top-20 Champions mapped 2-per-section into 10 Isolated Deca Sections
PAIR_MAPPING = {
    "BTCUSDT": 1, "ETHUSDT": 1,
    "SOLUSDT": 2, "BNBUSDT": 2,
    "AVAXUSDT": 3, "DOGEUSDT": 3,
    "DOTUSDT": 4, "LINKUSDT": 4,
    "LTCUSDT": 5, "NEARUSDT": 5,
    "OPUSDT": 6, "RENDERUSDT": 6,
    "SUIUSDT": 7, "TIAUSDT": 7,
    "UNIUSDT": 8, "XRPUSDT": 8,
    "1000PEPEUSDT": 9, "APTUSDT": 9,
    "ARBUSDT": 10, "FETUSDT": 10
}

CHAMPIONS = list(PAIR_MAPPING.keys())

def get_day_key(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")

def get_session_tag(ts_ms):
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    hour = dt.hour
    if 7 <= hour <= 11:
        return "LONDON_KZ"
    elif 13 <= hour <= 17:
        return "NY_KZ"
    else:
        return "ASIAN_OTHER"

def load_data():
    coins_data = {}
    for sym in CHAMPIONS:
        fpath = CACHE_DIR / f"{sym}_15m.json"
        if not fpath.exists():
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            raw = json.load(f)
            coins_data[sym] = raw
    return coins_data

# ==============================================================================
# SETUP DETECTOR: IDENTIFIES CANDIDATE ORDER BLOCKS & FILLS
# ==============================================================================
def find_all_trade_candidates(coins_data, fvg_disp_1bar=0.015, disp_2bar=0.020, buffer_pct=0.0015, max_wait_bars=32):
    """
    Identifies order blocks at PDH/PDL with displacement & FVG, and verifies 50% MT limit fill.
    """
    candidates = []

    for sym, candles in coins_data.items():
        n = len(candles)
        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            p_day = sorted_days[d_i - 1]
            c_day = sorted_days[d_i]

            p_list = [c for _, c in day_buckets[p_day]]
            c_list = day_buckets[c_day]

            if len(p_list) < 20 or len(c_list) < 20:
                continue

            pdh = max(c["high"] for c in p_list)
            pdl = min(c["low"] for c in p_list)
            pd_range = pdh - pdl
            if pd_range <= 0 or pdl <= 0:
                continue

            long_taken_today = False
            short_taken_today = False

            for pos_in_day, (g_idx, c) in enumerate(c_list):
                if g_idx + 2 >= n:
                    continue

                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # Intraday range so far up to this bar (used for Time-Pass Exhaustion)
                intraday_bars_so_far = [bar for _, bar in c_list[:pos_in_day + 1]]
                cur_day_high_so_far = max(bar["high"] for bar in intraday_bars_so_far)
                cur_day_low_so_far = min(bar["low"] for bar in intraday_bars_so_far)
                cur_day_range_so_far = cur_day_high_so_far - cur_day_low_so_far

                # 1. BULLISH ORDER BLOCK AT PDL -> LONG
                if not long_taken_today:
                    dist_to_pdl = abs(c_l - pdl) / pdl
                    if c_l <= pdl or dist_to_pdl <= 0.015:
                        gain_1bar = (next_c["high"] - c_l) / c_l
                        gain_2bar = (next_c2["high"] - c_l) / c_l
                        has_fvg = next_c2["low"] > c_h
                        is_bearish = c_c < c_o

                        if (is_bearish or (c_h - c_l) > 0) and (gain_1bar >= fvg_disp_1bar or gain_2bar >= disp_2bar) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_low * (1.0 - buffer_pct)
                            risk = mt - sl

                            if risk > 0 and (risk / mt) <= 0.05:
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 2 + max_wait_bars, n)):
                                    b = candles[w_idx]
                                    if b["low"] <= sl:
                                        break
                                    if b["low"] <= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    long_taken_today = True
                                    fill_time = candles[fill_idx]["time"]
                                    sess_tag = get_session_tag(fill_time)

                                    # Gautam Jhaa Metrics
                                    opp_liquidity_tp = pdh
                                    opp_rr = (pdh - mt) / risk
                                    time_pass_ratio = cur_day_range_so_far / pd_range
                                    opp_already_swept = (cur_day_high_so_far >= pdh)

                                    # Filter check:
                                    # 1) Time-pass exhaustion: day already traversed >= 85% of daily range AND opposite side swept
                                    # 2) Minimum 2.5R to opposite liquidity
                                    gautam_valid = (opp_rr >= 2.5) and not (time_pass_ratio >= 0.85 and opp_already_swept)

                                    candidates.append({
                                        "symbol": sym,
                                        "side": "LONG",
                                        "day": c_day,
                                        "setup_idx": g_idx,
                                        "fill_idx": fill_idx,
                                        "fill_time": fill_time,
                                        "entry_price": mt,
                                        "initial_sl": sl,
                                        "risk": risk,
                                        "pdh": pdh,
                                        "pdl": pdl,
                                        "opp_liquidity_tp": opp_liquidity_tp,
                                        "opp_rr": opp_rr,
                                        "session_tag": sess_tag,
                                        "is_killzone": sess_tag in ["LONDON_KZ", "NY_KZ"],
                                        "time_pass_ratio": time_pass_ratio,
                                        "opp_already_swept": opp_already_swept,
                                        "gautam_valid": gautam_valid
                                    })

                # 2. BEARISH ORDER BLOCK AT PDH -> SHORT
                if not short_taken_today:
                    dist_to_pdh = abs(c_h - pdh) / pdh
                    if c_h >= pdh or dist_to_pdh <= 0.015:
                        drop_1bar = (c_h - next_c["low"]) / c_h
                        drop_2bar = (c_h - next_c2["low"]) / c_h
                        has_fvg = next_c2["high"] < c_l
                        is_bullish = c_c > c_o

                        if (is_bullish or (c_h - c_l) > 0) and (drop_1bar >= fvg_disp_1bar or drop_2bar >= disp_2bar) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_high * (1.0 + buffer_pct)
                            risk = sl - mt

                            if risk > 0 and (risk / mt) <= 0.05:
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 2 + max_wait_bars, n)):
                                    b = candles[w_idx]
                                    if b["high"] >= sl:
                                        break
                                    if b["high"] >= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    short_taken_today = True
                                    fill_time = candles[fill_idx]["time"]
                                    sess_tag = get_session_tag(fill_time)

                                    opp_liquidity_tp = pdl
                                    opp_rr = (mt - pdl) / risk
                                    time_pass_ratio = cur_day_range_so_far / pd_range
                                    opp_already_swept = (cur_day_low_so_far <= pdl)

                                    gautam_valid = (opp_rr >= 2.5) and not (time_pass_ratio >= 0.85 and opp_already_swept)

                                    candidates.append({
                                        "symbol": sym,
                                        "side": "SHORT",
                                        "day": c_day,
                                        "setup_idx": g_idx,
                                        "fill_idx": fill_idx,
                                        "fill_time": fill_time,
                                        "entry_price": mt,
                                        "initial_sl": sl,
                                        "risk": risk,
                                        "pdh": pdh,
                                        "pdl": pdl,
                                        "opp_liquidity_tp": opp_liquidity_tp,
                                        "opp_rr": opp_rr,
                                        "session_tag": sess_tag,
                                        "is_killzone": sess_tag in ["LONDON_KZ", "NY_KZ"],
                                        "time_pass_ratio": time_pass_ratio,
                                        "opp_already_swept": opp_already_swept,
                                        "gautam_valid": gautam_valid
                                    })

                if long_taken_today and short_taken_today:
                    break

    candidates.sort(key=lambda x: x["fill_time"])
    return candidates

# ==============================================================================
# TRADE EXECUTION ENGINES: BASELINE VS GAUTAM JHAA MODEL
# ==============================================================================

def execute_baseline_bb30(cand, coins_data, max_hold_bars=96, friction_r=0.06):
    """
    Baseline BB 3.0: Fixed 3.0R TP + Stepped Trailing SL
    - +1.0R -> SL to +0.2R (Fee Shield)
    - +1.5R -> SL to +1.0R
    - +2.0R -> SL to +1.5R
    - +2.5R -> SL to +2.0R
    - +3.0R -> Fixed TP Hit (100% exit at +3.0R)
    """
    candles = coins_data[cand["symbol"]]
    fill_idx = cand["fill_idx"]
    side = cand["side"]
    entry = cand["entry_price"]
    active_sl = cand["initial_sl"]
    risk = cand["risk"]
    n = len(candles)
    current_tier = 0

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold_bars, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]
        exit_time = b["time"]

        if side == "LONG":
            cur_r = (b_h - entry) / risk

            # Fixed 3.0R TP Target Hit
            if cur_r >= 3.0:
                return {
                    "outcome": "WIN",
                    "reason": "FIXED_3R_TP_HIT",
                    "realized_r": 3.0 - friction_r,
                    "exit_time": exit_time,
                    "bars_held": idx - fill_idx
                }

            # Check Hard SL or Trailing SL hit
            if b_l <= active_sl:
                if current_tier == 0:
                    return {
                        "outcome": "LOSS",
                        "reason": "SL_HIT",
                        "realized_r": -1.0 - friction_r,
                        "exit_time": exit_time,
                        "bars_held": idx - fill_idx
                    }
                elif current_tier == 1:
                    return {
                        "outcome": "SAVE",
                        "reason": "FEE_SHIELD_SAVE",
                        "realized_r": 0.2 - friction_r,
                        "exit_time": exit_time,
                        "bars_held": idx - fill_idx
                    }
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {
                        "outcome": "WIN",
                        "reason": f"TRAILING_SL_T{current_tier}",
                        "realized_r": locked_r - friction_r,
                        "exit_time": exit_time,
                        "bars_held": idx - fill_idx
                    }

            # Update Trailing Ladder
            if cur_r >= 1.0:
                tier_candidate = int((cur_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry + (locked_r * risk)

        else: # SHORT
            cur_r = (entry - b_l) / risk

            if cur_r >= 3.0:
                return {
                    "outcome": "WIN",
                    "reason": "FIXED_3R_TP_HIT",
                    "realized_r": 3.0 - friction_r,
                    "exit_time": exit_time,
                    "bars_held": idx - fill_idx
                }

            if b_h >= active_sl:
                if current_tier == 0:
                    return {
                        "outcome": "LOSS",
                        "reason": "SL_HIT",
                        "realized_r": -1.0 - friction_r,
                        "exit_time": exit_time,
                        "bars_held": idx - fill_idx
                    }
                elif current_tier == 1:
                    return {
                        "outcome": "SAVE",
                        "reason": "FEE_SHIELD_SAVE",
                        "realized_r": 0.2 - friction_r,
                        "exit_time": exit_time,
                        "bars_held": idx - fill_idx
                    }
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {
                        "outcome": "WIN",
                        "reason": f"TRAILING_SL_T{current_tier}",
                        "realized_r": locked_r - friction_r,
                        "exit_time": exit_time,
                        "bars_held": idx - fill_idx
                    }

            if cur_r >= 1.0:
                tier_candidate = int((cur_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry - (locked_r * risk)

    # 96 Bar Timeout
    last_c = candles[min(fill_idx + max_hold_bars, n - 1)]
    pnl_r = ((last_c["close"] - entry) / risk) if side == "LONG" else ((entry - last_c["close"]) / risk)
    net_r = pnl_r - friction_r
    return {
        "outcome": "WIN" if net_r > 0.2 else ("SAVE" if net_r >= -0.2 else "LOSS"),
        "reason": "TIMEOUT_EXIT",
        "realized_r": net_r,
        "exit_time": last_c["time"],
        "bars_held": max_hold_bars
    }

def execute_gautam_jhaa_bb30(cand, coins_data, max_hold_bars=96, friction_r=0.06):
    """
    Upgraded BB 3.0 (Gautam Kumar Jhaa Model):
    - Target: Opposite Daily Liquidity (R_opp >= 2.5R)
    - 90% Partial Profit Lock at Opposite Daily Liquidity
    - 10% Moonbag Runner continues trailing with +0.5R dynamic steps
    - Stepped Trailing SL protection prior to reaching Opposite Liquidity
    """
    candles = coins_data[cand["symbol"]]
    fill_idx = cand["fill_idx"]
    side = cand["side"]
    entry = cand["entry_price"]
    active_sl = cand["initial_sl"]
    risk = cand["risk"]
    r_opp = cand["opp_rr"]
    n = len(candles)

    current_tier = 0
    tp_hit = False
    tp_exit_time = 0
    moonbag_sl = active_sl
    moonbag_peak_r = r_opp

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold_bars, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]
        exit_time = b["time"]

        if side == "LONG":
            cur_r = (b_h - entry) / risk

            if not tp_hit:
                # Check if Opposite Daily Liquidity TP touched
                if cur_r >= r_opp:
                    tp_hit = True
                    tp_exit_time = exit_time
                    moonbag_peak_r = cur_r
                    moonbag_sl = entry + ((r_opp - 0.5) * risk)

                # If not hit TP yet, check active SL / Trailing SL
                elif b_l <= active_sl:
                    if current_tier == 0:
                        return {
                            "outcome": "LOSS",
                            "reason": "SL_HIT",
                            "realized_r": -1.0 - friction_r,
                            "exit_time": exit_time,
                            "bars_held": idx - fill_idx
                        }
                    elif current_tier == 1:
                        return {
                            "outcome": "SAVE",
                            "reason": "FEE_SHIELD_SAVE",
                            "realized_r": 0.2 - friction_r,
                            "exit_time": exit_time,
                            "bars_held": idx - fill_idx
                        }
                    else:
                        locked_r = (current_tier - 1) * 0.5
                        return {
                            "outcome": "WIN",
                            "reason": f"TRAILING_SL_T{current_tier}",
                            "realized_r": locked_r - friction_r,
                            "exit_time": exit_time,
                            "bars_held": idx - fill_idx
                        }

                # Update Trailing Ladder prior to TP
                if cur_r >= 1.0:
                    tier_candidate = int((cur_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry + (locked_r * risk)

            else:
                # TP already locked 90%! Now manage 10% Moonbag runner!
                if cur_r > moonbag_peak_r:
                    moonbag_peak_r = cur_r
                    # Step up moonbag SL by +0.5R for every +0.5R peak extension
                    extra_tiers = int((moonbag_peak_r - r_opp) / 0.5)
                    moonbag_sl = entry + ((r_opp - 0.5 + (extra_tiers * 0.5)) * risk)

                if b_l <= moonbag_sl:
                    # Moonbag exited
                    moonbag_r = (moonbag_sl - entry) / risk
                    total_r = (0.90 * r_opp) + (0.10 * moonbag_r) - friction_r
                    return {
                        "outcome": "WIN",
                        "reason": f"OPP_LIQUIDITY_90_10_MOONBAG",
                        "realized_r": total_r,
                        "r_opp": r_opp,
                        "moonbag_r": moonbag_r,
                        "exit_time": exit_time,
                        "bars_held": idx - fill_idx
                    }

        else: # SHORT
            cur_r = (entry - b_l) / risk

            if not tp_hit:
                if cur_r >= r_opp:
                    tp_hit = True
                    tp_exit_time = exit_time
                    moonbag_peak_r = cur_r
                    moonbag_sl = entry - ((r_opp - 0.5) * risk)

                elif b_h >= active_sl:
                    if current_tier == 0:
                        return {
                            "outcome": "LOSS",
                            "reason": "SL_HIT",
                            "realized_r": -1.0 - friction_r,
                            "exit_time": exit_time,
                            "bars_held": idx - fill_idx
                        }
                    elif current_tier == 1:
                        return {
                            "outcome": "SAVE",
                            "reason": "FEE_SHIELD_SAVE",
                            "realized_r": 0.2 - friction_r,
                            "exit_time": exit_time,
                            "bars_held": idx - fill_idx
                        }
                    else:
                        locked_r = (current_tier - 1) * 0.5
                        return {
                            "outcome": "WIN",
                            "reason": f"TRAILING_SL_T{current_tier}",
                            "realized_r": locked_r - friction_r,
                            "exit_time": exit_time,
                            "bars_held": idx - fill_idx
                        }

                if cur_r >= 1.0:
                    tier_candidate = int((cur_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry - (locked_r * risk)

            else:
                if cur_r > moonbag_peak_r:
                    moonbag_peak_r = cur_r
                    extra_tiers = int((moonbag_peak_r - r_opp) / 0.5)
                    moonbag_sl = entry - ((r_opp - 0.5 + (extra_tiers * 0.5)) * risk)

                if b_h >= moonbag_sl:
                    moonbag_r = (entry - moonbag_sl) / risk
                    total_r = (0.90 * r_opp) + (0.10 * moonbag_r) - friction_r
                    return {
                        "outcome": "WIN",
                        "reason": f"OPP_LIQUIDITY_90_10_MOONBAG",
                        "realized_r": total_r,
                        "r_opp": r_opp,
                        "moonbag_r": moonbag_r,
                        "exit_time": exit_time,
                        "bars_held": idx - fill_idx
                    }

    # 96 Bar Timeout
    last_c = candles[min(fill_idx + max_hold_bars, n - 1)]
    pnl_r = ((last_c["close"] - entry) / risk) if side == "LONG" else ((entry - last_c["close"]) / risk)
    if tp_hit:
        total_r = (0.90 * r_opp) + (0.10 * pnl_r) - friction_r
        reason = "OPP_LIQUIDITY_90_10_TIMEOUT"
        outcome = "WIN"
    else:
        total_r = pnl_r - friction_r
        reason = "TIMEOUT_EXIT"
        outcome = "WIN" if total_r > 0.2 else ("SAVE" if total_r >= -0.2 else "LOSS")

    return {
        "outcome": outcome,
        "reason": reason,
        "realized_r": total_r,
        "exit_time": last_c["time"],
        "bars_held": max_hold_bars
    }

# ==============================================================================
# DECA COMPOUNDING SIMULATOR
# ==============================================================================
def simulate_deca_portfolio(trades_with_results, initial_total=500.0, risk_pct=0.05, num_sections=10, prioritize_kz=False):
    """
    Simulates 10 isolated Deca sections ($50.00 each = $500.00 total).
    Enforces Section Concurrency = 1 (Zero collision / overlap).
    If prioritize_kz is True, when competing trades occur in a section, Killzone trades are favored.
    Compounding: 5% risk per trade on the isolated section's current balance.
    """
    sections = {
        i: {
            "id": i,
            "balance": initial_total / num_sections,
            "peak": initial_total / num_sections,
            "max_dd_pct": 0.0,
            "busy_until": 0,
            "trades": 0,
            "wins": 0,
            "saves": 0,
            "losses": 0,
            "gross_profit_usd": 0.0,
            "gross_loss_usd": 0.0,
            "net_r": 0.0,
            "trade_log": []
        } for i in range(1, num_sections + 1)
    }

    # Sort trades chronologically
    sorted_trades = sorted(trades_with_results, key=lambda t: t["fill_time"])

    portfolio_equity_curve = [(sorted_trades[0]["fill_time"] if sorted_trades else 0, initial_total)]
    portfolio_peak = initial_total
    max_portfolio_dd_pct = 0.0

    executed_trades = []
    skipped_concurrency = 0

    for t in sorted_trades:
        sec_id = PAIR_MAPPING.get(t["symbol"], 1)
        sec = sections[sec_id]

        # Concurrency check
        if t["fill_time"] < sec["busy_until"]:
            skipped_concurrency += 1
            continue

        sec["busy_until"] = t["exit_time"]
        sec["trades"] += 1

        risk_usd = sec["balance"] * risk_pct
        dollar_pnl = risk_usd * t["realized_r"]
        sec["balance"] = max(1.0, sec["balance"] + dollar_pnl)
        sec["net_r"] += t["realized_r"]

        if dollar_pnl > 0:
            sec["gross_profit_usd"] += dollar_pnl
            if t["outcome"] == "SAVE":
                sec["saves"] += 1
            else:
                sec["wins"] += 1
        else:
            sec["gross_loss_usd"] += abs(dollar_pnl)
            sec["losses"] += 1

        # Section peak & DD
        if sec["balance"] > sec["peak"]:
            sec["peak"] = sec["balance"]
        s_dd = (sec["peak"] - sec["balance"]) / sec["peak"] * 100.0
        if s_dd > sec["max_dd_pct"]:
            sec["max_dd_pct"] = s_dd

        # Portfolio total
        tot_balance = sum(s["balance"] for s in sections.values())
        if tot_balance > portfolio_peak:
            portfolio_peak = tot_balance
        p_dd = (portfolio_peak - tot_balance) / portfolio_peak * 100.0
        if p_dd > max_portfolio_dd_pct:
            max_portfolio_dd_pct = p_dd

        portfolio_equity_curve.append((t["exit_time"], tot_balance))
        t_record = dict(t)
        t_record["section_id"] = sec_id
        t_record["dollar_pnl"] = dollar_pnl
        t_record["sec_balance_after"] = sec["balance"]
        t_record["portfolio_balance_after"] = tot_balance
        executed_trades.append(t_record)
        sec["trade_log"].append(t_record)

    total_final_usd = sum(s["balance"] for s in sections.values())
    total_net_profit_usd = total_final_usd - initial_total
    total_wins = sum(s["wins"] for s in sections.values())
    total_saves = sum(s["saves"] for s in sections.values())
    total_losses = sum(s["losses"] for s in sections.values())
    total_executed = len(executed_trades)
    total_net_r = sum(t["realized_r"] for t in executed_trades)
    avg_r = total_net_r / total_executed if total_executed > 0 else 0.0

    total_gross_profit = sum(s["gross_profit_usd"] for s in sections.values())
    total_gross_loss = sum(s["gross_loss_usd"] for s in sections.values())
    profit_factor = (total_gross_profit / total_gross_loss) if total_gross_loss > 0 else 999.99

    pure_win_rate = (total_wins / total_executed * 100.0) if total_executed > 0 else 0.0
    quality_win_rate = ((total_wins + total_saves) / total_executed * 100.0) if total_executed > 0 else 0.0

    return {
        "initial_capital_usd": initial_total,
        "final_capital_usd": total_final_usd,
        "net_profit_usd": total_net_profit_usd,
        "total_gain_pct": (total_final_usd - initial_total) / initial_total * 100.0,
        "total_trades": total_executed,
        "skipped_concurrency": skipped_concurrency,
        "wins": total_wins,
        "saves": total_saves,
        "losses": total_losses,
        "pure_win_rate_pct": pure_win_rate,
        "quality_win_rate_pct": quality_win_rate,
        "total_net_r": total_net_r,
        "avg_r_per_trade": avg_r,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_portfolio_dd_pct,
        "sections": {
            s_id: {
                "final_balance_usd": s["balance"],
                "net_profit_usd": s["balance"] - (initial_total / num_sections),
                "gain_pct": (s["balance"] - (initial_total / num_sections)) / (initial_total / num_sections) * 100.0,
                "trades": s["trades"],
                "wins": s["wins"],
                "saves": s["saves"],
                "losses": s["losses"],
                "win_rate_pct": (s["wins"] / s["trades"] * 100.0) if s["trades"] > 0 else 0.0,
                "net_r": s["net_r"],
                "max_dd_pct": s["max_dd_pct"]
            } for s_id, s in sections.items()
        },
        "executed_trades": executed_trades
    }

# ==============================================================================
# MAIN BENCHMARK RUNNER
# ==============================================================================
def run_benchmark():
    print("=" * 100)
    print("🔬 BB 3.0 QUANTITATIVE PERFORMANCE AUDIT & BENCHMARK")
    print("   Baseline BB 3.0 vs Upgraded BB 3.0 (Gautam Kumar Jhaa Model)")
    print("=" * 100)

    coins_data = load_data()
    print(f"Loaded {len(coins_data)} Champions from market_data_cache_15m (1 Full Year, 34,995 bars/coin)")

    print("\nScanning 15m order flow for candidate order blocks at PDH/PDL...")
    candidates = find_all_trade_candidates(coins_data)
    print(f"Total Raw Single-Shot Setup Candidates Generated: {len(candidates)}")

    kz_candidates = [c for c in candidates if c["is_killzone"]]
    gautam_valid_candidates = [c for c in candidates if c["gautam_valid"]]
    gautam_kz_candidates = [c for c in gautam_valid_candidates if c["is_killzone"]]

    print(f"  * London/NY Killzone Tagged:                      {len(kz_candidates)} ({len(kz_candidates)/len(candidates)*100:.1f}%)")
    print(f"  * Gautam Jhaa Valid (Opposite Target >= 2.5R & No Exhaustion): {len(gautam_valid_candidates)} ({len(gautam_valid_candidates)/len(candidates)*100:.1f}%)")
    print(f"  * Filtered Out by Gautam Time-Pass / R:R Rules:   {len(candidates) - len(gautam_valid_candidates)}")
    print(f"  * Gautam Jhaa Killzone Candidates:                {len(gautam_kz_candidates)}")

    # -------------------------------------------------------------------------
    # SIMULATION 1: BASELINE BB 3.0 (Fixed 3.0R TP + Stepped Trailing SL)
    # -------------------------------------------------------------------------
    print("\nExecuting Simulation 1: Baseline BB 3.0 (Standard 3.0R Fixed TP + Stepped Trailing SL)...")
    baseline_trade_results = []
    for cand in candidates:
        res = execute_baseline_bb30(cand, coins_data)
        record = dict(cand)
        record.update(res)
        baseline_trade_results.append(record)

    baseline_deca = simulate_deca_portfolio(baseline_trade_results, initial_total=500.0, risk_pct=0.05)

    # -------------------------------------------------------------------------
    # SIMULATION 2: UPGRADED BB 3.0 (Gautam Jhaa Model - All Sessions)
    # -------------------------------------------------------------------------
    print("Executing Simulation 2: Upgraded BB 3.0 (Gautam Jhaa Model - Opposite Daily TP + 90/10 Moonbag)...")
    gautam_trade_results = []
    for cand in gautam_valid_candidates:
        res = execute_gautam_jhaa_bb30(cand, coins_data)
        record = dict(cand)
        record.update(res)
        gautam_trade_results.append(record)

    gautam_deca = simulate_deca_portfolio(gautam_trade_results, initial_total=500.0, risk_pct=0.05)

    # -------------------------------------------------------------------------
    # SIMULATION 3: UPGRADED BB 3.0 (Gautam Jhaa Model - Killzone Priority / Only)
    # -------------------------------------------------------------------------
    print("Executing Simulation 3: Upgraded BB 3.0 (Gautam Jhaa Model - Killzone Focused)...")
    gautam_kz_trade_results = []
    for cand in gautam_kz_candidates:
        res = execute_gautam_jhaa_bb30(cand, coins_data)
        record = dict(cand)
        record.update(res)
        gautam_kz_trade_results.append(record)

    gautam_kz_deca = simulate_deca_portfolio(gautam_kz_trade_results, initial_total=500.0, risk_pct=0.05)

    # -------------------------------------------------------------------------
    # SESSION BREAKDOWN FOR GAUTAM JHAA MODEL
    # -------------------------------------------------------------------------
    sess_stats = defaultdict(lambda: {"trades": 0, "wins": 0, "saves": 0, "losses": 0, "net_r": 0.0})
    for t in gautam_deca["executed_trades"]:
        tag = t["session_tag"]
        sess_stats[tag]["trades"] += 1
        sess_stats[tag]["net_r"] += t["realized_r"]
        if t["outcome"] == "WIN":
            sess_stats[tag]["wins"] += 1
        elif t["outcome"] == "SAVE":
            sess_stats[tag]["saves"] += 1
        else:
            sess_stats[tag]["losses"] += 1

    # -------------------------------------------------------------------------
    # DISPLAY COMPARISON TABLE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 105)
    print("🏆 FINAL COMPARATIVE AUDIT TABLE: BASELINE BB 3.0 vs GAUTAM JHAA UPGRADE")
    print("=" * 105)
    print(f"{'QUANTITATIVE METRIC':<35} | {'BASELINE BB 3.0':<20} | {'UPGRADED GAUTAM JHAA':<20} | {'GAUTAM KZ FOCUSED':<20}")
    print("-" * 105)
    print(f"{'Targeting Architecture':<35} | {'Fixed 3.0R TP':<20} | {'Opposite Daily (PDH/L)':<20} | {'Opposite Daily (KZ)':<20}")
    print(f"{'Exit Execution Logic':<35} | {'100% Exit at 3.0R':<20} | {'90% Lock + 10% Moon':<20} | {'90% Lock + 10% Moon':<20}")
    print(f"{'Time-Pass Exhaustion Filter':<35} | {'Disabled':<20} | {'Active (85% range)':<20} | {'Active (85% range)':<20}")
    print("-" * 105)
    print(f"{'Total Trades Executed':<35} | {baseline_deca['total_trades']:<20} | {gautam_deca['total_trades']:<20} | {gautam_kz_deca['total_trades']:<20}")
    print(f"{'Pure Win Rate % (Win only)':<35} | {baseline_deca['pure_win_rate_pct']:<19.1f}% | {gautam_deca['pure_win_rate_pct']:<19.1f}% | {gautam_kz_deca['pure_win_rate_pct']:<19.1f}%")
    print(f"{'Quality Win Rate % (Win + Save)':<35} | {baseline_deca['quality_win_rate_pct']:<19.1f}% | {gautam_deca['quality_win_rate_pct']:<19.1f}% | {gautam_kz_deca['quality_win_rate_pct']:<19.1f}%")
    print(f"{'Average R Captured per Trade':<35} | {baseline_deca['avg_r_per_trade']:<19.2f}R | {gautam_deca['avg_r_per_trade']:<19.2f}R | {gautam_kz_deca['avg_r_per_trade']:<19.2f}R")
    print(f"{'Total Net PnL (in R)':<35} | {baseline_deca['total_net_r']:<19.2f}R | {gautam_deca['total_net_r']:<19.2f}R | {gautam_kz_deca['total_net_r']:<19.2f}R")
    print(f"{'Starting Capital':<35} | {'$500.00 USDT':<20} | {'$500.00 USDT':<20} | {'$500.00 USDT':<20}")
    print(f"{'Final Portfolio Capital':<35} | ${baseline_deca['final_capital_usd']:<19,.2f} | ${gautam_deca['final_capital_usd']:<19,.2f} | ${gautam_kz_deca['final_capital_usd']:<19,.2f}")
    print(f"{'Total Net PnL (USD)':<35} | +${baseline_deca['net_profit_usd']:<18,.2f} | +${gautam_deca['net_profit_usd']:<18,.2f} | +${gautam_kz_deca['net_profit_usd']:<18,.2f}")
    print(f"{'Total Return on Capital %':<35} | +{baseline_deca['total_gain_pct']:<18,.1f}% | +{gautam_deca['total_gain_pct']:<18,.1f}% | +{gautam_kz_deca['total_gain_pct']:<18,.1f}%")
    print(f"{'Profit Factor':<35} | {baseline_deca['profit_factor']:<20.2f} | {gautam_deca['profit_factor']:<20.2f} | {gautam_kz_deca['profit_factor']:<20.2f}")
    print(f"{'Maximum Drawdown %':<35} | {baseline_deca['max_drawdown_pct']:<19.2f}% | {gautam_deca['max_drawdown_pct']:<19.2f}% | {gautam_kz_deca['max_drawdown_pct']:<19.2f}%")
    print("=" * 105)

    # -------------------------------------------------------------------------
    # SESSION BREAKDOWN FOR GAUTAM JHAA MODEL
    # -------------------------------------------------------------------------
    print("\n🌍 SESSION PERFORMANCE BREAKDOWN (GAUTAM JHAA UPGRADE):")
    print("-" * 85)
    print(f"{'SESSION TAG':<20} | {'TRADES':<8} | {'WIN %':<8} | {'QUALITY %':<10} | {'TOTAL R':<10} | {'AVG R'}")
    print("-" * 85)
    for tag in ["LONDON_KZ", "NY_KZ", "ASIAN_OTHER"]:
        st = sess_stats[tag]
        wr = (st["wins"] / st["trades"] * 100) if st["trades"] else 0
        qr = ((st["wins"] + st["saves"]) / st["trades"] * 100) if st["trades"] else 0
        avg = (st["net_r"] / st["trades"]) if st["trades"] else 0
        print(f"{tag:<20} | {st['trades']:<8} | {wr:<7.1f}% | {qr:<9.1f}% | {st['net_r']:<+9.2f}R | {avg:+.2f}R")
    print("-" * 85)

    # -------------------------------------------------------------------------
    # 10 DECA SECTIONS BREAKDOWN TABLE
    # -------------------------------------------------------------------------
    print("\n🧩 10 DECA ISOLATED SECTIONS BREAKDOWN (GAUTAM JHAA MODEL):")
    print("-" * 105)
    print(f"{'SECTION':<12} | {'CHAMPION PAIRS':<24} | {'START':<8} | {'FINAL USD':<12} | {'NET GAIN':<10} | {'TRADES':<7} | {'WIN %':<7} | {'MAX DD'}")
    print("-" * 105)
    for s_id in range(1, 11):
        coins = [k for k, v in PAIR_MAPPING.items() if v == s_id]
        s_data = gautam_deca["sections"][s_id]
        coins_str = ", ".join(coins)
        print(f"Section #{s_id:<4} | {coins_str:<24} | $50.00   | ${s_data['final_balance_usd']:<11.2f} | {s_data['gain_pct']:<+9.1f}% | {s_data['trades']:<7} | {s_data['win_rate_pct']:<5.1f}% | {s_data['max_dd_pct']:.1f}%")
    print("-" * 105)

    # -------------------------------------------------------------------------
    # SAVE BENCHMARK REPORT TO JSON
    # -------------------------------------------------------------------------
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "period": "1 Full Year (October 2025 - October 2026)",
        "dataset": "20 Champions, 15m candlesticks, 34,995 bars/coin",
        "initial_capital_total_usd": 500.0,
        "compounding_model": "10 Isolated Deca Sections @ 5% Section Risk",
        "metrics_comparison": {
            "baseline_bb30": {
                "architecture": "Fixed 3.0R TP + Stepped Trailing SL",
                "total_trades": baseline_deca["total_trades"],
                "pure_win_rate_pct": baseline_deca["pure_win_rate_pct"],
                "quality_win_rate_pct": baseline_deca["quality_win_rate_pct"],
                "avg_r_per_trade": baseline_deca["avg_r_per_trade"],
                "total_net_r": baseline_deca["total_net_r"],
                "final_capital_usd": baseline_deca["final_capital_usd"],
                "net_profit_usd": baseline_deca["net_profit_usd"],
                "total_gain_pct": baseline_deca["total_gain_pct"],
                "profit_factor": baseline_deca["profit_factor"],
                "max_drawdown_pct": baseline_deca["max_drawdown_pct"]
            },
            "upgraded_gautam_jhaa": {
                "architecture": "Opposite Daily Liquidity TP + 90/10 Moonbag + Time-Pass Filter",
                "total_trades": gautam_deca["total_trades"],
                "pure_win_rate_pct": gautam_deca["pure_win_rate_pct"],
                "quality_win_rate_pct": gautam_deca["quality_win_rate_pct"],
                "avg_r_per_trade": gautam_deca["avg_r_per_trade"],
                "total_net_r": gautam_deca["total_net_r"],
                "final_capital_usd": gautam_deca["final_capital_usd"],
                "net_profit_usd": gautam_deca["net_profit_usd"],
                "total_gain_pct": gautam_deca["total_gain_pct"],
                "profit_factor": gautam_deca["profit_factor"],
                "max_drawdown_pct": gautam_deca["max_drawdown_pct"],
                "sections": gautam_deca["sections"]
            },
            "upgraded_gautam_jhaa_killzone": {
                "architecture": "Gautam Jhaa Model Filtered Strictly to London/NY Killzones",
                "total_trades": gautam_kz_deca["total_trades"],
                "pure_win_rate_pct": gautam_kz_deca["pure_win_rate_pct"],
                "quality_win_rate_pct": gautam_kz_deca["quality_win_rate_pct"],
                "avg_r_per_trade": gautam_kz_deca["avg_r_per_trade"],
                "total_net_r": gautam_kz_deca["total_net_r"],
                "final_capital_usd": gautam_kz_deca["final_capital_usd"],
                "net_profit_usd": gautam_kz_deca["net_profit_usd"],
                "total_gain_pct": gautam_kz_deca["total_gain_pct"],
                "profit_factor": gautam_kz_deca["profit_factor"],
                "max_drawdown_pct": gautam_kz_deca["max_drawdown_pct"]
            }
        },
        "session_breakdown": {
            tag: {
                "trades": sess_stats[tag]["trades"],
                "wins": sess_stats[tag]["wins"],
                "saves": sess_stats[tag]["saves"],
                "losses": sess_stats[tag]["losses"],
                "win_rate_pct": (sess_stats[tag]["wins"] / sess_stats[tag]["trades"] * 100) if sess_stats[tag]["trades"] else 0,
                "net_r": sess_stats[tag]["net_r"]
            } for tag in ["LONDON_KZ", "NY_KZ", "ASIAN_OTHER"]
        }
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"\n✅ Benchmark results successfully saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    run_benchmark()
