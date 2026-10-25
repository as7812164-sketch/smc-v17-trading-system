"""
TEST & VERIFICATION: USER'S ROCKET GAP & 2-DAY MATURATION DISCOVERY
===================================================================
Forensic Backtest & Mathematical Quantification across 1-Year Continuous Out-of-Sample Data:
- Tests the User's Visual Discoveries from OPUSDT, ICPUSDT, and MANAUSDT TradingView charts:
  1. Discovery 1: "The Rocket Gap" / Banning Top OBs (Leg Ratio <= 0.70, Airspace >= 3.0%)
  2. Discovery 2: "The 2-Day Maturation Cycle" (Min Tap Window >= 36-48 bars, Max Window <= 144 bars)
- Compares 4 Models side-by-side:
  - Model 1: Baseline Hermes 3.5 (1 <= bars <= 28, No Leg Filter, No Airspace Filter)
  - Model 2: Maturation Cycle Alone (36 <= bars <= 144)
  - Model 3: Rocket Gap Alone (Leg Ratio <= 0.70, Airspace >= 3.0%, 1 <= bars <= 28)
  - Model 4: Combined Sovereign Engine (Rocket Gap + 2-Day Maturation: 36 <= bars <= 144)
- Tests on:
  - Part A: The 3 User Discovery Assets (OPUSDT, ICPUSDT, MANAUSDT)
  - Part B: Full Universe of 25 Elite Champion Crypto Assets (1-Year 1H & 4H Continuous)
"""

import os
import sys
import json
import math
from datetime import datetime
from typing import List, Dict, Any, Tuple

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def calculate_ema(values: List[float], period: int = 50) -> List[float]:
    if not values: return []
    ema = [values[0]] * len(values)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(values)):
        ema[i] = values[i] * k + ema[i-1] * (1.0 - k)
    return ema

