import urllib.request
import json
from datetime import datetime
from typing import Dict, Any, Tuple

def verify_setup_forensic_lock(setup: Dict[str, Any], candles: list) -> Tuple[bool, str]:
    sym = setup.get("symbol", "").upper()
    side = setup.get("side", "").upper()
    tf = setup.get("interval", "4h").lower()
    entry_p = float(setup.get("entry_price", 0.0))
    ob_high = float(setup.get("ob_high", 0.0))
    ob_low = float(setup.get("ob_low", 0.0))
    min_mat = 18 if tf == "1h" else 8

    n = len(candles)
    if n < 40:
        return False, f"Insufficient candles ({n} < 40)"

    # 1. Find the exact base OB candle that formed this zone
    ob_candle_idx = -1
    for i in range(max(5, n - 200), n - 3):
        c = candles[i]
        # Match OB candle coordinates with tolerance
        if abs(c["high"] - ob_high) / ob_high < 0.003 and abs(c["low"] - ob_low) / ob_low < 0.003:
            ob_candle_idx = i
            break

    if ob_candle_idx == -1:
        return False, f"No matching Order Block found on {tf} chart at [{ob_low}, {ob_high}]"

    c3 = candles[ob_candle_idx]
    c2 = candles[ob_candle_idx + 1]
    c1 = candles[ob_candle_idx + 2]

    # 2. Strict Candle Color Gate
    if side in ("BUY", "LONG"):
        if c3["close"] >= c3["open"]:
            return False, f"OB candle is not strict RED (close {c3['close']} >= open {c3['open']})"
        # FVG Check
        if c1["low"] <= c3["high"]:
            return False, f"No Bullish Fair Value Gap (c1 low {c1['low']} <= c3 high {c3['high']})"
        # Displacement Wave Check
        impulse_h = max(c1["high"], c2["high"])
        disp_pct = (impulse_h - c3["low"]) / c3["low"] * 100.0
        if disp_pct < 5.0:
            return False, f"Displacement wave too weak ({disp_pct:.2f}% < 5.0%)"
        # Rocket Airspace Check
        peak_runway = max(candles[k]["high"] for k in range(ob_candle_idx + 1, min(ob_candle_idx + 25, n)))
        airspace_pct = (peak_runway - ob_high) / ob_high * 100.0
        if airspace_pct < 5.0:
            return False, f"Insufficient Rocket Airspace Void ({airspace_pct:.2f}% < 5.0%)"

    else: # SHORT / SELL
        if c3["close"] <= c3["open"]:
            return False, f"OB candle is not strict GREEN (close {c3['close']} <= open {c3['open']})"
        # Bear FVG Check
        if c1["high"] >= c3["low"]:
            return False, f"No Bearish Fair Value Gap (c1 high {c1['high']} >= c3 low {c3['low']})"
        # Displacement Wave Check
        impulse_l = min(c1["low"], c2["low"])
        disp_pct = (c3["high"] - impulse_l) / c3["high"] * 100.0
        if disp_pct < 5.0:
            return False, f"Displacement drop too weak ({disp_pct:.2f}% < 5.0%)"
        # Rocket Airspace Check
        peak_runway = min(candles[k]["low"] for k in range(ob_candle_idx + 1, min(ob_candle_idx + 25, n)))
        airspace_pct = (ob_low - peak_runway) / ob_low * 100.0
        if airspace_pct < 5.0:
            return False, f"Insufficient Rocket Airspace Void ({airspace_pct:.2f}% < 5.0%)"

    # 3. VIRGIN UNMITIGATED CHECK: No premature touches and no multi-taps
    for t in range(ob_candle_idx + 3, n):
        curr_c = candles[t]
        bars_alive = t - (ob_candle_idx + 2)

        if side in ("BUY", "LONG"):
            # Structure breakdown
            if curr_c["close"] < ob_low:
                return False, f"OB structure invalidated by bar {t} closing below OB low ({curr_c['close']} < {ob_low})"
            # Touch check
            if curr_c["low"] <= entry_p * 1.0005:
                # If touched before maturation -> Premature!
                if bars_alive < min_mat:
                    return False, f"Premature mitigation at bar {t} (alive {bars_alive}b < min {min_mat}b)"
                # If touched more than 1 bar ago -> Stale/Multi-tapped!
                age_from_now = (n - 1) - t
                if age_from_now > 1:
                    return False, f"Zone was already tapped {age_from_now} bars ago (Not a virgin fresh live tap!)"

        else: # SHORT
            if curr_c["close"] > ob_high:
                return False, f"OB structure invalidated by bar {t} closing above OB high ({curr_c['close']} > {ob_high})"
            if curr_c["high"] >= entry_p * 0.9995:
                if bars_alive < min_mat:
                    return False, f"Premature mitigation at bar {t} (alive {bars_alive}b < min {min_mat}b)"
                age_from_now = (n - 1) - t
                if age_from_now > 1:
                    return False, f"Zone was already tapped {age_from_now} bars ago (Not a virgin fresh live tap!)"

    return True, f"PASS: 100% Certified Virgin OB at [{ob_low}, {ob_high}] | Disp: {disp_pct:.1f}% | Airspace: {airspace_pct:.1f}%"

# Test on LDO 4H and OP 1H
print("Testing Forensic Lock on LDO 4H:")
req = urllib.request.Request('https://fapi.binance.com/fapi/v1/klines?symbol=LDOUSDT&interval=4h&limit=200', headers={'User-Agent': 'Mozilla/5.0'})
raw = json.loads(urllib.request.urlopen(req).read().decode())
candles = [{"time": int(d[0]), "open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4])} for d in raw]

test_setup = {
    "symbol": "LDOUSDT",
    "side": "LONG",
    "interval": "4h",
    "entry_price": 0.44771,
    "ob_high": 0.4478,
    "ob_low": 0.4395
}
ok, msg = verify_setup_forensic_lock(test_setup, candles)
print("LDO 4H Result:", ok, msg)

# Test on bad GALA multi-tapped setup
test_gala = {
    "symbol": "GALAUSDT",
    "side": "LONG",
    "interval": "1h",
    "entry_price": 0.0025353,
    "ob_high": 0.002538,
    "ob_low": 0.002465
}
req = urllib.request.Request('https://fapi.binance.com/fapi/v1/klines?symbol=GALAUSDT&interval=1h&limit=200', headers={'User-Agent': 'Mozilla/5.0'})
raw = json.loads(urllib.request.urlopen(req).read().decode())
candles_gala = [{"time": int(d[0]), "open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4])} for d in raw]
ok_gala, msg_gala = verify_setup_forensic_lock(test_gala, candles_gala)
print("GALA 1H Result (Should REJECT):", ok_gala, msg_gala)
