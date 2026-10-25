import time
from typing import List, Dict, Any, Optional, Tuple
from config import (
    AVG_BODY_PERIOD,
    DISPLACEMENT_MULT,
    ORIGIN_LOOKBACK,
    QUALIFICATION_PCT,
    TP_PCT,
    SL_PCT,
    MAX_ACTIVE_BUY_PER_COIN,
    MAX_ACTIVE_SELL_PER_COIN
)
from engine.tags import extract_soft_tags

def calculate_avg_body(candles: List[Dict[str, Any]], end_idx: int, period: int = AVG_BODY_PERIOD) -> float:
    """Calculate average candle body size |Close - Open| over `period` candles preceding end_idx."""
    if end_idx < period:
        return 0.0
    bodies = [abs(candles[i]["close"] - candles[i]["open"]) for i in range(end_idx - period, end_idx)]
    return sum(bodies) / len(bodies) if bodies else 0.0

def find_true_origin(candles: List[Dict[str, Any]], disp_idx: int, side: str) -> Optional[int]:
    """
    Find latest opposite-color candle within previous 6 candles from displacement candle.
    BUY: latest red candle (close < open)
    SELL: latest green candle (close > open)
    """
    start_lookback = max(0, disp_idx - ORIGIN_LOOKBACK)
    for i in range(disp_idx - 1, start_lookback - 1, -1):
        c = candles[i]
        if side == "BUY" and c["close"] < c["open"]:
            return i
        elif side == "SELL" and c["close"] > c["open"]:
            return i
    return None

def verify_inducement_sweep(candles: List[Dict[str, Any]], origin_idx: int, disp_idx: int, side: str) -> bool:
    """
    Checks if prior retail inducement (IDM) was swept before or at zone formation.
    For BUY: The lowest low of the minor pullback between origin and displacement was swept.
    For SELL: The highest high of the minor pullback was swept.
    """
    if origin_idx < 1 or disp_idx <= origin_idx:
        return False
    if side == "BUY":
        pullback_lows = [candles[i]["low"] for i in range(max(0, origin_idx - 5), origin_idx)]
        if pullback_lows and candles[origin_idx]["low"] < min(pullback_lows):
            return True
    elif side == "SELL":
        pullback_highs = [candles[i]["high"] for i in range(max(0, origin_idx - 5), origin_idx)]
        if pullback_highs and candles[origin_idx]["high"] > max(pullback_highs):
            return True
    return False

def check_btc_alignment(candle_time: int, alt_side: str, btc_candles: Optional[List[Dict[str, Any]]]) -> bool:
    """
    King Bitcoin 3-Tier Regime Shield:
    Disqualifies altcoin entries that oppose Bitcoin aggressive directional momentum
    or when Bitcoin drops > -1.5% in the same 1H candle.
    """
    if not btc_candles:
        return True
    
    btc_c = next((c for c in btc_candles if abs(c["time"] - candle_time) <= 3600000), None)
    if not btc_c:
        return True
    
    # 1. Delta check: If Alt is SELL, BTC must not have aggressive taker buy delta (> +250 BTC)
    btc_delta = btc_c.get("delta", 0.0)
    if alt_side == "SELL" and btc_delta > 250.0:
        return False
    
    # 2. Delta check: If Alt is BUY, BTC must not have aggressive taker sell delta (< -250 BTC)
    if alt_side == "BUY" and btc_delta < -250.0:
        return False
        
    # 3. Velocity Shock Check: BTC 1H drop > 1.5%
    if btc_c.get("open", 0) > 0:
        btc_ret = (btc_c["close"] - btc_c["open"]) / btc_c["open"]
        if alt_side == "BUY" and btc_ret <= -0.015:
            return False
        if alt_side == "SELL" and btc_ret >= 0.015:
            return False
            
    return True

def verify_rejection_wick(candle: Dict[str, Any], side: str, min_wick_pct: float = 0.35) -> bool:
    """
    Confirms that the mitigation candle closed with a sharp rejection wick (>= 35%),
    proving that smart money absorbed all selling/buying immediately.
    """
    total_range = candle.get("high", 0.0) - candle.get("low", 0.0)
    if total_range <= 0:
        return False
    
    if side == "BUY":
        lower_wick = min(candle["open"], candle["close"]) - candle["low"]
        return (lower_wick / total_range) >= min_wick_pct
    else:
        upper_wick = candle["high"] - max(candle["open"], candle["close"])
        return (upper_wick / total_range) >= min_wick_pct

