# 🏛️ HERMES 3.5 INSTITUTIONAL EXTREME ORDER BLOCK (EXTREME OB) SPECIFICATION

**Protocol Version**: 3.5.2-EXTREME-OB  
**Author**: Quant DeepMind & Algorithmic Trading Systems  
**Date**: October 3, 2026  
**Status**: APPROVED & CODIFIED IN SYSTEM REPOSITORY  

---

## 📌 1. EXECUTIVE RATIONALE
Standard retail Smart Money Concepts (SMC) systems often trigger on **Decisional Order Blocks** located within the 30%–70% Fibonacci retracement of a price leg. During high-volatility events, macro liquidation runs, or King BTC flash crashes, Decisional OBs consistently fail as institutional algorithmic market makers sweep past them to seek deep liquidity.

The **Extreme Order Block (Extreme OB)** represents the true institutional anchor—the absolute origin of manipulation and accumulation/distribution. This specification establishes the non-negotiable 5-pillar mathematical protocol for identifying, validating, and executing trades exclusively on Institutional Extreme Order Blocks.

---

## 📐 2. THE 5-PILLAR EXTREME OB IDENTIFICATION RULES

1. **Pillar 1: Absolute Swing Pivot Anchor (Lowest Low / Highest High)**
   - Bullish: Absolute swing low across $N \ge 15$ bars (`low == min(lows)`).
   - Bearish: Absolute swing high across $N \ge 15$ bars (`high == max(highs)`).

2. **Pillar 2: Opposite Candle Rule (Strict Red/Green Color Enforcement)**
   - Bullish Extreme OB: MUST be a strict **Bearish (Red) Candle** (`close < open`).
   - Bearish Extreme OB: MUST be a strict **Bullish (Green) Candle** (`close > open`).

3. **Pillar 3: Liquidity Judas Sweep (Wick Stop Hunt)**
   - Wick must pierce previous structure highs/lows to harvest retail stop losses before expansion.

4. **Pillar 4: Institutional Displacement ($\ge 5.0\%$) + Fair Value Gap (FVG)**
   - Immediate 1–3 candle explosive expansion of $\ge 5.0\%$ with a confirmed price imbalance void.

5. **Pillar 5: 50% Mean Threshold (MT) Equilibrium Execution**
   - Entry strictly at midpoint `(ob_high + ob_low) / 2.0` with 15M Micro Rejection Wick confirmation.
