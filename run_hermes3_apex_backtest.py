import os
import sys
import json
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_2year")

CANDLE_CACHE = {}

def load_candles(sym, interval):
    key = f"{sym}_{interval}"
    if key in CANDLE_CACHE:
        return CANDLE_CACHE[key]
    fpath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        c["volume"] = float(c.get("volume", 0.0))
    CANDLE_CACHE[key] = data
    return data

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_1h = load_candles("BTCUSDT", "1h")
    return {c["time"]: c for c in btc_4h}, {c["time"]: c for c in btc_1h}

def run_hermes3_vs_hermes25_comparison():
    print("=" * 75)
    print("🚀 RUNNING 2-YEAR BACKTEST: HERMES 2.5 APEX HYBRID VS HERMES 3.0 QUANTUM")
    print("=" * 75)
    
    btc_map_4h, btc_map_1h = build_btc_map()
    
    # 1. Harvest all candidate SMC setups
    raw_setups = []
    
    for tf in ["4h", "1h"]:
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.025
        hard_sl_pct = 0.038 if tf == "4h" else 0.036
        max_tap_window = 28
        max_hold = 30 if tf == "4h" else 40
        
        for sym in TOP_22_CHAMPIONS:
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < 40:
                continue
            
            # Precompute ATR(14)
            atr = [0.0] * n
            for k in range(1, n):
                tr = max(candles[k]["high"] - candles[k]["low"],
                         abs(candles[k]["high"] - candles[k-1]["close"]),
                         abs(candles[k]["low"] - candles[k-1]["close"]))
                atr[k] = tr if k < 14 else (atr[k-1] * 13 + tr) / 14
                
            for i in range(20, n - 2):
                # LONG SETUP
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
                                            btc_clean = btc_dump < 0.020
                                            
                                            if btc_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                                })
                                                break
                
                # SHORT SETUP
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
                                            btc_clean_short = btc_pump < 0.020
                                            
                                            if btc_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                                })
                                                break

    raw_setups.sort(key=lambda x: x["time"])
    print(f"Total candidate setups detected across 2 years: {len(raw_setups)}")
    
    engines = ["HERMES_2.5_APEX_HYBRID", "HERMES_3.0_QUANTUM"]
    results = {}
    
    for engine_name in engines:
        # Sequential execution across 4 independent slots (Binance 4H, Binance 1H, Bitget 4H, Bitget 1H)
        # To strictly replicate our real architecture:
        slot_busy_until = {
            "4h_slot1": 0,
            "4h_slot2": 0,
            "1h_slot1": 0,
            "1h_slot2": 0
        }
        
        executed_trades = []
        balance = 50.0
        vault = 0.0
        milestone_2k_hit = None
        
        for setup in raw_setups:
            sym = setup["sym"]
            tf = setup["tf"]
            t = setup["t_idx"]
            candles = load_candles(sym, tf)
            n = len(candles)
            side = setup["side"]
            s_time = setup["time"]
            
            # Select available slot
            target_slot = None
            if tf == "4h":
                if s_time >= slot_busy_until["4h_slot1"]:
                    target_slot = "4h_slot1"
                elif s_time >= slot_busy_until["4h_slot2"]:
                    target_slot = "4h_slot2"
            else: # 1h
                if s_time >= slot_busy_until["1h_slot1"]:
                    target_slot = "1h_slot1"
                elif s_time >= slot_busy_until["1h_slot2"]:
                    target_slot = "1h_slot2"
            
            if not target_slot:
                continue
                
            # EXECUTION LOGIC
            if engine_name == "HERMES_2.5_APEX_HYBRID":
                if side == "LONG":
                    entry = setup["dec_top"]
                    tp_p = entry * (1.0 + setup["std_tp_pct"])
                    soft_sl_p = entry * (1.0 - setup["soft_sl_pct"])
                    hard_sl_p = entry * (1.0 - setup["hard_sl_pct"])
                else:
                    entry = setup["dec_bot"]
                    tp_p = entry * (1.0 - setup["std_tp_pct"])
                    soft_sl_p = entry * (1.0 + setup["soft_sl_pct"])
                    hard_sl_p = entry * (1.0 + setup["hard_sl_pct"])
            else: # HERMES_3.0_QUANTUM (Mean Threshold + Dynamic Structural Armor)
                mt = setup["mt"]
                if side == "LONG":
                    # Fills at Mean Threshold if candle probed it, else mid-depth
                    entry = mt if setup["tap_low"] <= mt else (setup["dec_top"] + mt) / 2.0
                    tp_p = entry * (1.0 + setup["std_tp_pct"])
                    # Structural SL: below dec_bot or tap low with buffer, capped at 3.8%
                    struct_sl = min(setup["dec_bot"], setup["tap_low"]) - 0.20 * setup["atr"]
                    hard_sl_p = min(struct_sl, entry * (1.0 - setup["hard_sl_pct"]))
                    hard_sl_p = max(hard_sl_p, entry * 0.962)
                    soft_sl_p = (entry + hard_sl_p) / 2.0
                else: # SHORT
                    entry = mt if setup["tap_high"] >= mt else (setup["dec_bot"] + mt) / 2.0
                    tp_p = entry * (1.0 - setup["std_tp_pct"])
                    struct_sl = max(setup["dec_top"], setup["tap_high"]) + 0.20 * setup["atr"]
                    hard_sl_p = max(struct_sl, entry * (1.0 + setup["hard_sl_pct"]))
                    hard_sl_p = min(hard_sl_p, entry * 1.038)
                    soft_sl_p = (entry + hard_sl_p) / 2.0
            
            res = None
            exit_price = entry
            exit_time = s_time
            curr_sl = soft_sl_p
            be_locked = False
            sl_reason = None
            
            for m in range(t, min(t + setup["max_hold"], n)):
                c_m = candles[m]
                m_time = c_m["time"]
                
                # In-trade BTC Emergency Shield for Hermes 3.0
                if engine_name == "HERMES_3.0_QUANTUM":
                    # Check closest 1h BTC candle
                    btc_ts = m_time - (m_time % (3600 * 1000))
                    btc_1h_c = btc_map_1h.get(btc_ts)
                    if btc_1h_c:
                        btc_chg = (btc_1h_c["close"] - btc_1h_c["open"]) / btc_1h_c["open"]
                        if side == "LONG" and btc_chg < -0.010: # BTC flash dump > 1.0%
                            if not be_locked:
                                curr_sl = max(curr_sl, entry * 0.995) # Tighten to -0.5% max
                        elif side == "SHORT" and btc_chg > 0.010: # BTC flash pump > 1.0%
                            if not be_locked:
                                curr_sl = min(curr_sl, entry * 1.005)
                
                if side == "LONG":
                    # Dynamic Profit Armor (both 2.5 and 3.0)
                    if c_m["high"] >= entry * 1.022 and engine_name == "HERMES_3.0_QUANTUM":
                        curr_sl = max(curr_sl, entry * 1.012) # Stage 2 Trailing Lock
                        be_locked = True
                    elif c_m["high"] >= entry * 1.016:
                        curr_sl = max(curr_sl, entry * 1.002) # Stage 1 BE Lock
                        be_locked = True
                        
                    if c_m["high"] >= tp_p:
                        res = "WIN"
                        exit_price = tp_p
                        exit_time = m_time
                        break
                    if c_m["low"] <= hard_sl_p:
                        res = "LOSS"
                        exit_price = hard_sl_p
                        exit_time = m_time
                        sl_reason = "HARD_SL"
                        break
                    if c_m["close"] <= curr_sl:
                        res = "WIN" if (be_locked and curr_sl > entry) else "LOSS"
                        exit_price = c_m["close"]
                        exit_time = m_time
                        sl_reason = "BE_EXIT" if be_locked and curr_sl > entry else "SOFT_SL"
                        break
                else: # SHORT
                    if c_m["low"] <= entry * 0.978 and engine_name == "HERMES_3.0_QUANTUM":
                        curr_sl = min(curr_sl, entry * 0.988) # Stage 2 Trailing Lock
                        be_locked = True
                    elif c_m["low"] <= entry * 0.984:
                        curr_sl = min(curr_sl, entry * 0.998) # Stage 1 BE Lock
                        be_locked = True
                        
                    if c_m["low"] <= tp_p:
                        res = "WIN"
                        exit_price = tp_p
                        exit_time = m_time
                        break
                    if c_m["high"] >= hard_sl_p:
                        res = "LOSS"
                        exit_price = hard_sl_p
                        exit_time = m_time
                        sl_reason = "HARD_SL"
                        break
                    if c_m["close"] >= curr_sl:
                        res = "WIN" if (be_locked and curr_sl < entry) else "LOSS"
                        exit_price = c_m["close"]
                        exit_time = m_time
                        sl_reason = "BE_EXIT" if be_locked and curr_sl < entry else "SOFT_SL"
                        break
            
            if not res:
                fc = candles[min(t + setup["max_hold"], n - 1)]["close"]
                if side == "LONG":
                    res = "WIN" if fc >= entry else "LOSS"
                else:
                    res = "WIN" if fc <= entry else "LOSS"
                exit_price = fc
                exit_time = candles[min(t + setup["max_hold"], n - 1)]["time"]
                sl_reason = "TIME_EXPIRY"
                
            slot_busy_until[target_slot] = exit_time
            
            # Compounding PnL
            pos_size = balance * 5.0
            if side == "LONG":
                ret = (exit_price - entry) / entry
            else:
                ret = (entry - exit_price) / entry
            
            gross_pnl = pos_size * ret
            fees = pos_size * 0.0016
            net_pnl = gross_pnl - fees
            
            if net_pnl > 0:
                reinvest = net_pnl * 0.85
                vault_stash = net_pnl * 0.15
                balance += reinvest
                vault += vault_stash
            else:
                balance += net_pnl
                if balance < 10.0:
                    balance = 10.0 # Floor safety
            
            total_equity = balance + vault
            if not milestone_2k_hit and total_equity >= 2000.0:
                milestone_2k_hit = {
                    "trade_num": len(executed_trades) + 1,
                    "date": datetime.fromtimestamp(exit_time / 1000).strftime("%Y-%m-%d"),
                    "equity": round(total_equity, 2)
                }
            
            executed_trades.append({
                "sym": sym, "tf": tf, "side": side, "res": res,
                "net_pnl": net_pnl, "equity": total_equity, "sl_reason": sl_reason,
                "entry_time": s_time, "exit_time": exit_time
            })
        
        wins = sum(1 for t in executed_trades if t["res"] == "WIN")
        losses = sum(1 for t in executed_trades if t["res"] == "LOSS")
        long_trades = sum(1 for t in executed_trades if t["side"] == "LONG")
        long_wins = sum(1 for t in executed_trades if t["side"] == "LONG" and t["res"] == "WIN")
        long_losses = long_trades - long_wins
        short_trades = sum(1 for t in executed_trades if t["side"] == "SHORT")
        short_wins = sum(1 for t in executed_trades if t["side"] == "SHORT" and t["res"] == "WIN")
        short_losses = short_trades - short_wins
        
        wr = (wins / len(executed_trades) * 100) if executed_trades else 0
        long_wr = (long_wins / long_trades * 100) if long_trades else 0
        short_wr = (short_wins / short_trades * 100) if short_trades else 0
        
        results[engine_name] = {
            "total_trades": len(executed_trades),
            "wins": wins,
            "losses": losses,
            "win_rate": round(wr, 2),
            "long_trades": long_trades,
            "long_losses": long_losses,
            "long_wr": round(long_wr, 2),
            "short_trades": short_trades,
            "short_losses": short_losses,
            "short_wr": round(short_wr, 2),
            "milestone_2k": milestone_2k_hit,
            "final_balance": round(balance, 2),
            "final_vault": round(vault, 2),
            "total_equity": round(total_equity, 2)
        }
        
        print(f"\n📊 [{engine_name}] RESULTS:")
        print(f"Total Trades: {len(executed_trades)} (~{len(executed_trades)//24} trades/month)")
        print(f"Wins: {wins} | Losses (SL hits): {losses}")
        print(f"Overall Win Rate: {wr:.2f}% | Loss Rate: {losses/len(executed_trades)*100:.2f}%")
        print(f"Long Win Rate: {long_wr:.2f}% (Losses: {long_losses} out of {long_trades})")
        print(f"Short Win Rate: {short_wr:.2f}% (Losses: {short_losses} out of {short_trades})")
        if milestone_2k_hit:
            print(f"$50 ➔ $2,000 Milestone: SMASHED in Trade #{milestone_2k_hit['trade_num']} on {milestone_2k_hit['date']}!")

    with open("hermes3_vs_hermes25_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\n✅ Results successfully saved to hermes3_vs_hermes25_results.json")

if __name__ == "__main__":
    run_hermes3_vs_hermes25_comparison()
