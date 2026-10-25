import asyncio
import os
import sys
import json
import math
from datetime import datetime, timezone, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from feed.binance_feed import binance_feed
from engine.hermes3_5_apex import TOP_45_CHAMPIONS, hermes35_engine

IST = timezone(timedelta(hours=5, minutes=30))

async def fetch_5day_market_data(symbols):
    print(f"📥 Fetching last 5 days of live market klines across {len(symbols)} coins from Binance Futures...")
    data_1h = {}
    data_4h = {}
    
    # Also fetch BTC for macro sentry
    all_syms = list(set(symbols + ["BTCUSDT"]))
    
    for sym in all_syms:
        try:
            # 5 days = 120 hours. Fetch 140 to be safe
            k1 = await binance_feed.fetch_klines(sym, interval="1h", limit=140)
            if k1 and len(k1) >= 40:
                data_1h[sym] = k1
        except Exception:
            pass
            
        try:
            # 5 days = 30 4h candles. Fetch 50 to compute displacement
            k4 = await binance_feed.fetch_klines(sym, interval="4h", limit=60)
            if k4 and len(k4) >= 20:
                data_4h[sym] = k4
        except Exception:
            pass
            
    print(f"✅ Successfully fetched data for {len(data_1h)} coins (1h) and {len(data_4h)} coins (4h)")
    return data_1h, data_4h

def harvest_5day_setups(data_1h, data_4h):
    raw_setups = []
    
    btc_4h = data_4h.get("BTCUSDT", [])
    btc_map_4h = {c["time"]: c for c in btc_4h}
    
    # 5-day window start timestamp (approx 5 days ago from latest candle)
    latest_time = max(c["time"] for c in btc_4h) if btc_4h else 0
    five_days_ago = latest_time - (5 * 24 * 3600 * 1000)
    
    for tf, dataset in [("4h", data_4h), ("1h", data_1h)]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        max_tap_window = 28
        max_hold = 24 if tf == "4h" else 30
        
        for sym, candles in dataset.items():
            if sym == "BTCUSDT":
                continue
            n = len(candles)
            if n < 25:
                continue
                
            atr = [0.0] * n
            for k in range(1, n):
                tr = max(candles[k]["high"] - candles[k]["low"],
                         abs(candles[k]["high"] - candles[k-1]["close"]),
                         abs(candles[k]["low"] - candles[k-1]["close"]))
                atr[k] = tr if k < 14 else (atr[k-1] * 13 + tr) / 14
                
            for i in range(15, n - 2):
                # LONG SETUPS
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-12):i+1]):
                    sub_w = candles[i:min(i+14, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 1:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.045: # 4.5%+ impulse
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1; max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.25 <= fib <= 0.75 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        if tap_c["time"] < five_days_ago:
                                            continue # Only setups in last 5 days
                                        if tap_c["low"] <= dec_top * 1.0005:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean = btc_dump < 0.020
                                            
                                            if btc_clean and swept and w_ratio >= 0.15 and tap_c["close"] >= mt:
                                                # Check 15m / Micro-Sniper gate
                                                sniper_pass, sniper_reason = hermes35_engine.evaluate_15m_micro_sniper_gate(tap_c, "LONG")
                                                tier_info = hermes35_engine.classify_dual_tier_setup(candles, t, "LONG")
                                                cvd_pass = tier_info.get("cvd_confirmed", False)
                                                
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold,
                                                    "sniper_pass": sniper_pass, "cvd_pass": cvd_pass,
                                                    "sniper_reason": sniper_reason
                                                })
                                                break
                
                # SHORT SETUPS
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-12):i+1]):
                    sub_w = candles[i:min(i+14, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 1:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.045: # 4.5%+ impulse
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1; max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.25 <= fib <= 0.75 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        if tap_c["time"] < five_days_ago:
                                            continue
                                        if tap_c["high"] >= dec_bot * 0.9995:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean_short = btc_pump < 0.020
                                            
                                            if btc_clean_short and swept and w_ratio >= 0.15 and tap_c["close"] <= mt:
                                                sniper_pass, sniper_reason = hermes35_engine.evaluate_15m_micro_sniper_gate(tap_c, "SHORT")
                                                tier_info = hermes35_engine.classify_dual_tier_setup(candles, t, "SHORT")
                                                cvd_pass = tier_info.get("cvd_confirmed", False)
                                                
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold,
                                                    "sniper_pass": sniper_pass, "cvd_pass": cvd_pass,
                                                    "sniper_reason": sniper_reason
                                                })
                                                break
                                                
    raw_setups.sort(key=lambda x: x["time"])
    return raw_setups, five_days_ago

