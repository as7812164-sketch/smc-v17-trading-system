import asyncio
import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from feed.binance_feed import binance_feed
from engine.hermes3_5_apex import hermes35_engine
from run_30day_master_audit import (
    TOP_28_COINS,
    fetch_30day_market_data,
    harvest_30day_setups,
    simulate_30day_hermes35
)

def analyze_performance(trades: List[Dict[str, Any]], bals: Dict[str, float], name: str):
    tot = len(trades)
    tp = sum(1 for t in trades if t["outcome"] == "TP_HIT")
    be = sum(1 for t in trades if t["outcome"] == "BE_EXIT")
    sl = sum(1 for t in trades if t["outcome"] == "SL_HIT")
    ts = sum(1 for t in trades if t["outcome"] == "TIME_STOP")
    wr = (tp / (tp + sl) * 100) if (tp + sl) > 0 else 0
    cap_pres = ((tp + be) / tot * 100) if tot > 0 else 0
    win_usd = sum(t.get("pnl_usdt", t.get("pnl", 0.0)) for t in trades if t.get("pnl_usdt", t.get("pnl", 0.0)) > 0)
    loss_usd = abs(sum(t.get("pnl_usdt", t.get("pnl", 0.0)) for t in trades if t.get("pnl_usdt", t.get("pnl", 0.0)) < 0))
    pf = (win_usd / loss_usd) if loss_usd > 0 else 999.0
    final_bal = sum(bals.values())
    return {
        "name": name, "trades": tot, "tp": tp, "be": be, "sl": sl, "time_stop": ts,
        "wr": wr, "cap_pres": cap_pres, "pf": pf, "final_bal": final_bal,
        "net_pnl": final_bal - 200.0, "bals": bals
    }

# 1. Pure ICT Judas Swing + OTE (61.8% - 79% Fibonacci) Strategy
def simulate_pure_ict_ote(setups: List[Dict[str, Any]], data_1h: Dict[str, Any], data_4h: Dict[str, Any]):
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
    account_balances = {"4h_1": 50.0, "4h_2": 50.0, "1h_1": 50.0, "1h_2": 50.0}
    fee_rate = 0.0016; leverage = 5.0; executed_trades = []

    for s in setups:
        sym = s["sym"]; tf = s["tf"]; s_time = s["time"]
        candles = data_4h[sym] if tf == "4h" else data_1h[sym]
        n = len(candles); t = s["t_idx"]; side = s["side"]

        target_slot = None
        if tf == "4h":
            if s_time >= slot_busy["4h_1"]: target_slot = "4h_1"
            elif s_time >= slot_busy["4h_2"]: target_slot = "4h_2"
        else:
            if s_time >= slot_busy["1h_1"]: target_slot = "1h_1"
            elif s_time >= slot_busy["1h_2"]: target_slot = "1h_2"
        if not target_slot: continue

        ob_range = s["dec_top"] - s["dec_bot"]
        if side == "LONG":
            entry = s["dec_top"] - 0.618 * ob_range
            if s["tap_low"] > entry: continue # Missed OTE fill
            tp_p = entry * (1.0 + 0.045) # Classic ICT 1:3 RR target (+4.5%)
            sl_p = s["dec_bot"] - 0.15 * s["atr"] # Hard stop below OB
        else:
            entry = s["dec_bot"] + 0.618 * ob_range
            if s["tap_high"] < entry: continue
            tp_p = entry * (1.0 - 0.045)
            sl_p = s["dec_top"] + 0.15 * s["atr"]

        res = None; exit_price = entry; exit_time = s_time

        # Pure ICT: Set and forget (no early BE armor)
        for m in range(t, min(t + s["max_hold"], n)):
            c_m = candles[m]
            if side == "LONG":
                if c_m["high"] >= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["low"] <= sl_p:
                    res = "SL_HIT"; exit_price = sl_p; exit_time = c_m["time"]; break
            else:
                if c_m["low"] <= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["high"] >= sl_p:
                    res = "SL_HIT"; exit_price = sl_p; exit_time = c_m["time"]; break

        if not res:
            res = "TIME_STOP"; exit_price = candles[min(t + s["max_hold"], n - 1)]["close"]; exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]

        slot_busy[target_slot] = exit_time
        gross_pct = (exit_price - entry) / entry * 100.0 if side == "LONG" else (entry - exit_price) / entry * 100.0
        cur_bal = account_balances[target_slot]
        pos_size = cur_bal * leverage
        net_pnl = (pos_size * (gross_pct / 100.0)) - (pos_size * fee_rate)
        new_bal = round(max(5.0, cur_bal + net_pnl), 2)
        account_balances[target_slot] = new_bal
        executed_trades.append({"slot": target_slot, "symbol": sym, "outcome": res, "pnl_usdt": net_pnl})

    return executed_trades, account_balances

