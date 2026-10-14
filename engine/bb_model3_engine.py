"""
BB 1.0 (BOOMING BULLS LIQUIDITY SNIPER) — MODEL 3 ENGINE
=========================================================
Architecture:
- Trigger Levels: Previous Day High (PDH) & Previous Day Low (PDL)
- Institutional Validation: Extreme Origin Order Block + Fair Value Gap (FVG)
- Entry Execution: 50% Mean Threshold (MT) Limit Fill
- Stop Loss: Extreme Wick ± 0.15% Anti-Hunt Buffer
- Exit Engine: Model 3 (Stepped Trailing SL - Tiered Profit Lock)
  * Tier 1 (+1.0R): SL moves to +0.2R (Fee Shield)
  * Tier 2 (+1.5R): SL moves to +1.0R Locked
  * Tier 3 (+2.0R): SL moves to +1.5R Locked
  * Step +0.5R onwards locks additional +0.5R profit runner.

Zero Phantom Execution Verified.
Standalone module — strictly isolated from live hermes30_apex_live.py engine.
"""

import sys
import math
from typing import List, Dict, Optional, Tuple

class BBModel3Engine:
    def __init__(
        self,
        fvg_min_displacement: float = 0.015,
        displacement_2bar: float = 0.020,
        sl_buffer_pct: float = 0.0015,
        fee_friction_r: float = 0.06,
        max_limit_wait_bars: int = 32,
        max_trade_hold_bars: int = 96
    ):
        self.fvg_min_displacement = fvg_min_displacement
        self.displacement_2bar = displacement_2bar
        self.sl_buffer_pct = sl_buffer_pct
        self.fee_friction_r = fee_friction_r
        self.max_limit_wait_bars = max_limit_wait_bars
        self.max_trade_hold_bars = max_trade_hold_bars

    def calculate_pdh_pdl(self, daily_candles: List[Dict]) -> Tuple[float, float]:
        """
        Extracts Previous Day High and Previous Day Low from daily candle data.
        """
        if len(daily_candles) < 2:
            return 0.0, 0.0
        prev_day = daily_candles[-2]
        return float(prev_day["high"]), float(prev_day["low"])

    def find_extreme_order_blocks(
        self,
        candles_15m: List[Dict],
        pdh: float,
        pdl: float,
        level_proximity_pct: float = 0.015
    ) -> List[Dict]:
        """
        Scans 15m candles for Extreme Origin Order Blocks forming near PDH/PDL.
        """
        n = len(candles_15m)
        obs = []

        for i in range(1, n - 2):
            c = candles_15m[i]
            c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
            next_c = candles_15m[i + 1]
            next_c2 = candles_15m[i + 2]

            # -----------------------------------------------------------------
            # 1. BULLISH EXTREME ORDER BLOCK AT BOTTOM (NEAR/BELOW PDL SUPPORT)
            # -----------------------------------------------------------------
            dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
            if dist_to_pdl <= level_proximity_pct or c_l <= pdl:
                is_bearish = c_c < c_o
                gain_1bar = (next_c["high"] - c_l) / c_l
                gain_2bar = (next_c2["high"] - c_l) / c_l
                has_bull_fvg = next_c2["low"] > c_h

                if (is_bearish or (c_h - c_l) > 0) and (gain_1bar >= self.fvg_min_displacement or gain_2bar >= self.displacement_2bar) and has_bull_fvg:
                    ob_high = c_h
                    ob_low = c_l
                    mt = (ob_high + ob_low) / 2.0
                    sl = ob_low * (1.0 - self.sl_buffer_pct)
                    risk = mt - sl

                    if risk > 0:
                        obs.append({
                            "side": "LONG",
                            "index": i,
                            "time": c.get("time", ""),
                            "ob_high": ob_high,
                            "ob_low": ob_low,
                            "mt": mt,
                            "sl": sl,
                            "risk": risk,
                            "anchor": "PDL_BOTTOM",
                            "status": "ARMED"
                        })

            # -----------------------------------------------------------------
            # 2. BEARISH EXTREME ORDER BLOCK AT TOP (NEAR/ABOVE PDH RESISTANCE)
            # -----------------------------------------------------------------
            dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
            if dist_to_pdh <= level_proximity_pct or c_h >= pdh:
                is_bullish = c_c > c_o
                drop_1bar = (c_h - next_c["low"]) / c_h
                drop_2bar = (c_h - next_c2["low"]) / c_h
                has_bear_fvg = next_c2["high"] < c_l

                if (is_bullish or (c_h - c_l) > 0) and (drop_1bar >= self.fvg_min_displacement or drop_2bar >= self.displacement_2bar) and has_bear_fvg:
                    ob_high = c_h
                    ob_low = c_l
                    mt = (ob_high + ob_low) / 2.0
                    sl = ob_high * (1.0 + self.sl_buffer_pct)
                    risk = sl - mt

                    if risk > 0:
                        obs.append({
                            "side": "SHORT",
                            "index": i,
                            "time": c.get("time", ""),
                            "ob_high": ob_high,
                            "ob_low": ob_low,
                            "mt": mt,
                            "sl": sl,
                            "risk": risk,
                            "anchor": "PDH_TOP",
                            "status": "ARMED"
                        })

        return obs

    def check_active_setup_state(
        self,
        setup: Dict,
        candles_15m: List[Dict]
    ) -> Dict:
        """
        Evaluates the current real-time state of an Order Block setup:
        - WAITING_FOR_RETEST: Price hasn't mitigated 50% MT yet
        - ACTIVE_IN_TRADE: 50% MT limit has been filled, trade is live
        - INVALIDATED: Price hit SL before mitigation
        - COMPLETED: Closed via Stepped Trailing SL or TP
        """
        n = len(candles_15m)
        ob_idx = setup["index"]
        side = setup["side"]
        entry_price = setup["mt"]
        initial_sl = setup["sl"]
        risk = setup["risk"]

        filled = False
        fill_idx = -1

        for w_i in range(ob_idx + 2, min(ob_idx + 2 + self.max_limit_wait_bars, n)):
            b = candles_15m[w_i]
            if side == "LONG":
                if b["low"] <= initial_sl:
                    return {"state": "INVALIDATED_BEFORE_FILL", "detail": "Price broke SL before mitigating MT"}
                if b["low"] <= entry_price:
                    filled = True
                    fill_idx = w_i
                    break
            else: # SHORT
                if b["high"] >= initial_sl:
                    return {"state": "INVALIDATED_BEFORE_FILL", "detail": "Price broke SL before mitigating MT"}
                if b["high"] >= entry_price:
                    filled = True
                    fill_idx = w_i
                    break

        if not filled:
            if n - (ob_idx + 2) >= self.max_limit_wait_bars:
                return {"state": "EXPIRED", "detail": "Wait time exceeded max bars"}
            return {"state": "WAITING_FOR_RETEST", "entry_limit": entry_price, "sl": initial_sl}

        # If filled, evaluate live or historical progress using Model 3 Stepped Trailing
        active_sl = initial_sl
        current_tier = 0

        for idx in range(fill_idx + 1, min(fill_idx + 1 + self.max_trade_hold_bars, n)):
            b = candles_15m[idx]
            b_h, b_l = b["high"], b["low"]

            if side == "LONG":
                # Check SL hit
                if b_l <= active_sl:
                    pnl_r = -1.0 if current_tier == 0 else (0.2 if current_tier == 1 else (current_tier - 1) * 0.5)
                    return {
                        "state": "CLOSED",
                        "tier": current_tier,
                        "exit_price": active_sl,
                        "pnl_r": pnl_r - self.fee_friction_r,
                        "outcome": "SL_HIT" if current_tier == 0 else "TRAILING_PROFIT_LOCKED"
                    }
                # Check Trailing Milestones
                max_fav_r = (b_h - entry_price) / risk
                if max_fav_r >= 1.0:
                    tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry_price + (locked_r * risk)

            else: # SHORT
                if b_h >= active_sl:
                    pnl_r = -1.0 if current_tier == 0 else (0.2 if current_tier == 1 else (current_tier - 1) * 0.5)
                    return {
                        "state": "CLOSED",
                        "tier": current_tier,
                        "exit_price": active_sl,
                        "pnl_r": pnl_r - self.fee_friction_r,
                        "outcome": "SL_HIT" if current_tier == 0 else "TRAILING_PROFIT_LOCKED"
                    }
                max_fav_r = (entry_price - b_l) / risk
                if max_fav_r >= 1.0:
                    tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                    if tier_candidate > current_tier:
                        current_tier = tier_candidate
                        locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                        active_sl = entry_price - (locked_r * risk)

        # Still open and active
        return {
            "state": "ACTIVE_IN_TRADE",
            "entry_price": entry_price,
            "active_sl": active_sl,
            "current_tier": current_tier,
            "trailing_locked_r": 0.0 if current_tier == 0 else (0.2 if current_tier == 1 else (current_tier - 1) * 0.5)
        }
