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
    harvest_30day_setups
)

IST = timezone(timedelta(hours=5, minutes=30))

def simulate_engine(setups: List[Dict[str, Any]], data_1h: Dict[str, Any], data_4h: Dict[str, Any], routing_mode: str):
    """
    Simulates Hermes 3.5 Dual-Tier Sniper with specified routing mode:
    'waterfall': Baseline (Primary VIP + Secondary Overflow)
    'round_robin': Even Load Balancing between Alpha and Beta
    'coin_buckets': Dedicated 7-Coin Buckets per Account
    """
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
    account_balances = {"4h_1": 50.0, "4h_2": 50.0, "1h_1": 50.0, "1h_2": 50.0}
    fee_rate = 0.0016
    leverage = 5.0
    
    turn_4h = "4h_1"
    turn_1h = "1h_1"
    
    # 7-coin buckets for Model 3
    bucket_map = {}
    for sym in ["DOGEUSDT", "ALGOUSDT", "AVAXUSDT", "NEARUSDT", "ADAUSDT", "TIAUSDT", "ETCUSDT"]:
        bucket_map[sym] = "4h_1" # Section A
    for sym in ["SUIUSDT", "APTUSDT", "FILUSDT", "ICPUSDT", "RENDERUSDT", "RUNEUSDT", "OPUSDT"]:
        bucket_map[sym] = "4h_2" # Section B
    for sym in ["UNIUSDT", "AAVEUSDT", "MKRUSDT", "LDOUSDT", "FETUSDT", "THETAUSDT", "PYTHUSDT"]:
        bucket_map[sym] = "1h_1" # Section C
    for sym in ["GALAUSDT", "SANDUSDT", "AXSUSDT", "MANAUSDT", "ORDIUSDT", "SHIBUSDT"]:
        bucket_map[sym] = "1h_2" # Section D
        
    trades_executed = []
    
    for s in setups:
        if not s["sniper_pass"]:
            continue
            
        sym = s["sym"]
        tf = s["tf"]
        s_time = s["time"]
        candles = data_4h[sym] if tf == "4h" else data_1h[sym]
        n = len(candles)
        t = s["t_idx"]
        side = s["side"]
        
        target_slot = None
        
        if routing_mode == "waterfall":
            if tf == "4h":
                if s_time >= slot_busy["4h_1"]: target_slot = "4h_1"
                elif s_time >= slot_busy["4h_2"]: target_slot = "4h_2"
            else:
                if s_time >= slot_busy["1h_1"]: target_slot = "1h_1"
                elif s_time >= slot_busy["1h_2"]: target_slot = "1h_2"
                
        elif routing_mode == "round_robin":
            if tf == "4h":
                pref = turn_4h
                other = "4h_2" if pref == "4h_1" else "4h_1"
                if s_time >= slot_busy[pref]:
                    target_slot = pref
                    turn_4h = other
                elif s_time >= slot_busy[other]:
                    target_slot = other
            else: # 1h
                pref = turn_1h
                other = "1h_2" if pref == "1h_1" else "1h_1"
                if s_time >= slot_busy[pref]:
                    target_slot = pref
                    turn_1h = other
                elif s_time >= slot_busy[other]:
                    target_slot = other
                    
        elif routing_mode == "coin_buckets":
            assigned = bucket_map.get(sym)
            if not assigned:
                continue
            if assigned.startswith("4h") and tf != "4h":
                continue
            if assigned.startswith("1h") and tf != "1h":
                continue
            if s_time >= slot_busy[assigned]:
                target_slot = assigned
                
        if not target_slot:
            continue
            
        mt = s["mt"]
        if side == "LONG":
            entry = mt if s["tap_low"] <= mt else (s["dec_top"] + mt) / 2.0
            tp_p = entry * (1.0 + s["std_tp_pct"])
            struct_sl = min(s["dec_bot"], s["tap_low"]) - 0.20 * s["atr"]
            hard_sl_p = min(struct_sl, entry * (1.0 - s["hard_sl_pct"]))
            hard_sl_p = max(hard_sl_p, entry * 0.962)
            soft_sl_p = (entry + hard_sl_p) / 2.0
        else:
            entry = mt if s["tap_high"] >= mt else (s["dec_bot"] + mt) / 2.0
            tp_p = entry * (1.0 - s["std_tp_pct"])
            struct_sl = max(s["dec_top"], s["tap_high"]) + 0.20 * s["atr"]
            hard_sl_p = max(struct_sl, entry * (1.0 + s["hard_sl_pct"]))
            hard_sl_p = min(hard_sl_p, entry * 1.038)
            soft_sl_p = (entry + hard_sl_p) / 2.0
            
        res = None; exit_price = entry; exit_time = s_time; curr_sl = soft_sl_p; be_locked = False
        be_threshold = 0.016 if s["cvd_pass"] else 0.010
        
        for m in range(t, min(t + s["max_hold"], n)):
            c_m = candles[m]
            if side == "LONG":
                if not be_locked and c_m["high"] >= entry * (1.0 + be_threshold):
                    be_locked = True
                    curr_sl = entry * 1.002
                if c_m["high"] >= entry * 1.020:
                    curr_sl = max(curr_sl, entry * 1.008)
                if c_m["high"] >= tp_p:
                    res = "TP_HIT"
                    exit_price = tp_p
                    exit_time = c_m["time"]
                    break
                elif c_m["low"] <= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"
                    exit_price = curr_sl
                    exit_time = c_m["time"]
                    break
            else: # SHORT
                if not be_locked and c_m["low"] <= entry * (1.0 - be_threshold):
                    be_locked = True
                    curr_sl = entry * 0.998
                if c_m["low"] <= entry * 0.980:
                    curr_sl = min(curr_sl, entry * 0.992)
                if c_m["low"] <= tp_p:
                    res = "TP_HIT"
                    exit_price = tp_p
                    exit_time = c_m["time"]
                    break
                elif c_m["high"] >= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"
                    exit_price = curr_sl
                    exit_time = c_m["time"]
                    break
                    
        if not res:
            res = "TIME_STOP"
            exit_c = candles[min(t + s["max_hold"], n - 1)]
            exit_price = exit_c["close"]
            exit_time = exit_c["time"]
            
        slot_busy[target_slot] = exit_time
        
        gross_pnl_pct = (exit_price - entry) / entry * 100.0 if side == "LONG" else (entry - exit_price) / entry * 100.0
        cur_bal = account_balances[target_slot]
        pos_size = cur_bal * leverage
        fee = pos_size * fee_rate
        net_pnl = (pos_size * (gross_pnl_pct / 100.0)) - fee
        new_bal = round(max(5.0, cur_bal + net_pnl), 2)
        account_balances[target_slot] = new_bal
        
        trades_executed.append({
            "slot": target_slot,
            "symbol": sym,
            "outcome": res,
            "pnl": net_pnl,
            "new_bal": new_bal
        })
        
    return account_balances, trades_executed