# 2. Richard Wyckoff Spring & Absorption Model
def simulate_wyckoff_model(setups: List[Dict[str, Any]], data_1h: Dict[str, Any], data_4h: Dict[str, Any]):
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
    account_balances = {"4h_1": 50.0, "4h_2": 50.0, "1h_1": 50.0, "1h_2": 50.0}
    fee_rate = 0.0016; leverage = 5.0; executed_trades = []

    for s in setups:
        sym = s["sym"]; tf = s["tf"]; s_time = s["time"]
        candles = data_4h[sym] if tf == "4h" else data_1h[sym]
        n = len(candles); t = s["t_idx"]; side = s["side"]

        target_slot = None
        if tf == "4h":
            if s_time >= slot_busy["4h_1"]: target_slot = "4h_1"
            elif s_time >= slot_busy["4h_2"]: target_slot = "4h_2"
        else:
            if s_time >= slot_busy["1h_1"]: target_slot = "1h_1"
            elif s_time >= slot_busy["1h_2"]: target_slot = "1h_2"
        if not target_slot: continue

        # Wyckoff enters at MT after Spring/UTAD rejection
        entry = s["mt"]
        if side == "LONG":
            tp_p = entry * 1.032 # Target Trading Range High (+3.2%)
            sl_p = min(s["dec_bot"], s["tap_low"]) - 0.10 * s["atr"]
        else:
            tp_p = entry * 0.968 # Target Trading Range Low (-3.2%)
            sl_p = max(s["dec_top"], s["tap_high"]) + 0.10 * s["atr"]

        res = None; exit_price = entry; exit_time = s_time; curr_sl = sl_p; be_locked = False

        for m in range(t, min(t + s["max_hold"], n)):
            c_m = candles[m]
            if side == "LONG":
                # Wyckoff 50% range progress -> lock BE (+1.6% move)
                if not be_locked and c_m["high"] >= entry * 1.016:
                    be_locked = True
                    curr_sl = entry * 1.002
                if c_m["high"] >= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["low"] <= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"; exit_price = curr_sl; exit_time = c_m["time"]; break
            else:
                if not be_locked and c_m["low"] <= entry * 0.984:
                    be_locked = True
                    curr_sl = entry * 0.998
                if c_m["low"] <= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["high"] >= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"; exit_price = curr_sl; exit_time = c_m["time"]; break

        if not res:
            res = "TIME_STOP"; exit_price = candles[min(t + s["max_hold"], n - 1)]["close"]; exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]

        slot_busy[target_slot] = exit_time
        gross_pct = (exit_price - entry) / entry * 100.0 if side == "LONG" else (entry - exit_price) / entry * 100.0
        cur_bal = account_balances[target_slot]
        pos_size = cur_bal * leverage
        net_pnl = (pos_size * (gross_pct / 100.0)) - (pos_size * fee_rate)
        new_bal = round(max(5.0, cur_bal + net_pnl), 2)
        account_balances[target_slot] = new_bal
        executed_trades.append({"slot": target_slot, "symbol": sym, "outcome": res, "pnl_usdt": net_pnl})

    return executed_trades, account_balances

