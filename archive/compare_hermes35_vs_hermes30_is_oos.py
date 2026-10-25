import os
import sys
import json
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from run_hermes3_apex_backtest import load_candles, build_btc_map, TOP_22_CHAMPIONS

print("=" * 85)
print("⚔️ HEAD-TO-HEAD DUEL: HERMES 3.0 QUANTUM VS HERMES 3.5 SINGLE TIER")
print("Full 2-Year Continuous Dataset (470,532 Candlesticks | Top-22 Binance Futures Assets)")
print("In-Sample (Year 1: 2024-09 to 2025-09) & Out-of-Sample (Year 2: 2025-09 to 2026-09)")
print("=" * 85)

btc_map_4h, btc_map_1h = build_btc_map()

def calculate_ema(values, period=50):
    if not values: return []
    ema = [values[0]] * len(values)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(values)):
        ema[i] = values[i] * k + ema[i-1] * (1.0 - k)
    return ema

# Precompute BTC 4H EMA50 Macro Trend for Hermes 3.5
btc_candles_4h = load_candles("BTCUSDT", "4h")
btc_closes = [c["close"] for c in btc_candles_4h]
btc_ema50 = calculate_ema(btc_closes, 50)
btc_4h_ema50_map = {}
for idx, c in enumerate(btc_candles_4h):
    btc_4h_ema50_map[c["time"]] = (c["close"] >= btc_ema50[idx])

# Harvest Candidate Setups for both engines
raw_setups_h30 = []
raw_setups_h35 = []