def simulate_5day_engine(model_name, setups, data_1h, data_4h):
    slot_busy = {"4h_1": 0, "4h_2": 0, "1h_1": 0, "1h_2": 0}
    executed_trades = []
    balance = 50.0
    vault = 0.0
    peak = 50.0
    max_dd = 0.0
    fee_rate = 0.0016
    
    for s in setups:
        # Filtering per model
        if model_name == "HERMES_3.5_DUAL_SNIPER":
            # Must pass 15m sniper gate (reject runaway knives/rockets)
            if not s["sniper_pass"]:
                continue
            # If not CVD pass, we require micro-sniper pass with tight profit armor
            
        sym = s["sym"]
        tf = s["tf"]
        candles = data_4h[sym] if tf == "4h" else data_1h[sym]
        n = len(candles)
        t = s["t_idx"]
        side = s["side"]
        s_time = s["time"]
        
        target_slot = None
        if tf == "4h":
            if s_time >= slot_busy["4h_1"]: target_slot = "4h_1"
            elif s_time >= slot_busy["4h_2"]: target_slot = "4h_2"
        else:
            if s_time >= slot_busy["1h_1"]: target_slot = "1h_1"
            elif s_time >= slot_busy["1h_2"]: target_slot = "1h_2"
            
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
        
        # In Hermes 3.5 Dual Sniper, if CVD was confirmed we use standard armor, else fast BE armor (+1.0%)
        be_threshold = 0.016
        if model_name == "HERMES_3.5_DUAL_SNIPER" and not s["cvd_pass"]:
            be_threshold = 0.010 # Fast BE lock on non-CVD trades
            
        for m in range(t, min(t + s["max_hold"], n)):
            c_m = candles[m]
            m_time = c_m["time"]
            
            if side == "LONG":
                if c_m["high"] >= entry * 1.022:
                    curr_sl = max(curr_sl, entry * 1.012); be_locked = True
                elif c_m["high"] >= entry * (1.0 + be_threshold):
                    curr_sl = max(curr_sl, entry * 1.002); be_locked = True
                    
                if c_m["high"] >= tp_p:
                    res = "WIN"; exit_price = tp_p; exit_time = m_time; break
                if c_m["low"] <= hard_sl_p:
                    res = "LOSS"; exit_price = hard_sl_p; exit_time = m_time; break
                if c_m["close"] <= curr_sl:
                    res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                    exit_price = c_m["close"]; exit_time = m_time; break
            else:
                if c_m["low"] <= entry * 0.978:
                    curr_sl = min(curr_sl, entry * 0.988); be_locked = True
                elif c_m["low"] <= entry * (1.0 - be_threshold):
                    curr_sl = min(curr_sl, entry * 0.998); be_locked = True
                    
                if c_m["low"] <= tp_p:
                    res = "WIN"; exit_price = tp_p; exit_time = m_time; break
                if c_m["high"] >= hard_sl_p:
                    res = "LOSS"; exit_price = hard_sl_p; exit_time = m_time; break
                if c_m["close"] >= curr_sl:
                    res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                    exit_price = c_m["close"]; exit_time = m_time; break
                    
        if not res:
            fc = candles[min(t + s["max_hold"], n - 1)]["close"]
            res = "WIN" if (fc > entry if side == "LONG" else fc < entry) else "LOSS"
            exit_price = fc
            exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]
            
        slot_busy[target_slot] = exit_time
        
        gross_pct = ((exit_price - entry) / entry) if side == "LONG" else ((entry - exit_price) / entry)
        net_pct = gross_pct - fee_rate
        
        # 100% Full Compounding Sizing!
        pos_size = balance * 5.0
        pnl = pos_size * net_pct
        
        if res == "WIN":
            balance += (pnl * 0.85)
            vault += (pnl * 0.15)
        else:
            balance += pnl
            if balance < 5.0: balance = 5.0
            
        tot_eq = balance + vault
        if tot_eq > peak: peak = tot_eq
        dd = (peak - tot_eq) / peak if peak > 0 else 0
        if dd > max_dd: max_dd = dd
        
        dt_in = datetime.fromtimestamp(s_time/1000.0, tz=IST)
        dt_out = datetime.fromtimestamp(exit_time/1000.0, tz=IST)
        
        executed_trades.append({
            "num": len(executed_trades) + 1,
            "sym": sym,
            "tf": tf,
            "side": side,
            "time_in": dt_in.strftime("%d-%b %H:%M"),
            "time_out": dt_out.strftime("%d-%b %H:%M"),
            "entry": round(entry, 4),
            "exit": round(exit_price, 4),
            "net_pct": round(net_pct * 100.0, 2),
            "roe_pct": round(net_pct * 5.0 * 100.0, 2),
            "pnl": round(pnl, 2),
            "res": res,
            "tot_eq": round(tot_eq, 2)
        })
        
    wins = sum(1 for e in executed_trades if e["res"] == "WIN")
    tot = len(executed_trades)
    wr = (wins / tot * 100.0) if tot > 0 else 0
    
    return {
        "model": model_name,
        "total_trades": tot,
        "wins": wins,
        "losses": tot - wins,
        "win_rate": round(wr, 2),
        "final_equity": round(tot_eq, 2),
        "growth_pct": round(((tot_eq - 50.0) / 50.0) * 100.0, 2),
        "max_drawdown": round(max_dd * 100.0, 2),
        "trades": executed_trades
    }