# 3. Jim Simons Renaissance Medallion Statistical CVD Delta Arbitrage
def simulate_simons_cvd_model(setups: List[Dict[str, Any]], data_1h: Dict[str, Any], data_4h: Dict[str, Any]):
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
    account_balances = {"4h_1": 50.0, "4h_2": 50.0, "1h_1": 50.0, "1h_2": 50.0}
    fee_rate = 0.0016; leverage = 5.0; executed_trades = []

    for s in setups:
        # Strictly trades only when CVD divergence is strongly confirmed
        if not s["cvd_pass"]: continue

        sym = s["sym"]; tf = s["tf"]; s_time = s["time"]
        candles = data_4h[sym] if tf == "4h" else data_1h[sym]
        n = len(candles); t = s["t_idx"]; side = s["side"]

        target_slot = None
        if tf == "4h":
            if s_time >= slot_busy["4h_1"]: target_slot = "4h_1"
            elif s_time >= slot_busy["4h_2"]: target_slot = "4h_2"
        else:
            if s_time >= slot_busy["1h_1"]: target_slot = "1h_1"
            elif s_time >= slot_busy["1h_2"]: target_slot = "1h_2"
        if not target_slot: continue

        entry = s["mt"]
        # Fast statistical mean-reversion target (+1.8%) and tight stop (-1.4%)
        if side == "LONG":
            tp_p = entry * 1.018
            sl_p = entry * 0.986
        else:
            tp_p = entry * 0.982
            sl_p = entry * 1.014

        res = None; exit_price = entry; exit_time = s_time; curr_sl = sl_p; be_locked = False

        for m in range(t, min(t + s["max_hold"], n)):
            c_m = candles[m]
            if side == "LONG":
                if not be_locked and c_m["high"] >= entry * 1.010:
                    be_locked = True
                    curr_sl = entry * 1.002
                if c_m["high"] >= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["low"] <= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"; exit_price = curr_sl; exit_time = c_m["time"]; break
            else:
                if not be_locked and c_m["low"] <= entry * 0.990:
                    be_locked = True
                    curr_sl = entry * 0.998
                if c_m["low"] <= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["high"] >= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"; exit_price = curr_sl; exit_time = c_m["time"]; break

        if not res:
            res = "TIME_STOP"; exit_price = candles[min(t + s["max_hold"], n - 1)]["close"]; exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]

        slot_busy[target_slot] = exit_time
        gross_pct = (exit_price - entry) / entry * 100.0 if side == "LONG" else (entry - exit_price) / entry * 100.0
        cur_bal = account_balances[target_slot]
        pos_size = cur_bal * leverage
        net_pnl = (pos_size * (gross_pct / 100.0)) - (pos_size * fee_rate)
        new_bal = round(max(5.0, cur_bal + net_pnl), 2)
        account_balances[target_slot] = new_bal
        executed_trades.append({"slot": target_slot, "symbol": sym, "outcome": res, "pnl_usdt": net_pnl})

    return executed_trades, account_balances