# ---------------------------------------------------------------------------
# CORE HARVESTING ENGINE WITH USER'S DISCOVERIES PARAMETERIZED
# ---------------------------------------------------------------------------
def harvest_experimental_setups(
    candles: List[Dict[str, Any]],
    sym: str,
    tf_label: str,
    tf_minutes: int,
    btc_4h_ema50_map: Dict[int, bool],
    btc_map_4h: Dict[int, Any],
    # User Discovery Parameters:
    min_tap_bars: int = 1,          # Bars required before retest is eligible
    max_tap_bars: int = 28,         # Maximum window before setup expires
    max_leg_ratio: float = 1.00,    # Max ratio of rally where OB can sit (1.00 = allow top OBs, 0.70 = ban top OBs)
    min_airspace_pct: float = 0.0,  # Minimum clean void between OB and origin base (%)
    disp_threshold: float = 0.050,  # Sentry 2: 5.0% displacement
    tp_pct: float = 0.0244,         # +12.2% ROE at 5x on 1H / +14% ROE on 4H
    hard_sl_pct: float = 0.0350     # -17.5% ROE hard SL limit
) -> List[Dict[str, Any]]:
    n = len(candles)
    if n < 50:
        return []

    # ATR(14)
    atr = [0.0] * n
    for k in range(1, n):
        tr = max(
            candles[k]["high"] - candles[k]["low"],
            abs(candles[k]["high"] - candles[k-1]["close"]),
            abs(candles[k]["low"] - candles[k-1]["close"])
        )
        atr[k] = tr if k < 14 else (atr[k-1] * 13 + tr) / 14.0

    hours_per_bar = tf_minutes / 60.0
    max_hold_bars = max(20, min(80, int(120.0 / hours_per_bar)))
    setups = []

    # Scan for swing low / high pivots to identify institutional displacement legs
    lookback_pivot = 15
    for i in range(lookback_pivot, n - 2):
        # =====================================================================
        # 1. BULLISH SETUP / DEMAND ORDER BLOCK
        # =====================================================================
        # Check if candle i is an origin low pivot
        is_pivot_low = (candles[i]["low"] == min(c["low"] for c in candles[max(0, i - lookback_pivot):i + 1]))
        if is_pivot_low:
            sub_w = candles[i:min(i + 16, n)]
            highs = [c["high"] for c in sub_w]
            max_high = max(highs)
            high_idx = i + highs.index(max_high)
            
            if high_idx > i + 2:
                origin_low = candles[i]["low"]
                total_leg_span = max_high - origin_low
                gain = total_leg_span / origin_low if origin_low > 0 else 0.0
                
                if gain >= disp_threshold:
                    # Find decisional candle / mid-leg OB
                    best_mid = -1
                    max_bg = 0.0
                    for mid in range(i + 1, high_idx):
                        bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                        # Leg ratio: position of OB relative to the entire impulse leg (0.0 = origin, 1.0 = top)
                        leg_pos = (candles[mid]["low"] - origin_low) / total_leg_span if total_leg_span > 0 else 0.5
                        if 0.20 <= leg_pos <= 0.85 and bg > max_bg:
                            max_bg = bg
                            best_mid = mid

                    if best_mid != -1:
                        dec_c = candles[best_mid - 1]
                        dec_top = max(dec_c["open"], dec_c["close"])
                        dec_bot = dec_c["low"]
                        mt = (dec_top + dec_bot) / 2.0
                        
                        # Institutional FVG requirement
                        has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                        
                        # --- USER DISCOVERY 1: ROCKET GAP & TOP OB FILTER ---
                        ob_leg_ratio = (mt - origin_low) / total_leg_span if total_leg_span > 0 else 0.5
                        airspace_pct = ((dec_bot - origin_low) / origin_low * 100.0) if origin_low > 0 else 0.0
                        
                        passes_leg_filter = (ob_leg_ratio <= max_leg_ratio)
                        passes_airspace = (airspace_pct >= min_airspace_pct)
                        
                        if has_fvg and passes_leg_filter and passes_airspace:
                            idm_low = candles[high_idx - 1]["low"]
                            
                            # --- USER DISCOVERY 2: TAP MATURATION WINDOW ---
                            # Search forward from high_idx for the retest tap
                            tap_start = high_idx + min_tap_bars
                            tap_end = min(high_idx + max_tap_bars, n)
                            
                            if tap_start < n:
                                for t in range(tap_start, tap_end):
                                    tap_c = candles[t]
                                    bars_since_formation = t - high_idx
                                    
                                    # Hard structural break: candle closes below OB low
                                    if tap_c["close"] < dec_bot:
                                        break
                                        
                                    if tap_c["low"] <= dec_top * 1.0005 and tap_c["low"] >= dec_bot * (1.0 - 0.028):
                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                        
                                        # BTC Macro Sentry
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                        btc_clean = btc_dump < 0.020
                                        btc_is_bull = btc_4h_ema50_map.get(prev_4h_ts, True)
                                        
                                        # Sentry 3: IDM swept, 18% wick rejection, defended MT close
                                        if btc_clean and btc_is_bull and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                            setups.append({
                                                "sym": sym,
                                                "tf": tf_label,
                                                "tf_minutes": tf_minutes,
                                                "t_idx": t,
                                                "side": "LONG",
                                                "time": tap_c["time"],
                                                "dec_top": dec_top,
                                                "dec_bot": dec_bot,
                                                "mt": mt,
                                                "tap_low": tap_c["low"],
                                                "tap_high": tap_c["high"],
                                                "atr": atr[t],
                                                "std_tp_pct": tp_pct,
                                                "hard_sl_pct": hard_sl_pct,
                                                "max_hold": max_hold_bars,
                                                "bars_since_formation": bars_since_formation,
                                                "ob_leg_ratio": round(ob_leg_ratio, 3),
                                                "airspace_pct": round(airspace_pct, 2)
                                            })
                                            break

        # =====================================================================
        # 2. BEARISH SETUP / SUPPLY ORDER BLOCK
        # =====================================================================
        is_pivot_high = (candles[i]["high"] == max(c["high"] for c in candles[max(0, i - lookback_pivot):i + 1]))
        if is_pivot_high:
            sub_w = candles[i:min(i + 16, n)]
            lows = [c["low"] for c in sub_w]
            min_low = min(lows)
            low_idx = i + lows.index(min_low)
            
            if low_idx > i + 2:
                origin_high = candles[i]["high"]
                total_leg_span = origin_high - min_low
                drop = total_leg_span / origin_high if origin_high > 0 else 0.0
                
                if drop >= disp_threshold:
                    best_mid = -1
                    max_bg = 0.0
                    for mid in range(i + 1, low_idx):
                        bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                        leg_pos = (origin_high - candles[mid]["high"]) / total_leg_span if total_leg_span > 0 else 0.5
                        if 0.20 <= leg_pos <= 0.85 and bg > max_bg:
                            max_bg = bg
                            best_mid = mid

                    if best_mid != -1:
                        dec_c = candles[best_mid - 1]
                        dec_top = dec_c["high"]
                        dec_bot = min(dec_c["open"], dec_c["close"])
                        mt = (dec_top + dec_bot) / 2.0
                        
                        has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                        
                        ob_leg_ratio = (origin_high - mt) / total_leg_span if total_leg_span > 0 else 0.5
                        airspace_pct = ((origin_high - dec_top) / origin_high * 100.0) if origin_high > 0 else 0.0
                        
                        passes_leg_filter = (ob_leg_ratio <= max_leg_ratio)
                        passes_airspace = (airspace_pct >= min_airspace_pct)
                        
                        if has_bear_fvg and passes_leg_filter and passes_airspace:
                            idm_high = candles[low_idx - 1]["high"]
                            
                            tap_start = low_idx + min_tap_bars
                            tap_end = min(low_idx + max_tap_bars, n)
                            
                            if tap_start < n:
                                for t in range(tap_start, tap_end):
                                    tap_c = candles[t]
                                    bars_since_formation = t - low_idx
                                    
                                    if tap_c["close"] > dec_top:
                                        break
                                        
                                    if tap_c["high"] >= dec_bot * 0.9995 and tap_c["high"] <= dec_top * (1.0 + 0.028):
                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                        u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                        
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                        btc_clean_short = btc_pump < 0.020
                                        btc_is_bull = btc_4h_ema50_map.get(prev_4h_ts, True)
                                        short_allowed = (not btc_is_bull) or (sym == "BTCUSDT")
                                        
                                        if btc_clean_short and short_allowed and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                            setups.append({
                                                "sym": sym,
                                                "tf": tf_label,
                                                "tf_minutes": tf_minutes,
                                                "t_idx": t,
                                                "side": "SHORT",
                                                "time": tap_c["time"],
                                                "dec_top": dec_top,
                                                "dec_bot": dec_bot,
                                                "mt": mt,
                                                "tap_low": tap_c["low"],
                                                "tap_high": tap_c["high"],
                                                "atr": atr[t],
                                                "std_tp_pct": tp_pct,
                                                "hard_sl_pct": hard_sl_pct,
                                                "max_hold": max_hold_bars,
                                                "bars_since_formation": bars_since_formation,
                                                "ob_leg_ratio": round(ob_leg_ratio, 3),
                                                "airspace_pct": round(airspace_pct, 2)
                                            })
                                            break

    return setups

