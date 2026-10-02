"""
HERMES 3.5 APEX ORDER FLOW & DUAL-TIER MICRO-SNIPER ENGINE
===========================================================
Engineers the complete Quant Blueprint requested by the user:
1. PILLAR 1: Dual-Tier Sizing Architecture (Tier 1 Full Size vs Tier 2 Half Size)
   - Ensures trade frequency remains HIGH without discarding candidate setups.
   - Tier 1 (A+ Institutional God-Tier): Full $50 Margin (5x) when CVD & OI confirm.
   - Tier 2 (A Standard Structural): Half $25 Margin (5x) with Quick BE Armor (+1.0%)
     when CVD is neutral/pending. Cuts risk in half while keeping action active!
2. PILLAR 2: 15m Micro-Confirmation Trigger (The Sniper Gate)
   - Macro zone (4H/1H) defines WHERE to look (Order Block at 50% Mean Threshold).
   - Micro trigger validates WHEN to enter: rejects runaway momentum knives & rockets
     (like today's FET/APT traps) by requiring a minimum rejection reaction.
3. PILLAR 3: Universe Expansion (Top-45 Liquid Champions)
   - Expands opportunity flow from 22 to 45 high-volume institutional movers.
"""

from typing import Dict, Any, List, Optional, Tuple

TOP_45_CHAMPIONS = [
    # Top-22 Baseline Champions
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT",
    # 23 Extended High-Volume Institutional Movers
    "SOLUSDT", "ETHUSDT", "BNBUSDT", "LINKUSDT", "INJUSDT", "TIAUSDT", "SEIUSDT", "ARBUSDT",
    "PEPEUSDT", "WIFUSDT", "BONKUSDT", "DOTUSDT", "ADAUSDT", "PENDLEUSDT", "KASUSDT", "JUPUSDT",
    "ENAUSDT", "ONDOUSDT", "TAOUSDT", "CRVUSDT", "LTCUSDT", "STXUSDT", "PEOPLEUSDT"
]