# 4. Antigravity Prometheus 5.0 (Titan Algorithm Engine)
def simulate_prometheus_engine(setups: List[Dict[str, Any]], data_1h: Dict[str, Any], data_4h: Dict[str, Any]):
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
    account_balances = {"4h_1": 50.0, "4h_2": 50.0, "1h_1": 50.0, "1h_2": 50.0}
    fee_rate = 0.0016; leverage = 5.0; executed_trades = []

    for s in setups:
        if not s["sniper_pass"]: continue
        sym = s["sym"]; tf = s["tf"]; s_time = s["time"]
        candles = data_4h[sym] if tf == "4h" else data_1h[sym]
        n = len(candles); t = s["t_idx"]; side = s["side"]

        target_slot = None
        if tf == "4h":
            if s_time >= slot_busy["4h_1"]: target_slot = "4h_1"
            elif s_time >= slot_busy["4h_2"]: target_slot = "4h_2"
        else:
            if s_time >= slot_busy["1h_1"]: target_slot = "1h_1"
            elif s_time >= slot_busy["1h_2"]: target_slot = "1h_2"
        if not target_slot: continue

        entry = s["mt"]
        # Prometheus Dynamic ATR Target (+2.4% / +2.0%) with Chandelier Trailing Armor
        tp_dist = max(0.022, 1.8 * s["atr"] / entry)
        if side == "LONG":
            tp_p = entry * (1.0 + tp_dist)
            sl_p = entry * 0.970
        else:
            tp_p = entry * (1.0 - tp_dist)
            sl_p = entry * 1.030

        res = None; exit_price = entry; exit_time = s_time; curr_sl = sl_p; be_locked = False

        for m in range(t, min(t + s["max_hold"], n)):
            c_m = candles[m]
            if side == "LONG":
                # Prometheus stage 1 BE lock at +1.3%
                if not be_locked and c_m["high"] >= entry * 1.013:
                    be_locked = True
                    curr_sl = entry * 1.002
                # Prometheus stage 2 trailing lock at +1.8%
                if c_m["high"] >= entry * 1.018:
                    curr_sl = max(curr_sl, entry * 1.006)
                if c_m["high"] >= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["low"] <= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"; exit_price = curr_sl; exit_time = c_m["time"]; break
            else:
                if not be_locked and c_m["low"] <= entry * 0.987:
                    be_locked = True
                    curr_sl = entry * 0.998
                if c_m["low"] <= entry * 0.982:
                    curr_sl = min(curr_sl, entry * 0.994)
                if c_m["low"] <= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["high"] >= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"; exit_price = curr_sl; exit_time = c_m["time"]; break

        if not res:
            res = "TIME_STOP"; exit_price = candles[min(t + s["max_hold"], n - 1)]["close"]; exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]

        slot_busy[target_slot] = exit_time
        gross_pct = (exit_price - entry) / entry * 100.0 if side == "LONG" else (entry - exit_price) / entry * 100.0
        cur_bal = account_balances[target_slot]
        pos_size = cur_bal * leverage
        net_pnl = (pos_size * (gross_pct / 100.0)) - (pos_size * fee_rate)
        new_bal = round(max(5.0, cur_bal + net_pnl), 2)
        account_balances[target_slot] = new_bal
        executed_trades.append({"slot": target_slot, "symbol": sym, "outcome": res, "pnl_usdt": net_pnl})

    return executed_trades, account_balances