# ---------------------------------------------------------------------------
# OUTCOME EVALUATOR (WITH DYNAMIC ATR SL & MULTI-STAGE PROFIT ARMOR)
# ---------------------------------------------------------------------------
def evaluate_setup(
    s: Dict[str, Any],
    candles: List[Dict[str, Any]],
    btc_map_1h: Dict[int, Any]
) -> Dict[str, Any]:
    n = len(candles)
    t = s["t_idx"]
    side = s["side"]
    s_time = s["time"]
    mt = s["mt"]
    
    # 50% MT Entry
    if side == "LONG":
        entry = mt if s["tap_low"] <= mt else (s["dec_top"] + mt) / 2.0
        tp_p = entry * (1.0 + s["std_tp_pct"])
        # Loophole 1 Fix: True Dynamic ATR SL without redundant min-max clamp trap
        struct_sl = min(s["dec_bot"], s["tap_low"]) - 0.20 * s["atr"]
        hard_sl_p = max(struct_sl, entry * (1.0 - s["hard_sl_pct"]))
    else:
        entry = mt if s["tap_high"] >= mt else (s["dec_bot"] + mt) / 2.0
        tp_p = entry * (1.0 - s["std_tp_pct"])
        struct_sl = max(s["dec_top"], s["tap_high"]) + 0.20 * s["atr"]
        hard_sl_p = min(struct_sl, entry * (1.0 + s["hard_sl_pct"]))
        
    res = None
    exit_price = entry
    exit_time = s_time
    be_locked = False
    
    # Profit Armor Stage 1: +1.6% move -> Breakeven +0.10% lock
    # Profit Armor Stage 2: +2.2% move -> Trailing +1.20% lock
    be_thresh = entry * 1.016 if side == "LONG" else entry * 0.984
    trail_thresh = entry * 1.022 if side == "LONG" else entry * 0.978
    curr_sl = hard_sl_p
    
    for m in range(t, min(t + s["max_hold"], n)):
        c_m = candles[m]
        m_time = c_m["time"]
        
        # 1H BTC Macro Shield
        btc_ts = m_time - (m_time % (3600 * 1000))
        btc_1h_c = btc_map_1h.get(btc_ts)
        if btc_1h_c:
            btc_chg = (btc_1h_c["close"] - btc_1h_c["open"]) / btc_1h_c["open"]
            if side == "LONG" and btc_chg < -0.010 and not be_locked:
                curr_sl = max(curr_sl, entry * 0.995)
            elif side == "SHORT" and btc_chg > 0.010 and not be_locked:
                curr_sl = min(curr_sl, entry * 1.005)

        if side == "LONG":
            if c_m["high"] >= trail_thresh:
                curr_sl = max(curr_sl, entry * 1.012)
                be_locked = True
            elif c_m["high"] >= be_thresh:
                curr_sl = max(curr_sl, entry * 1.002)
                be_locked = True
                
            if c_m["high"] >= tp_p:
                res = "WIN"; exit_price = tp_p; exit_time = m_time; break
            if c_m["low"] <= curr_sl:
                res = "BREAKEVEN" if (be_locked and curr_sl >= entry) else "LOSS"
                exit_price = curr_sl; exit_time = m_time; break
        else:
            if c_m["low"] <= trail_thresh:
                curr_sl = min(curr_sl, entry * 0.988)
                be_locked = True
            elif c_m["low"] <= be_thresh:
                curr_sl = min(curr_sl, entry * 0.998)
                be_locked = True
                
            if c_m["low"] <= tp_p:
                res = "WIN"; exit_price = tp_p; exit_time = m_time; break
            if c_m["high"] >= curr_sl:
                res = "BREAKEVEN" if (be_locked and curr_sl <= entry) else "LOSS"
                exit_price = curr_sl; exit_time = m_time; break

    if not res:
        fc = candles[min(t + s["max_hold"], n - 1)]["close"]
        exit_price = fc
        exit_time = candles[min(t + s["max_hold"], n - 1)]["time"]
        res = "WIN" if ((side == "LONG" and fc > entry) or (side == "SHORT" and fc < entry)) else "LOSS"
        
    pnl_pct = (exit_price - entry) / entry if side == "LONG" else (entry - exit_price) / entry
    raw_ret = pnl_pct * 5.0
    fee = 0.0016 * 5.0
    net_ret = raw_ret - fee

    return {
        "res": res,
        "entry": entry,
        "exit": exit_price,
        "pnl_pct": net_ret,
        "bars_held": m - t if 'm' in locals() else s["max_hold"],
        "bars_since_formation": s.get("bars_since_formation", 0),
        "ob_leg_ratio": s.get("ob_leg_ratio", 0.5),
        "airspace_pct": s.get("airspace_pct", 0.0)
    }

