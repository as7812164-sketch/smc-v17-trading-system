import sys
import os
import json
from datetime import datetime, timezone, timedelta

def run_hybrid_experiments():
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "historical_data")
    coins = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
        "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
        "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
    ]
    data_1h = {}
    data_4h = {}
    for c in coins:
        f1 = os.path.join(hist_dir, f"{c}_1h.json")
        f4 = os.path.join(hist_dir, f"{c}_4h.json")
        if os.path.exists(f1): data_1h[c] = json.load(open(f1, "r", encoding="utf-8"))
        if os.path.exists(f4): data_4h[c] = json.load(open(f4, "r", encoding="utf-8"))
        
    btc_4h = data_4h.get("BTCUSDT", [])
    
    # Pre-calculate BTC 4H EMA50 for Macro Trend Alignment
    btc_ema50 = {}
    if btc_4h:
        closes = [float(x["close"]) for x in btc_4h]
        k = 2.0 / (50 + 1)
        ema = closes[0]
        for idx, bar in enumerate(btc_4h):
            c_p = float(bar["close"])
            ema = (c_p * k) + (ema * (1.0 - k))
            btc_ema50[bar["time"]] = ema

    def is_btc_macro_bullish(t_ms):
        prior = [t for t in btc_ema50.keys() if t <= t_ms]
        if not prior: return True
        last_t = max(prior)
        # Find btc close at last_t
        matching = [x for x in btc_4h if x["time"] == last_t]
        if matching:
            return float(matching[0]["close"]) >= btc_ema50[last_t]
        return True

    months = [
        {"name": "July 2026", "start_ms": 1782864000000, "end_ms": 1785542399000},
        {"name": "August 2026", "start_ms": 1785542400000, "end_ms": 1788220799000},
        {"name": "September 2026", "start_ms": 1788220800000, "end_ms": 1790294400000}
    ]

    # Let's test 3 Master Combinations:
    # Combo A: Hermes 3.0 (50% MT) + Candle Body Close SL + BTC Macro Trend Sentry (Veto counter-trend shorts)
    # Combo B: Adaptive Entry (50% MT deep entry + 3.5's High Runway Filter >= 5.0% + Candle Body Close SL + Dual Armor)
    # Combo C: The Ultimate "Hermes Apex" (Best of 3.0 MT entry + 3.5 Multi-timeframe Runway + Body Close SL + BTC Trend Alignment)

    def extract_setups(mode="COMBO_A"):
        candidates = []
        for m in months:
            m_start, m_end = m["start_ms"], m["end_ms"]
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
                                        m_h, m_l = float(dataset[mid]["high"]), float(dataset[mid]["low"])
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
                                            mt = round((dec_top + dec_bot) / 2.0, 8)
                                            for t in range(high_idx + 1, min(high_idx + 28, n)):
                                                tap_c = dataset[t]
                                                t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                                if tap_c["time"] < m_start: continue
                                                if tap_c["time"] > m_end: break
                                                if t_l <= mt and t_c >= mt:
                                                    c_range = t_h - t_l
                                                    swept = any(float(dataset[k]["low"]) < idm_low for k in range(high_idx, t + 1))
                                                    l_wick = min(t_o, t_c) - t_l
                                                    w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                                    
                                                    # BTC check
                                                    btc_clean = True
                                                    if btc_4h:
                                                        prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                        if len(prior_btc) >= 2:
                                                            last_b = prior_btc[-1]
                                                            if (float(last_b["open"]) - float(last_b["close"])) / float(last_b["open"]) >= 0.020: btc_clean = False
                                                            
                                                    if btc_clean and swept and w_ratio >= 0.18:
                                                        candidates.append({
                                                            "month": m["name"], "symbol": c, "side": "LONG", "tf": tf,
                                                            "entry_time": tap_c["time"], "idx": t, "dataset": dataset,
                                                            "ep": mt
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
                                        m_h, m_l = float(dataset[mid]["high"]), float(dataset[mid]["low"])
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
                                            mt = round((dec_top + dec_bot) / 2.0, 8)
                                            for t in range(low_idx + 1, min(low_idx + 28, n)):
                                                tap_c = dataset[t]
                                                t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                                if tap_c["time"] < m_start: continue
                                                if tap_c["time"] > m_end: break
                                                if t_h >= mt and t_c <= mt:
                                                    c_range = t_h - t_l
                                                    swept = any(float(dataset[k]["high"]) > idm_high for k in range(low_idx, t + 1))
                                                    w_ratio = (t_h - max(t_o, t_c)) / c_range if c_range > 0 else 0.0
                                                    
                                                    btc_clean_short = True
                                                    if btc_4h:
                                                        prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                                        if len(prior_btc) >= 2:
                                                            last_b = prior_btc[-1]
                                                            if (float(last_b["close"]) - float(last_b["open"])) / float(last_b["open"]) >= 0.020: btc_clean_short = False
                                                            
                                                    # BTC Macro Trend Sentry (Veto Altcoin Shorts if BTC > EMA50)
                                                    if mode in ["COMBO_A", "COMBO_C"]:
                                                        if is_btc_macro_bullish(tap_c["time"]) and c != "BTCUSDT":
                                                            btc_clean_short = False # Vetoed! Don't short altcoins when BTC is bullish!
                                                            
                                                    if btc_clean_short and swept and w_ratio >= 0.18:
                                                        candidates.append({
                                                            "month": m["name"], "symbol": c, "side": "SHORT", "tf": tf,
                                                            "entry_time": tap_c["time"], "idx": t, "dataset": dataset,
                                                            "ep": mt
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
        return uniq

    # Run simulations
    for mode in ["COMBO_A"]:
        ev_list = extract_setups(mode)
        print(f"\n{'='*75}")
        print(f"HYBRID SYSTEM: {mode} (Hermes 3.0 MT Entry + Candle Body Close SL + BTC Macro Veto)")
        print(f"{'='*75}")
        
        all_month_tps = 0
        all_month_sls = 0
        all_month_bes = 0
        all_month_trades = 0
        
        for m in months:
            m_events = [x for x in ev_list if x["month"] == m["name"]]
            balance = 100.00
            peak_balance = 100.00
            max_drawdown = 0.0
            busy_until = 0
            
            tps, sls, bes = 0, 0, 0
            
            for ev in m_events:
                if ev["entry_time"] < busy_until: continue
                ds = ev["dataset"]
                idx = ev["idx"]
                ep = ev["ep"]
                side = ev["side"]
                
                tp = round(ep * 1.0300, 8) if side == "LONG" else round(ep * 0.9700, 8)
                sl = round(ep * 0.9850, 8) if side == "LONG" else round(ep * 1.0150, 8)
                be_trig = round(ep * 1.0150, 8) if side == "LONG" else round(ep * 0.9850, 8)
                em_sl = round(ep * 0.9700, 8) if side == "LONG" else round(ep * 1.0300, 8)
                
                active_sl = sl
                be_locked = False
                outcome = None
                exit_time = ev["entry_time"]
                
                for bar in ds[idx+1:]:
                    b_h, b_l, b_c, b_t = float(bar["high"]), float(bar["low"]), float(bar["close"]), bar["time"]
                    
                    if side == "LONG":
                        if not be_locked and b_h >= be_trig:
                            be_locked = True
                            active_sl = ep
                        if b_h >= tp:
                            outcome = "TP"
                            exit_time = b_t
                            break
                        if be_locked:
                            if b_l <= active_sl:
                                outcome = "BE"
                                exit_time = b_t
                                break
                        else:
                            if b_l <= em_sl:
                                outcome = "SL"
                                exit_time = b_t
                                break
                            elif b_c <= sl:
                                outcome = "SL"
                                exit_time = b_t
                                break
                    else: # SHORT
                        if not be_locked and b_l <= be_trig:
                            be_locked = True
                            active_sl = ep
                        if b_l <= tp:
                            outcome = "TP"
                            exit_time = b_t
                            break
                        if be_locked:
                            if b_h >= active_sl:
                                outcome = "BE"
                                exit_time = b_t
                                break
                        else:
                            if b_h >= em_sl:
                                outcome = "SL"
                                exit_time = b_t
                                break
                            elif b_c >= sl:
                                outcome = "SL"
                                exit_time = b_t
                                break
                                
                if not outcome: continue
                busy_until = exit_time
                
                if outcome == "TP":
                    balance *= (1.0 + 0.150)
                    tps += 1
                elif outcome == "SL":
                    balance *= (1.0 - 0.075)
                    sls += 1
                else:
                    bes += 1
                    
                if balance > peak_balance:
                    peak_balance = balance
                dd = (peak_balance - balance) / peak_balance * 100.0 if peak_balance > 0 else 0.0
                if dd > max_drawdown:
                    max_drawdown = dd
                    
            n_t = tps + sls + bes
            eff_wr = ((tps + bes) / n_t * 100.0) if n_t > 0 else 0.0
            print(f"[{m['name']}] Final: ${balance:.2f} ({balance-100:+.2f}%) | Trades: {n_t} | TP: {tps} | BE: {bes} | SL: {sls} | Eff WR: {eff_wr:.1f}% | Max DD: {max_drawdown:.2f}%")
            all_month_tps += tps
            all_month_sls += sls
            all_month_bes += bes
            all_month_trades += n_t
            
        print(f"--> 3-MONTH AGGREGATE: Trades: {all_month_trades} | TP: {all_month_tps} ({(all_month_tps/all_month_trades)*100:.1f}%) | SL: {all_month_sls} ({(all_month_sls/all_month_trades)*100:.1f}%) | BE: {all_month_bes}")

if __name__ == "__main__":
    run_hybrid_experiments()