for tf in ["4h", "1h"]:
    std_tp_pct = 0.028 if tf == "4h" else 0.022
    soft_sl_pct = 0.028 if tf == "4h" else 0.025
    hard_sl_pct = 0.038 if tf == "4h" else 0.036
    max_tap_window = 28
    max_hold = 30 if tf == "4h" else 40
    
    for sym in TOP_22_CHAMPIONS:
        candles = load_candles(sym, tf)
        n = len(candles)
        if n < 40: continue
        
        atr = [0.0] * n
        for k in range(1, n):
            tr = max(candles[k]["high"] - candles[k]["low"],
                     abs(candles[k]["high"] - candles[k-1]["close"]),
                     abs(candles[k]["low"] - candles[k-1]["close"]))
            atr[k] = tr if k < 14 else (atr[k-1] * 13 + tr) / 14
            
        for i in range(20, n - 2):
            # LONG
            if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 2:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= 0.050:
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
                                    if candles[t]["low"] <= dec_top * 1.0005:
                                        tap_c = candles[t]
                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0
                                        
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                        btc_clean_h30 = btc_dump < 0.020
                                        
                                        # BTC Macro EMA50 check for Hermes 3.5
                                        btc_is_bull_h35 = btc_4h_ema50_map.get(prev_4h_ts, True)
                                        
                                        # Qualifying setup for H3.0
                                        if btc_clean_h30 and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                            raw_setups_h30.append({
                                                "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                            })
                                            
                                        # Qualifying setup for H3.5 (King BTC Bull Alignment)
                                        if btc_is_bull_h35 and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                            raw_setups_h35.append({
                                                "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                            })
                                            break

            # SHORT
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
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                            fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = dec_c["high"]
                            dec_bot = min(dec_c["open"], dec_c["close"])
                            has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                            if has_bear_fvg:
                                for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                    if candles[t]["high"] >= dec_bot * 0.9995:
                                        tap_c = candles[t]
                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                        u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0
                                        
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                        btc_clean_short_h30 = btc_pump < 0.020
                                        
                                        # BTC Macro EMA50 check for Hermes 3.5 (STRICT VETO: If BTC Bullish, Alt Shorts 100% FORBIDDEN!)
                                        btc_is_bull_h35 = btc_4h_ema50_map.get(prev_4h_ts, True)
                                        
                                        # Qualifying setup for H3.0
                                        if btc_clean_short_h30 and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                            raw_setups_h30.append({
                                                "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                            })
                                            
                                        # Qualifying setup for H3.5: Strictly block Alt Shorts if BTC is Bullish!
                                        short_allowed_h35 = (not btc_is_bull_h35) or (sym == "BTCUSDT")
                                        if short_allowed_h35 and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                            raw_setups_h35.append({
                                                "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                            })
                                            break

raw_setups_h30.sort(key=lambda x: x["time"])
raw_setups_h35.sort(key=lambda x: x["time"])

def simulate_engine(setups, engine_name):
    slot_busy_until = {"4h_slot1": 0, "4h_slot2": 0, "1h_slot1": 0, "1h_slot2": 0}
    all_executed = []
    bal = 50.0
    vault = 0.0
    m2k_hit = None
    
    for setup in setups:
        sym, tf, t = setup["sym"], setup["tf"], setup["t_idx"]
        candles = load_candles(sym, tf)
        n, side, s_time = len(candles), setup["side"], setup["time"]
        
        target_slot = None
        if tf == "4h":
            if s_time >= slot_busy_until["4h_slot1"]: target_slot = "4h_slot1"
            elif s_time >= slot_busy_until["4h_slot2"]: target_slot = "4h_slot2"
        else:
            if s_time >= slot_busy_until["1h_slot1"]: target_slot = "1h_slot1"
            elif s_time >= slot_busy_until["1h_slot2"]: target_slot = "1h_slot2"
        if not target_slot: continue
        
        mt = setup["mt"]
        if side == "LONG":
            entry = mt if setup["tap_low"] <= mt else (setup["dec_top"] + mt) / 2.0
            tp_p = entry * (1.0 + setup["std_tp_pct"])
            struct_sl = min(setup["dec_bot"], setup["tap_low"]) - 0.20 * setup["atr"]
            hard_sl_p = max(min(struct_sl, entry * (1.0 - setup["hard_sl_pct"])), entry * 0.962)
            soft_sl_p = (entry + hard_sl_p) / 2.0
        else:
            entry = mt if setup["tap_high"] >= mt else (setup["dec_bot"] + mt) / 2.0
            tp_p = entry * (1.0 - setup["std_tp_pct"])
            struct_sl = max(setup["dec_top"], setup["tap_high"]) + 0.20 * setup["atr"]
            hard_sl_p = min(max(struct_sl, entry * (1.0 + setup["hard_sl_pct"])), entry * 1.038)
            soft_sl_p = (entry + hard_sl_p) / 2.0
            
        res = None
        exit_price = entry
        exit_time = s_time
        curr_sl = soft_sl_p
        be_locked = False
        
        for m in range(t, min(t + setup["max_hold"], n)):
            c_m = candles[m]
            m_time = c_m["time"]
            
            # In-trade BTC Emergency Shield
            btc_ts = m_time - (m_time % (3600 * 1000))
            btc_1h_c = btc_map_1h.get(btc_ts)
            if btc_1h_c:
                btc_chg = (btc_1h_c["close"] - btc_1h_c["open"]) / btc_1h_c["open"]
                if side == "LONG" and btc_chg < -0.010 and not be_locked:
                    curr_sl = max(curr_sl, entry * 0.995)
                elif side == "SHORT" and btc_chg > 0.010 and not be_locked:
                    curr_sl = min(curr_sl, entry * 1.005)
                    
            if side == "LONG":
                if c_m["high"] >= entry * 1.022:
                    curr_sl = max(curr_sl, entry * 1.012)
                    be_locked = True
                elif c_m["high"] >= entry * 1.016:
                    curr_sl = max(curr_sl, entry * 1.002)
                    be_locked = True
                    
                if c_m["high"] >= tp_p:
                    res = "WIN"; exit_price = tp_p; exit_time = m_time; break
                if c_m["low"] <= hard_sl_p:
                    res = "LOSS"; exit_price = hard_sl_p; exit_time = m_time; break
                if c_m["close"] <= curr_sl:
                    res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                    exit_price = c_m["close"]; exit_time = m_time; break
            else:
                if c_m["low"] <= entry * 0.978:
                    curr_sl = min(curr_sl, entry * 0.988)
                    be_locked = True
                elif c_m["low"] <= entry * 0.984:
                    curr_sl = min(curr_sl, entry * 0.998)
                    be_locked = True
                    
                if c_m["low"] <= tp_p:
                    res = "WIN"; exit_price = tp_p; exit_time = m_time; break
                if c_m["high"] >= hard_sl_p:
                    res = "LOSS"; exit_price = hard_sl_p; exit_time = m_time; break
                if c_m["close"] >= curr_sl:
                    res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                    exit_price = c_m["close"]; exit_time = m_time; break
                    
        if not res:
            fc = candles[min(t + setup["max_hold"], n - 1)]["close"]
            res = "WIN" if ((side == "LONG" and fc >= entry) or (side == "SHORT" and fc <= entry)) else "LOSS"
            exit_price = fc
            exit_time = candles[min(t + setup["max_hold"], n - 1)]["time"]
            
        slot_busy_until[target_slot] = exit_time
        
        pos_size = bal * 5.0
        ret = ((exit_price - entry)/entry) if side == "LONG" else ((entry - exit_price)/entry)
        net_pnl = (pos_size * ret) - (pos_size * 0.0016)
        
        if net_pnl > 0:
            bal += net_pnl * 0.85
            vault += net_pnl * 0.15
        else:
            bal += net_pnl
            if bal < 10.0: bal = 10.0
            
        tot = bal + vault
        if not m2k_hit and tot >= 2000.0:
            m2k_hit = {
                "trade_num": len(all_executed) + 1,
                "date": datetime.fromtimestamp(exit_time / 1000).strftime("%Y-%m-%d"),
                "equity": round(tot, 2)
            }
            
        all_executed.append({
            "sym": sym, "tf": tf, "side": side, "res": res,
            "entry_time": s_time, "exit_time": exit_time,
            "dt": datetime.fromtimestamp(s_time / 1000),
            "roe": ret * 500.0
        })
        
    return all_executed, m2k_hit, bal, vault

trades_h30, m2k_h30, b30, v30 = simulate_engine(raw_setups_h30, "HERMES_3.0")
trades_h35, m2k_h35, b35, v35 = simulate_engine(raw_setups_h35, "HERMES_3.5")

midpoint = datetime(2025, 9, 25)

def analyze(trades, name):
    is_t = [t for t in trades if t["dt"] < midpoint]
    oos_t = [t for t in trades if t["dt"] >= midpoint]
    
    is_w = sum(1 for t in is_t if t["res"] == "WIN")
    oos_w = sum(1 for t in oos_t if t["res"] == "WIN")
    
    is_wr = (is_w / len(is_t) * 100.0) if is_t else 0.0
    oos_wr = (oos_w / len(oos_t) * 100.0) if oos_t else 0.0
    tot_wr = (sum(1 for t in trades if t["res"] == "WIN") / len(trades) * 100.0) if trades else 0.0
    
    shorts = [t for t in trades if t["side"] == "SHORT"]
    short_wr = (sum(1 for t in shorts if t["res"] == "WIN") / len(shorts) * 100.0) if shorts else 0.0
    short_losses = sum(1 for t in shorts if t["res"] == "LOSS")
    
    longs = [t for t in trades if t["side"] == "LONG"]
    long_wr = (sum(1 for t in longs if t["res"] == "WIN") / len(longs) * 100.0) if longs else 0.0
    
    return {
        "total_trades": len(trades),
        "wins": sum(1 for t in trades if t["res"] == "WIN"),
        "losses": sum(1 for t in trades if t["res"] == "LOSS"),
        "total_wr": round(tot_wr, 2),
        "is_trades": len(is_t),
        "is_wr": round(is_wr, 2),
        "oos_trades": len(oos_t),
        "oos_wr": round(oos_wr, 2),
        "short_trades": len(shorts),
        "short_losses": short_losses,
        "short_wr": round(short_wr, 2),
        "long_trades": len(longs),
        "long_wr": round(long_wr, 2),
        "net_roe": round(sum(t["roe"] for t in trades), 1)
    }

stat30 = analyze(trades_h30, "Hermes 3.0")
stat35 = analyze(trades_h35, "Hermes 3.5")

print("\n" + "=" * 85)
print("📊 2-YEAR MASTER COMPARISON AUDIT TABLE: HERMES 3.0 VS HERMES 3.5")
print("=" * 85)
print(f"{'Performance Metric':<32} | {'HERMES 3.0 QUANTUM':<22} | {'HERMES 3.5 SINGLE TIER':<22}")
print("-" * 85)
print(f"{'Total Executed Trades':<32} | {stat30['total_trades']:<22,} | {stat35['total_trades']:<22,}")
print(f"{'Total Wins (TP / Armor)':<32} | {stat30['wins']:<22,} | {stat35['wins']:<22,}")
print(f"{'Total Stop Loss Hits (Losses)':<32} | {stat30['losses']:<22,} | {stat35['losses']:<22,}")
print(f"{'Overall 2-Year Win Rate':<32} | {stat30['total_wr']:>6.2f}%               | {stat35['total_wr']:>6.2f}%")
print(f"{'In-Sample Win Rate (Year 1)':<32} | {stat30['is_wr']:>6.2f}%               | {stat35['is_wr']:>6.2f}%")
print(f"{'Out-of-Sample Win Rate (Year 2)':<32} | {stat30['oos_wr']:>6.2f}%               | {stat35['oos_wr']:>6.2f}%")
print(f"{'Out-of-Sample Trades':<32} | {stat30['oos_trades']:<22,} | {stat35['oos_trades']:<22,}")
print(f"{'Long Win Rate':<32} | {stat30['long_wr']:>6.2f}%               | {stat35['long_wr']:>6.2f}%")
print(f"{'Short Trades Taken':<32} | {stat30['short_trades']:<22,} | {stat35['short_trades']:<22,}")
print(f"{'Short Losses (SL Hits)':<32} | {stat30['short_losses']:<22,} | {stat35['short_losses']:<22,}")
print(f"{'Short Win Rate':<32} | {stat30['short_wr']:>6.2f}%               | {stat35['short_wr']:>6.2f}%")
print(f"{'Net Cumulative ROE':<32} | +{stat30['net_roe']:<21,} | +{stat35['net_roe']:<21,}")
if m2k_h30 and m2k_h35:
    print(f"{'$2,000 Milestone Speed':<32} | Trade #{m2k_h30['trade_num']} ({m2k_h30['date']})    | Trade #{m2k_h35['trade_num']} ({m2k_h35['date']})")
print("=" * 85)

duel_results = {
    "hermes30": stat30,
    "hermes35": stat35,
    "m2k_h30": m2k_h30,
    "m2k_h35": m2k_h35
}

with open("HERMES30_VS_HERMES35_DUEL_REPORT.json", "w") as f:
    json.dump(duel_results, f, indent=2)

print("\nSaved full duel report to HERMES30_VS_HERMES35_DUEL_REPORT.json")