def analyze_candles_smc_v17(symbol: str, candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scans a series of 4H candles according to strict SMC V17 rules.
    Returns detected Order Block zones with their complete lifecycle status:
    - 'QUALIFIED': 7% achieved cleanly, fresh & waiting for first tap.
    - 'ACTIVE': First tap occurred, currently inside trade towards TP/SL.
    - 'TP_HIT': Reached +4% TP.
    - 'SL_HIT': Reached -3% SL.
    - 'INVALIDATED': Retested OB before achieving 7% qualification (permanently invalid).
    """
    n = len(candles)
    if n < AVG_BODY_PERIOD + 2:
        return []

    detected_zones: List[Dict[str, Any]] = []

    # Iterate through candles looking for displacement candidates
    for disp_idx in range(AVG_BODY_PERIOD, n):
        disp_candle = candles[disp_idx]
        avg_body = calculate_avg_body(candles, disp_idx, AVG_BODY_PERIOD)
        if avg_body <= 0:
            continue

        disp_body = abs(disp_candle["close"] - disp_candle["open"])
        is_displacement = disp_body >= (DISPLACEMENT_MULT * avg_body)
        if not is_displacement:
            continue

        # Determine side
        side = None
        if disp_candle["close"] > disp_candle["open"]:
            side = "BUY"
        elif disp_candle["close"] < disp_candle["open"]:
            side = "SELL"
        else:
            continue

        # Find True Origin
        origin_idx = find_true_origin(candles, disp_idx, side)
        if origin_idx is None:
            continue

        origin_candle = candles[origin_idx]
        ob_high = origin_candle["high"]
        ob_low = origin_candle["low"]

        # 7% Qualification target
        if side == "BUY":
            target_7pct = ob_high * (1.0 + QUALIFICATION_PCT)
        else:
            target_7pct = ob_low * (1.0 - QUALIFICATION_PCT)

        # Soft confluence tags
        tags = extract_soft_tags(candles, origin_idx, disp_idx, side)

        # Check qualification and lifecycle across subsequent candles
        is_qualified = False
        qualified_idx = None
        is_invalidated = False
        status = "PENDING"
        entry_idx = None
        entry_price = None
        entry_time = None
        tp_price = None
        sl_price = None

        # Check candles between displacement and current
        # Pre-7% Invalidation Check:
        for scan_idx in range(disp_idx + 1, n):
            c = candles[scan_idx]

            if not is_qualified:
                # Check if price breaks through OB before reaching qualification target
                if side == "BUY":
                    if c["low"] <= ob_low:
                        # Price broke below OB Low before reaching qualification target -> REJECT!
                        is_invalidated = True
                        status = "INVALIDATED"
                        break
                    if c["high"] >= target_7pct:
                        is_qualified = True
                        qualified_idx = scan_idx
                elif side == "SELL":
                    if c["high"] >= ob_high:
                        # Price broke above OB High before reaching qualification target -> REJECT!
                        is_invalidated = True
                        status = "INVALIDATED"
                        break
                    if c["low"] <= target_7pct:
                        is_qualified = True
                        qualified_idx = scan_idx

            else:
                # Setup is qualified. Check for FIRST TAP ENTRY.
                if entry_idx is None:
                    if side == "BUY" and c["low"] <= ob_high:
                        # First tap on OB High
                        entry_idx = scan_idx
                        entry_price = ob_high
                        entry_time = c["time"]
                        tp_price = entry_price * (1.0 + TP_PCT)
                        sl_price = entry_price * (1.0 - SL_PCT)
                        status = "ACTIVE"
                    elif side == "SELL" and c["high"] >= ob_low:
                        # First tap on OB Low
                        entry_idx = scan_idx
                        entry_price = ob_low
                        entry_time = c["time"]
                        tp_price = entry_price * (1.0 - TP_PCT)
                        sl_price = entry_price * (1.0 + SL_PCT)
                        status = "ACTIVE"

                else:
                    # Setup has entered! Track TP / SL outcomes
                    if side == "BUY":
                        if c["high"] >= tp_price:
                            status = "TP_HIT"
                            break
                        elif c["low"] <= sl_price:
                            status = "SL_HIT"
                            break
                    elif side == "SELL":
                        if c["low"] <= tp_price:
                            status = "TP_HIT"
                            break
                        elif c["high"] >= sl_price:
                            status = "SL_HIT"
                            break

        if is_invalidated:
            # We don't store invalidated zones as active, but can record them if needed
            continue

        if not is_qualified:
            # Did not reach 7% qualification yet
            continue

        if status == "PENDING" and is_qualified:
            status = "QUALIFIED"

        qualified_time = candles[qualified_idx]["time"] if qualified_idx is not None else None

        # LOCKED SMC V17 RULE:
        # Long/BUY Entry Price MUST ALWAYS be the TOP BOUNDARY (ob_high) of the Order Block!
        # Short/SELL Entry Price MUST ALWAYS be the BOTTOM BOUNDARY (ob_low) of the Order Block!
        locked_entry = entry_price if entry_price else (ob_high if side == "BUY" else ob_low)
        locked_tp = tp_price if tp_price else (locked_entry * (1.0 + TP_PCT) if side == "BUY" else locked_entry * (1.0 - TP_PCT))
        locked_sl = sl_price if sl_price else (locked_entry * (1.0 - SL_PCT) if side == "BUY" else locked_entry * (1.0 + SL_PCT))

        zone = {
            "symbol": symbol,
            "side": side,
            "origin_time": origin_candle["time"],
            "origin_open": origin_candle["open"],
            "origin_high": ob_high,
            "origin_low": ob_low,
            "origin_close": origin_candle["close"],
            "displacement_time": disp_candle["time"],
            "ob_high": ob_high,
            "ob_low": ob_low,
            "target_7pct": round(target_7pct, 6),
            "qualified": 1,
            "qualified_time": qualified_time,
            "status": status,
            "entry_price": round(locked_entry, 6),
            "entry_time": entry_time,
            "tp_price": round(locked_tp, 6),
            "sl_price": round(locked_sl, 6),
            "tags": tags,
            "is_second_ob": False,
            "created_at": int(time.time() * 1000)
        }
        detected_zones.append(zone)

    return detected_zones

def filter_active_zones(zones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Applies constraints from Image 1 & 2:
    - Deduplicates multiple detections pointing to the exact same origin candle
    - Max active zones per coin: 2 BUY + 2 SELL
    - Only fresh/qualified or active zones
    - Strictly locks 2nd OB priority and Entry Price = Top Boundary (ob_high) for BUY
    """
    seen = set()
    unique_zones = []
    for z in zones:
        key = (z["symbol"], z["side"], z["origin_time"])
        if key not in seen:
            seen.add(key)
            unique_zones.append(z)

    buy_zones = [z for z in unique_zones if z["side"] == "BUY" and z["status"] in ("QUALIFIED", "ACTIVE")]
    sell_zones = [z for z in unique_zones if z["side"] == "SELL" and z["status"] in ("QUALIFIED", "ACTIVE")]

    # Sort by origin_time descending (freshest first)
    buy_zones.sort(key=lambda x: x["origin_time"], reverse=True)
    sell_zones.sort(key=lambda x: x["origin_time"], reverse=True)

    kept_buy = buy_zones[:MAX_ACTIVE_BUY_PER_COIN]
    kept_sell = sell_zones[:MAX_ACTIVE_SELL_PER_COIN]

    # Tag 2nd OB priority: Hierarchical Dual-Mode Engine (Mode A & Mode B)
    if len(kept_buy) >= 3:
        sorted_by_p = sorted(kept_buy, key=lambda x: x["ob_high"], reverse=True)
        sorted_by_p[0]["is_second_ob"] = False # Topmost 1st OB
        sorted_by_p[1]["is_second_ob"] = True  # 👑 Mode A Middle 2nd OB
        sorted_by_p[1]["engine_mode"] = "MODE_A_3OB"
        sorted_by_p[2]["is_second_ob"] = False # Bottom 3rd OB
    elif len(kept_buy) == 2:
        sorted_by_p = sorted(kept_buy, key=lambda x: x["ob_high"], reverse=True)
        sorted_by_p[0]["is_second_ob"] = False # Topmost OB
        sorted_by_p[1]["is_second_ob"] = True  # 👑 Mode B 2nd OB Dynamic Expansion
        sorted_by_p[1]["engine_mode"] = "MODE_B_2OB"
    elif len(kept_buy) == 1:
        kept_buy[0]["is_second_ob"] = False

    if len(kept_sell) >= 3:
        sorted_by_p = sorted(kept_sell, key=lambda x: x["ob_low"])
        sorted_by_p[0]["is_second_ob"] = False
        sorted_by_p[1]["is_second_ob"] = True
        sorted_by_p[1]["engine_mode"] = "MODE_A_3OB"
        sorted_by_p[2]["is_second_ob"] = False
    elif len(kept_sell) == 2:
        sorted_by_p = sorted(kept_sell, key=lambda x: x["ob_low"])
        sorted_by_p[0]["is_second_ob"] = False
        sorted_by_p[1]["is_second_ob"] = True
        sorted_by_p[1]["engine_mode"] = "MODE_B_2OB"
    elif len(kept_sell) == 1:
        kept_sell[0]["is_second_ob"] = False

    # Enforce locked entry rule on all active zones:
    for z in kept_buy:
        z["entry_price"] = z["ob_high"] # LOCKED RULE: Top Boundary for BUY
        z["tp_price"] = round(z["entry_price"] * (1.0 + TP_PCT), 6)
        z["sl_price"] = round(z["entry_price"] * (1.0 - SL_PCT), 6)

    for z in kept_sell:
        z["entry_price"] = z["ob_low"]  # LOCKED RULE: Bottom Boundary for SELL
        z["tp_price"] = round(z["entry_price"] * (1.0 - TP_PCT), 6)
        z["sl_price"] = round(z["entry_price"] * (1.0 + SL_PCT), 6)

    return kept_buy + kept_sell