async def main():
    print("=" * 80)
    print("⚔️ 5-DAY REAL MARKET BATTLE: HERMES 3.0 vs HERMES 3.5 DUAL SNIPER")
    print("=" * 80)
    
    # Use Top Champions
    test_coins = TOP_45_CHAMPIONS[:30] # 30 top liquid pairs
    data_1h, data_4h = await fetch_5day_market_data(test_coins)
    
    raw_setups, start_time = harvest_5day_setups(data_1h, data_4h)
    dt_start = datetime.fromtimestamp(start_time/1000.0, tz=IST)
    print(f"\nAudit Window: {dt_start.strftime('%d-%b-%Y %H:%M IST')} to TODAY ({datetime.now(IST).strftime('%d-%b-%Y %H:%M IST')})")
    print(f"Total candidate setups detected across market: {len(raw_setups)}")
    
    # 1. Run Hermes 3.0 Quantum
    res_h30 = simulate_5day_engine("HERMES_3.0_QUANTUM", raw_setups, data_1h, data_4h)
    
    # 2. Run Hermes 3.5 Dual Sniper
    res_h35 = simulate_5day_engine("HERMES_3.5_DUAL_SNIPER", raw_setups, data_1h, data_4h)
    
    print("\n" + "=" * 80)
    print("📋 5-DAY TRADE-BY-TRADE AUDIT LIST:")
    print("=" * 80)
    
    print(f"\n--- HERMES 3.0 QUANTUM ({res_h30['total_trades']} Trades taken) ---")
    print(f"{'#':<3} | {'Time In':<12} | {'Symbol':<10} | {'TF':<3} | {'Side':<5} | {'Entry':<8} | {'Exit':<8} | {'ROE %':<8} | {'PnL $':<8} | {'Res':<5} | {'Equity $'}")
    print("-" * 88)
    for t in res_h30["trades"]:
        icon = "🟢" if t["res"] == "WIN" else "🔴"
        print(f"{t['num']:<3} | {t['time_in']:<12} | {t['sym']:<10} | {t['tf']:<3} | {t['side']:<5} | {t['entry']:<8} | {t['exit']:<8} | {t['roe_pct']:+6.1f}% | ${t['pnl']:+6.2f} | {icon} {t['res']:<4} | ${t['tot_eq']:.2f}")

    print(f"\n--- HERMES 3.5 DUAL SNIPER ({res_h35['total_trades']} Trades taken) ---")
    print(f"{'#':<3} | {'Time In':<12} | {'Symbol':<10} | {'TF':<3} | {'Side':<5} | {'Entry':<8} | {'Exit':<8} | {'ROE %':<8} | {'PnL $':<8} | {'Res':<5} | {'Equity $'}")
    print("-" * 88)
    for t in res_h35["trades"]:
        icon = "🟢" if t["res"] == "WIN" else "🔴"
        print(f"{t['num']:<3} | {t['time_in']:<12} | {t['sym']:<10} | {t['tf']:<3} | {t['side']:<5} | {t['entry']:<8} | {t['exit']:<8} | {t['roe_pct']:+6.1f}% | ${t['pnl']:+6.2f} | {icon} {t['res']:<4} | ${t['tot_eq']:.2f}")

    print("\n" + "=" * 80)
    print("🏆 5-DAY HEAD-TO-HEAD BATTLE SCORECARD:")
    print("=" * 80)
    print(f"{'Metric':<30} | {'HERMES 3.0 (Quantum)':<22} | {'HERMES 3.5 (Dual Sniper)':<22}")
    print("-" * 80)
    print(f"{'Total Trades Taken':<30} | {res_h30['total_trades']:<22} | {res_h35['total_trades']:<22}")
    print(f"{'Wins / Losses':<30} | {res_h30['wins']}W / {res_h30['losses']}L{'':<14} | {res_h35['wins']}W / {res_h35['losses']}L{'':<14}")
    print(f"{'5-DAY WIN RATE':<30} | {res_h30['win_rate']}%{'':<16} | {res_h35['win_rate']}%{'':<16}")
    print(f"{'Max Drawdown':<30} | {res_h30['max_drawdown']}%{'':<16} | {res_h35['max_drawdown']}%{'':<16}")
    print(f"{'Starting Capital':<30} | $50.00{'':<16} | $50.00{'':<16}")
    print(f"{'Final 5-Day Balance':<30} | ${res_h30['final_equity']:.2f}{'':<16} | ${res_h35['final_equity']:.2f}{'':<16}")
    print(f"{'Net Capital Growth %':<30} | +{res_h30['growth_pct']}%{'':<15} | +{res_h35['growth_pct']}%{'':<15}")
    print("=" * 80)

    # Save to JSON
    with open("battle_5days_h30_vs_h35.json", "w") as f:
        json.dump({"hermes_30": res_h30, "hermes_35": res_h35}, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
