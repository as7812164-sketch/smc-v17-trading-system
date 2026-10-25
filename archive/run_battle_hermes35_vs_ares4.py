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

def simulate_ares4_engine(setups: List[Dict[str, Any]], data_1h: Dict[str, Any], data_4h: Dict[str, Any]):
    """Simulates ARES QUANT-TITAN 4.0 on the 4 Quad tracks."""
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
    account_balances = {"4h_1": 50.0, "4h_2": 50.0, "1h_1": 50.0, "1h_2": 50.0}
    fee_rate = 0.0016
    leverage = 5.0
    executed_trades = []

    for s in setups:
        if not s["sniper_pass"]: continue
        sym = s["sym"]
        tf = s["tf"]
        s_time = s["time"]
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

        # ARES 4.0: 61.8% OTE Deep Entry
        ob_range = s["dec_top"] - s["dec_bot"]
        if side == "LONG":
            entry = s["dec_top"] - 0.618 * ob_range
            # Check if tap reached 61.8% OTE
            if s["tap_low"] > entry:
                entry = s["mt"] # Fallback to MT if OTE was not reached
            tp_dist = max(0.028, (2.0 * s["atr"] / entry))
            tp_p = entry * (1.0 + tp_dist)
            sl_p = max(entry * 0.962, s["dec_bot"] - 0.15 * s["atr"])
        else:
            entry = s["dec_bot"] + 0.618 * ob_range
            if s["tap_high"] < entry:
                entry = s["mt"]
            tp_dist = max(0.028, (2.0 * s["atr"] / entry))
            tp_p = entry * (1.0 - tp_dist)
            sl_p = min(entry * 1.038, s["dec_top"] + 0.15 * s["atr"])

        res = None; exit_price = entry; exit_time = s_time; curr_sl = sl_p; be_locked = False

        for m in range(t, min(t + s["max_hold"], n)):
            c_m = candles[m]
            if side == "LONG":
                # Chandelier Trail: Once up +1.2%, trail behind 2-bar low
                if c_m["high"] >= entry * 1.012:
                    be_locked = True
                    trail_p = min(candles[m-1]["low"], c_m["low"]) if m > 0 else entry * 1.002
                    curr_sl = max(curr_sl, max(entry * 1.002, trail_p))
                if c_m["high"] >= tp_p:
                    res = "TP_HIT"; exit_price = tp_p; exit_time = c_m["time"]; break
                elif c_m["low"] <= curr_sl:
                    res = "BE_EXIT" if be_locked else "SL_HIT"; exit_price = curr_sl; exit_time = c_m["time"]; break
            else:
                if c_m["low"] <= entry * 0.988:
                    be_locked = True
                    trail_p = max(candles[m-1]["high"], c_m["high"]) if m > 0 else entry * 0.998
                    curr_sl = min(curr_sl, min(entry * 0.998, trail_p))
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
        fee = pos_size * fee_rate
        net_pnl = (pos_size * (gross_pct / 100.0)) - fee
        new_bal = round(max(5.0, cur_bal + net_pnl), 2)
        account_balances[target_slot] = new_bal

        executed_trades.append({
            "slot": target_slot, "symbol": sym, "outcome": res,
            "pnl": net_pnl, "pnl_usdt": net_pnl, "account_balance": new_bal
        })

    return executed_trades, account_balances