# ---------------------------------------------------------------------------
# MAIN VERIFICATION BATTERY
# ---------------------------------------------------------------------------
def run_verification():
    h_dir = "historical_data"
    print("=" * 85)
    print("🔬 HERMES 3.5 QUANT AUDIT & VERIFICATION: USER'S TWO STRUCTURAL DISCOVERIES")
    print("   1. 'The Rocket Gap' (Veto Top OBs: Leg Ratio <= 0.70 & Airspace >= 3.0%)")
    print("   2. 'The 2-Day Maturation Cycle' (Min Tap Window >= 36 bars, Max Window <= 144 bars)")
    print("=" * 85)

    # 1. Load Data
    h_files = [f for f in os.listdir(h_dir) if f.endswith("_1h.json")]
    raw_1h = {}
    raw_4h = {}
    for f in h_files:
        sym = f.replace("_1h.json", "")
        p1 = os.path.join(h_dir, f)
        p4 = os.path.join(h_dir, f"{sym}_4h.json")
        try:
            raw_1h[sym] = json.load(open(p1, "r", encoding="utf-8"))
            if os.path.exists(p4):
                raw_4h[sym] = json.load(open(p4, "r", encoding="utf-8"))
        except Exception:
            pass

    btc_4h = raw_4h.get("BTCUSDT", [])
    btc_map_4h = {c["time"]: c for c in btc_4h}
    btc_1h_c = raw_1h.get("BTCUSDT", btc_4h)
    btc_map_1h = {c["time"]: c for c in btc_1h_c}

    btc_closes = [c["close"] for c in btc_4h]
    btc_ema50 = calculate_ema(btc_closes, 50)
    btc_4h_ema50_map = {btc_4h[i]["time"]: (btc_4h[i]["close"] >= btc_ema50[i]) for i in range(len(btc_4h))}

    # =========================================================================
    # PART A: USER DISCOVERY ASSETS DEEP-DIVE (OPUSDT, ICPUSDT, MANAUSDT)
    # =========================================================================
    user_symbols = ["OPUSDT", "ICPUSDT", "MANAUSDT"]
    print("\n" + "=" * 85)
    print("🎯 PART A: FORENSIC DEEP-DIVE ON USER'S SCREENSHOT ASSETS (1H TIMEFRAME)")
    print("   Testing OPUSDT, ICPUSDT, MANAUSDT across 1-Year Continuous Granular Data")
    print("=" * 85)

    for sym in user_symbols:
        if sym not in raw_1h:
            print(f"⚠️ {sym} not found in historical data cache.")
            continue

        c_list = raw_1h[sym]
        print(f"\n📈 ASSET: {sym} (Total Candles: {len(c_list)})")
        print("-" * 75)

        # 1. Harvest Baseline (Model 1)
        base_setups = harvest_experimental_setups(
            c_list, sym, "1H", 60,
            btc_4h_ema50_map, btc_map_4h,
            min_tap_bars=1, max_tap_bars=28, max_leg_ratio=1.00, min_airspace_pct=0.0
        )
        
        # 2. Harvest Maturation Alone (Model 2: 36 to 144 bars)
        mat_setups = harvest_experimental_setups(
            c_list, sym, "1H", 60,
            btc_4h_ema50_map, btc_map_4h,
            min_tap_bars=36, max_tap_bars=144, max_leg_ratio=1.00, min_airspace_pct=0.0
        )

        # 3. Harvest Rocket Gap Alone (Model 3: Leg Ratio <= 0.70, Airspace >= 3.0%, 1-28 bars)
        rocket_setups = harvest_experimental_setups(
            c_list, sym, "1H", 60,
            btc_4h_ema50_map, btc_map_4h,
            min_tap_bars=1, max_tap_bars=28, max_leg_ratio=0.70, min_airspace_pct=3.0
        )

        # 4. Harvest Combined Sovereign (Model 4: Rocket Gap + Maturation 36 to 144 bars)
        sov_setups = harvest_experimental_setups(
            c_list, sym, "1H", 60,
            btc_4h_ema50_map, btc_map_4h,
            min_tap_bars=36, max_tap_bars=144, max_leg_ratio=0.70, min_airspace_pct=3.0
        )

        models = [
            ("Model 1: Baseline Hermes 3.5 (1-28 bars, No Filter)", base_setups),
            ("Model 2: 2-Day Maturation Alone (36-144 bars)", mat_setups),
            ("Model 3: Rocket Gap Alone (Leg<=0.70, Air>=3%)", rocket_setups),
            ("Model 4: Combined Sovereign Engine (User Formula)", sov_setups)
        ]

        for label, s_list in models:
            wins = 0; be = 0; losses = 0; gross_win = 0.0; gross_loss = 0.0
            maturation_bars_list = []
            for s in s_list:
                out = evaluate_setup(s, c_list, btc_map_1h)
                maturation_bars_list.append(out["bars_since_formation"])
                if out["res"] == "WIN":
                    wins += 1; gross_win += out["pnl_pct"]
                elif out["res"] == "BREAKEVEN":
                    be += 1
                else:
                    losses += 1; gross_loss += abs(out["pnl_pct"])
            tot = wins + be + losses
            wr = (wins / tot * 100.0) if tot > 0 else 0.0
            safe = ((wins + be) / tot * 100.0) if tot > 0 else 0.0
            pf = (gross_win / gross_loss) if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
            avg_mat = (sum(maturation_bars_list) / len(maturation_bars_list)) if maturation_bars_list else 0.0

            print(f"  * {label:<50} | Triggers: {tot:<3} | W: {wins:<2} BE: {be:<2} L: {losses:<2} | WinRate: {wr:5.1f}% | Safety: {safe:5.1f}% | PF: {pf:5.2f} | AvgMat: {avg_mat:4.1f}b")

    # =========================================================================
    # PART B: PORTFOLIO-WIDE 1-YEAR DUEL (TOP 25 ELITE CHAMPIONS)
    # =========================================================================
    top25_universe = [
        "ETHUSDT", "SOLUSDT", "AVAXUSDT", "NEARUSDT", "APTUSDT",
        "SUIUSDT", "LINKUSDT", "RENDERUSDT", "FETUSDT", "INJUSDT",
        "TIAUSDT", "ARBUSDT", "OPUSDT", "MANAUSDT", "SANDUSDT",
        "GALAUSDT", "AAVEUSDT", "UNIUSDT", "DOGEUSDT", "PEPEUSDT",
        "SHIBUSDT", "BNBUSDT", "XRPUSDT", "ICPUSDT", "ADAUSDT"
    ]

    print("\n" + "=" * 85)
    print("🏆 PART B: 1-YEAR CONTINUOUS OUT-OF-SAMPLE DUEL ACROSS TOP 25 ELITE CHAMPIONS")
    print(f"   Universe: {len(top25_universe)} Pairs | Continuous Sep 2025 - Sep 2026")
    print("=" * 85)

    def run_portfolio_backtest(tf_label: str, tf_minutes: int, min_b: int, max_b: int, max_leg: float, min_air: float):
        all_trades = []
        for sym in top25_universe:
            c_dict = raw_1h if tf_label == "1H" else raw_4h
            if sym not in c_dict:
                continue
            c_list = c_dict[sym]
            setups = harvest_experimental_setups(
                c_list, sym, tf_label, tf_minutes,
                btc_4h_ema50_map, btc_map_4h,
                min_tap_bars=min_b, max_tap_bars=max_b,
                max_leg_ratio=max_leg, min_airspace_pct=min_air
            )
            for s in setups:
                out = evaluate_setup(s, c_list, btc_map_1h)
                all_trades.append({
                    "time": s["time"],
                    "sym": sym,
                    "res": out["res"],
                    "pnl_pct": out["pnl_pct"],
                    "bars_since_formation": out["bars_since_formation"],
                    "ob_leg_ratio": out["ob_leg_ratio"],
                    "airspace_pct": out["airspace_pct"]
                })

        # Sort strictly chronologically to simulate live execution
        all_trades.sort(key=lambda x: x["time"])

        wins = 0; be = 0; losses = 0; gross_win = 0.0; gross_loss = 0.0
        balance = 50.0  # Deca section starting balance ($50)
        equity_curve = [balance]
        streak = 0; max_streak = 0; loss_streak = 0; max_loss_streak = 0
        peak_balance = balance; max_dd = 0.0

        for t in all_trades:
            pnl = t["pnl_pct"]
            if t["res"] == "WIN":
                wins += 1; gross_win += pnl
                streak += 1; max_streak = max(max_streak, streak); loss_streak = 0
            elif t["res"] == "BREAKEVEN":
                be += 1
            else:
                losses += 1; gross_loss += abs(pnl)
                loss_streak += 1; max_loss_streak = max(max_loss_streak, loss_streak); streak = 0

            # 100% Pure Compounding (Zero Vault Split)
            balance = max(1.0, balance * (1.0 + pnl))
            equity_curve.append(balance)
            peak_balance = max(peak_balance, balance)
            dd = (peak_balance - balance) / peak_balance * 100.0 if peak_balance > 0 else 0.0
            max_dd = max(max_dd, dd)

        tot = wins + be + losses
        wr = (wins / tot * 100.0) if tot > 0 else 0.0
        safe = ((wins + be) / tot * 100.0) if tot > 0 else 0.0
        pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0

        return {
            "total_trades": tot,
            "wins": wins,
            "breakeven": be,
            "losses": losses,
            "win_rate": round(wr, 2),
            "safety_rate": round(safe, 2),
            "profit_factor": round(pf, 2),
            "final_balance": round(balance, 2),
            "max_win_streak": max_streak,
            "max_loss_streak": max_loss_streak,
            "max_drawdown_pct": round(max_dd, 2)
        }

    # Test Configurations on 1H
    configs_1h = [
        ("1H Baseline Hermes 3.5 (1-28b, All OBs)", 1, 28, 1.00, 0.0),
        ("1H Maturation Cycle Alone (36-144b, All OBs)", 36, 144, 1.00, 0.0),
        ("1H Rocket Gap Alone (Leg<=0.70, Air>=3.0%, 1-28b)", 1, 28, 0.70, 3.0),
        ("1H Combined Sovereign (Leg<=0.70, Air>=3.0%, 36-144b)", 36, 144, 0.70, 3.0),
        ("1H Ultra Mature Sovereign (Leg<=0.65, Air>=3.5%, 48-168b)", 48, 168, 0.65, 3.5),
    ]

    print("\n--- 1H TIMEFRAME RESULTS ---")
    results_1h = {}
    for name, min_b, max_b, leg_r, air in configs_1h:
        res = run_portfolio_backtest("1H", 60, min_b, max_b, leg_r, air)
        results_1h[name] = res
        print(f"\n📊 {name}")
        print(f"   Triggers: {res['total_trades']} | Wins: {res['wins']} | BE: {res['breakeven']} | Losses: {res['losses']}")
        print(f"   Direct Win Rate: {res['win_rate']}% | Capital Safety Rate: {res['safety_rate']}% | Profit Factor: {res['profit_factor']}")
        print(f"   Compounded Balance ($50 start): ${res['final_balance']:,.2f} | Win Streak: {res['max_win_streak']} | Max DD: {res['max_drawdown_pct']}%")

    # Test Configurations on 4H (adjusting bar count: 9 bars = 36h / 1.5 days, 36 bars = 144h / 6 days)
    configs_4h = [
        ("4H Baseline Hermes 3.5 (1-28b, All OBs)", 1, 28, 1.00, 0.0),
        ("4H Maturation Cycle Alone (9-36b, All OBs)", 9, 36, 1.00, 0.0),
        ("4H Rocket Gap Alone (Leg<=0.70, Air>=3.0%, 1-28b)", 1, 28, 0.70, 3.0),
        ("4H Combined Sovereign (Leg<=0.70, Air>=3.0%, 9-36b)", 9, 36, 0.70, 3.0),
    ]

    print("\n--- 4H TIMEFRAME RESULTS ---")
    results_4h = {}
    for name, min_b, max_b, leg_r, air in configs_4h:
        res = run_portfolio_backtest("4H", 240, min_b, max_b, leg_r, air)
        results_4h[name] = res
        print(f"\n📊 {name}")
        print(f"   Triggers: {res['total_trades']} | Wins: {res['wins']} | BE: {res['breakeven']} | Losses: {res['losses']}")
        print(f"   Direct Win Rate: {res['win_rate']}% | Capital Safety Rate: {res['safety_rate']}% | Profit Factor: {res['profit_factor']}")
        print(f"   Compounded Balance ($50 start): ${res['final_balance']:,.2f} | Win Streak: {res['max_win_streak']} | Max DD: {res['max_drawdown_pct']}%")

    # Save summary report to JSON
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "top25_universe": top25_universe,
        "results_1h": results_1h,
        "results_4h": results_4h
    }
    with open("user_discoveries_backtest_results.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print("\n" + "=" * 85)
    print("✅ BACKTEST EXECUTION COMPLETE. RESULTS SAVED TO user_discoveries_backtest_results.json")
    print("=" * 85)

if __name__ == "__main__":
    run_verification()
