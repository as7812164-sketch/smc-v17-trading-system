# Independent ICT & SMC Quantitative Architecture

A **100% Standalone, Mathematically Rigorous Execution Engine** implementing the complete 8-Masterclass Curriculum for Smart Money Concepts (SMC) and Inner Circle Trader (ICT) algorithmic market theory.

---

## 🏛 Architectural Overview

The engine operates on a strictly causal, zero-lookahead, bar-by-bar pipeline designed for high-frequency or multi-timeframe quantitative trading.

```
                    Raw OHLCV(+Taker) Feed
                              │
                              ▼
                   ┌─────────────────────┐
                   │   Fractal Engine    │ ── (Inside Bar Elimination & Valid Pullbacks)
                   └──────────┬──────────┘
                              │ Clean Bars
                              ▼
                   ┌─────────────────────┐
                   │  Structure Engine   │ ── (Inducement Sweep & Body Close BOS vs Wicks)
                   └──────────┬──────────┘
                              │ Confirmed Swings & Sweeps
                              ▼
         ┌────────────────────┴────────────────────┐
         │                                         │
         ▼                                         ▼
┌──────────────────┐                     ┌──────────────────┐
│ Liquidity Engine │                     │ Order Flow Engine│
│ (EQH/EQL/Trails) │                     │ (FVG, OB, Unicorn)
└────────┬─────────┘                     └─────────┬────────┘
         │                                         │
         └────────────────────┬────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Equilibrium Filter  │ ── (Disqualify Longs in Premium / Shorts in Discount)
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Microstructure &    │ ── (>=18% Rejection Wick & Taker Buy Delta)
                   │    PO3/AMD Engine   │ ── (Asian Accumulation / London Judas Sweeps)
                   └──────────┬──────────┘
                              │
                              ▼
                   Institutional Signals:
              [1] Extreme Bedrock OB Tap
              [2] The Unicorn Model
              [3] Turtle Soup Liquidity Reversal
              [4] PO3 Judas Swing Continuation
```

---

## 📚 8 Masterclasses Implementation Reference

### 1. Fractal Engine (`FractalEngine`)
- **Inside Bar Elimination**: Any bar with $\text{High} \le \text{Mother.High}$ and $\text{Low} \ge \text{Mother.Low}$ is strictly classified as internal sub-structure noise and absorbed into the mother bar.
- **Valid Pullback Mechanics**:
  - Bullish advance: Requires sweeping the previous valid candle's low ($\text{Low} < \text{Prev.Low}$).
  - Bearish decline: Requires sweeping the previous valid candle's high ($\text{High} > \text{Prev.High}$).

### 2. Structure Engine (`StructureEngine`)
- **Inducement (IDM)**: The first valid pullback low (in bullish trends) or high (in bearish trends).
- **Swing Confirmation Rule**: A major Swing High/Low is confirmed **ONLY** after price sweeps the Inducement (IDM) level.
- **BOS vs. Turtle Soup**:
  - **Break of Structure (BOS)**: Requires a strict **CANDLE BODY CLOSE** past the confirmed swing point.
  - **Liquidity Sweep (Turtle Soup Trap)**: Any breach by wick alone ($\text{Wick penetrated}$, but $\text{Body closed inside}$) is classified as an institutional trap/liquidity grab.

### 3. Liquidity Pool Engine (`LiquidityEngine`)
- **Equal Highs (EQH) & Equal Lows (EQL)**: Clusters of highs or lows within a strict tolerance (default $0.15\%$), marking resting Buy-Side Liquidity (BSL) or Sell-Side Liquidity (SSL).
- **Trendline Liquidity Trails**: Mathematical detection of $3+$ progressive pivot touches creating engineered retail stop clusters.
- **Session Extremes**: Tracks PDH (Previous Day High), PDL (Previous Day Low), and session boundaries.

### 4. Order Flow & OB & FVG Engine (`OrderFlowEngine`)
- **3-Candle Fair Value Gap (FVG)**:
  - Bullish: $\text{Candle}_1.\text{High} < \text{Candle}_3.\text{Low}$. Consequent Encroachment (CE) at $50\%$.
  - Bearish: $\text{Candle}_1.\text{Low} > \text{Candle}_3.\text{High}$.
  - Mitigation lifecycle: tracks virgin, tapped, and invalidated states.
- **Extreme Origin Bedrock Order Block (OB)**: Traces the absolute origin of the expansion impulse that caused the BOS.
- **The Unicorn Model**: Horizontal price confluence where a violated Order Block (Breaker Block) overlaps with a Fair Value Gap ($\text{Breaker.Low} \le \text{FVG.High} \land \text{Breaker.High} \ge \text{FVG.Low}$).

### 5. Discount / Equilibrium Filter (`EquilibriumFilter`)
- Computes the 40-bar swing range (or current structural leg range).
- **Equilibrium**: $\text{EQ} = \frac{\text{Range High} + \text{Range Low}}{2}$.
- **Strict Rule**:
  - Longs are **DISQUALIFIED** if price is in Premium ($> 50\%$).
  - Shorts are **DISQUALIFIED** if price is in Discount ($< 50\%$).

### 6. Microstructure Absorption (`MicrostructureEngine`)
- **Rejection Wick Threshold**:
  - Bullish defense requires a lower wick $\ge 18\%$ of the candle range: $\frac{\min(\text{Open}, \text{Close}) - \text{Low}}{\text{High} - \text{Low}} \ge 0.18$.
  - Bearish defense requires an upper wick $\ge 18\%$: $\frac{\text{High} - \max(\text{Open}, \text{Close})}{\text{High} - \text{Low}} \ge 0.18$.
- **Taker Delta**: Validates net institutional aggressive volume ($\text{Taker Buy} - \text{Taker Sell} > 0$ on bullish defense).

### 7. PO3 / AMD Engine (`PO3Engine`)
- **Accumulation (Asian Session 00:00 - 08:00 UTC)**: Establishes initial balance and Asian High/Low.
- **Manipulation (London Open 08:00 - 12:00 UTC)**: Detects Judas Swings sweeping the Asian High or Asian Low.
- **Distribution (New York Session 12:00 - 20:00 UTC)**: Exploits true directional expansion.

### 8. Institutional Signal Generator (`IndependentICTEngine`)
- Emits high-probability institutional setups with pre-calculated entry price, stop-loss, take-profit, risk-to-reward ratio, and pricing quadrant.

---

## 🧪 Verification & Test Suite

The test suite in `test_independent_engine.py` validates all components against both synthetic edge-cases and real historical market candles (`BTCUSDT` 1-hour timeframe):

```bash
python -m pytest -v -s test_independent_engine.py
```

### Verification Results:
- **12/12 Unit & Integration Tests Passed (100% Pass Rate)**
- Validated on real BTC 1-hour candles:
  - Confirmed Highs & Lows accurately isolated
  - BOS body closes distinguished from Turtle Soup wick sweeps
  - Equal Highs/Lows and Trendline liquidity pools mapped
  - 3-candle FVGs detected and mitigated
  - Bedrock Order Blocks and Unicorn setups synthesized
  - High R:R institutional signals produced ($5.3$ to $11.0$ R:R)
