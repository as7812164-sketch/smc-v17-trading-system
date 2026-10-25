"""
===============================================================================
INDEPENDENT ICT & SMC QUANTITATIVE ENGINE
===============================================================================
A 100% standalone, mathematically rigorous Smart Money Concepts (SMC) and 
Inner Circle Trader (ICT) quantitative execution engine.

Modules Integrated:
1. FRACTAL ENGINE:
   - Inside Bar elimination (pure sub-structure noise removal).
   - Valid pullback validation (requires sweeping prior candle high/low).
2. STRUCTURE ENGINE:
   - Inducement (IDM) tracking: Swings confirmed ONLY after IDM sweep.
   - Break of Structure (BOS): Strict CANDLE BODY CLOSE requirement.
   - Liquidity Sweep (Turtle Soup Trap): Wick-only breaches classified as fakeouts.
   - Change of Character (CHoCH): Structural trend reversal detection.
3. LIQUIDITY POOL ENGINE:
   - Equal Highs (EQH) and Equal Lows (EQL) detection.
   - Trendline liquidity trails (retail liquidity pools).
   - Session extremes: PDH / PDL, Asian, London, and NY highs/lows.
4. ORDER FLOW & OB & FVG ENGINE:
   - 3-Candle Fair Value Gap (FVG) footprint & Consequent Encroachment (CE).
   - Extreme Origin Bedrock Order Block (OB).
   - The Unicorn Model: Breaker Block + FVG horizontal confluence overlap.
5. DISCOUNT / EQUILIBRIUM FILTER:
   - 40-bar / structural swing range calculation.
   - Strict rule: Disqualifies longs in Premium (>50%), shorts in Discount (<50%).
6. MICROSTRUCTURE ABSORPTION:
   - Rejection wick defense (>=18% wick threshold).
   - Taker Buy Delta absorption calculation.
7. PO3 / AMD ENGINE:
   - Power of 3 (Accumulation, Manipulation, Distribution).
   - Judas Swing sweep detection during London/NY opens.
8. INDEPENDENT ICT ORCHESTRATOR:
   - Complete unified pipeline producing institutional trade setups.
===============================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timezone
import math


# =============================================================================
# DATA STRUCTURES & DOMAIN MODELS
# =============================================================================

class TrendDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class SwingType(Enum):
    SWING_HIGH = "SWING_HIGH"
    SWING_LOW = "SWING_LOW"


class BreakType(Enum):
    BOS = "BOS"                       # Valid break with body close
    LIQUIDITY_SWEEP = "LIQUIDITY_SWEEP"  # Wick breach only (Turtle Soup Trap)
    CHOCH = "CHOCH"                   # Change of Character (trend flip)


class ZoneType(Enum):
    ORDER_BLOCK = "ORDER_BLOCK"
    BREAKER_BLOCK = "BREAKER_BLOCK"
    FVG = "FVG"
    UNICORN = "UNICORN"


class LiquidityType(Enum):
    EQH = "EQH"             # Equal Highs (Buy-side liquidity)
    EQL = "EQL"             # Equal Lows (Sell-side liquidity)
    TRENDLINE = "TRENDLINE" # Trendline retail liquidity trail
    PDH = "PDH"             # Previous Day High
    PDL = "PDL"             # Previous Day Low
    SESSION_HIGH = "SESSION_HIGH"
    SESSION_LOW = "SESSION_LOW"


class SignalType(Enum):
    EXTREME_BEDROCK_TAP = "EXTREME_BEDROCK_TAP"
    UNICORN_MODEL = "UNICORN_MODEL"
    TURTLE_SOUP_REVERSAL = "TURTLE_SOUP_REVERSAL"
    PO3_JUDAS_SWEEP = "PO3_JUDAS_SWEEP"


@dataclass
class Candle:
    index: int
    timestamp: int          # Epoch milliseconds or seconds
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    taker_buy_volume: Optional[float] = None

    @property
    def range(self) -> float:
        return max(self.high - self.low, 1e-9)

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low

    @property
    def upper_wick_pct(self) -> float:
        return self.upper_wick / self.range

    @property
    def lower_wick_pct(self) -> float:
        return self.lower_wick / self.range

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def taker_sell_volume(self) -> float:
        if self.taker_buy_volume is not None:
            return max(0.0, self.volume - self.taker_buy_volume)
        return self.volume * 0.5

    @property
    def taker_delta(self) -> float:
        """Net aggressive taker delta (Taker Buy - Taker Sell)."""
        if self.taker_buy_volume is not None:
            return self.taker_buy_volume - self.taker_sell_volume
        # Proxy based on close position within range if taker data omitted
        return (self.close - (self.high + self.low) / 2.0) / self.range * self.volume


@dataclass
class CleanCandle:
    """Mother candle representation after inside bar absorption."""
    candle: Candle
    original_indices: List[int] = field(default_factory=list)


@dataclass
class SwingPoint:
    index: int
    timestamp: int
    price: float
    swing_type: SwingType
    confirmed: bool = False
    confirmed_at_index: Optional[int] = None
    idm_price: Optional[float] = None
    swept: bool = False
    broken: bool = False


@dataclass
class StructureBreakEvent:
    index: int
    timestamp: int
    break_type: BreakType
    direction: TrendDirection
    broken_swing: SwingPoint
    break_candle: Candle
    price: float
    description: str


@dataclass
class LiquidityPool:
    pool_type: LiquidityType
    price: float
    candles: List[int]
    description: str
    swept: bool = False
    swept_at_index: Optional[int] = None


@dataclass
class FVG:
    index: int                   # Middle candle index
    direction: TrendDirection    # Bullish (gap up) or Bearish (gap down)
    high: float                  # Upper bound of gap
    low: float                   # Lower bound of gap
    consequent_encroachment: float  # 50% midpoint of gap
    mitigated: bool = False
    mitigated_at_index: Optional[int] = None
    invalidated: bool = False    # Closed completely through


@dataclass
class OrderBlock:
    index: int
    direction: TrendDirection    # BULLISH (demand) or BEARISH (supply)
    high: float
    low: float
    is_extreme_origin: bool
    mitigated: bool = False
    mitigated_at_index: Optional[int] = None
    violated: bool = False       # Displaced through (becomes Breaker Block candidate)
    violated_at_index: Optional[int] = None


@dataclass
class BreakerBlock:
    origin_ob: OrderBlock
    index: int                   # Candle index where OB was violated
    direction: TrendDirection    # Flipped direction: BULLISH breaker if bearish OB broken up
    high: float
    low: float
    mitigated: bool = False


@dataclass
class UnicornZone:
    index: int
    direction: TrendDirection
    high: float                  # Overlapping zone high
    low: float                   # Overlapping zone low
    breaker: BreakerBlock
    fvg: FVG


@dataclass
class ICTSignal:
    index: int
    timestamp: int
    signal_type: SignalType
    direction: TrendDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    equilibrium_status: str       # "DISCOUNT" or "PREMIUM"
    lower_wick_pct: float
    upper_wick_pct: float
    taker_delta: float
    confidence_score: float
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 1. FRACTAL ENGINE: VALID PULLBACK & INSIDE BAR ELIMINATION
# =============================================================================

class FractalEngine:
    """
    Identifies valid pullbacks and swing pivots according to institutional SMC:
    1. Inside Bars are strictly eliminated as sub-structure noise.
       An inside bar has High <= Prev_High and Low >= Prev_Low.
       It is absorbed into the mother candle.
    2. Valid Pullback Rule:
       - Upward impulse: A pullback is ONLY valid if price sweeps the LOW
         of the previous valid candle (low < prev.low).
       - Downward impulse: A pullback is ONLY valid if price sweeps the HIGH
         of the previous valid candle (high > prev.high).
    """

    @staticmethod
    def eliminate_inside_bars(candles: List[Candle]) -> List[CleanCandle]:
        """
        Filters out inside bars, absorbing them into mother bars.
        Returns a list of CleanCandle objects where every bar has either
        a higher high, lower low, or both (outside bar).
        """
        if not candles:
            return []

        clean: List[CleanCandle] = []
        mother = candles[0]
        absorbed_indices = [mother.index]

        for i in range(1, len(candles)):
            curr = candles[i]
            # Check if curr is inside mother bar
            is_inside = (curr.high <= mother.high) and (curr.low >= mother.low)

            if is_inside:
                # Absorbed into mother bar as internal noise
                absorbed_indices.append(curr.index)
            else:
                # Mother bar finalized, save it
                clean.append(CleanCandle(candle=mother, original_indices=absorbed_indices))
                # New mother bar
                mother = curr
                absorbed_indices = [curr.index]

        clean.append(CleanCandle(candle=mother, original_indices=absorbed_indices))
        return clean

    @staticmethod
    def is_valid_pullback(curr: Candle, prev: Candle, impulse_dir: TrendDirection) -> bool:
        """
        Verifies if current candle creates a mathematically valid pullback:
        - If previous move was BULLISH: must take out the previous candle's LOW.
        - If previous move was BEARISH: must take out the previous candle's HIGH.
        """
        if impulse_dir == TrendDirection.BULLISH:
            return curr.low < prev.low
        elif impulse_dir == TrendDirection.BEARISH:
            return curr.high > prev.high
        return False

    @staticmethod
    def find_fractal_pivots(clean_candles: List[CleanCandle]) -> Tuple[List[int], List[int]]:
        """
        Finds fractal highs and lows across clean candles.
        A fractal high has higher high than left and right.
        A fractal low has lower low than left and right.
        """
        high_indices: List[int] = []
        low_indices: List[int] = []

        if len(clean_candles) < 3:
            return high_indices, low_indices

        for i in range(1, len(clean_candles) - 1):
            c_prev = clean_candles[i - 1].candle
            c_curr = clean_candles[i].candle
            c_next = clean_candles[i + 1].candle

            if c_curr.high > c_prev.high and c_curr.high > c_next.high:
                high_indices.append(c_curr.index)

            if c_curr.low < c_prev.low and c_curr.low < c_next.low:
                low_indices.append(c_curr.index)

        return high_indices, low_indices


# =============================================================================
# 2. STRUCTURE ENGINE: INDUCEMENT (IDM), BOS VS LIQUIDITY SWEEP, CHOCH
# =============================================================================

class StructureEngine:
    """
    Implements the core ICT / SMC Structural Rules:
    1. Swing High/Low is confirmed ONLY after Inducement (IDM) is swept.
       - In Bullish trend: A higher high is NOT confirmed until price pulls back
         and sweeps the first valid pullback low (IDM).
       - In Bearish trend: A lower low is NOT confirmed until price pulls back
         and sweeps the first valid pullback high (IDM).
    2. Break of Structure (BOS):
       - Requires a STRICT CANDLE BODY CLOSE beyond the confirmed swing point.
       - A wick-only breach that closes back inside is classified as a
         `LIQUIDITY_SWEEP` (Turtle Soup Trap).
    3. Change of Character (CHoCH):
       - When price breaks the major opposing structural swing point with a body close.
    """

    def __init__(self):
        self.trend: TrendDirection = TrendDirection.NEUTRAL
        self.confirmed_highs: List[SwingPoint] = []
        self.confirmed_lows: List[SwingPoint] = []
        self.unconfirmed_high: Optional[SwingPoint] = None
        self.unconfirmed_low: Optional[SwingPoint] = None
        self.active_idm_low: Optional[float] = None
        self.active_idm_high: Optional[float] = None
        self.events: List[StructureBreakEvent] = []

    def process_candles(self, candles: List[Candle]) -> List[StructureBreakEvent]:
        """
        Processes candle sequence chronologically to track IDM, confirmed swings,
        BOS, and Turtle Soup Liquidity Sweeps.
        """
        if len(candles) < 3:
            return []

        # We first filter out inside bars to evaluate clean pullbacks
        clean_bars = FractalEngine.eliminate_inside_bars(candles)
        events: List[StructureBreakEvent] = []

        # Initialize reference points from early bars
        last_confirmed_high: Optional[SwingPoint] = None
        last_confirmed_low: Optional[SwingPoint] = None
        
        # Track candidate swings & inducement
        candidate_high: Optional[Candle] = None
        candidate_low: Optional[Candle] = None
        idm_low_candle: Optional[Candle] = None
        idm_high_candle: Optional[Candle] = None

        for i in range(1, len(clean_bars)):
            prev = clean_bars[i - 1].candle
            curr = clean_bars[i].candle

            # Check if curr reaches new high/low
            if candidate_high is None or curr.high > candidate_high.high:
                candidate_high = curr
                # Reset or update IDM candidate: when making a new high, the IDM will be
                # the first valid pullback low formed after this peak.
                idm_low_candle = None

            if candidate_low is None or curr.low < candidate_low.low:
                candidate_low = curr
                idm_high_candle = None

            # Detect valid pullback to define Inducement (IDM)
            # In bullish flow: if curr takes out prev.low, prev is the peak, curr.low begins pullback
            if candidate_high is not None and curr.index > candidate_high.index:
                if curr.low < prev.low:
                    if idm_low_candle is None:
                        idm_low_candle = curr
                    elif curr.low < idm_low_candle.low:
                        # Swept prior IDM low! Confirm candidate high
                        if (last_confirmed_high is None or candidate_high.index != last_confirmed_high.index):
                            confirmed_sp = SwingPoint(
                                index=candidate_high.index,
                                timestamp=candidate_high.timestamp,
                                price=candidate_high.high,
                                swing_type=SwingType.SWING_HIGH,
                                confirmed=True,
                                confirmed_at_index=curr.index,
                                idm_price=idm_low_candle.low
                            )
                            self.confirmed_highs.append(confirmed_sp)
                            last_confirmed_high = confirmed_sp
                        idm_low_candle = curr
                elif idm_low_candle is not None and curr.low < idm_low_candle.low:
                    # Swept IDM low!
                    if (last_confirmed_high is None or candidate_high.index != last_confirmed_high.index):
                        confirmed_sp = SwingPoint(
                            index=candidate_high.index,
                            timestamp=candidate_high.timestamp,
                            price=candidate_high.high,
                            swing_type=SwingType.SWING_HIGH,
                            confirmed=True,
                            confirmed_at_index=curr.index,
                            idm_price=idm_low_candle.low
                        )
                        self.confirmed_highs.append(confirmed_sp)
                        last_confirmed_high = confirmed_sp
                        idm_low_candle = None

            # In bearish flow: if curr takes out prev.high, prev is the trough, curr.high begins pullback
            if candidate_low is not None and curr.index > candidate_low.index:
                if curr.high > prev.high:
                    if idm_high_candle is None:
                        idm_high_candle = curr
                    elif curr.high > idm_high_candle.high:
                        # Swept prior IDM high! Confirm candidate low
                        if (last_confirmed_low is None or candidate_low.index != last_confirmed_low.index):
                            confirmed_sp = SwingPoint(
                                index=candidate_low.index,
                                timestamp=candidate_low.timestamp,
                                price=candidate_low.low,
                                swing_type=SwingType.SWING_LOW,
                                confirmed=True,
                                confirmed_at_index=curr.index,
                                idm_price=idm_high_candle.high
                            )
                            self.confirmed_lows.append(confirmed_sp)
                            last_confirmed_low = confirmed_sp
                        idm_high_candle = curr
                elif idm_high_candle is not None and curr.high > idm_high_candle.high:
                    # Swept IDM high!
                    if (last_confirmed_low is None or candidate_low.index != last_confirmed_low.index):
                        confirmed_sp = SwingPoint(
                            index=candidate_low.index,
                            timestamp=candidate_low.timestamp,
                            price=candidate_low.low,
                            swing_type=SwingType.SWING_LOW,
                            confirmed=True,
                            confirmed_at_index=curr.index,
                            idm_price=idm_high_candle.high
                        )
                        self.confirmed_lows.append(confirmed_sp)
                        last_confirmed_low = confirmed_sp
                        idm_high_candle = None

            # -------------------------------------------------------------
            # 2. BREAK OF STRUCTURE (BOS) vs LIQUIDITY SWEEP (TURTLE SOUP)
            # -------------------------------------------------------------
            # Check breach of last confirmed Swing High
            if last_confirmed_high and not last_confirmed_high.broken and not last_confirmed_high.swept:
                if curr.high > last_confirmed_high.price:
                    # Price penetrated the confirmed swing high!
                    # Rule: Strict Candle Body Close required for BOS.
                    if curr.close > last_confirmed_high.price:
                        # VALID BULLISH BOS
                        last_confirmed_high.broken = True
                        self.trend = TrendDirection.BULLISH
                        evt = StructureBreakEvent(
                            index=curr.index,
                            timestamp=curr.timestamp,
                            break_type=BreakType.BOS,
                            direction=TrendDirection.BULLISH,
                            broken_swing=last_confirmed_high,
                            break_candle=curr,
                            price=curr.close,
                            description=f"Bullish BOS: Body closed at {curr.close:.4f} > High {last_confirmed_high.price:.4f}"
                        )
                        events.append(evt)
                        self.events.append(evt)
                    else:
                        # Wick breach only: TURTLE SOUP LIQUIDITY SWEEP
                        last_confirmed_high.swept = True
                        evt = StructureBreakEvent(
                            index=curr.index,
                            timestamp=curr.timestamp,
                            break_type=BreakType.LIQUIDITY_SWEEP,
                            direction=TrendDirection.BEARISH,  # Liquidity sweep generates counter-trend trap
                            broken_swing=last_confirmed_high,
                            break_candle=curr,
                            price=curr.high,
                            description=f"Turtle Soup Sweep: Wick {curr.high:.4f} > High {last_confirmed_high.price:.4f}, but Body Closed {curr.close:.4f}"
                        )
                        events.append(evt)
                        self.events.append(evt)

            # Check breach of last confirmed Swing Low
            if last_confirmed_low and not last_confirmed_low.broken and not last_confirmed_low.swept:
                if curr.low < last_confirmed_low.price:
                    # Price penetrated confirmed swing low!
                    # Rule: Strict Candle Body Close required for BOS.
                    if curr.close < last_confirmed_low.price:
                        # VALID BEARISH BOS
                        last_confirmed_low.broken = True
                        self.trend = TrendDirection.BEARISH
                        evt = StructureBreakEvent(
                            index=curr.index,
                            timestamp=curr.timestamp,
                            break_type=BreakType.BOS,
                            direction=TrendDirection.BEARISH,
                            broken_swing=last_confirmed_low,
                            break_candle=curr,
                            price=curr.close,
                            description=f"Bearish BOS: Body closed at {curr.close:.4f} < Low {last_confirmed_low.price:.4f}"
                        )
                        events.append(evt)
                        self.events.append(evt)
                    else:
                        # Wick breach only: TURTLE SOUP LIQUIDITY SWEEP
                        last_confirmed_low.swept = True
                        evt = StructureBreakEvent(
                            index=curr.index,
                            timestamp=curr.timestamp,
                            break_type=BreakType.LIQUIDITY_SWEEP,
                            direction=TrendDirection.BULLISH,  # Liquidity sweep generates counter-trend trap
                            broken_swing=last_confirmed_low,
                            break_candle=curr,
                            price=curr.low,
                            description=f"Turtle Soup Sweep: Wick {curr.low:.4f} < Low {last_confirmed_low.price:.4f}, but Body Closed {curr.close:.4f}"
                        )
                        events.append(evt)
                        self.events.append(evt)

        return events


# =============================================================================
# 3. LIQUIDITY POOL ENGINE: EQH, EQL, TRENDLINE & SESSION EXTREMES
# =============================================================================

class LiquidityEngine:
    """
    Identifies institutional liquidity pools where retail stop orders accumulate:
    1. Equal Highs (EQH) - Buy-Side Liquidity (BSL)
    2. Equal Lows (EQL) - Sell-Side Liquidity (SSL)
    3. Trendline Liquidity Trails (3+ pivot touches)
    4. Session Extremes (Previous Day High/Low, Session Highs/Lows)
    """

    def __init__(self, eq_tolerance_pct: float = 0.0015):
        # 0.15% threshold for equal highs/lows
        self.eq_tolerance_pct = eq_tolerance_pct
        self.pools: List[LiquidityPool] = []

    def detect_equal_highs_lows(self, candles: List[Candle]) -> List[LiquidityPool]:
        """
        Scans for clusters of highs or lows that are within the tolerance threshold.
        """
        if len(candles) < 5:
            return []

        clean_bars = FractalEngine.eliminate_inside_bars(candles)
        h_idx, l_idx = FractalEngine.find_fractal_pivots(clean_bars)
        
        pools: List[LiquidityPool] = []

        # Find Equal Highs (EQH)
        candle_map = {c.index: c for c in candles}
        for i in range(len(h_idx)):
            for j in range(i + 1, min(i + 6, len(h_idx))):
                idx1, idx2 = h_idx[i], h_idx[j]
                c1, c2 = candle_map[idx1], candle_map[idx2]
                diff = abs(c1.high - c2.high) / max(c1.high, 1e-9)

                if diff <= self.eq_tolerance_pct:
                    avg_price = (c1.high + c2.high) / 2.0
                    pools.append(LiquidityPool(
                        pool_type=LiquidityType.EQH,
                        price=avg_price,
                        candles=[idx1, idx2],
                        description=f"EQH Buy-Side Liquidity at {avg_price:.4f} (diff {diff*100:.3f}%)"
                    ))

        # Find Equal Lows (EQL)
        for i in range(len(l_idx)):
            for j in range(i + 1, min(i + 6, len(l_idx))):
                idx1, idx2 = l_idx[i], l_idx[j]
                c1, c2 = candle_map[idx1], candle_map[idx2]
                diff = abs(c1.low - c2.low) / max(c1.low, 1e-9)

                if diff <= self.eq_tolerance_pct:
                    avg_price = (c1.low + c2.low) / 2.0
                    pools.append(LiquidityPool(
                        pool_type=LiquidityType.EQL,
                        price=avg_price,
                        candles=[idx1, idx2],
                        description=f"EQL Sell-Side Liquidity at {avg_price:.4f} (diff {diff*100:.3f}%)"
                    ))

        self.pools.extend(pools)
        return pools

    def detect_trendline_liquidity(self, candles: List[Candle]) -> List[LiquidityPool]:
        """
        Identifies trendline liquidity trails with >= 3 progressive touches.
        """
        clean_bars = FractalEngine.eliminate_inside_bars(candles)
        h_idx, l_idx = FractalEngine.find_fractal_pivots(clean_bars)
        candle_map = {c.index: c for c in candles}
        pools: List[LiquidityPool] = []

        # Ascending support trendline (retail trail stops below)
        if len(l_idx) >= 3:
            for i in range(len(l_idx) - 2):
                p1, p2, p3 = candle_map[l_idx[i]], candle_map[l_idx[i+1]], candle_map[l_idx[i+2]]
                if p1.low < p2.low < p3.low:
                    # Check linearity
                    slope = (p3.low - p1.low) / max(p3.index - p1.index, 1)
                    expected_p2 = p1.low + slope * (p2.index - p1.index)
                    if abs(p2.low - expected_p2) / p2.low < 0.005:
                        pools.append(LiquidityPool(
                            pool_type=LiquidityType.TRENDLINE,
                            price=p3.low,
                            candles=[p1.index, p2.index, p3.index],
                            description="Ascending Retail Trendline Liquidity Trail (Sell Stops Engineered Below)"
                        ))

        return pools

    @staticmethod
    def extract_session_extremes(candles: List[Candle]) -> Dict[str, float]:
        """
        Extracts Previous Day High (PDH) and Previous Day Low (PDL)
        or rolling session extremes.
        """
        if not candles:
            return {"PDH": 0.0, "PDL": 0.0}

        # Last 24 hourly candles or full set
        window = candles[-24:] if len(candles) >= 24 else candles
        pdh = max(c.high for c in window)
        pdl = min(c.low for c in window)
        return {"PDH": pdh, "PDL": pdl}


# =============================================================================
# 4. ORDER FLOW ENGINE: 3-CANDLE FVG, BEDROCK OB, & THE UNICORN MODEL
# =============================================================================

class OrderFlowEngine:
    """
    Implements Order Flow Institutional Footprints:
    1. 3-Candle Fair Value Gap (FVG):
       - Bullish FVG: Candle 1 High < Candle 3 Low (Gap = [C1.High, C3.Low]).
       - Bearish FVG: Candle 1 Low > Candle 3 High (Gap = [C3.High, C1.Low]).
       - Consequent Encroachment (CE): 50% midpoint.
    2. Extreme Origin Bedrock Order Block (OB):
       - The unmitigated order block at the root/origin of the impulse that broke structure.
    3. The Unicorn Model:
       - Confluence of Breaker Block (failed/swept OB) + Fair Value Gap in the same zone!
    """

    def __init__(self, min_fvg_size_pct: float = 0.0005):
        self.min_fvg_size_pct = min_fvg_size_pct
        self.fvgs: List[FVG] = []
        self.order_blocks: List[OrderBlock] = []
        self.breaker_blocks: List[BreakerBlock] = []
        self.unicorn_zones: List[UnicornZone] = []

    def detect_fvg(self, candles: List[Candle]) -> List[FVG]:
        """
        Detects 3-candle Fair Value Gaps across the candle series.
        """
        if len(candles) < 3:
            return []

        fvgs: List[FVG] = []
        for i in range(len(candles) - 2):
            c1 = candles[i]
            c2 = candles[i + 1]  # The displacement candle
            c3 = candles[i + 2]

            # Bullish FVG (C1 High < C3 Low)
            if c1.high < c3.low:
                gap_size = (c3.low - c1.high) / c1.high
                if gap_size >= self.min_fvg_size_pct:
                    ce = (c1.high + c3.low) / 2.0
                    fvg = FVG(
                        index=c2.index,
                        direction=TrendDirection.BULLISH,
                        high=c3.low,
                        low=c1.high,
                        consequent_encroachment=ce
                    )
                    fvgs.append(fvg)

            # Bearish FVG (C1 Low > C3 High)
            elif c1.low > c3.high:
                gap_size = (c1.low - c3.high) / c1.low
                if gap_size >= self.min_fvg_size_pct:
                    ce = (c1.low + c3.high) / 2.0
                    fvg = FVG(
                        index=c2.index,
                        direction=TrendDirection.BEARISH,
                        high=c1.low,
                        low=c3.high,
                        consequent_encroachment=ce
                    )
                    fvgs.append(fvg)

        self.fvgs.extend(fvgs)
        return fvgs

    def update_fvg_mitigations(self, candles: List[Candle]) -> None:
        """
        Tracks whether active FVGs have been mitigated or invalidated.
        """
        candle_map = {c.index: c for c in candles}
        for fvg in self.fvgs:
            if fvg.mitigated:
                continue

            for c in candles:
                if c.index <= fvg.index + 1:
                    continue

                if fvg.direction == TrendDirection.BULLISH:
                    # Price dips into gap
                    if c.low <= fvg.high:
                        fvg.mitigated = True
                        fvg.mitigated_at_index = c.index
                        # Fully invalidated if body closes below gap low
                        if c.close < fvg.low:
                            fvg.invalidated = True
                        break
                elif fvg.direction == TrendDirection.BEARISH:
                    # Price rallies into gap
                    if c.high >= fvg.low:
                        fvg.mitigated = True
                        fvg.mitigated_at_index = c.index
                        # Fully invalidated if body closes above gap high
                        if c.close > fvg.high:
                            fvg.invalidated = True
                        break

    def detect_extreme_bedrock_ob(self, candles: List[Candle], bos_events: List[StructureBreakEvent]) -> List[OrderBlock]:
        """
        Traces back from a BOS to identify the Extreme Origin Bedrock Order Block.
        - Bullish BOS: The lowest bearish candle before the impulse up.
        - Bearish BOS: The highest bullish candle before the impulse down.
        """
        candle_map = {c.index: c for c in candles}
        obs: List[OrderBlock] = []

        for evt in bos_events:
            if evt.break_type != BreakType.BOS:
                continue

            origin_idx = evt.broken_swing.index
            break_idx = evt.break_candle.index

            # Search range between origin and break
            segment = [c for c in candles if origin_idx <= c.index <= break_idx]
            if not segment:
                continue

            if evt.direction == TrendDirection.BULLISH:
                # Find lowest candle (extreme origin)
                lowest_candle = min(segment, key=lambda c: c.low)
                # Find the last bearish candle at/near that low
                ob_candle = lowest_candle
                for c in reversed(segment[:segment.index(lowest_candle) + 1]):
                    if c.is_bearish:
                        ob_candle = c
                        break

                ob = OrderBlock(
                    index=ob_candle.index,
                    direction=TrendDirection.BULLISH,
                    high=ob_candle.high,
                    low=ob_candle.low,
                    is_extreme_origin=True
                )
                obs.append(ob)

            elif evt.direction == TrendDirection.BEARISH:
                # Find highest candle (extreme origin)
                highest_candle = max(segment, key=lambda c: c.high)
                ob_candle = highest_candle
                for c in reversed(segment[:segment.index(highest_candle) + 1]):
                    if c.is_bullish:
                        ob_candle = c
                        break

                ob = OrderBlock(
                    index=ob_candle.index,
                    direction=TrendDirection.BEARISH,
                    high=ob_candle.high,
                    low=ob_candle.low,
                    is_extreme_origin=True
                )
                obs.append(ob)

        self.order_blocks.extend(obs)
        return obs

    def detect_breakers_and_unicorns(self, candles: List[Candle]) -> Tuple[List[BreakerBlock], List[UnicornZone]]:
        """
        Identifies Breaker Blocks and The Unicorn Model:
        1. Breaker Block: An Order Block that was violated with displacement.
           - Bearish OB broken upwards -> Bullish Breaker
           - Bullish OB broken downwards -> Bearish Breaker
        2. Unicorn Setup: Horizontal confluence where Breaker Block and FVG overlap!
        """
        breakers: List[BreakerBlock] = []
        unicorns: List[UnicornZone] = []

        candle_map = {c.index: c for c in candles}

        for ob in self.order_blocks:
            if ob.violated:
                continue

            for c in candles:
                if c.index <= ob.index:
                    continue

                if ob.direction == TrendDirection.BEARISH:
                    # Bearish OB broken by upward body close -> flips to Bullish Breaker
                    if c.close > ob.high:
                        ob.violated = True
                        ob.violated_at_index = c.index
                        bb = BreakerBlock(
                            origin_ob=ob,
                            index=c.index,
                            direction=TrendDirection.BULLISH,
                            high=ob.high,
                            low=ob.low
                        )
                        breakers.append(bb)
                        break

                elif ob.direction == TrendDirection.BULLISH:
                    # Bullish OB broken by downward body close -> flips to Bearish Breaker
                    if c.close < ob.low:
                        ob.violated = True
                        ob.violated_at_index = c.index
                        bb = BreakerBlock(
                            origin_ob=ob,
                            index=c.index,
                            direction=TrendDirection.BEARISH,
                            high=ob.high,
                            low=ob.low
                        )
                        breakers.append(bb)
                        break

        self.breaker_blocks.extend(breakers)

        # Find Unicorn Confluence: Breaker Block overlapping with an FVG
        for bb in breakers:
            for fvg in self.fvgs:
                if fvg.direction != bb.direction:
                    continue
                # Time proximity: FVG created around or after the breaker formation
                if abs(fvg.index - bb.index) > 10:
                    continue

                # Check horizontal price overlap: [bb.low, bb.high] overlaps [fvg.low, fvg.high]
                overlap_low = max(bb.low, fvg.low)
                overlap_high = min(bb.high, fvg.high)

                if overlap_low < overlap_high:
                    unicorn = UnicornZone(
                        index=max(bb.index, fvg.index),
                        direction=bb.direction,
                        high=overlap_high,
                        low=overlap_low,
                        breaker=bb,
                        fvg=fvg
                    )
                    unicorns.append(unicorn)

        self.unicorn_zones.extend(unicorns)
        return breakers, unicorns


# =============================================================================
# 5. DISCOUNT / EQUILIBRIUM FILTER
# =============================================================================

class EquilibriumFilter:
    """
    ICT 50% Rule:
    Measures the 40-bar swing range (or structural swing range).
    - Equilibrium (EQ) = (Range High + Range Low) / 2
    - Premium: Price > EQ (>50% range)
    - Discount: Price < EQ (<50% range)
    - Optimal Trade Entry (OTE): 62% - 79% retracement depth

    STRICT DIRECTIVE:
    - DISQUALIFIES ANY LONG IF PRICE IS IN PREMIUM.
    - DISQUALIFIES ANY SHORT IF PRICE IS IN DISCOUNT.
    """

    @staticmethod
    def calculate_range(candles: List[Candle], lookback: int = 40) -> Tuple[float, float, float]:
        """
        Returns (range_low, range_high, equilibrium).
        """
        window = candles[-lookback:] if len(candles) >= lookback else candles
        if not window:
            return 0.0, 0.0, 0.0

        r_low = min(c.low for c in window)
        r_high = max(c.high for c in window)
        eq = (r_low + r_high) / 2.0
        return r_low, r_high, eq

    @staticmethod
    def evaluate_pricing(price: float, r_low: float, r_high: float) -> str:
        """
        Returns 'DISCOUNT' if price <= equilibrium, otherwise 'PREMIUM'.
        """
        eq = (r_low + r_high) / 2.0
        return "DISCOUNT" if price <= eq else "PREMIUM"

    @staticmethod
    def is_valid_trade_location(direction: TrendDirection, price: float, r_low: float, r_high: float) -> bool:
        """
        Validates if setup complies with strict ICT Discount/Premium rules.
        """
        eq = (r_low + r_high) / 2.0
        if direction == TrendDirection.BULLISH:
            # Longs MUST be in Discount (<= 50%)
            return price <= eq
        elif direction == TrendDirection.BEARISH:
            # Shorts MUST be in Premium (>= 50%)
            return price >= eq
        return False


# =============================================================================
# 6. MICROSTRUCTURE ABSORPTION: WICK DEFENSE & TAKER BUY DELTA
# =============================================================================

class MicrostructureEngine:
    """
    Measures institutional absorption defending the zone:
    1. Rejection Wick:
       - Bullish defense requires Lower Wick >= 18% of total candle range.
       - Bearish defense requires Upper Wick >= 18% of total candle range.
    2. Taker Buy Delta:
       - Positive aggressive buy delta confirms demand absorption.
       - Negative delta confirms supply absorption.
    """

    def __init__(self, min_wick_pct: float = 0.18):
        self.min_wick_pct = min_wick_pct

    def verify_absorption(self, candle: Candle, direction: TrendDirection) -> Tuple[bool, Dict[str, float]]:
        """
        Verifies microstructure absorption defense.
        """
        stats = {
            "lower_wick_pct": candle.lower_wick_pct,
            "upper_wick_pct": candle.upper_wick_pct,
            "taker_delta": candle.taker_delta,
            "range": candle.range
        }

        if direction == TrendDirection.BULLISH:
            wick_pass = candle.lower_wick_pct >= self.min_wick_pct
            delta_pass = candle.taker_delta >= 0.0
            return (wick_pass and delta_pass), stats

        elif direction == TrendDirection.BEARISH:
            wick_pass = candle.upper_wick_pct >= self.min_wick_pct
            delta_pass = candle.taker_delta <= 0.0
            return (wick_pass and delta_pass), stats

        return False, stats


# =============================================================================
# 7. PO3 / AMD FILTER (Power of 3 & Judas Swings)
# =============================================================================

class PO3Phase(Enum):
    ACCUMULATION = "ACCUMULATION"    # Asian Session consolidation
    MANIPULATION = "MANIPULATION"    # London/NY Judas Swing sweep
    DISTRIBUTION = "DISTRIBUTION"    # Expansion toward target


@dataclass
class PO3JudasEvent:
    index: int
    timestamp: int
    phase: PO3Phase
    swept_extreme: str               # "ASIAN_HIGH" or "ASIAN_LOW"
    bias: TrendDirection             # Predicted distribution bias
    description: str


class PO3Engine:
    """
    ICT Power of 3 (PO3) / Accumulation-Manipulation-Distribution (AMD) Engine:
    - Asian Range (00:00 - 08:00 UTC): Accumulation phase.
    - London Open (08:00 - 11:00 UTC): Judas Swing (Manipulation phase).
      Sweeping Asian Low triggers Bullish Day distribution.
      Sweeping Asian High triggers Bearish Day distribution.
    - New York Open (12:00 - 15:00 UTC): Distribution phase.
    """

    def __init__(self):
        self.asian_high: Optional[float] = None
        self.asian_low: Optional[float] = None
        self.judas_events: List[PO3JudasEvent] = []

    def process_candle(self, candle: Candle) -> Optional[PO3JudasEvent]:
        """
        Evaluates UTC timestamp to track session phases and detect Judas Swings.
        """
        # Convert timestamp to UTC datetime
        dt = datetime.fromtimestamp(candle.timestamp / 1000.0 if candle.timestamp > 1e11 else candle.timestamp, tz=timezone.utc)
        hour = dt.hour

        # 00:00 - 08:00 UTC: Asian Accumulation
        if 0 <= hour < 8:
            if self.asian_high is None or candle.high > self.asian_high:
                self.asian_high = candle.high
            if self.asian_low is None or candle.low < self.asian_low:
                self.asian_low = candle.low
            return None

        # 08:00 - 12:00 UTC: London Open Judas Window
        if 8 <= hour < 12 and self.asian_high is not None and self.asian_low is not None:
            # Judas Sweep of Asian Low -> Bullish PO3 Manipulation complete
            if candle.low < self.asian_low and candle.close >= self.asian_low:
                evt = PO3JudasEvent(
                    index=candle.index,
                    timestamp=candle.timestamp,
                    phase=PO3Phase.MANIPULATION,
                    swept_extreme="ASIAN_LOW",
                    bias=TrendDirection.BULLISH,
                    description=f"London Judas Sweep of Asian Low ({self.asian_low:.4f}) -> Bullish Expansion Expected"
                )
                self.judas_events.append(evt)
                return evt

            # Judas Sweep of Asian High -> Bearish PO3 Manipulation complete
            elif candle.high > self.asian_high and candle.close <= self.asian_high:
                evt = PO3JudasEvent(
                    index=candle.index,
                    timestamp=candle.timestamp,
                    phase=PO3Phase.MANIPULATION,
                    swept_extreme="ASIAN_HIGH",
                    bias=TrendDirection.BEARISH,
                    description=f"London Judas Sweep of Asian High ({self.asian_high:.4f}) -> Bearish Expansion Expected"
                )
                self.judas_events.append(evt)
                return evt

        # Reset Asian range at new UTC day midnight
        if hour == 0 and dt.minute == 0:
            self.asian_high = candle.high
            self.asian_low = candle.low

        return None


# =============================================================================
# 8. MASTER ORCHESTRATOR: INDEPENDENT ICT ENGINE
# =============================================================================

class IndependentICTEngine:
    """
    Master ICT & SMC Quantitative Engine Orchestrator.
    Integrates all 8 masterclasses to generate verified institutional setups:
    1. EXTREME_BEDROCK_TAP
    2. UNICORN_MODEL (Breaker + FVG overlap)
    3. TURTLE_SOUP_REVERSAL (Liquidity Sweep trap)
    4. PO3_JUDAS_SWEEP
    """

    def __init__(
        self,
        lookback_range: int = 40,
        min_rejection_wick_pct: float = 0.18,
        min_fvg_size_pct: float = 0.0005,
        eq_tolerance_pct: float = 0.0015
    ):
        self.lookback_range = lookback_range
        self.fractal_engine = FractalEngine()
        self.structure_engine = StructureEngine()
        self.liquidity_engine = LiquidityEngine(eq_tolerance_pct=eq_tolerance_pct)
        self.order_flow_engine = OrderFlowEngine(min_fvg_size_pct=min_fvg_size_pct)
        self.eq_filter = EquilibriumFilter()
        self.microstructure_engine = MicrostructureEngine(min_wick_pct=min_rejection_wick_pct)
        self.po3_engine = PO3Engine()
        self.signals: List[ICTSignal] = []

    def run(self, raw_candles: List[Dict[str, Any]] | List[Candle]) -> Dict[str, Any]:
        """
        Executes complete institutional pipeline across candle history.
        """
        candles: List[Candle] = []
        for i, item in enumerate(raw_candles):
            if isinstance(item, Candle):
                candles.append(item)
            else:
                candles.append(Candle(
                    index=i,
                    timestamp=int(item.get("timestamp") or item.get("time") or i),
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=float(item.get("volume", 0.0)),
                    taker_buy_volume=(
                        float(item["taker_buy_volume"]) if "taker_buy_volume" in item and item["taker_buy_volume"] is not None
                        else (float(item["taker_buy"]) if "taker_buy" in item and item["taker_buy"] is not None else None)
                    )
                ))

        if len(candles) < 10:
            return {"status": "insufficient_data", "signals": []}

        # 1. Structure & Fractals
        structure_events = self.structure_engine.process_candles(candles)

        # 2. Liquidity Pools
        eq_pools = self.liquidity_engine.detect_equal_highs_lows(candles)
        trendline_pools = self.liquidity_engine.detect_trendline_liquidity(candles)

        # 3. Order Flow: FVGs, Bedrock OBs, Breakers, Unicorns
        fvgs = self.order_flow_engine.detect_fvg(candles)
        self.order_flow_engine.update_fvg_mitigations(candles)
        obs = self.order_flow_engine.detect_extreme_bedrock_ob(candles, structure_events)
        breakers, unicorns = self.order_flow_engine.detect_breakers_and_unicorns(candles)

        # 4. Signal Synthesis & Execution Checks
        signals: List[ICTSignal] = []

        for i in range(10, len(candles)):
            curr = candles[i]
            window = candles[:i+1]
            r_low, r_high, eq = self.eq_filter.calculate_range(window, self.lookback_range)
            pricing_state = self.eq_filter.evaluate_pricing(curr.close, r_low, r_high)

            # Check PO3 Session Judas Swings
            po3_evt = self.po3_engine.process_candle(curr)
            if po3_evt:
                valid_loc = self.eq_filter.is_valid_trade_location(po3_evt.bias, curr.close, r_low, r_high)
                if valid_loc:
                    wick_pass, stats = self.microstructure_engine.verify_absorption(curr, po3_evt.bias)
                    if wick_pass:
                        sl = curr.low if po3_evt.bias == TrendDirection.BULLISH else curr.high
                        tp = r_high if po3_evt.bias == TrendDirection.BULLISH else r_low
                        rr = abs(tp - curr.close) / max(abs(curr.close - sl), 1e-9)
                        sig = ICTSignal(
                            index=curr.index,
                            timestamp=curr.timestamp,
                            signal_type=SignalType.PO3_JUDAS_SWEEP,
                            direction=po3_evt.bias,
                            entry_price=curr.close,
                            stop_loss=sl,
                            take_profit=tp,
                            risk_reward=round(rr, 2),
                            equilibrium_status=pricing_state,
                            lower_wick_pct=round(stats["lower_wick_pct"], 4),
                            upper_wick_pct=round(stats["upper_wick_pct"], 4),
                            taker_delta=stats["taker_delta"],
                            confidence_score=0.92,
                            description=f"PO3 Judas Sweep: {po3_evt.description} in {pricing_state}",
                            metadata={"event": po3_evt}
                        )
                        signals.append(sig)

            # Check Turtle Soup Liquidity Sweeps
            for sevt in structure_events:
                if sevt.index == curr.index and sevt.break_type == BreakType.LIQUIDITY_SWEEP:
                    # Liquidity sweep generates counter-trend setup
                    dir_target = sevt.direction
                    valid_loc = self.eq_filter.is_valid_trade_location(dir_target, curr.close, r_low, r_high)
                    if valid_loc:
                        wick_pass, stats = self.microstructure_engine.verify_absorption(curr, dir_target)
                        if wick_pass:
                            sl = curr.low if dir_target == TrendDirection.BULLISH else curr.high
                            tp = r_high if dir_target == TrendDirection.BULLISH else r_low
                            rr = abs(tp - curr.close) / max(abs(curr.close - sl), 1e-9)
                            sig = ICTSignal(
                                index=curr.index,
                                timestamp=curr.timestamp,
                                signal_type=SignalType.TURTLE_SOUP_REVERSAL,
                                direction=dir_target,
                                entry_price=curr.close,
                                stop_loss=sl,
                                take_profit=tp,
                                risk_reward=round(rr, 2),
                                equilibrium_status=pricing_state,
                                lower_wick_pct=round(stats["lower_wick_pct"], 4),
                                upper_wick_pct=round(stats["upper_wick_pct"], 4),
                                taker_delta=stats["taker_delta"],
                                confidence_score=0.90,
                                description=f"Turtle Soup Reversal: {sevt.description} in {pricing_state}",
                                metadata={"structure_event": sevt}
                            )
                            signals.append(sig)

            # Check Unicorn Model Setups
            for uni in unicorns:
                if uni.index <= curr.index and not getattr(uni, "triggered", False):
                    # Check if price taps into unicorn zone
                    tapped = (curr.low <= uni.high and curr.high >= uni.low)
                    if tapped:
                        valid_loc = self.eq_filter.is_valid_trade_location(uni.direction, curr.close, r_low, r_high)
                        if valid_loc:
                            wick_pass, stats = self.microstructure_engine.verify_absorption(curr, uni.direction)
                            if wick_pass:
                                uni.triggered = True
                                sl = uni.low if uni.direction == TrendDirection.BULLISH else uni.high
                                tp = r_high if uni.direction == TrendDirection.BULLISH else r_low
                                rr = abs(tp - curr.close) / max(abs(curr.close - sl), 1e-9)
                                sig = ICTSignal(
                                    index=curr.index,
                                    timestamp=curr.timestamp,
                                    signal_type=SignalType.UNICORN_MODEL,
                                    direction=uni.direction,
                                    entry_price=curr.close,
                                    stop_loss=sl,
                                    take_profit=tp,
                                    risk_reward=round(rr, 2),
                                    equilibrium_status=pricing_state,
                                    lower_wick_pct=round(stats["lower_wick_pct"], 4),
                                    upper_wick_pct=round(stats["upper_wick_pct"], 4),
                                    taker_delta=stats["taker_delta"],
                                    confidence_score=0.95,
                                    description=f"The Unicorn Model: Breaker + FVG Tap [{uni.low:.4f} - {uni.high:.4f}] in {pricing_state}",
                                    metadata={"unicorn_zone": uni}
                                )
                                signals.append(sig)

            # Check Extreme Bedrock OB Taps
            for ob in obs:
                if ob.index < curr.index and not ob.mitigated:
                    # Check if candle taps OB zone
                    tapped = (curr.low <= ob.high and curr.high >= ob.low)
                    if tapped:
                        ob.mitigated = True
                        ob.mitigated_at_index = curr.index
                        valid_loc = self.eq_filter.is_valid_trade_location(ob.direction, curr.close, r_low, r_high)
                        if valid_loc:
                            wick_pass, stats = self.microstructure_engine.verify_absorption(curr, ob.direction)
                            if wick_pass:
                                sl = ob.low if ob.direction == TrendDirection.BULLISH else ob.high
                                tp = r_high if ob.direction == TrendDirection.BULLISH else r_low
                                rr = abs(tp - curr.close) / max(abs(curr.close - sl), 1e-9)
                                sig = ICTSignal(
                                    index=curr.index,
                                    timestamp=curr.timestamp,
                                    signal_type=SignalType.EXTREME_BEDROCK_TAP,
                                    direction=ob.direction,
                                    entry_price=curr.close,
                                    stop_loss=sl,
                                    take_profit=tp,
                                    risk_reward=round(rr, 2),
                                    equilibrium_status=pricing_state,
                                    lower_wick_pct=round(stats["lower_wick_pct"], 4),
                                    upper_wick_pct=round(stats["upper_wick_pct"], 4),
                                    taker_delta=stats["taker_delta"],
                                    confidence_score=0.88,
                                    description=f"Extreme Bedrock OB Tap [{ob.low:.4f} - {ob.high:.4f}] in {pricing_state}",
                                    metadata={"order_block": ob}
                                )
                                signals.append(sig)

        self.signals = signals

        return {
            "status": "success",
            "candles_analyzed": len(candles),
            "confirmed_highs": len(self.structure_engine.confirmed_highs),
            "confirmed_lows": len(self.structure_engine.confirmed_lows),
            "structure_events": len(structure_events),
            "liquidity_pools": len(eq_pools) + len(trendline_pools),
            "fvgs_detected": len(fvgs),
            "order_blocks": len(obs),
            "breaker_blocks": len(breakers),
            "unicorns": len(unicorns),
            "signals_generated": len(signals),
            "signals": signals
        }
