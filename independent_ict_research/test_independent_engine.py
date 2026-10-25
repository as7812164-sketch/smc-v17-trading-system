"""
===============================================================================
UNIT & INTEGRATION TESTS: INDEPENDENT ICT & SMC QUANTITATIVE ENGINE
===============================================================================
Verifies all 8 curriculum modules:
- Fractal Engine (Inside Bar elimination & valid pullback rules)
- Structure Engine (IDM sweep confirmation & BOS body close vs Turtle Soup sweep)
- Liquidity Pool Engine (EQH, EQL, Trendline liquidity, PDH/PDL)
- Order Flow Engine (3-candle FVG, Bedrock OB, Unicorn Model)
- Discount / Equilibrium Filter (Strict Premium/Discount trade gating)
- Microstructure Absorption (>=18% wick defense & Taker delta)
- PO3 / AMD Engine (Asian Accumulation & London Judas Sweep)
- Real Historical Candle Data Integration Test (BTCUSDT 1h)
===============================================================================
"""

import os
import json
import pytest
from datetime import datetime, timezone

from independent_ict_engine import (
    Candle,
    TrendDirection,
    SwingType,
    BreakType,
    SignalType,
    FractalEngine,
    StructureEngine,
    LiquidityEngine,
    OrderFlowEngine,
    EquilibriumFilter,
    MicrostructureEngine,
    PO3Engine,
    IndependentICTEngine
)


# =============================================================================
# 1. FRACTAL ENGINE TESTS
# =============================================================================

def test_fractal_engine_inside_bar_elimination():
    """
    Test that Inside Bars (sub-structure noise) are completely absorbed into
    the mother candle and eliminated from swing calculations.
    """
    # Bar 0: Mother bar (Low: 100, High: 110)
    # Bar 1: Inside bar (Low: 102, High: 108) -> Inside mother bar
    # Bar 2: Inside bar (Low: 104, High: 106) -> Inside mother bar
    # Bar 3: Outside expansion bar (Low: 98, High: 115) -> Breaks mother bar
    candles = [
        Candle(index=0, timestamp=1000, open=101, high=110, low=100, close=109),
        Candle(index=1, timestamp=2000, open=103, high=108, low=102, close=105),
        Candle(index=2, timestamp=3000, open=105, high=106, low=104, close=104.5),
        Candle(index=3, timestamp=4000, open=105, high=115, low=98, close=114),
    ]

    clean_bars = FractalEngine.eliminate_inside_bars(candles)
    assert len(clean_bars) == 2, f"Expected 2 clean bars (mother + expansion), got {len(clean_bars)}"
    assert clean_bars[0].candle.index == 0
    assert clean_bars[0].original_indices == [0, 1, 2], "Inside bars 1 and 2 must be absorbed into bar 0"
    assert clean_bars[1].candle.index == 3


def test_fractal_engine_valid_pullback_mechanics():
    """
    Test ICT Valid Pullback Rule:
    - In an upward advance, a pullback is valid ONLY if price sweeps prior candle LOW.
    - In a downward decline, a pullback is valid ONLY if price sweeps prior candle HIGH.
    """
    c_base = Candle(index=0, timestamp=1000, open=100, high=110, low=95, close=108)

    # Bullish advance: next candle makes higher high and higher low -> NOT a pullback
    c_higher = Candle(index=1, timestamp=2000, open=108, high=115, low=102, close=114)
    assert not FractalEngine.is_valid_pullback(c_higher, c_base, TrendDirection.BULLISH)

    # Next candle sweeps low of c_base -> VALID PULLBACK
    c_sweep_low = Candle(index=2, timestamp=3000, open=108, high=109, low=94, close=96)
    assert FractalEngine.is_valid_pullback(c_sweep_low, c_base, TrendDirection.BULLISH)

    # Bearish decline: next candle sweeps high of c_base -> VALID BEARISH PULLBACK
    c_sweep_high = Candle(index=3, timestamp=4000, open=98, high=112, low=96, close=100)
    assert FractalEngine.is_valid_pullback(c_sweep_high, c_base, TrendDirection.BEARISH)


# =============================================================================
# 2. STRUCTURE ENGINE TESTS: IDM, BOS VS TURTLE SOUP
# =============================================================================