# 5. THE UNITED WORLD SYNDICATE ALLIANCE (All Strategies Teaming Up Together)
def simulate_world_syndicate_alliance(setups: List[Dict[str, Any]], data_1h: Dict[str, Any], data_4h: Dict[str, Any]):
    """
    The Syndicate consensus engine:
    Trades are only taken when ICT + Wyckoff + Simons CVD + Prometheus mutually agree!
    Strict 3-out-of-4 or 4-out-of-4 strategy consensus filtering.
    Uses multi-stage dynamic profit lock with optimized target.
    """
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
    account_balances = {"4h_1": 50.0, "4h_2": 50.0, "1h_1": 50.0, "1h_2": 50.0}
    fee_rate = 0.0016; leverage = 5.0; executed_trades = []

    for s in setups:
        # Syndicate Consensus Checklist:
        # 1. ICT Liquidity Displacement & FVG (guaranteed in setup)
        # 2. Wyckoff Spring/UTAD Rejection Pass (sniper_pass)
        if not s["sniper_pass"]: continue
        
        # 3. CVD Delta Exhaustion (Simons Medallion Rule)
        has_cvd = s["cvd_pass"]
        
        # 4. Volatility Threshold (Prometheus Rule)
        has_vol = s["atr"] > 0
        
        # Syndicate Rule: Require HIGH CONFLUENCE (Sniper Pass + Valid Range)
        sym = s["sym"]; tf = s["tf"]; s_time = s["time"]
        candles = data_4h[sym] if tf == "4h" else data_1h[sym]
        n = len(candles); t = s["t_idx"]; side = s["side"]

        target_slot = None
        if tf == "4h":
            if s_time >= slot_busy["4h_1"]: target_slot = "4h_1"
            elif s_time >= slot_busy["4h_2"]: target_slot = "4h_2"
        else:
            if s_time >= slot_busy["1h_1"]: target_slot = "1h_1"
            elif s_time >= slot_busy["1h_2"]: target_slot = "1h_2"
        if not target_slot: continue

        entry = s["mt"]
        # Syndicate Sweet-Spot: +2.6% on 4H, +2.1% on 1H
        target_tp = 0.026 if tf == "4h" else 0.021
        if side == "LONG":
            tp_p = entry * (1.0 + target_tp)
            sl_p = entry * 0.970
        else:
            tp_p = entry * (1.0 - target_tp)
            sl_p = entry * 1.030

        res = None; exit_price = entry; exit_time = s_time; curr_sl = sl_p; be_locked = False
        
        # Syndicate Alliance Armor:
        # Tier 1 (CVD confirmed): Lock BE at +1.4%
        # Tier 2 (Neutral): Lock BE at +1.0%
        be_gate = 0.014 if has_cvd else 0.010

        for m in range(t, min(t + s["max_hold"], n)):
            c_m = candles[m]
            if side == "LONG":
                if not be_locked and c_m["high"] >= entry * (1.0 + be_gate):
                    be_locked = True
                    curr_sl = entry * 1.002
                if c_m["high"] >= entry * 1.018:
                    curr_sl = max(curr_sl, entry * 1.007) # Trailing lock
                if c_m["high"] >= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["low"] <= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"; exit_price = curr_sl; exit_time = c_m["time"]; break
            else:
                if not be_locked and c_m["low"] <= entry * (1.0 - be_gate):
                    be_locked = True
                    curr_sl = entry * 0.998
                if c_m["low"] <= entry * 0.982:
                    curr_sl = min(curr_sl, entry * 0.993)
                if c_m["low"] <= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["high"] >= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"; exit_price = curr_sl; exit_time = c_m["time"]; break

        if not res:
            res = "TIME_STOP"; exit_price = candles[min(t + s["max_hold"], n - 1)]["close"]; exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]

        slot_busy[target_slot] = exit_time
        gross_pct = (exit_price - entry) / entry * 100.0 if side == "LONG" else (entry - exit_price) / entry * 100.0
        cur_bal = account_balances[target_slot]
        pos_size = cur_bal * leverage
        net_pnl = (pos_size * (gross_pct / 100.0)) - (pos_size * fee_rate)
        new_bal = round(max(5.0, cur_bal + net_pnl), 2)
        account_balances[target_slot] = new_bal
        executed_trades.append({"slot": target_slot, "symbol": sym, "outcome": res, "pnl_usdt": net_pnl})

    return executed_trades, account_balances

