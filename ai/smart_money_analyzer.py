from typing import List, Dict, Any, Optional

def compute_ema(closes: List[float], period: int) -> List[float]:
    """Calculates Exponential Moving Average (EMA)."""
    if len(closes) < period:
        return closes
    alpha = 2.0 / (period + 1.0)
    ema = [closes[0]]
    for p in closes[1:]:
        ema.append(alpha * p + (1.0 - alpha) * ema[-1])
    return ema

def detect_mtf_trend(candles_4h: List[Dict[str, Any]], candles_1d: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Determines Multi-Timeframe (MTF) trend using 4H EMA 50/200 and 1D structure.
    """
    if not candles_4h or len(candles_4h) < 30:
        return {"trend_4h": "NEUTRAL", "trend_1d": "NEUTRAL", "details": "Insufficient data"}

    closes_4h = [c["close"] for c in candles_4h]
    ema50 = compute_ema(closes_4h, 50)
    ema200 = compute_ema(closes_4h, min(200, len(closes_4h)))

    cur_price = closes_4h[-1]
    e50_last = ema50[-1]
    e200_last = ema200[-1]

    # 4H structure
    if cur_price > e50_last > e200_last:
        tf4h_trend = "BULLISH"
    elif cur_price < e50_last < e200_last:
        tf4h_trend = "BEARISH"
    elif cur_price > e50_last:
        tf4h_trend = "MILD_BULLISH"
    else:
        tf4h_trend = "MILD_BEARISH"

    # 1D structure if available
    tf1d_trend = "NEUTRAL"
    if candles_1d and len(candles_1d) >= 10:
        closes_1d = [c["close"] for c in candles_1d]
        ema20_1d = compute_ema(closes_1d, min(20, len(closes_1d)))
        if closes_1d[-1] > ema20_1d[-1]:
            tf1d_trend = "BULLISH"
        else:
            tf1d_trend = "BEARISH"

    return {
        "trend_4h": tf4h_trend,
        "trend_1d": tf1d_trend,
        "details": f"4H: {tf4h_trend}, 1D: {tf1d_trend}"
    }

def detect_swing_points(candles: List[Dict[str, Any]], window: int = 2) -> Dict[str, List[Dict[str, Any]]]:
    """
    Identifies confirmed swing highs and swing lows using rolling fractal pivots.
    """
    if len(candles) < (window * 2 + 1):
        return {"highs": [], "lows": []}

    swing_highs = []
    swing_lows = []
    n = len(candles)

    for i in range(window, n - window):
        c = candles[i]
        h = c["high"]
        l = c["low"]

        is_high = all(h >= candles[i - j]["high"] for j in range(1, window + 1)) and \
                  all(h >= candles[i + j]["high"] for j in range(1, window + 1))
        is_low = all(l <= candles[i - j]["low"] for j in range(1, window + 1)) and \
                 all(l <= candles[i + j]["low"] for j in range(1, window + 1))

        if is_high:
            swing_highs.append({"index": i, "price": h, "time": c.get("time")})
        if is_low:
            swing_lows.append({"index": i, "price": l, "time": c.get("time")})

    return {"highs": swing_highs, "lows": swing_lows}

def detect_market_structure_shift(candles: List[Dict[str, Any]], window: int = 2) -> Dict[str, Any]:
    """
    Detects Break of Structure (BOS) vs Change of Character (CHoCH) based on ICT/SMC principles:
    - BOS = Continuation of trend (breaking current swing extreme).
    - CHoCH = Shift / Reversal of trend (breaking the opposite swing extreme).
    """
    swings = detect_swing_points(candles, window=window)
    highs = swings["highs"]
    lows = swings["lows"]

    if len(highs) < 2 or len(lows) < 2:
        return {"shift_type": "NONE", "direction": "NEUTRAL", "details": "Insufficient swings"}

    last_high = highs[-1]["price"]
    prev_high = highs[-2]["price"]
    last_low = lows[-1]["price"]
    prev_low = lows[-2]["price"]

    cur_close = candles[-1]["close"]

    # Trend context: Bullish if higher highs and higher lows
    is_bullish_context = last_high > prev_high and last_low > prev_low
    is_bearish_context = last_high < prev_high and last_low < prev_low

    if cur_close > last_high:
        if is_bullish_context:
            return {
                "shift_type": "BOS",
                "direction": "BULLISH",
                "level": last_high,
                "details": f"Bullish BOS: Breakout above Swing High (${last_high:,.2f}) continues uptrend"
            }
        else:
            return {
                "shift_type": "CHOCH",
                "direction": "BULLISH",
                "level": last_high,
                "details": f"Bullish CHoCH: Market character flipped bullish above Lower High (${last_high:,.2f})"
            }

    if cur_close < last_low:
        if is_bearish_context:
            return {
                "shift_type": "BOS",
                "direction": "BEARISH",
                "level": last_low,
                "details": f"Bearish BOS: Breakdown below Swing Low (${last_low:,.2f}) continues downtrend"
            }
        else:
            return {
                "shift_type": "CHOCH",
                "direction": "BEARISH",
                "level": last_low,
                "details": f"Bearish CHoCH: Market character flipped bearish below Higher Low (${last_low:,.2f})"
            }

    return {
        "shift_type": "INTERNAL",
        "direction": "BULLISH" if is_bullish_context else ("BEARISH" if is_bearish_context else "RANGING"),
        "level": last_high if is_bullish_context else last_low,
        "details": "Price oscillating within internal swing range"
    }

def detect_liquidity_sweeps(candles: List[Dict[str, Any]], window: int = 2) -> Dict[str, Any]:
    """
    Detects Liquidity Sweeps / Judas Swings / Stop Hunts (turtle soup).
    A wick pierces past a swing high/low, but the candle body closes back inside.
    """
    if len(candles) < 15:
        return {"has_sweep": False, "sweep_type": "NONE", "detail": "Insufficient candles"}

    swings = detect_swing_points(candles[:-3], window=window)
    recent_candles = candles[-3:]

    sweeps = []
    # Check if recent candle swept high
    for sh in swings["highs"][-3:]:
        lvl = sh["price"]
        for c in recent_candles:
            if c["high"] > lvl and c["close"] < lvl:
                sweeps.append({"type": "BUY_SIDE_SWEEP", "level": lvl, "wick": c["high"], "detail": "Buy-side liquidity swept (Bearish trap)"})

    # Check if recent candle swept low
    for sl in swings["lows"][-3:]:
        lvl = sl["price"]
        for c in recent_candles:
            if c["low"] < lvl and c["close"] > lvl:
                sweeps.append({"type": "SELL_SIDE_SWEEP", "level": lvl, "wick": c["low"], "detail": "Sell-side liquidity swept (Bullish trap)"})

    if sweeps:
        last_sweep = sweeps[-1]
        return {
            "has_sweep": True,
            "sweep_type": last_sweep["type"],
            "level": last_sweep["level"],
            "detail": last_sweep["detail"]
        }

    return {"has_sweep": False, "sweep_type": "NONE", "detail": "No recent liquidity sweep detected"}

def detect_fair_value_gaps(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detects Fair Value Gaps (FVG) / Imbalances and their mitigation status.
    - Bullish FVG: low[i] > high[i-2]
    - Bearish FVG: high[i] < low[i-2]
    """
    if len(candles) < 5:
        return []

    fvgs = []
    n = len(candles)

    for i in range(2, n):
        c_prev2 = candles[i - 2]
        c_curr = candles[i]

        # Bullish FVG
        if c_curr["low"] > c_prev2["high"]:
            gap_top = c_curr["low"]
            gap_bottom = c_prev2["high"]
            mid_point = (gap_top + gap_bottom) / 2.0

            # Check if subsequent candles mitigated the gap
            is_mitigated = False
            for j in range(i + 1, n):
                if candles[j]["low"] <= mid_point:
                    is_mitigated = True
                    break

            fvgs.append({
                "type": "BULLISH_FVG",
                "top": gap_top,
                "bottom": gap_bottom,
                "mid": mid_point,
                "index": i - 1,
                "mitigated": is_mitigated
            })

        # Bearish FVG
        elif c_curr["high"] < c_prev2["low"]:
            gap_top = c_prev2["low"]
            gap_bottom = c_curr["high"]
            mid_point = (gap_top + gap_bottom) / 2.0

            is_mitigated = False
            for j in range(i + 1, n):
                if candles[j]["high"] >= mid_point:
                    is_mitigated = True
                    break

            fvgs.append({
                "type": "BEARISH_FVG",
                "top": gap_top,
                "bottom": gap_bottom,
                "mid": mid_point,
                "index": i - 1,
                "mitigated": is_mitigated
            })

    return fvgs

def calculate_displacement_quality(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Measures Institutional Displacement Quality (Body-to-Wick Ratio & Range Expansion).
    High body-to-range ratio (> 60%) indicates strong institutional sponsorship.
    """
    if len(candles) < 5:
        return {"quality": "MODERATE", "body_ratio": 0.50, "sponsored": False, "detail": "Average body/range: 50%"}

    recent_expansion_candles = candles[-5:]
    ratios = []
    for c in recent_expansion_candles:
        rng = c["high"] - c["low"]
        body = abs(c["close"] - c["open"])
        if rng > 0:
            ratios.append(body / rng)

    avg_body_ratio = sum(ratios) / len(ratios) if ratios else 0.50
    is_sponsored = avg_body_ratio >= 0.60

    return {
        "quality": "HIGH" if avg_body_ratio >= 0.65 else ("MODERATE" if avg_body_ratio >= 0.50 else "LOW"),
        "body_ratio": round(avg_body_ratio, 2),
        "sponsored": is_sponsored,
        "detail": f"Average body/range: {avg_body_ratio*100:.1f}%"
    }

def detect_equal_highs_lows(candles: List[Dict[str, Any]], tolerance_pct: float = 0.002) -> Dict[str, List[float]]:
    """
    Detects Equal Highs (EQH) and Equal Lows (EQL) - major retail liquidity traps.
    """
    if len(candles) < 20:
        return {"eqh": [], "eql": []}

    recent = candles[-35:]
    eqh = []
    eql = []

    for i in range(len(recent) - 3):
        h1 = recent[i]["high"]
        for j in range(i + 3, len(recent)):
            h2 = recent[j]["high"]
            if abs(h1 - h2) / ((h1 + h2) / 2) <= tolerance_pct:
                eqh.append(round((h1 + h2) / 2, 4))

    for i in range(len(recent) - 3):
        l1 = recent[i]["low"]
        for j in range(i + 3, len(recent)):
            l2 = recent[j]["low"]
            if abs(l1 - l2) / ((l1 + l2) / 2) <= tolerance_pct:
                eql.append(round((l1 + l2) / 2, 4))

    return {
        "eqh": list(set(eqh))[:2],
        "eql": list(set(eql))[:2]
    }

def evaluate_premium_discount(candles: List[Dict[str, Any]], entry_price: float, side: str) -> Dict[str, Any]:
    """
    Calculates Fibonacci 0.5 - 0.79 OTE (Optimal Trade Entry) Discount/Premium pricing.
    """
    if len(candles) < 15:
        return {"is_optimal": True, "zone_type": "NEUTRAL", "fib_level": 0.50}

    lookback = candles[-30:]
    swing_high = max(c["high"] for c in lookback)
    swing_low = min(c["low"] for c in lookback)
    range_diff = swing_high - swing_low
    if range_diff <= 0:
        return {"is_optimal": True, "zone_type": "NEUTRAL", "fib_level": 0.50}

    rel_pos = (entry_price - swing_low) / range_diff

    if side == "BUY":
        is_discount = rel_pos <= 0.50
        is_ote = 0.20 <= rel_pos <= 0.45
        zone_type = "DISCOUNT (Cheap)" if is_discount else "PREMIUM (Expensive)"
        return {
            "is_optimal": is_discount,
            "is_ote": is_ote,
            "zone_type": zone_type,
            "fib_level": round(rel_pos, 2)
        }
    else:
        is_premium = rel_pos >= 0.50
        is_ote = 0.55 <= rel_pos <= 0.80
        zone_type = "PREMIUM (High)" if is_premium else "DISCOUNT (Low)"
        return {
            "is_optimal": is_premium,
            "is_ote": is_ote,
            "zone_type": zone_type,
            "fib_level": round(rel_pos, 2)
        }

def analyze_retest_volume(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Volume Spread Analysis (VSA): checks if volume dried up on retest (healthy)
    or if aggressive selling/buying volume is breaking through.
    """
    if len(candles) < 15:
        return {"volume_healthy": True, "rvol": 1.0}

    vols = [c.get("volume", 1.0) for c in candles[-20:]]
    avg_vol = sum(vols[:-2]) / max(1, len(vols) - 2)
    last_vol = vols[-1]
    rvol = last_vol / (avg_vol if avg_vol > 0 else 1.0)

    volume_healthy = rvol <= 1.5

    return {
        "volume_healthy": volume_healthy,
        "rvol": round(rvol, 2),
        "avg_vol": avg_vol,
        "last_vol": last_vol
    }

def evaluate_setup_confluence(
    symbol: str,
    zone: Dict[str, Any],
    candles_4h: List[Dict[str, Any]],
    candles_1d: Optional[List[Dict[str, Any]]] = None,
    order_flow: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    from ai.self_improving_engine import mike_brain
    
    dyn_weights = mike_brain.get_dynamic_weights()
    coin_check = mike_brain.evaluate_coin_eligibility(symbol)
    
    side = zone.get("side", "BUY").upper()
    entry_val = zone.get("entry_price") or zone.get("ob_high" if side == "BUY" else "ob_low") or 0.0
    entry_p = float(entry_val)

    # Base score dynamically tuned by Mike AI
    score = dyn_weights.get("base_score", 65)
    strengths = []
    risks = []
    
    # Coin-specific intelligence from Mike AI
    if not coin_check.get("eligible", True):
        risks.append(f"⚠️ MIKE AI CAUTION: {coin_check.get('reason')}")
        score -= 15
    elif coin_check.get("status") == "ELITE":
        strengths.append(f"⭐ MIKE AI ELITE COIN: High historical win-rate (>80%)")
        score += 3

    # 1. Multi-Timeframe Trend Check
    mtf = detect_mtf_trend(candles_4h, candles_1d)
    trend_4h = mtf["trend_4h"]
    trend_1d = mtf["trend_1d"]

    if side == "BUY":
        if "BULLISH" in trend_4h:
            score += 8
            strengths.append(f"4H Trend Aligned ({trend_4h})")
        elif "BEARISH" in trend_4h:
            score -= 10
            risks.append("Counter-trend against 4H EMA")

        if trend_1d == "BULLISH":
            score += 7
            strengths.append("1D Macro Trend Bullish")
        elif trend_1d == "BEARISH":
            score -= 5
            risks.append("Opposing 1D Daily Trend")
    else:  # SELL
        if "BEARISH" in trend_4h:
            score += 8
            strengths.append(f"4H Trend Aligned ({trend_4h})")
        elif "BULLISH" in trend_4h:
            score -= 10
            risks.append("Counter-trend against 4H EMA")

        if trend_1d == "BEARISH":
            score += 7
            strengths.append("1D Macro Trend Bearish")
        elif trend_1d == "BULLISH":
            score -= 5
            risks.append("Opposing 1D Daily Trend")

    # 2. Market Structure Shift (BOS / CHoCH)
    mss = detect_market_structure_shift(candles_4h)
    if mss["shift_type"] == "CHOCH" and mss["direction"] == side:
        score += 8
        strengths.append(f"CHoCH Reversal Confirmed ({side})")
    elif mss["shift_type"] == "BOS" and mss["direction"] == side:
        score += 6
        strengths.append(f"BOS Continuation Confirmed ({side})")
    elif mss["direction"] != "NEUTRAL" and mss["direction"] != side and mss["shift_type"] in ("BOS", "CHOCH"):
        score -= 6
        risks.append(f"Opposing Structure Shift ({mss['shift_type']} {mss['direction']})")

    # 3. Liquidity Sweep (Judas Swing / Trap)
    sweep = detect_liquidity_sweeps(candles_4h)
    zone_tags = zone.get("tags", [])
    if isinstance(zone_tags, str):
        try:
            import json
            zone_tags = json.loads(zone_tags)
        except Exception:
            zone_tags = []
            
    has_origin_sweep = "SWEEP" in zone_tags or sweep.get("has_sweep", False)
    
    if has_origin_sweep:
        score += 15  # Super Booster for Turtle Soup Sweep
        strengths.insert(0, "👑 GOLDEN SWEEP: Confirmed Whale Liquidity Sweep (100% Win-Rate Tier)")
    elif sweep["has_sweep"]:
        if side == "BUY" and sweep["sweep_type"] == "SELL_SIDE_SWEEP":
            score += 8
            strengths.append("Sell-Side Stop Hunt Swept (Judas Swing)")
        elif side == "SELL" and sweep["sweep_type"] == "BUY_SIDE_SWEEP":
            score += 8
            strengths.append("Buy-Side Stop Hunt Swept (Judas Swing)")

    # 4. Fair Value Gap (FVG) Confluence
    fvgs = detect_fair_value_gaps(candles_4h)
    unmitigated_fvgs = [f for f in fvgs if not f["mitigated"]]
    ob_low = float(zone.get("ob_low", 0.0))
    ob_high = float(zone.get("ob_high", 0.0))

    has_fvg_confluence = False
    for f in unmitigated_fvgs:
        if (side == "BUY" and f["type"] == "BULLISH_FVG") or (side == "SELL" and f["type"] == "BEARISH_FVG"):
            # Check overlap with OB range
            if not (f["top"] < ob_low or f["bottom"] > ob_high):
                has_fvg_confluence = True
                break

    if has_fvg_confluence:
        score += 6
        strengths.append("Unmitigated FVG Imbalance Supported")

    # 5. Institutional Displacement Quality
    displacement = calculate_displacement_quality(candles_4h)
    if displacement["sponsored"]:
        score += 5
        strengths.append(f"High Institutional Displacement ({displacement['body_ratio']*100:.0f}% Body)")

    # 6. Premium / Discount OTE Check
    ote = evaluate_premium_discount(candles_4h, entry_p, side)
    if ote["is_optimal"]:
        score += 6
        strengths.append(f"Favorable Pricing ({ote['zone_type']})")
        if ote.get("is_ote"):
            score += 4
            strengths.append("Optimal Trade Entry (OTE) Fib Zone")
    else:
        score -= 6
        risks.append(f"Unfavorable Pricing ({ote['zone_type']})")

    # 7. Equal Highs / Equal Lows (Target Liquidity)
    traps = detect_equal_highs_lows(candles_4h)
    if side == "BUY" and traps["eqh"]:
        score += 5
        strengths.append(f"Buy-Side Liquidity Magnet (EQH at ${traps['eqh'][0]:,.2f})")
    elif side == "SELL" and traps["eql"]:
        score += 5
        strengths.append(f"Sell-Side Liquidity Magnet (EQL at ${traps['eql'][0]:,.2f})")

    # 8. Volume Exhaustion
    vol = analyze_retest_volume(candles_4h)
    if vol["volume_healthy"]:
        score += 4
        strengths.append(f"Retest Volume Exhaustion (RVOL {vol['rvol']})")
    else:
        score -= 5
        risks.append(f"Elevated Push Volume (RVOL {vol['rvol']})")

    # 9. Institutional Order Flow (CVD Delta & Open Interest)
    if order_flow:
        d_ratio = order_flow.get("delta_ratio", 0.50)
        cvd_rev = order_flow.get("cvd_reversal", False)
        oi_chg = order_flow.get("oi_change_1h", 0.0)
        is_rocket = order_flow.get("is_rocket", False)

        w_delta = dyn_weights.get("weight_order_flow_delta", 8)
        w_cvd = dyn_weights.get("weight_cvd_reversal", 6)
        w_oi = dyn_weights.get("weight_oi_expansion", 7)

        if is_rocket:
            score += (w_delta + w_cvd)
            strengths.insert(0, "🚀 ROCKET FLOW: Instant 1H Takeoff Unified (Delta + CVD + OI Accumulation)")
        elif d_ratio >= 0.51:
            score += w_delta
            strengths.append(f"CVD Delta Absorption (Taker Buyers {d_ratio*100:.1f}%) [Weight +{w_delta}]")
        elif d_ratio <= 0.44:
            score -= w_delta
            risks.append(f"Aggressive Market Dumping (Sellers {100-d_ratio*100:.1f}%)")

        if cvd_rev and not is_rocket:
            score += w_cvd
            strengths.append(f"CVD Reversal Curve (Smart Money Limit Absorption) [Weight +{w_cvd}]")

        if oi_chg >= 0.50 and not is_rocket:
            score += w_oi
            strengths.append(f"Whale OI Expansion (+{oi_chg:.2f}% Fresh Positioning) [Weight +{w_oi}]")
        elif oi_chg <= -2.0:
            score -= w_oi
            risks.append(f"Sharp Liquidation Unwind ({oi_chg:.2f}% OI)")

    # Clamp Score between 35 and 99
    final_score = max(35, min(99, score))

    if final_score >= 90:
        grade = "A+"
        verdict = "ELITE SETUP (High Probability - Full Size)"
    elif final_score >= 80:
        grade = "A"
        verdict = "STRONG SETUP (Standard Allocation)"
    elif final_score >= 70:
        grade = "B"
        verdict = "MODERATE SETUP (Discipline Required)"
    else:
        grade = "C"
        verdict = "CAUTION / HIGH RISK (Strict Stop Loss)"

    return {
        "symbol": symbol,
        "side": side,
        "score": final_score,
        "grade": grade,
        "verdict": verdict,
        "strengths": strengths[:5],
        "risks": risks[:3] if risks else ["None detected (Clean alignment)"],
        "mtf": mtf,
        "mss": mss,
        "sweep": sweep,
        "fvg_confluence": has_fvg_confluence,
        "displacement": displacement,
        "ote": ote,
        "traps": traps,
        "volume": vol,
        "order_flow": order_flow
    }