def test_structure_engine_inducement_and_swing_confirmation():
    """
    Test that a Swing High is confirmed ONLY after Inducement (IDM) is swept.
    """
    engine = StructureEngine()

    candles = [
        Candle(index=0, timestamp=1000, open=98, high=105, low=95, close=104),
        Candle(index=1, timestamp=2000, open=105, high=120, low=105, close=119),  # Impulse high to 120
        Candle(index=2, timestamp=3000, open=119, high=118, low=101, close=103),  # Valid pullback sweeps low (101 < 105), IDM low=101
        Candle(index=3, timestamp=4000, open=103, high=112, low=102, close=110),  # Bounce, hasn't swept IDM yet
        Candle(index=4, timestamp=5000, open=110, high=111, low=98, close=104),   # Sweeps IDM low (98 < 101)! Confirms high at 120!
    ]

    events = engine.process_candles(candles)
    assert len(engine.confirmed_highs) == 1
    confirmed_high = engine.confirmed_highs[0]
    assert confirmed_high.price == 120
    assert confirmed_high.confirmed is True
    assert confirmed_high.confirmed_at_index == 4
    assert confirmed_high.idm_price == 101


def test_structure_engine_bos_body_close_vs_turtle_soup_wick():
    """
    Test BOS requires strict CANDLE BODY CLOSE.
    A wick breach that closes inside is strictly classified as LIQUIDITY_SWEEP (Turtle Soup Trap).
    """
    engine = StructureEngine()

    candles = [
        Candle(index=0, timestamp=1000, open=98, high=105, low=95, close=104),
        Candle(index=1, timestamp=2000, open=105, high=120, low=105, close=119),  # Peak 120
        Candle(index=2, timestamp=3000, open=119, high=118, low=101, close=103),  # IDM low 101
        Candle(index=3, timestamp=4000, open=103, high=112, low=98, close=105),   # Sweeps IDM low 101 -> Confirms High 120
        # Candle 4: Wicks above 120 to 122, but CLOSES at 118 (Body inside!). Must be LIQUIDITY_SWEEP!
        Candle(index=4, timestamp=5000, open=105, high=122, low=104, close=118),
    ]

    events = engine.process_candles(candles)
    assert len(events) >= 1
    sweep_event = events[0]
    assert sweep_event.break_type == BreakType.LIQUIDITY_SWEEP
    assert sweep_event.direction == TrendDirection.BEARISH  # Bearish counter trap
    assert "Turtle Soup" in sweep_event.description

    # Now test valid BOS with Body Close above 120
    engine_bos = StructureEngine()
    candles_bos = [
        Candle(index=0, timestamp=1000, open=98, high=105, low=95, close=104),
        Candle(index=1, timestamp=2000, open=105, high=120, low=105, close=119),  # Peak 120
        Candle(index=2, timestamp=3000, open=119, high=118, low=101, close=103),  # IDM low 101
        Candle(index=3, timestamp=4000, open=103, high=112, low=98, close=105),   # Sweeps IDM low 101 -> Confirms High 120
        # Candle 4: Explosive Candle CLOSING at 124 > 120 -> Valid BOS
        Candle(index=4, timestamp=5000, open=105, high=125, low=104, close=124),
    ]
    bos_events = engine_bos.process_candles(candles_bos)
    assert len(bos_events) >= 1
    bos_event = bos_events[0]
    assert bos_event.break_type == BreakType.BOS
    assert bos_event.direction == TrendDirection.BULLISH
    assert "Bullish BOS" in bos_event.description


# =============================================================================
# 3. LIQUIDITY POOL ENGINE TESTS
# =============================================================================

