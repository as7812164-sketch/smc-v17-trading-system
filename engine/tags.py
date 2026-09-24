from typing import List, Dict, Any

def detect_fvg(candles: List[Dict[str, Any]], index: int, side: str) -> bool:
    """
    Checks if a Fair Value Gap exists around the displacement candle index.
    Candles format: list of dicts with 'open', 'high', 'low', 'close', 'time'.
    """
    if index < 1 or index >= len(candles) - 1:
        return False
    c1 = candles[index - 1]
    c3 = candles[index + 1]

    if side == "BUY":
        # Bullish FVG: Space between candle 1 high and candle 3 low
        return c3["low"] > c1["high"]
    elif side == "SELL":
        # Bearish FVG: Space between candle 1 low and candle 3 high
        return c3["high"] < c1["low"]
    return False

def detect_liquidity_sweep(candles: List[Dict[str, Any]], origin_idx: int, side: str) -> bool:
    """
    Checks if the origin candle swept liquidity of prior swing highs/lows (lookback 10 candles before origin).
    """
    if origin_idx < 3:
        return False
    start_lookback = max(0, origin_idx - 10)
    origin_candle = candles[origin_idx]

    if side == "BUY":
        # Swept lowest low of prior swing
        prior_lows = [c["low"] for c in candles[start_lookback:origin_idx]]
        if prior_lows and origin_candle["low"] < min(prior_lows):
            return True
    elif side == "SELL":
        # Swept highest high of prior swing
        prior_highs = [c["high"] for c in candles[start_lookback:origin_idx]]
        if prior_highs and origin_candle["high"] > max(prior_highs):
            return True
    return False

def detect_bos(candles: List[Dict[str, Any]], disp_idx: int, side: str) -> bool:
    """
    Checks if displacement broke structural swing high/low within prior 20 candles.
    """
    if disp_idx < 5:
        return False
    lookback = max(0, disp_idx - 20)
    disp_candle = candles[disp_idx]

    if side == "BUY":
        prior_highs = [c["high"] for c in candles[lookback:disp_idx - 1]]
        if prior_highs and disp_candle["close"] > max(prior_highs):
            return True
    elif side == "SELL":
        prior_lows = [c["low"] for c in candles[lookback:disp_idx - 1]]
        if prior_lows and disp_candle["close"] < min(prior_lows):
            return True
    return False

def extract_soft_tags(candles: List[Dict[str, Any]], origin_idx: int, disp_idx: int, side: str) -> List[str]:
    tags = []
    if detect_liquidity_sweep(candles, origin_idx, side):
        tags.append("SWEEP")
    if detect_fvg(candles, disp_idx, side):
        tags.append("FVG")
    if detect_bos(candles, disp_idx, side):
        tags.append("BOS")
    return tags