class Hermes35OrderFlowEngine:
    def __init__(self):
        self.version = "HERMES_3.5_DUAL_TIER_SNIPER"
        self.is_experimental = True

    def calculate_candle_order_flow(self, candle: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates taker buy vs sell delta ratio for a candlestick."""
        h = float(candle["high"])
        l = float(candle["low"])
        c = float(candle["close"])
        v = float(candle.get("volume", 0.0))
        rng = h - l
        if rng > 0:
            d_ratio = (c - l) / rng
            delta = v * (2.0 * d_ratio - 1.0)
        else:
            d_ratio = 0.50
            delta = 0.0
        return {
            "delta_ratio": d_ratio,
            "delta": delta,
            "volume": v
        }

    def evaluate_15m_micro_sniper_gate(
        self,
        tap_candle: Dict[str, Any],
        side: str
    ) -> Tuple[bool, str]:
        """
        Pillar 2: 15m Micro-Confirmation Trigger.
        Validates that the mitigation candle is NOT a runaway momentum train:
        - For LONG: Rejects falling knives (must have >=15% lower wick OR close >= open).
        - For SHORT: Rejects runaway rockets (must have >=15% upper wick OR close <= open).
        """
        h = float(tap_candle["high"])
        l = float(tap_candle["low"])
        o = float(tap_candle["open"])
        c = float(tap_candle["close"])
        rng = h - l
        if rng <= 0:
            return True, "Flat candle"

        is_long = side.upper() in ("BUY", "LONG")

        if is_long:
            l_wick = min(o, c) - l
            w_ratio = l_wick / rng
            is_green = c >= o
            # Pass if lower wick >= 15% OR candle closed green
            if w_ratio >= 0.15 or is_green:
                return True, f"SNIPER PASS: Lower Wick {w_ratio*100:.1f}% or Bullish Close"
            return False, f"SNIPER VETO: Falling Knife (Lower Wick {w_ratio*100:.1f}%, Heavy Red Close)"
        else:
            u_wick = h - max(o, c)
            w_ratio = u_wick / rng
            is_red = c <= o
            # Pass if upper wick >= 15% OR candle closed red
            if w_ratio >= 0.15 or is_red:
                return True, f"SNIPER PASS: Upper Wick {w_ratio*100:.1f}% or Bearish Close"
            return False, f"SNIPER VETO: Runaway Rocket (Upper Wick {w_ratio*100:.1f}%, Heavy Green Close)"

    def classify_dual_tier_setup(
        self,
        candles: List[Dict[str, Any]],
        tap_idx: int,
        side: str
    ) -> Dict[str, Any]:
        """
        Pillar 1: Dual-Tier Sizing & Risk Allocation.
        Classifies candidate setup into TIER 1 (A+ Institutional) or TIER 2 (A Structural):
        - Tier 1: CVD Delta Aligned + Volume Participation -> Full $50 Margin (1.0x).
        - Tier 2: Structural 50% MT without full CVD alignment -> Half $25 Margin (0.5x), Faster BE Armor (+1.0%).
        """
        if tap_idx < 3 or tap_idx >= len(candles):
            return {
                "tier": "TIER_2_STRUCTURAL",
                "tier_name": "Tier 2 (Structural Half-Size)",
                "margin_mult": 0.50,
                "be_lock_pct": 0.010,
                "trail_lock_pct": 0.018,
                "cvd_confirmed": False,
                "metrics": {}
            }

        tap_c = candles[tap_idx]
        flow = self.calculate_candle_order_flow(tap_c)

        # 3-bar CVD slope
        running_cvd = 0.0
        cvd_history = []
        for i in range(max(0, tap_idx - 10), tap_idx + 1):
            f = self.calculate_candle_order_flow(candles[i])
            running_cvd += f["delta"]
            cvd_history.append(running_cvd)
            
        cvd_slope = cvd_history[-1] - cvd_history[-4] if len(cvd_history) >= 4 else 0.0

        # Volume vs 20-bar SMA
        vol_lookback = [float(candles[k].get("volume", 0.0)) for k in range(max(0, tap_idx - 20), tap_idx)]
        vol_sma20 = sum(vol_lookback) / len(vol_lookback) if vol_lookback else flow["volume"]
        vol_ratio = flow["volume"] / vol_sma20 if vol_sma20 > 0 else 1.0

        metrics = {
            "delta_ratio": round(flow["delta_ratio"], 3),
            "delta": round(flow["delta"], 2),
            "cvd_slope": round(cvd_slope, 2),
            "vol_ratio": round(vol_ratio, 2)
        }

        is_long = side.upper() in ("BUY", "LONG")

        if is_long:
            cvd_absorbed = (flow["delta_ratio"] >= 0.49 or flow["delta"] > 0)
            cvd_trending_up = cvd_slope > 0
            oi_participating = vol_ratio >= 0.85
            is_tier_1 = cvd_absorbed and cvd_trending_up and oi_participating
        else:
            cvd_exhausted = (flow["delta_ratio"] <= 0.51 or flow["delta"] < 0)
            cvd_trending_down = cvd_slope < 0
            oi_participating = vol_ratio >= 0.85
            is_tier_1 = cvd_exhausted and cvd_trending_down and oi_participating

        if is_tier_1:
            return {
                "tier": "TIER_1_INSTITUTIONAL",
                "tier_name": "Tier 1 (A+ Institutional Full-Size)",
                "margin_mult": 1.0,
                "be_lock_pct": 0.016,       # Standard +1.6% BE Lock
                "trail_lock_pct": 0.022,    # Standard +2.2% Trailing Lock
                "cvd_confirmed": True,
                "metrics": metrics
            }
        else:
            return {
                "tier": "TIER_2_STRUCTURAL",
                "tier_name": "Tier 2 (A Structural Half-Size Defensive)",
                "margin_mult": 0.50,        # Half size cuts risk by 50%
                "be_lock_pct": 0.010,       # Fast BE Lock at +1.0% to insulate capital
                "trail_lock_pct": 0.018,    # Earlier Trailing Lock at +1.8%
                "cvd_confirmed": False,
                "metrics": metrics
            }

hermes35_engine = Hermes35OrderFlowEngine()
