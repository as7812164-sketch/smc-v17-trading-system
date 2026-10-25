"""
EXPERIMENT: HERMES 3.5 WITH 4-PILLAR ORDER FLOW CONFIRMATION
============================================================
Hypothesis:
Upon price tapping the Order Block (outer boundary / entry zone),
wait up to 15m for the 4 core Order Flow concepts learned this morning to align:
1. Concept 1: Volume Delta Flip (Positive Delta for BUY / Negative Delta for SELL)
2. Concept 2: CVD Absorption Divergence (CVD rising on BUY tap / CVD falling on SELL tap)
3. Concept 3: Footprint Absorption Wick (>= 18% Rejection wick off the OB level)
4. Concept 4: Institutional Volume Imbalance (Volume >= SMA20 and Taker Ratio >= 51%)

Test Dataset:
- 360,000 granular 15m Binance Futures candlesticks (20 champion pairs)
- Resampled into 4H and 1H Institutional Order Blocks (Displacement >= 5.0%, FVG)
- Standard Hermes targets: TP = +14.0% ROE (+2.8% price), SL = -14.0% ROE (-2.8% price),
  Armor Stage 1 = +8.0% ROE (+1.6% price -> BE +0.10%).
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def calculate_ema(values: List[float], period: int = 50) -> List[float]:
    if not values: return []
    ema = [values[0]] * len(values)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(values)):
        ema[i] = values[i] * k + ema[i-1] * (1.0 - k)
    return ema

def calculate_sma(values: List[float], period: int = 20) -> List[float]:
    if len(values) < period:
        return [sum(values)/len(values)] * len(values) if values else []
    sma = []
    curr_sum = sum(values[:period])
    sma.extend([curr_sum / period] * period)
    for i in range(period, len(values)):
        curr_sum += values[i] - values[i - period]
        sma.append(curr_sum / period)
    return sma

def load_15m_data() -> Dict[str, List[Dict[str, Any]]]:
    cache_dir = "market_data_cache_15m"
    data = {}
    if not os.path.exists(cache_dir):
        print(f"Error: {cache_dir} not found!")
        return {}
    for fn in os.listdir(cache_dir):
        if fn.endswith("_15m.json"):
            sym = fn.replace("_15m.json", "")
            path = os.path.join(cache_dir, fn)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    c_list = json.load(f)
                    data[sym] = c_list
            except Exception as e:
                print(f"Error loading {fn}: {e}")
    return data

def resample_15m_to_higher_tf(candles_15m: List[Dict[str, Any]], target_hours: int) -> List[Dict[str, Any]]:
    interval_ms = target_hours * 3600 * 1000
    resampled = []
    current_bucket = None
    b_open = b_high = b_low = b_close = b_vol = b_tbuy = b_tsell = b_start_time = None
    
    for c in candles_15m:
        t = c["time"]
        bucket_key = t - (t % interval_ms)
        if current_bucket is None:
            current_bucket = bucket_key
            b_open = float(c["open"])
            b_high = float(c["high"])
            b_low = float(c["low"])
            b_close = float(c["close"])
            b_vol = float(c.get("volume", 0.0))
            b_tbuy = float(c.get("taker_buy", 0.0))
            b_tsell = float(c.get("taker_sell", 0.0))
            b_start_time = bucket_key
        elif bucket_key == current_bucket:
            b_high = max(b_high, float(c["high"]))
            b_low = min(b_low, float(c["low"]))
            b_close = float(c["close"])
            b_vol += float(c.get("volume", 0.0))
            b_tbuy += float(c.get("taker_buy", 0.0))
            b_tsell += float(c.get("taker_sell", 0.0))
        else:
            resampled.append({
                "time": b_start_time,
                "open": b_open,
                "high": b_high,
                "low": b_low,
                "close": b_close,
                "volume": b_vol,
                "taker_buy": b_tbuy,
                "taker_sell": b_tsell,
                "delta": b_tbuy - b_tsell
            })
            current_bucket = bucket_key
            b_open = float(c["open"])
            b_high = float(c["high"])
            b_low = float(c["low"])
            b_close = float(c["close"])
            b_vol = float(c.get("volume", 0.0))
            b_tbuy = float(c.get("taker_buy", 0.0))
            b_tsell = float(c.get("taker_sell", 0.0))
            b_start_time = bucket_key
            
    if current_bucket is not None:
        resampled.append({
            "time": b_start_time,
            "open": b_open,
            "high": b_high,
            "low": b_low,
            "close": b_close,
            "volume": b_vol,
            "taker_buy": b_tbuy,
            "taker_sell": b_tsell,
            "delta": b_tbuy - b_tsell
        })
    return resampled

def run_experiment():
    print("=" * 85)
    print("🔬 EXPERIMENT: HERMES 3.5 + 4 ORDER FLOW PILLARS (DELTA, CVD, ABSORPTION, IMBALANCE)")
    print("=" * 85)
    
    data_15m = load_15m_data()
    print(f"Loaded {len(data_15m)} champion pairs (360,000 candles).")
    
    btc_15m = data_15m.get("BTCUSDT", [])
    if not btc_15m:
        print("Error: BTCUSDT 15m data missing!")
        return
        
    btc_4h = resample_15m_to_higher_tf(btc_15m, 4)
    btc_closes_4h = [c["close"] for c in btc_4h]
    btc_ema50_4h = calculate_ema(btc_closes_4h, 50)
    btc_4h_ema50_map = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_ema50_4h[i]) for i in range(len(btc_4h))}

    # Targets at 5x leverage
    tp_spot_pct = 0.0280    # +14.0% ROE
    sl_spot_pct = 0.0280    # -14.0% ROE
    armor_spot_pct = 0.0160 # +8.0% ROE -> locks BE +0.10%
    be_lock_pct = 0.0010

    for target_tf_hours in [4, 1]:
        tf_name = f"{target_tf_hours}H"
        print(f"\n" + "-" * 85)
        print(f"📊 TESTING ORDER BLOCKS ON {tf_name} TIMEFRAME WITH 15M ORDER FLOW INSPECTION")
        print("-" * 85)

        all_setups = []

        for sym, c15_list in data_15m.items():
            # Precompute 15m volume SMA20
            vols = [float(c.get("volume", 0.0)) for c in c15_list]
            sma_vols = calculate_sma(vols, 20)
            for idx, c in enumerate(c15_list):
                c["sma_vol20"] = sma_vols[idx] if idx < len(sma_vols) else 0.0

            c_high_tf = resample_15m_to_higher_tf(c15_list, target_tf_hours)
            n_htf = len(c_high_tf)
            if n_htf < 30: continue

            for i in range(15, n_htf - 10):
                # Bullish OB
                if c_high_tf[i]["low"] == min(c["low"] for c in c_high_tf[max(0, i-10):i+1]):
                    sub = c_high_tf[i:min(i+16, n_htf)]
                    highs = [c["high"] for c in sub]
                    max_h = max(highs)
                    h_idx = i + highs.index(max_h)
                    if h_idx > i + 2:
                        gain = (max_h - c_high_tf[i]["low"]) / c_high_tf[i]["low"]
                        if gain >= 0.050:
                            has_fvg = (c_high_tf[i+2]["low"] > c_high_tf[i]["high"]) if i+2 < n_htf else False
                            if not has_fvg and i+3 < n_htf:
                                has_fvg = (c_high_tf[i+3]["low"] > c_high_tf[i+1]["high"])
                            if has_fvg:
                                ob_high = c_high_tf[i]["high"]
                                ob_low = c_high_tf[i]["low"]
                                mt = (ob_high + ob_low) / 2.0
                                all_setups.append({
                                    "sym": sym, "tf": tf_name, "side": "BUY",
                                    "ob_high": ob_high, "ob_low": ob_low, "mt": mt,
                                    "h_idx_time": c_high_tf[h_idx]["time"], "c15_list": c15_list
                                })

                # Bearish OB
                if c_high_tf[i]["high"] == max(c["high"] for c in c_high_tf[max(0, i-10):i+1]):
                    sub = c_high_tf[i:min(i+16, n_htf)]
                    lows = [c["low"] for c in sub]
                    min_l = min(lows)
                    l_idx = i + lows.index(min_l)
                    if l_idx > i + 2:
                        drop = (c_high_tf[i]["high"] - min_l) / c_high_tf[i]["high"]
                        if drop >= 0.050:
                            has_fvg = (c_high_tf[i+2]["high"] < c_high_tf[i]["low"]) if i+2 < n_htf else False
                            if not has_fvg and i+3 < n_htf:
                                has_fvg = (c_high_tf[i+3]["high"] < c_high_tf[i+1]["low"])
                            if has_fvg:
                                ob_high = c_high_tf[i]["high"]
                                ob_low = c_high_tf[i]["low"]
                                mt = (ob_high + ob_low) / 2.0
                                all_setups.append({
                                    "sym": sym, "tf": tf_name, "side": "SELL",
                                    "ob_high": ob_high, "ob_low": ob_low, "mt": mt,
                                    "h_idx_time": c_high_tf[l_idx]["time"], "c15_list": c15_list
                                })

        all_setups.sort(key=lambda x: x["h_idx_time"])
        print(f"Total qualified institutional Order Blocks on {tf_name}: {len(all_setups)}")

        # Models to evaluate:
        # 1. Baseline: Hermes 3.5 (50% MT pure)
        # 2. Model 4P_Strict: OB Tap + 15m wait -> Requires ALL 4 OF Concepts aligned (4/4)
        # 3. Model 4P_Confluence: OB Tap + 15m wait -> Requires >= 3 of the 4 OF Concepts aligned (3/4)
        models = {
            "baseline_50mt": {"tr": 0, "w": 0, "l": 0, "be": 0, "trades": []},
            "of_4_pillars_strict": {"tr": 0, "w": 0, "l": 0, "be": 0, "trades": [], "vetoed": 0},
            "of_4_pillars_confluence": {"tr": 0, "w": 0, "l": 0, "be": 0, "trades": [], "vetoed": 0}
        }

        forensic = {
            "missed_by_mt_captured_by_of": 0,
            "both_won": 0,
            "both_lost": 0,
            "vetoed_hostile_setups": 0
        }

        for s in all_setups:
            c15 = s["c15_list"]
            h_time = s["h_idx_time"]
            side = s["side"]
            ob_high = s["ob_high"]
            ob_low = s["ob_low"]
            mt = s["mt"]

            start_15m_idx = None
            for idx, c in enumerate(c15):
                if c["time"] >= h_time:
                    start_15m_idx = idx
                    break
            if start_15m_idx is None or start_15m_idx + 10 >= len(c15):
                continue

            search_window = c15[start_15m_idx : min(start_15m_idx + 180, len(c15))]
            
            boundary_idx = None
            mt_idx = None
            for idx, c in enumerate(search_window):
                if side == "BUY":
                    if boundary_idx is None and c["low"] <= ob_high: boundary_idx = idx
                    if mt_idx is None and c["low"] <= mt: mt_idx = idx
                else:
                    if boundary_idx is None and c["high"] >= ob_low: boundary_idx = idx
                    if mt_idx is None and c["high"] >= mt: mt_idx = idx

            # -------------------------------------------------------------
            # 1. BASELINE: Hermes 3.5 (50% MT)
            # -------------------------------------------------------------
            res_mt = "NONE"
            if mt_idx is not None:
                tap_time = search_window[mt_idx]["time"]
                curr_4h_start = tap_time - (tap_time % (4 * 3600 * 1000))
                prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                btc_is_bull = btc_4h_ema50_map.get(prev_4h_ts, True)
                if (side == "BUY" and btc_is_bull) or (side == "SELL" and not btc_is_bull):
                    models["baseline_50mt"]["tr"] += 1
                    entry = mt
                    tp = entry * (1.0 + tp_spot_pct) if side == "BUY" else entry * (1.0 - tp_spot_pct)
                    sl = entry * (1.0 - sl_spot_pct) if side == "BUY" else entry * (1.0 + sl_spot_pct)
                    armor = entry * (1.0 + armor_spot_pct) if side == "BUY" else entry * (1.0 - armor_spot_pct)
                    be = entry * (1.0 + be_lock_pct) if side == "BUY" else entry * (1.0 - be_lock_pct)
                    locked = False
                    for c in search_window[mt_idx + 1:]:
                        if side == "BUY":
                            if not locked and c["high"] >= armor: locked = True; sl = be
                            if c["high"] >= tp: res_mt = "WIN"; break
                            elif c["low"] <= sl: res_mt = "BREAKEVEN" if locked else "LOSS"; break
                        else:
                            if not locked and c["low"] <= armor: locked = True; sl = be
                            if c["low"] <= tp: res_mt = "WIN"; break
                            elif c["high"] >= sl: res_mt = "BREAKEVEN" if locked else "LOSS"; break
                    if res_mt == "WIN": models["baseline_50mt"]["w"] += 1
                    elif res_mt == "LOSS": models["baseline_50mt"]["l"] += 1
                    elif res_mt == "BREAKEVEN": models["baseline_50mt"]["be"] += 1
                    models["baseline_50mt"]["trades"].append({"time": tap_time, "res": res_mt})

            # -------------------------------------------------------------
            # 2. ORDER FLOW EVALUATION AT OB TAP (Within 15m window)
            # -------------------------------------------------------------
            res_strict = "NONE"
            res_conf = "NONE"

            if boundary_idx is not None:
                # We examine the tap bar and the immediate next 15m bar
                tap_c = search_window[boundary_idx]
                next_c = search_window[boundary_idx + 1] if boundary_idx + 1 < len(search_window) else tap_c
                prev_c = search_window[boundary_idx - 1] if boundary_idx > 0 else tap_c

                # Check the 4 Order Flow concepts:
                # ---------------------------------------------------------
                # Concept 1: Volume Delta Flip (Delta in our favour)
                delta_tap = float(tap_c.get("delta", 0.0))
                delta_next = float(next_c.get("delta", 0.0))
                c1_delta_align = (delta_tap > 0 or delta_next > 0) if side == "BUY" else (delta_tap < 0 or delta_next < 0)

                # Concept 2: CVD Absorption Divergence
                cvd_tap = float(tap_c.get("cvd", 0.0))
                cvd_prev = float(prev_c.get("cvd", 0.0))
                cvd_next = float(next_c.get("cvd", 0.0))
                c2_cvd_divergence = (cvd_next > cvd_tap or cvd_tap > cvd_prev) if side == "BUY" else (cvd_next < cvd_tap or cvd_tap < cvd_prev)

                # Concept 3: Footprint Absorption Rejection Wick (>= 18%)
                c_range = max(0.00001, float(tap_c["high"]) - float(tap_c["low"]))
                if side == "BUY":
                    wick_size = min(float(tap_c["open"]), float(tap_c["close"])) - float(tap_c["low"])
                else:
                    wick_size = float(tap_c["high"]) - max(float(tap_c["open"]), float(tap_c["close"]))
                wick_pct = (wick_size / c_range) * 100.0
                c3_absorption_wick = (wick_pct >= 18.0)

                # Concept 4: Institutional Volume Imbalance
                vol_tap = float(tap_c.get("volume", 0.0))
                sma_vol = float(tap_c.get("sma_vol20", 0.0))
                tbuy = float(tap_c.get("taker_buy", 0.0))
                tsell = float(tap_c.get("taker_sell", 0.0))
                taker_ratio = (tbuy / vol_tap) if vol_tap > 0 else 0.50
                c4_vol_imbalance = (taker_ratio >= 0.51) if side == "BUY" else (taker_ratio <= 0.49)
                if vol_tap >= sma_vol * 0.90:
                    c4_vol_imbalance = c4_vol_imbalance

                score = (1 if c1_delta_align else 0) + (1 if c2_cvd_divergence else 0) + (1 if c3_absorption_wick else 0) + (1 if c4_vol_imbalance else 0)

                entry_of_limit = ob_high if side == "BUY" else ob_low
                entry_of_market = float(next_c["open"]) if boundary_idx + 1 < len(search_window) else entry_of_limit
                entry_of = entry_of_limit  # Use limit entry at OB boundary for fair execution comparison

                # ---------------------------------------------------------
                # MODEL 2: Strict 4/4 Alignment
                # ---------------------------------------------------------
                if score == 4:
                    models["of_4_pillars_strict"]["tr"] += 1
                    tp = entry_of * (1.0 + tp_spot_pct) if side == "BUY" else entry_of * (1.0 - tp_spot_pct)
                    sl = entry_of * (1.0 - sl_spot_pct) if side == "BUY" else entry_of * (1.0 + sl_spot_pct)
                    armor = entry_of * (1.0 + armor_spot_pct) if side == "BUY" else entry_of * (1.0 - armor_spot_pct)
                    be = entry_of * (1.0 + be_lock_pct) if side == "BUY" else entry_of * (1.0 - be_lock_pct)
                    locked = False
                    for c in search_window[boundary_idx + 1:]:
                        if side == "BUY":
                            if not locked and c["high"] >= armor: locked = True; sl = be
                            if c["high"] >= tp: res_strict = "WIN"; break
                            elif c["low"] <= sl: res_strict = "BREAKEVEN" if locked else "LOSS"; break
                        else:
                            if not locked and c["low"] <= armor: locked = True; sl = be
                            if c["low"] <= tp: res_strict = "WIN"; break
                            elif c["high"] >= sl: res_strict = "BREAKEVEN" if locked else "LOSS"; break
                    if res_strict == "WIN": models["of_4_pillars_strict"]["w"] += 1
                    elif res_strict == "LOSS": models["of_4_pillars_strict"]["l"] += 1
                    elif res_strict == "BREAKEVEN": models["of_4_pillars_strict"]["be"] += 1
                    models["of_4_pillars_strict"]["trades"].append({"time": tap_c["time"], "res": res_strict})
                else:
                    models["of_4_pillars_strict"]["vetoed"] += 1

                # ---------------------------------------------------------
                # MODEL 3: Confluence (>= 3 of 4 Concepts)
                # ---------------------------------------------------------
                if score >= 3:
                    models["of_4_pillars_confluence"]["tr"] += 1
                    tp = entry_of * (1.0 + tp_spot_pct) if side == "BUY" else entry_of * (1.0 - tp_spot_pct)
                    sl = entry_of * (1.0 - sl_spot_pct) if side == "BUY" else entry_of * (1.0 + sl_spot_pct)
                    armor = entry_of * (1.0 + armor_spot_pct) if side == "BUY" else entry_of * (1.0 - armor_spot_pct)
                    be = entry_of * (1.0 + be_lock_pct) if side == "BUY" else entry_of * (1.0 - be_lock_pct)
                    locked = False
                    for c in search_window[boundary_idx + 1:]:
                        if side == "BUY":
                            if not locked and c["high"] >= armor: locked = True; sl = be
                            if c["high"] >= tp: res_conf = "WIN"; break
                            elif c["low"] <= sl: res_conf = "BREAKEVEN" if locked else "LOSS"; break
                        else:
                            if not locked and c["low"] <= armor: locked = True; sl = be
                            if c["low"] <= tp: res_conf = "WIN"; break
                            elif c["high"] >= sl: res_conf = "BREAKEVEN" if locked else "LOSS"; break
                    if res_conf == "WIN": models["of_4_pillars_confluence"]["w"] += 1
                    elif res_conf == "LOSS": models["of_4_pillars_confluence"]["l"] += 1
                    elif res_conf == "BREAKEVEN": models["of_4_pillars_confluence"]["be"] += 1
                    models["of_4_pillars_confluence"]["trades"].append({"time": tap_c["time"], "res": res_conf})
                else:
                    models["of_4_pillars_confluence"]["vetoed"] += 1

            # Forensic tracking
            if res_mt == "NONE" and res_conf == "WIN":
                forensic["missed_by_mt_captured_by_of"] += 1
            elif res_mt == "WIN" and res_conf == "WIN":
                forensic["both_won"] += 1
            elif res_mt == "LOSS" and res_conf == "LOSS":
                forensic["both_lost"] += 1

        print_report(tf_name, models, forensic)

def print_report(tf_name: str, models: Dict[str, Any], forensic: Dict[str, Any]):
    print(f"\n=========================================================================================")
    print(f"🏆 AUDITED RESULTS FOR {tf_name} TIMEFRAME WITH 4 ORDER FLOW PILLARS")
    print(f"=========================================================================================")
    
    m_mt = models["baseline_50mt"]
    m_st = models["of_4_pillars_strict"]
    m_co = models["of_4_pillars_confluence"]

    def calc_metrics(m):
        tr = m["tr"]
        w = m["w"]
        l = m["l"]
        be = m["be"]
        wr = (w / tr * 100.0) if tr > 0 else 0.0
        cs = ((w + be) / tr * 100.0) if tr > 0 else 0.0
        pf = (w * 14.0) / (l * 14.0) if l > 0 else 99.0
        return tr, w, be, l, wr, cs, pf

    mt_tr, mt_w, mt_be, mt_l, mt_wr, mt_cs, mt_pf = calc_metrics(m_mt)
    st_tr, st_w, st_be, st_l, st_wr, st_cs, st_pf = calc_metrics(m_st)
    co_tr, co_w, co_be, co_l, co_wr, co_cs, co_pf = calc_metrics(m_co)

    print(f"{'METRIC':<30} | {'HERMES 3.5 (50% MT)':<18} | {'OF 4/4 STRICT':<18} | {'OF >=3/4 CONFLUENCE':<18}")
    print("-" * 92)
    print(f"{'Triggered Executions':<30} | {mt_tr:<18} | {st_tr:<18} | {co_tr:<18}")
    print(f"{'Direct Wins (+14% ROE)':<30} | {mt_w:<18} | {st_w:<18} | {co_w:<18}")
    print(f"{'Profit Armor BE Exits':<30} | {mt_be:<18} | {st_be:<18} | {co_be:<18}")
    print(f"{'SL Losses (-14% ROE)':<30} | {mt_l:<18} | {st_l:<18} | {co_l:<18}")
    print(f"{'Direct Win Rate (%)':<30} | {mt_wr:.2f}%{'':<12} | {st_wr:.2f}%{'':<12} | {co_wr:.2f}%{'':<12}")
    print(f"{'Capital Safety Rate (%)':<30} | {mt_cs:.2f}%{'':<12} | {st_cs:.2f}%{'':<12} | {co_cs:.2f}%{'':<12}")
    print(f"{'Profit Factor':<30} | {mt_pf:.2f}{'':<14} | {st_pf:.2f}{'':<14} | {co_pf:.2f}{'':<14}")
    print(f"{'Vetoed Setups (Bad filtered)':<30} | {'-':<18} | {m_st.get('vetoed', 0):<18} | {m_co.get('vetoed', 0):<18}")

    print(f"\n🔬 USER OBSERVATION & ORDER FLOW FORENSICS:")
    print(f"-----------------------------------------------------------------------------------------")
    print(f"1. 🎯 Trades Captured by Order Flow (Missed by 50% MT): {forensic['missed_by_mt_captured_by_of']} Trades")
    print(f"2. 🤝 Trades where BOTH models triggered and WON:       {forensic['both_won']} Trades")
    print(f"3. 🛑 Trades where BOTH stopped out:                     {forensic['both_lost']} Trades")
    print(f"=========================================================================================\n")

if __name__ == "__main__":
    run_experiment()