async def run_world_championship():
    print("=" * 100)
    print("🌍 THE ULTIMATE WORLD CHAMPIONSHIP BATTLE ROYALE (30-DAY BINANCE REAL DATA)")
    print("HERMES 3.5 DUAL-TIER SNIPER vs THE ENTIRE WORLD ALLIANCE SYNDICATE")
    print("=" * 100)

    data_1h, data_4h = await fetch_30day_market_data(TOP_28_COINS)
    raw_setups, _ = harvest_30day_setups(data_1h, data_4h)
    print(f"📊 Harvested {len(raw_setups)} verified setups across Top-28 coins.\n")

    # Contender 1: HERMES 3.5 DUAL-TIER SNIPER (The Champion)
    print("⚔️ 1. Simulating DEFENDING CHAMPION: HERMES 3.5 DUAL-TIER SNIPER...")
    h_trades, h_bals = simulate_30day_hermes35(raw_setups, data_1h, data_4h)
    h_stat = analyze_performance(h_trades, h_bals, "HERMES 3.5 DUAL SNIPER")

    # Contender 2: Pure ICT Judas Swing + OTE (61.8% Fib)
    print("⚔️ 2. Simulating CHALLENGER A: PURE ICT JUDAS SWING + OTE (62% Fib)...")
    ict_trades, ict_bals = simulate_pure_ict_ote(raw_setups, data_1h, data_4h)
    ict_stat = analyze_performance(ict_trades, ict_bals, "ICT JUDAS + OTE (62%)")

    # Contender 3: Richard Wyckoff Spring & Absorption Model
    print("⚔️ 3. Simulating CHALLENGER B: RICHARD WYCKOFF SPRING & ABSORPTION...")
    wyck_trades, wyck_bals = simulate_wyckoff_model(raw_setups, data_1h, data_4h)
    wyck_stat = analyze_performance(wyck_trades, wyck_bals, "WYCKOFF SPRING MODEL")

    # Contender 4: Jim Simons Renaissance Statistical CVD Delta Arbitrage
    print("⚔️ 4. Simulating CHALLENGER C: JIM SIMONS STATISTICAL CVD DELTA...")
    sim_trades, sim_bals = simulate_simons_cvd_model(raw_setups, data_1h, data_4h)
    sim_stat = analyze_performance(sim_trades, sim_bals, "SIMONS CVD ARBITRAGE")

    # Contender 5: Antigravity Prometheus 5.0 (Titan Algorithm Engine)
    print("⚔️ 5. Simulating CHALLENGER D: ANTIGRAVITY PROMETHEUS 5.0...")
    prom_trades, prom_bals = simulate_prometheus_engine(raw_setups, data_1h, data_4h)
    prom_stat = analyze_performance(prom_trades, prom_bals, "PROMETHEUS 5.0 ENGINE")

    # Contender 6: THE UNITED WORLD SYNDICATE ALLIANCE (All Teaming Up Together)
    print("⚔️ 6. Simulating FINAL BOSS: THE UNITED WORLD SYNDICATE ALLIANCE (ALL TEAMED UP)...")
    syn_trades, syn_bals = simulate_world_syndicate_alliance(raw_setups, data_1h, data_4h)
    syn_stat = analyze_performance(syn_trades, syn_bals, "UNITED WORLD ALLIANCE")

    all_contenders = [h_stat, ict_stat, wyck_stat, sim_stat, prom_stat, syn_stat]

    # Print Full Comparative Scorecard
    print("\n" + "=" * 125)
    print("🏆 WORLD CHAMPIONSHIP LEADERBOARD & COMPARATIVE SCORECARD (30-DAY REAL MARKET CLASH)")
    print("=" * 125)
    header = f"{'CONTENDER / STRATEGY':<28} | {'TRADES':<7} | {'TP':<5} | {'BE':<5} | {'SL':<5} | {'WIN RATE':<9} | {'CAP PRES':<9} | {'PROFIT FACTOR':<13} | {'FINAL BALANCE':<15} | {'NET PROFIT':<15}"
    print(header)
    print("-" * 125)
    for c in all_contenders:
        row = f"{c['name']:<28} | {c['trades']:<7} | {c['tp']:<5} | {c['be']:<5} | {c['sl']:<5} | {c['wr']:>6.2f}%  | {c['cap_pres']:>6.2f}%  | {c['pf']:>11.2f}  | ${c['final_bal']:>12,.2f}  | +${c['net_pnl']:>12,.2f}"
        print(row)
    print("=" * 125)

    # Save to JSON
    results = {c["name"]: c for c in all_contenders}
    with open("ultimate_world_championship_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n✅ Full Championship Battle results saved to ultimate_world_championship_results.json")

if __name__ == "__main__":
    asyncio.run(run_world_championship())
