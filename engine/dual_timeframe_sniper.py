"""
Dual Timeframe (1H & 4H) Crypto Sniper Coordinator.
Combines 4H Macro Trend Anchor with 1H Intraday Precision 2nd OB Entry.
Follows strictly locked outer boundary rules:
- Long: Top Boundary (ob_high) of 2nd OB
- Short: Bottom Boundary (ob_low) of 2nd OB
"""

from typing import Dict, Any, List, Optional
import time
from engine.smc_v17 import analyze_candles_smc_v17, filter_active_zones
from engine.order_flow import analyze_order_flow

class DualTimeframeSniper:
    def __init__(self):
        self.min_confluence_threshold = 85

    def evaluate_dual_setup(
        self,
        symbol: str,
        candles_4h: List[Dict[str, Any]],
        candles_1h: List[Dict[str, Any]],
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates 4H macro context and 1H precision zones to find high-probability Sniper setups.
        """
        if not candles_4h or not candles_1h:
            return {"status": "INSUFFICIENT_DATA", "symbol": symbol}

        if current_price is None:
            current_price = candles_1h[-1]["close"]

        # 1. Analyze 4H Macro Structure
        zones_4h = analyze_candles_smc_v17(symbol, candles_4h)
        active_4h = filter_active_zones(zones_4h)

        macro_trend = "NEUTRAL"
        bullish_4h = [z for z in active_4h if z.get("side") == "BUY"]
        bearish_4h = [z for z in active_4h if z.get("side") == "SELL"]

        if bullish_4h and not bearish_4h:
            macro_trend = "BULLISH"
        elif bearish_4h and not bullish_4h:
            macro_trend = "BEARISH"
        elif bullish_4h and bearish_4h:
            # Check latest origin time
            macro_trend = "BULLISH" if bullish_4h[-1]["origin_time"] > bearish_4h[-1]["origin_time"] else "BEARISH"

        # 2. Analyze 1H Precision Zones
        zones_1h = analyze_candles_smc_v17(symbol, candles_1h)
        active_1h = filter_active_zones(zones_1h)

        # 3. Find 2nd OB on 1H
        target_zone_1h = None
        for z in reversed(active_1h):
            if z.get("is_second_ob") or z.get("status") in ("QUALIFIED", "ACTIVE"):
                target_zone_1h = z
                break

        if not target_zone_1h and active_1h:
            target_zone_1h = active_1h[-1]

        # 4. Evaluate Order Flow Confluence
        try:
            flow_metrics = analyze_order_flow(candles_1h)
        except Exception:
            flow_metrics = {"delta": 0, "cvd_trend": "NEUTRAL", "absorption": False, "oi_expanding": False}

        # 5. Score Confluence
        score = 60
        confluence_reasons = []

        if target_zone_1h:
            side = target_zone_1h["side"]
            is_second = target_zone_1h.get("is_second_ob", False)

            # Locked Entry Rule & Targets (1H: +1.5% TP / -10% ROE SL | 4H: +2.1% TP / -15% ROE SL)
            # Default to 1H execution parameters
            tp_move = 0.0160   # +1.60% move = +8.00% ROE @ 5x
            sl_move = 0.0200   # -2.00% move = -10.00% ROE @ 5x
            be_move = 0.0075   # +0.75% move = shift to $0 BE
            hard_sl_buffer = 0.995

            # If evaluating 4H macro target
            tp_4h_move = 0.0240 # +2.40% move = +12.00% ROE @ 5x
            sl_4h_move = 0.0225 # -2.25% move = -11.25% (~11%) ROE @ 5x
            hard_sl_dump_move = 0.0320 # -3.20% move = -16.00% ROE @ 5x (Sudden Dump Shield)

            # 7 Safety Guardrails: Fee buffer & Airbag SL
            fee_buffer = 0.0010  # +0.10% fee shield buffer for true $0 net exit

            if side == "BUY":
                entry_price = target_zone_1h["ob_high"]  # Strictly Top Boundary of 2nd OB
                tp_price = entry_price * (1.0 + tp_move)
                sl_price = entry_price * (1.0 - sl_move)
                hard_sl_price = target_zone_1h["ob_low"] * hard_sl_buffer
                be_price = entry_price * (1.0 + be_move)
                be_fee_protected = entry_price * (1.0 + fee_buffer)
                hard_airbag_sl_16pct = entry_price * (1.0 - hard_sl_dump_move) # -16.00% ROE
                front_run_entry = entry_price * 1.0005
                dist_pct = ((current_price - entry_price) / entry_price) * 100
                
                # 4H macro projection
                tp_4h_price = entry_price * (1.0 + tp_4h_move)
                sl_4h_price = entry_price * (1.0 - sl_4h_move)
            else:
                entry_price = target_zone_1h["ob_low"]   # Strictly Bottom Boundary
                tp_price = entry_price * (1.0 - tp_move)
                sl_price = entry_price * (1.0 + sl_move)
                hard_sl_price = target_zone_1h["ob_high"] * (2 - hard_sl_buffer)
                be_price = entry_price * (1.0 - be_move)
                be_fee_protected = entry_price * (1.0 - fee_buffer)
                hard_airbag_sl_16pct = entry_price * (1.0 + hard_sl_dump_move) # -16.00% ROE
                front_run_entry = entry_price * 0.9995
                dist_pct = ((entry_price - current_price) / entry_price) * 100
                
                tp_4h_price = entry_price * (1.0 - tp_4h_move)
                sl_4h_price = entry_price * (1.0 + sl_4h_move)

            if is_second:
                score += 15
                confluence_reasons.append("2nd OB Continuation Pattern (Middle Zone)")

            # 4H Macro Alignment
            if (side == "BUY" and macro_trend == "BULLISH") or (side == "SELL" and macro_trend == "BEARISH"):
                score += 15
                confluence_reasons.append(f"4H Macro Trend Confluence ({macro_trend})")

            # CVD Confluence
            if (side == "BUY" and flow_metrics.get("cvd_trend") == "BULLISH") or \
               (side == "SELL" and flow_metrics.get("cvd_trend") == "BEARISH"):
                score += 10
                confluence_reasons.append("CVD Delta Reversal / Absorption")

            # Whale OI Expansion
            if flow_metrics.get("oi_expanding", False):
                score += 10
                confluence_reasons.append("Whale Open Interest Expansion (>0.5%)")

            # First-tap proximity bonus
            if abs(dist_pct) <= 0.8:
                score += 10
                confluence_reasons.append(f"Imminent Tap ({dist_pct:+.2f}% away)")

            score = min(score, 99)

            recommendation = "STANDBY"
            if score >= 90 and abs(dist_pct) <= 0.5:
                recommendation = "READY_FOR_ENTRY"
            elif score >= 85:
                recommendation = "ARMED_WATCHLIST"

            return {
                "symbol": symbol,
                "status": "VALID_SETUP",
                "macro_4h_trend": macro_trend,
                "timeframe": "1h_4h_dual",
                "side": side,
                "is_second_ob": is_second,
                "locked_entry_price": round(entry_price, 6),
                "current_price": round(current_price, 6),
                "distance_pct": round(dist_pct, 2),
                "tp_price_1h": round(tp_price, 6),
                "sl_price_1h": round(sl_price, 6),
                "roe_target_1h": 8.0,
                "roe_sl_1h": -10.0,
                "tp_price_4h": round(tp_4h_price, 6),
                "sl_price_4h": round(sl_4h_price, 6),
                "roe_target_4h": 12.0,
                "roe_sl_4h": -11.25,
                "hard_sl_price": round(hard_sl_price, 6),
                "hard_airbag_sl_16pct": round(hard_airbag_sl_16pct, 6),
                "breakeven_price": round(be_price, 6),
                "fee_protected_be_price": round(be_fee_protected, 6),
                "front_run_limit_entry": round(front_run_entry, 6),
                "leverage": 5,
                "confluence_score": score,
                "confluence_reasons": confluence_reasons,
                "recommendation": recommendation,
                "timestamp_ms": int(time.time() * 1000)
            }

        return {
            "symbol": symbol,
            "status": "NO_CLEAN_ZONE",
            "macro_4h_trend": macro_trend,
            "current_price": current_price,
            "confluence_score": 50,
            "recommendation": "WATCH"
        }

dual_sniper = DualTimeframeSniper()
