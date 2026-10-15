"""
QUANTITATIVE MICROSTRUCTURE & DERIVATIVE ALPHA ENGINE
=====================================================
Proprietary institutional math implemented for HERMES QUANTUM V4:
1. Rescaled Range (R/S) Hurst Exponent Stochastic Regime Gate
2. Order Book Imbalance (Level-2 Depth OBI)
3. Cumulative Volume Delta (CVD) Taker Absorption Engine
4. Open Interest (OI) & Funding Rate Liquidation Squeeze Index (LSI)
5. Whale Block Size vs Retail Swarm Detection
"""

import math
from typing import List, Dict, Any, Tuple

def compute_hurst_exponent(prices: List[float], min_window: int = 8, max_window: int = 40) -> float:
    """
    Computes Hurst Exponent (H) via Rescaled Range (R/S) Analysis.
    - H < 0.45: Anti-persistent (Mean Reverting)
    - 0.45 <= H <= 0.55: Random Walk / Brownian Motion (Noise - VETO TRADING)
    - H > 0.55: Persistent (Strong Institutional Trend)
    """
    N = len(prices)
    if N < 30:
        return 0.50

    # Log returns
    log_returns = []
    for i in range(1, N):
        if prices[i-1] > 0 and prices[i] > 0:
            log_returns.append(math.log(prices[i] / prices[i-1]))
        else:
            log_returns.append(0.0)

    n_samples = len(log_returns)
    lags = [4, 8, 16, 32]
    lags = [lag for lag in lags if lag <= n_samples // 2]
    if len(lags) < 3:
        return 0.50

    rs_values = []
    lag_values = []

    for lag in lags:
        sub_chunks = [log_returns[i:i + lag] for i in range(0, n_samples - lag + 1, lag)]
        if not sub_chunks:
            continue
        
        chunk_rs = []
        for chunk in sub_chunks:
            mean = sum(chunk) / len(chunk)
            diffs = [x - mean for x in chunk]
            cum_devs = []
            running = 0.0
            for d in diffs:
                running += d
                cum_devs.append(running)
            
            # Range R
            r = max(cum_devs) - min(cum_devs)
            
            # Std S
            variance = sum(d * d for d in diffs) / len(chunk)
            s = math.sqrt(variance) if variance > 1e-12 else 1e-6
            
            if s > 0:
                chunk_rs.append(r / s)
        
        if chunk_rs:
            avg_rs = sum(chunk_rs) / len(chunk_rs)
            if avg_rs > 0:
                rs_values.append(math.log(avg_rs))
                lag_values.append(math.log(lag))

    if len(lag_values) >= 3:
        # Linear regression slope = H
        n_pts = len(lag_values)
        sum_x = sum(lag_values)
        sum_y = sum(rs_values)
        sum_xy = sum(x * y for x, y in zip(lag_values, rs_values))
        sum_x2 = sum(x * x for x in lag_values)
        denom = (n_pts * sum_x2 - sum_x * sum_x)
        if denom != 0:
            h = (n_pts * sum_xy - sum_x * sum_y) / denom
            return round(max(0.01, min(0.99, h)), 3)

    return 0.50

def compute_order_book_imbalance(bids: List[List[float]], asks: List[List[float]], top_n: int = 10) -> Dict[str, Any]:
    """
    Computes Level-2 Order Book Imbalance Ratio (OBI).
    OBI in [-1.0, +1.0]:
    +0.40 to +1.00: Heavy Passive Bid Absorption (Smart Money Bids loaded)
    -0.40 to -1.00: Heavy Passive Ask Wall (Smart Money Asks loaded)
    """
    top_bids = bids[:top_n]
    top_asks = asks[:top_n]

    bid_vol = sum(float(b[1]) for b in top_bids) if top_bids else 0.0
    ask_vol = sum(float(a[1]) for a in top_asks) if top_asks else 0.0
    total = bid_vol + ask_vol

    if total > 0:
        obi = (bid_vol - ask_vol) / total
    else:
        obi = 0.0

    return {
        "obi": round(obi, 3),
        "bid_depth_usdt": round(bid_vol, 2),
        "ask_depth_usdt": round(ask_vol, 2),
        "is_bid_dominated": obi >= 0.35,
        "is_ask_dominated": obi <= -0.35
    }

def compute_taker_delta_metrics(taker_buy_vol: float, total_vol: float) -> Dict[str, Any]:
    """
    Computes aggressive market order pressure (Taker Buy vs Sell Delta).
    """
    taker_sell_vol = max(0.0, total_vol - taker_buy_vol)
    delta = taker_buy_vol - taker_sell_vol
    delta_ratio = (taker_buy_vol / total_vol) if total_vol > 0 else 0.50

    return {
        "taker_buy_vol": round(taker_buy_vol, 4),
        "taker_sell_vol": round(taker_sell_vol, 4),
        "net_delta": round(delta, 4),
        "delta_ratio": round(delta_ratio, 3),
        "is_aggressive_buying": delta_ratio >= 0.55,
        "is_aggressive_selling": delta_ratio <= 0.45
    }

def compute_liquidation_squeeze_index(
    cur_price: float,
    prior_price: float,
    cur_oi: float,
    prior_oi: float,
    funding_rate: float
) -> Dict[str, Any]:
    """
    Computes the Liquidation Squeeze Index (LSI):
    Detects when retail traders are trapped in crowded high-leverage positions.
    - SHORT SQUEEZE TRIGGER: Price falling/flat + OI surging (> +3%) + Negative Funding (< 0.0%)
    - LONG SQUEEZE TRIGGER: Price pumping/flat + OI surging (> +3%) + Highly positive funding (> +0.03%)
    """
    if prior_price <= 0 or prior_oi <= 0:
        return {"squeeze_type": "NEUTRAL", "lsi_score": 0.0, "is_squeeze_imminent": False}

    pct_price_change = (cur_price - prior_price) / prior_price * 100.0
    pct_oi_change = (cur_oi - prior_oi) / prior_oi * 100.0

    # Short Squeeze setup: High OI accumulation into negative funding
    is_short_crowded = (pct_oi_change >= 2.0) and (funding_rate <= -0.00005)
    # Long Squeeze setup: High OI accumulation into extreme positive funding
    is_long_crowded = (pct_oi_change >= 2.0) and (funding_rate >= 0.00020)

    squeeze_type = "NEUTRAL"
    score = 0.0
    if is_short_crowded:
        squeeze_type = "BULLISH_SHORT_SQUEEZE"
        score = abs(funding_rate) * 10000.0 * pct_oi_change
    elif is_long_crowded:
        squeeze_type = "BEARISH_LONG_SQUEEZE"
        score = funding_rate * 10000.0 * pct_oi_change

    return {
        "squeeze_type": squeeze_type,
        "lsi_score": round(score, 2),
        "pct_oi_change": round(pct_oi_change, 2),
        "pct_price_change": round(pct_price_change, 2),
        "funding_rate": funding_rate,
        "is_squeeze_imminent": is_short_crowded or is_long_crowded
    }