async def main():
    print("🚀 Fetching 30-day real market data across Top-28 coins from Binance Futures...")
    data_1h, data_4h = await fetch_30day_market_data(TOP_28_COINS)
    raw_setups, _ = harvest_30day_setups(data_1h, data_4h)
    print(f"📊 Harvested {len(raw_setups)} verified setups.")

    print("\n⚔️ Executing Contender 1: HERMES 3.5 DUAL-TIER SNIPER...")
    h_trades, h_bals = simulate_30day_hermes35(raw_setups, data_1h, data_4h)

    print("⚔️ Executing Contender 2: ARES QUANT-TITAN 4.0...")
    a_trades, a_bals = simulate_ares4_engine(raw_setups, data_1h, data_4h)

    def analyze(trades, bals):
        tot = len(trades)
        tp = sum(1 for t in trades if t["outcome"] == "TP_HIT")
        be = sum(1 for t in trades if t["outcome"] == "BE_EXIT")
        sl = sum(1 for t in trades if t["outcome"] == "SL_HIT")
        wr = (tp / (tp + sl) * 100) if (tp + sl) > 0 else 0
        cap_pres = ((tp + be) / tot * 100) if tot > 0 else 0
        win_usd = sum(t.get("pnl_usdt", t.get("pnl", 0.0)) for t in trades if t.get("pnl_usdt", t.get("pnl", 0.0)) > 0)
        loss_usd = abs(sum(t.get("pnl_usdt", t.get("pnl", 0.0)) for t in trades if t.get("pnl_usdt", t.get("pnl", 0.0)) < 0))
        pf = (win_usd / loss_usd) if loss_usd > 0 else 999.0
        final_bal = sum(bals.values())
        return {
            "trades": tot, "tp": tp, "be": be, "sl": sl, "wr": wr,
            "cap_pres": cap_pres, "pf": pf, "final_bal": final_bal,
            "net_pnl": final_bal - 200.0, "bals": bals
        }

    h_stat = analyze(h_trades, h_bals)
    a_stat = analyze(a_trades, a_bals)

    print("\n" + "=" * 95)
    print("🏆 FINAL GLADIATOR DUEL RESULTS (30-DAY CLASH)")
    print("=" * 95)
    print(f"{'METRIC':<32} | {'HERMES 3.5 DUAL SNIPER':<28} | {'ARES QUANT-TITAN 4.0':<28}")
    print("-" * 95)
    print(f"{'Total Trades Executed':<32} | {h_stat['trades']:<28} | {a_stat['trades']:<28}")
    print(f"{'Take Profit Hits (TP)':<32} | {h_stat['tp']} ({h_stat['tp']/h_stat['trades']*100:.1f}%){'':<20} | {a_stat['tp']} ({a_stat['tp']/a_stat['trades']*100:.1f}%)")
    print(f"{'Breakeven Exits (BE)':<32} | {h_stat['be']} ({h_stat['be']/h_stat['trades']*100:.1f}%){'':<20} | {a_stat['be']} ({a_stat['be']/a_stat['trades']*100:.1f}%)")
    print(f"{'Stop Loss Hits (SL)':<32} | {h_stat['sl']} ({h_stat['sl']/h_stat['trades']*100:.1f}%){'':<20} | {a_stat['sl']} ({a_stat['sl']/a_stat['trades']*100:.1f}%)")
    print(f"{'Decisive Win Rate (TP vs SL)':<32} | {h_stat['wr']:.2f}%{'':<23} | {a_stat['wr']:.2f}%")
    print(f"{'Capital Preservation Rate':<32} | {h_stat['cap_pres']:.2f}%{'':<22} | {a_stat['cap_pres']:.2f}%")
    print(f"{'Initial Combined Capital':<32} | $200.00{'':<23} | $200.00")
    print(f"{'Final Combined Balance':<32} | ${h_stat['final_bal']:,.2f}{'':<19} | ${a_stat['final_bal']:,.2f}")
    print(f"{'Net Realized Profit':<32} | +${h_stat['net_pnl']:,.2f} USDT{'':<14} | +${a_stat['net_pnl']:,.2f} USDT")
    print(f"{'Profit Factor':<32} | {h_stat['pf']:.2f}{'':<24} | {a_stat['pf']:.2f}")
    print("=" * 95)

    with open("gladiator_duel_30day_results.json", "w") as f:
        json.dump({"hermes35": h_stat, "ares4": a_stat}, f, indent=2)
    print("✅ Results saved to gladiator_duel_30day_results.json")

if __name__ == "__main__":
    asyncio.run(main())