async def main():
    print("🚀 Running 3-Model Compounding Load Balancing Simulation on 30-Day Market Data...")
    data_1h, data_4h = await fetch_30day_market_data(TOP_28_COINS)
    raw_setups, _ = harvest_30day_setups(data_1h, data_4h)
    print(f"📊 Harvested {len(raw_setups)} raw setups across 28 coins.")
    
    models = ["waterfall", "round_robin", "coin_buckets"]
    results = {}
    
    for m in models:
        bals, trs = simulate_engine(raw_setups, data_1h, data_4h, m)
        results[m] = {"bals": bals, "trades": trs}
        
    print("\n" + "="*80)
    print("🏆 FINAL COMPARISON RESULTS (30-DAY COMPASSION)")
    print("="*80)
    
    for m in models:
        r = results[m]
        trs = r["trades"]
        bals = r["bals"]
        total_pnl = sum(bals.values()) - 200.0
        total_trades = len(trs)
        tps = sum(1 for t in trs if t["outcome"] == "TP_HIT")
        bes = sum(1 for t in trs if t["outcome"] == "BE_EXIT")
        sls = sum(1 for t in trs if t["outcome"] == "SL_HIT")
        wr = (tps / (tps + sls) * 100) if (tps + sls) > 0 else 0
        cap_pres = ((tps + bes) / total_trades * 100) if total_trades > 0 else 0
        
        print(f"\n📌 MODEL: {m.upper()}")
        print(f"   Total Trades: {total_trades} | TP: {tps} | BE: {bes} | SL: {sls}")
        print(f"   Decisive Win Rate: {wr:.2f}% | Capital Preservation: {cap_pres:.2f}%")
        print(f"   Net Realized Profit: +${total_pnl:,.2f} USDT (Combined Balance: ${sum(bals.values()):,.2f})")
        print("   --- Breakdown per Account ($50 Start) ---")
        for s in ["4h_1", "4h_2", "1h_1", "1h_2"]:
            s_trades = [t for t in trs if t["slot"] == s]
            s_tp = sum(1 for t in s_trades if t["outcome"] == "TP_HIT")
            s_sl = sum(1 for t in s_trades if t["outcome"] == "SL_HIT")
            s_wr = (s_tp / (s_tp + s_sl) * 100) if (s_tp + s_sl) > 0 else 0
            print(f"     * Section {s}: Trades={len(s_trades):3d} | WR={s_wr:5.1f}% | Final Balance = ${bals[s]:10,.2f}")
            
    # Save comparison to JSON
    out_file = "load_balancing_3models_comparison.json"
    with open(out_file, "w") as f:
        json.dump({
            m: {
                "final_balances": results[m]["bals"],
                "total_trades": len(results[m]["trades"]),
                "net_profit": sum(results[m]["bals"].values()) - 200.0
            } for m in models
        }, f, indent=2)
    print(f"\n✅ Saved comparison to {out_file}")

if __name__ == "__main__":
    asyncio.run(main())