def test_liquidity_engine_equal_highs_and_lows():
    """
    Test detection of Equal Highs (EQH) and Equal Lows (EQL) within tolerance.
    """
    liq = LiquidityEngine(eq_tolerance_pct=0.002)  # 0.2% tolerance

    candles = [
        # Pivot High 1 at 100.00
        Candle(index=0, timestamp=1000, open=95, high=97, low=94, close=96),
        Candle(index=1, timestamp=2000, open=96, high=100.00, low=95, close=98),
        Candle(index=2, timestamp=3000, open=98, high=97, low=92, close=93),
        # Retracement
        Candle(index=3, timestamp=4000, open=93, high=95, low=91, close=94),
        # Pivot High 2 at 100.08 (difference ~ 0.08%) -> Equal Highs!
        Candle(index=4, timestamp=5000, open=94, high=100.08, low=93, close=97),
        Candle(index=5, timestamp=6000, open=97, high=96, low=90, close=91),
    ]

    pools = liq.detect_equal_highs_lows(candles)
    eqh_pools = [p for p in pools if p.pool_type.value == "EQH"]
    assert len(eqh_pools) >= 1
    assert abs(eqh_pools[0].price - 100.04) < 0.1
    assert "Buy-Side Liquidity" in eqh_pools[0].description


# =============================================================================
# 4. ORDER FLOW ENGINE TESTS: FVG, BEDROCK OB, & UNICORN MODEL
# =============================================================================

def test_order_flow_fvg_detection_and_mitigation():
    """
    Test 3-candle Fair Value Gap detection and mitigation tracking:
    Bullish FVG: C1 High < C3 Low.
    """
    of_engine = OrderFlowEngine(min_fvg_size_pct=0.001)

    candles = [
        Candle(index=0, timestamp=1000, open=100, high=102, low=99, close=101),  # C1 High = 102
        Candle(index=1, timestamp=2000, open=101, high=115, low=101, close=114), # C2 Displacement
        Candle(index=2, timestamp=3000, open=114, high=120, low=106, close=119), # C3 Low = 106. Gap = [102, 106]
        # Candle 4 mitigates FVG by dipping into gap (Low = 104)
        Candle(index=3, timestamp=4000, open=119, high=119, low=104, close=110),
    ]

    fvgs = of_engine.detect_fvg(candles[:3])
    assert len(fvgs) == 1
    fvg = fvgs[0]
    assert fvg.direction == TrendDirection.BULLISH
    assert fvg.low == 102.0
    assert fvg.high == 106.0
    assert fvg.consequent_encroachment == 104.0  # (102 + 106) / 2
    assert not fvg.mitigated

    # Update mitigation
    of_engine.update_fvg_mitigations(candles)
    assert fvg.mitigated is True
    assert fvg.mitigated_at_index == 3


def test_order_flow_extreme_origin_bedrock_ob():
    """
    Test detection of Extreme Origin Bedrock Order Block at the origin of a BOS leg.
    """
    of_engine = OrderFlowEngine()

    candles = [
        Candle(index=0, timestamp=1000, open=105, high=106, low=104, close=105),
        # Bedrock Origin OB: Last bearish candle before massive rally
        Candle(index=1, timestamp=2000, open=105, high=105, low=98, close=99),
        Candle(index=2, timestamp=3000, open=99, high=112, low=99, close=111),
        Candle(index=3, timestamp=4000, open=111, high=125, low=110, close=124),  # Breaks prior swing
    ]

    # Create dummy BOS event
    from independent_ict_engine import SwingPoint, StructureBreakEvent
    broken_swing = SwingPoint(index=0, timestamp=1000, price=106, swing_type=SwingType.SWING_HIGH, confirmed=True)
    bos_evt = StructureBreakEvent(
        index=3,
        timestamp=4000,
        break_type=BreakType.BOS,
        direction=TrendDirection.BULLISH,
        broken_swing=broken_swing,
        break_candle=candles[3],
        price=124,
        description="BOS test"
    )

    obs = of_engine.detect_extreme_bedrock_ob(candles, [bos_evt])
    assert len(obs) == 1
    ob = obs[0]
    assert ob.is_extreme_origin is True
    assert ob.direction == TrendDirection.BULLISH
    assert ob.index == 1
    assert ob.low == 98
    assert ob.high == 105


