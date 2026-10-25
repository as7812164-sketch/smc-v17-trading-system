import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import json
from feed.binance_feed import binance_feed

async def run_pessimistic_and_realistic_audit():
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    
    data_1h = {}
    data_4h = {}
    for c in coins:
        try:
            k1 = await binance_feed.fetch_klines(c, interval="1h", limit=720)
            if len(k1) >= 200: data_1h[c] = k1
            k4 = await binance_feed.fetch_klines(c, interval="4h", limit=200)
            if len(k4) >= 50: data_4h[c] = k4
        except Exception as e:
            pass
            
    btc_4h = data_4h.get("BTCUSDT", [])
    max_tap_window = 28
    
    # Extract candidates
    candidates = []
    for c in coins:
        for tf, dataset in [("1h", data_1h.get(c, [])), ("4h", data_4h.get(c, []))]:
            n = len(dataset)
            if n < 40: continue
            for i in range(20, n - 2):
                # LONG
                prior_lows = [float(x["low"]) for x in dataset[max(0, i-15):i+1]]
                if float(dataset[i]["low"]) == min(prior_lows):
                    sub_w = dataset[i:min(i+16, n)]
                    highs = [float(x["high"]) for x in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        origin_l = float(dataset[i]["low"])
                        gain = (max_high - origin_l) / origin_l if origin_l > 0 else 0.0
                        if gain >= 0.050:
                            idm_low = float(dataset[high_idx - 1]["low"])
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i + 1, high_idx):
                                m_h = float(dataset[mid]["high"])
                                m_l = float(dataset[mid]["low"])
                                bg = (m_h - m_l) / m_l if m_l > 0 else 0.0
                                fib = (m_l - origin_l) / (max_high - origin_l) if max_high > origin_l else 0.0
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = dataset[best_mid - 1]
                                dec_top = max(float(dec_c["open"]), float(dec_c["close"]))
                                dec_bot = float(dec_c["low"])
                                has_fvg = (float(dataset[best_mid + 1]["low"]) > float(dataset[best_mid - 1]["high"])) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        tap_c = dataset[t]
                                        t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                        if t_l <= dec_top * 1.0005:
                                            c_range = t_h - t_l
                                            swept = any(float(dataset[k]["low"]) < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(t_o, t_c) - t_l
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                            mt = round((dec_top + dec_bot) / 2.0, 8)
                                            btc_clean = True
                                            if btc_4h:
                                                prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                if len(prior_btc) >= 2:
                                                    last_b = prior_btc[-1]
                                                    o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                    btc_dump = (o_b - c_b) / o_b if o_b > 0 else 0.0
                                                    if btc_dump >= 0.020: btc_clean = False
                                            if btc_clean and swept and w_ratio >= 0.18 and t_c >= mt:
                                                entry_mt = mt if t_l <= mt else round((dec_top + mt) / 2.0, 8)
                                                candidates.append({
                                                    "symbol": c, "side": "LONG", "timeframe": tf,
                                                    "entry_time": tap_c["time"], "entry_mt": entry_mt,
                                                    "close_price": t_c, "idx": t, "dataset": dataset
                                                })
                                            break
                # SHORT
                prior_highs = [float(x["high"]) for x in dataset[max(0, i-15):i+1]]
                if float(dataset[i]["high"]) == max(prior_highs):
                    sub_w = dataset[i:min(i+16, n)]
                    lows = [float(x["low"]) for x in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        origin_h = float(dataset[i]["high"])
                        drop = (origin_h - min_low) / origin_h if origin_h > 0 else 0.0
                        if drop >= 0.050:
                            idm_high = float(dataset[low_idx - 1]["high"])
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i + 1, low_idx):
                                m_h = float(dataset[mid]["high"])
                                m_l = float(dataset[mid]["low"])
                                bg = (m_h - m_l) / m_h if m_h > 0 else 0.0
                                fib = (origin_h - m_h) / (origin_h - min_low) if origin_h > min_low else 0.0
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = dataset[best_mid - 1]
                                dec_top = float(dec_c["high"])
                                dec_bot = min(float(dec_c["open"]), float(dec_c["close"]))
                                has_bear_fvg = (float(dataset[best_mid + 1]["high"]) < float(dataset[best_mid - 1]["low"])) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        tap_c = dataset[t]
                                        t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                        if t_h >= dec_bot * 0.9995:
                                            c_range = t_h - t_l
                                            swept = any(float(dataset[k]["high"]) > idm_high for k in range(low_idx, t + 1))
                                            u_wick = t_h - max(t_o, t_c)
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                            mt = round((dec_top + dec_bot) / 2.0, 8)
                                            btc_clean_short = True
                                            if btc_4h:
                                                prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                if len(prior_btc) >= 2:
                                                    last_b = prior_btc[-1]
                                                    o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                    btc_pump = (c_b - o_b) / o_b if o_b > 0 else 0.0
                                                    if btc_pump >= 0.020: btc_clean_short = False
                                            if btc_clean_short and swept and w_ratio >= 0.18 and t_c <= mt:
                                                entry_mt = mt if t_h >= mt else round((dec_bot + mt) / 2.0, 8)
                                                candidates.append({
                                                    "symbol": c, "side": "SHORT", "timeframe": tf,
                                                    "entry_time": tap_c["time"], "entry_mt": entry_mt,
                                                    "close_price": t_c, "idx": t, "dataset": dataset
                                                })
                                            break

    seen = set()
    uniq = []
    for ev in candidates:
        k = (ev["symbol"], ev["entry_time"])
        if k not in seen:
            seen.add(k)
            uniq.append(ev)
    uniq.sort(key=lambda x: x["entry_time"])
    
    # -------------------------------------------------------------
    # SIMULATION 1: Pessimistic Same-Bar Conflict (If both hit on same bar, SL wins)
    # -------------------------------------------------------------
    def run_sim(entry_type="MT", same_bar_sl_first=True, add_slippage_pct=0.0005):
        bal = 100.00
        busy_until = 0
        trades = []
        same_bar_conflicts = 0
        
        for ev in uniq:
            if ev["entry_time"] < busy_until: continue
            ds, idx, side = ev["dataset"], ev["idx"], ev["side"]
            
            # Entry Price
            if entry_type == "MT":
                ep = ev["entry_mt"]
            else: # Market Order at Candle Close
                ep = ev["close_price"]
                
            if side == "LONG":
                ep_slip = ep * (1.0 + add_slippage_pct) # adverse slippage on fill
                tp = ep_slip * 1.0300
                sl = ep_slip * 0.9850
                be = ep_slip * 1.0150
            else:
                ep_slip = ep * (1.0 - add_slippage_pct)
                tp = ep_slip * 0.9700
                sl = ep_slip * 1.0150
                be = ep_slip * 0.9850
                
            active_sl = sl
            be_locked = False
            outcome = None
            exit_time = ev["entry_time"]
            
            for bar in ds[idx+1:]:
                b_h, b_l, b_t = float(bar["high"]), float(bar["low"]), bar["time"]
                
                if side == "LONG":
                    if not be_locked and b_h >= be:
                        be_locked = True
                        active_sl = ep_slip
                        
                    # Check same-bar touch
                    if b_h >= tp and b_l <= active_sl:
                        same_bar_conflicts += 1
                        if same_bar_sl_first:
                            outcome = "BE_SAVE" if be_locked else "SL_HIT"
                            exit_time = b_t
                            break
                        else:
                            outcome = "TP_HIT"
                            exit_time = b_t
                            break
                    elif b_h >= tp:
                        outcome = "TP_HIT"
                        exit_time = b_t
                        break
                    elif b_l <= active_sl:
                        outcome = "BE_SAVE" if be_locked else "SL_HIT"
                        exit_time = b_t
                        break
                else: # SHORT
                    if not be_locked and b_l <= be:
                        be_locked = True
                        active_sl = ep_slip
                        
                    if b_l <= tp and b_h >= active_sl:
                        same_bar_conflicts += 1
                        if same_bar_sl_first:
                            outcome = "BE_SAVE" if be_locked else "SL_HIT"
                            exit_time = b_t
                            break
                        else:
                            outcome = "TP_HIT"
                            exit_time = b_t
                            break
                    elif b_l <= tp:
                        outcome = "TP_HIT"
                        exit_time = b_t
                        break
                    elif b_h >= active_sl:
                        outcome = "BE_SAVE" if be_locked else "SL_HIT"
                        exit_time = b_t
                        break
                        
            if not outcome: continue
            
            margin = bal
            pos_size = margin * 5.0
            roe = 15.0 if outcome == "TP_HIT" else (0.0 if outcome == "BE_SAVE" else -7.5)
            gross = round(margin * (roe / 100.0), 2)
            fee = round(pos_size * 0.0016, 2)
            net = round(gross - fee, 2)
            bal = round(max(5.0, bal + net), 2)
            busy_until = exit_time
            trades.append(outcome)
            
        wins = trades.count("TP_HIT")
        bes = trades.count("BE_SAVE")
        losses = trades.count("SL_HIT")
        return {
            "entry_type": entry_type,
            "final_balance": bal,
            "trades": len(trades),
            "wins": wins,
            "bes": bes,
            "losses": losses,
            "win_rate": (wins + bes) / len(trades) * 100 if trades else 0,
            "same_bar_conflicts": same_bar_conflicts
        }

    # Audit 1: Same bar SL first (Pessimistic)
    res_pess = run_sim("MT", same_bar_sl_first=True, add_slippage_pct=0.0005)
    # Audit 2: Market Order on Candle Close (Confirmed Wick)
    res_mkt = run_sim("MARKET_CLOSE", same_bar_sl_first=True, add_slippage_pct=0.0005)
    
    print("\n================ AUDIT VERIFICATION RESULTS ================")
    print(f"1. PESSIMISTIC AUDIT (Limit MT + Same-Bar SL Priority + Slippage):")
    print(f"   Final Balance: ${res_pess['final_balance']} | Trades: {res_pess['trades']} (W:{res_pess['wins']}, BE:{res_pess['bes']}, L:{res_pess['losses']})")
    print(f"   Effective Win Rate: {res_pess['win_rate']:.2f}% | Same-Bar Conflicts: {res_pess['same_bar_conflicts']}")
    print(f"\n2. MARKET ORDER ON CLOSE AUDIT (Wait for candle close confirmation):")
    print(f"   Final Balance: ${res_mkt['final_balance']} | Trades: {res_mkt['trades']} (W:{res_mkt['wins']}, BE:{res_mkt['bes']}, L:{res_mkt['losses']})")
    print(f"   Effective Win Rate: {res_mkt['win_rate']:.2f}% | Same-Bar Conflicts: {res_mkt['same_bar_conflicts']}")
    print("============================================================\n")

if __name__ == "__main__":
    asyncio.run(run_pessimistic_and_realistic_audit())
