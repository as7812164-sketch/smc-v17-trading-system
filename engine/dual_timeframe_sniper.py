"""
Dual Timeframe (1H & 4H) Crypto Coordinator (HERMES 3.5 SINGLE TIER).
Combines 4H Macro Trend Anchor with 1H Intraday Precision 5% Boundary Penetration Entry.
"""

from typing import Dict, Any, List, Optional
import time
from engine.hermes35_live import hermes35_live_engine
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
        Evaluates 4H macro context and 1H precision zones to find high-probability Hermes 3.5 setups.
        """
        if not candles_4h or not candles_1h:
            return {"status": "INSUFFICIENT_DATA", "symbol": symbol}

        if current_price is None:
            current_price = candles_1h[-1]["close"]

        # 1. Analyze 4H Macro Structure with Hermes 3.5
        setups_4h = hermes35_live_engine.detect_apex_setups_on_candles(symbol, "4h", candles_4h, current_price)
        bullish_4h = [s for s in setups_4h if s.get("side") in ("BUY", "LONG")]
        bearish_4h = [s for s in setups_4h if s.get("side") in ("SELL", "SHORT")]

        macro_trend = "NEUTRAL"
        if bullish_4h and not bearish_4h:
            macro_trend = "BULLISH"
        elif bearish_4h and not bullish_4h:
            macro_trend = "BEARISH"
        elif bullish_4h and bearish_4h:
            macro_trend = "BULLISH" if bullish_4h[-1]["tap_time"] > bearish_4h[-1]["tap_time"] else "BEARISH"

        # 2. Analyze 1H Precision Zones with Hermes 3.5
        setups_1h = hermes35_live_engine.detect_apex_setups_on_candles(symbol, "1h", candles_1h, current_price)
        target_setup_1h = setups_1h[0] if setups_1h else (setups_4h[0] if setups_4h else None)

        if target_setup_1h:
            side = target_setup_1h["side"]
            entry_price = target_setup_1h["entry_price"]
            radar_price = target_setup_1h["radar_price"]
            tp_price = target_setup_1h["tp_price"]
            soft_sl_price = target_setup_1h["soft_sl_price"]
            hard_sl_price = target_setup_1h["hard_sl_price"]
            armor_stage1 = target_setup_1h["armor_stage1_price"]
            armor_stage2 = target_setup_1h["armor_stage2_price"]
            harvest_lock = target_setup_1h["harvest_lock_price"]
            is_origin = target_setup_1h.get("is_origin", False)

            dist_pct = ((current_price - entry_price) / entry_price) * 100 if side in ("BUY", "LONG") else ((entry_price - current_price) / entry_price) * 100

            score = 75
            confluence_reasons = ["Hermes 3.5 5% Boundary Penetration Zone"]
            if is_origin:
                score += 10
                confluence_reasons.append("Origin Bedrock Structural Defense")
            if (side in ("BUY", "LONG") and macro_trend == "BULLISH") or (side in ("SELL", "SHORT") and macro_trend == "BEARISH"):
                score += 15
                confluence_reasons.append(f"4H Macro Trend Alignment ({macro_trend})")

            score = min(score, 99)
            recommendation = "STANDBY"
            if target_setup_1h.get("status") == "FRESH_TRIGGERED":
                recommendation = "READY_FOR_ENTRY"
            elif target_setup_1h.get("status") == "RADAR_PRE_ARMED":
                recommendation = "RADAR_PRE_ARMED"
            elif score >= 85:
                recommendation = "ARMED_WATCHLIST"

            return {
                "symbol": symbol,
                "status": "VALID_SETUP",
                "macro_4h_trend": macro_trend,
                "timeframe": target_setup_1h.get("interval", "1h"),
                "side": side,
                "entry_price": round(entry_price, 6),
                "radar_price": round(radar_price, 6),
                "current_price": round(current_price, 6),
                "distance_pct": round(dist_pct, 2),
                "tp_price": round(tp_price, 6),
                "soft_sl_price": round(soft_sl_price, 6),
                "hard_sl_price": round(hard_sl_price, 6),
                "armor_stage1_price": round(armor_stage1, 6),
                "armor_stage2_price": round(armor_stage2, 6),
                "harvest_lock_price": round(harvest_lock, 6),
                "leverage": 5,
                "confluence_score": score,
                "confluence_reasons": confluence_reasons,
                "recommendation": recommendation,
                "is_origin": is_origin,
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