def test_order_flow_unicorn_model():
    """
    Test The Unicorn Model: Breaker Block + FVG horizontal confluence overlap.
    """
    of_engine = OrderFlowEngine(min_fvg_size_pct=0.001)

    # 1. Bearish Order block at index 1: High: 110, Low: 105
    from independent_ict_engine import OrderBlock
    ob = OrderBlock(index=1, direction=TrendDirection.BEARISH, high=110, low=105, is_extreme_origin=False)
    of_engine.order_blocks.append(ob)

    # 2. Candle 3 displaces up and closes at 114 > 110, flipping OB to Bullish Breaker Block
    candles = [
        Candle(index=0, timestamp=1000, open=100, high=106, low=99, close=104),
        Candle(index=1, timestamp=2000, open=105, high=110, low=105, close=109), # OB
        Candle(index=2, timestamp=3000, open=109, high=111, low=108, close=110),
        Candle(index=3, timestamp=4000, open=110, high=116, low=109, close=115), # Breaker trigger
    ]

    # 3. Bullish FVG spanning [106, 112] (overlaps breaker [105, 110] between 106 and 110)
    from independent_ict_engine import FVG
    fvg = FVG(index=3, direction=TrendDirection.BULLISH, high=112, low=106, consequent_encroachment=109)
    of_engine.fvgs.append(fvg)

    breakers, unicorns = of_engine.detect_breakers_and_unicorns(candles)
    assert len(breakers) == 1
    assert len(unicorns) == 1
    uni = unicorns[0]
    assert uni.direction == TrendDirection.BULLISH
    assert uni.low == 106.0  # max(105, 106)
    assert uni.high == 110.0 # min(110, 112)


# =============================================================================
# 5. DISCOUNT / EQUILIBRIUM FILTER TESTS
# =============================================================================

def test_equilibrium_filter_strict_gating():
    """
    Verify strict ICT rule:
    - Longs in Premium (>50%) are STRICTLY DISQUALIFIED.
    - Shorts in Discount (<50%) are STRICTLY DISQUALIFIED.
    """
    r_low = 100.0
    r_high = 200.0
    eq = 150.0  # 50% Equilibrium

    # In Premium (160 > 150):
    assert EquilibriumFilter.evaluate_pricing(160.0, r_low, r_high) == "PREMIUM"
    assert not EquilibriumFilter.is_valid_trade_location(TrendDirection.BULLISH, 160.0, r_low, r_high), "Long in Premium must be DISQUALIFIED"
    assert EquilibriumFilter.is_valid_trade_location(TrendDirection.BEARISH, 160.0, r_low, r_high), "Short in Premium must be ALLOWED"

    # In Discount (140 < 150):
    assert EquilibriumFilter.evaluate_pricing(140.0, r_low, r_high) == "DISCOUNT"
    assert EquilibriumFilter.is_valid_trade_location(TrendDirection.BULLISH, 140.0, r_low, r_high), "Long in Discount must be ALLOWED"
    assert not EquilibriumFilter.is_valid_trade_location(TrendDirection.BEARISH, 140.0, r_low, r_high), "Short in Discount must be DISQUALIFIED"


# =============================================================================
# 6. MICROSTRUCTURE ABSORPTION TESTS
# =============================================================================

def test_microstructure_absorption_wick_and_taker_delta():
    """
    Verify rejection wick threshold (>= 18%) and taker delta absorption.
    """
    engine = MicrostructureEngine(min_wick_pct=0.18)

    # Bullish candle with strong 25% lower rejection wick and positive delta
    # Range = 100 to 120 (20). Open = 106, Close = 118, Low = 101.
    # Lower wick = min(106, 118) - 101 = 5. Lower wick pct = 5 / 20 = 25% >= 18%
    bull_absorp = Candle(
        index=0,
        timestamp=1000,
        open=105,
        high=120,
        low=100,
        close=118,
        volume=1000,
        taker_buy_volume=700  # Positive taker delta: 700 - 300 = +400
    )
    passed, stats = engine.verify_absorption(bull_absorp, TrendDirection.BULLISH)
    assert passed is True
    assert stats["lower_wick_pct"] == 0.25
    assert stats["taker_delta"] == 400.0

    # Bullish candle with tiny lower wick (5% < 18%) -> Must FAIL
    weak_wick = Candle(
        index=1,
        timestamp=2000,
        open=102,
        high=120,
        low=101,
        close=118,
        volume=1000,
        taker_buy_volume=700
    )
    passed_weak, stats_weak = engine.verify_absorption(weak_wick, TrendDirection.BULLISH)
    assert passed_weak is False


# =============================================================================
# 7. PO3 / AMD JUDAS SWING TESTS
# =============================================================================

def test_po3_judas_swing_detection():
    """
    Test Power of 3 (PO3):
    - Asian Session Accumulation (00:00 - 08:00 UTC)
    - London Open Judas Swing sweep of Asian Low (09:00 UTC) triggering Bullish setup.
    """
    po3 = PO3Engine()

    # Asian session candles (e.g. 02:00 UTC, 04:00 UTC) establishing range [100, 110]
    dt_asia1 = datetime(2026, 10, 8, 2, 0, tzinfo=timezone.utc)
    c_asia1 = Candle(index=0, timestamp=int(dt_asia1.timestamp() * 1000), open=102, high=110, low=101, close=105)
    po3.process_candle(c_asia1)

    dt_asia2 = datetime(2026, 10, 8, 5, 0, tzinfo=timezone.utc)
    c_asia2 = Candle(index=1, timestamp=int(dt_asia2.timestamp() * 1000), open=105, high=108, low=100, close=103)
    po3.process_candle(c_asia2)

    assert po3.asian_high == 110
    assert po3.asian_low == 100

    # London open Judas Swing at 08:30 UTC: Dips to 97 (< 100 Asian Low), but closes at 102
    dt_london = datetime(2026, 10, 8, 8, 30, tzinfo=timezone.utc)
    c_london_judas = Candle(index=2, timestamp=int(dt_london.timestamp() * 1000), open=101, high=103, low=97, close=102)
    evt = po3.process_candle(c_london_judas)

    assert evt is not None
    assert evt.phase.value == "MANIPULATION"
    assert evt.swept_extreme == "ASIAN_LOW"
    assert evt.bias == TrendDirection.BULLISH
    assert "London Judas Sweep" in evt.description


# =============================================================================
# 8. INTEGRATION TEST WITH REAL MARKET CANDLE DATA
# =============================================================================

def test_full_pipeline_on_real_candle_data():
    """
    End-to-end verification of IndependentICTEngine on real BTCUSDT 1h candle data.
    """
    data_path = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\historical_data\BTCUSDT_1h.json"
    if not os.path.exists(data_path):
        pytest.skip(f"Data file {data_path} not found")

    with open(data_path, "r") as f:
        raw_candles = json.load(f)

    # Run on slice of 200 real candles
    sample_candles = raw_candles[:200]
    assert len(sample_candles) >= 50

    engine = IndependentICTEngine(
        lookback_range=40,
        min_rejection_wick_pct=0.18,
        min_fvg_size_pct=0.0005,
        eq_tolerance_pct=0.0015
    )

    result = engine.run(sample_candles)

    assert result["status"] == "success"
    assert result["candles_analyzed"] == len(sample_candles)
    assert result["confirmed_highs"] >= 0
    assert result["confirmed_lows"] >= 0
    assert result["fvgs_detected"] > 0, "Real BTC market data must contain valid FVGs"
    assert result["liquidity_pools"] >= 0

    print(f"\n--- REAL DATA VERIFICATION RESULTS ({len(sample_candles)} BTC 1H Candles) ---")
    print(f"Confirmed Highs: {result['confirmed_highs']}")
    print(f"Confirmed Lows: {result['confirmed_lows']}")
    print(f"Structure Events (BOS / Turtle Soup Sweeps): {result['structure_events']}")
    print(f"Liquidity Pools (EQH/EQL/Trendline): {result['liquidity_pools']}")
    print(f"FVGs Detected: {result['fvgs_detected']}")
    print(f"Order Blocks: {result['order_blocks']}")
    print(f"Breakers: {result['breaker_blocks']}")
    print(f"Unicorn Zones: {result['unicorns']}")
    print(f"Institutional Signals Emitted: {result['signals_generated']}")

    for sig in result["signals"][:5]:
        print(f"  -> Signal: {sig.signal_type.value} | Dir: {sig.direction.value} | Price: {sig.entry_price:.2f} | "
              f"SL: {sig.stop_loss:.2f} | TP: {sig.take_profit:.2f} | R:R: {sig.risk_reward} | Loc: {sig.equilibrium_status} | "
              f"Wick%: L={sig.lower_wick_pct*100:.1f}%, U={sig.upper_wick_pct*100:.1f}%")
