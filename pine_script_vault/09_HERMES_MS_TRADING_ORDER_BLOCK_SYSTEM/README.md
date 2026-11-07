# 🏛️ Hermes MS Trading Order Block Engine v2.0
**Institutional Smart Money Concepts & 7-Model Order Block Architecture**
*Based on Shoaib Khan / MS Trading Forensic Deconstruction (`https://youtu.be/aXTA1gpfwfE`)*

---

## ⚡ Overview
This system implements the complete quantitative Order Block classification methodology from Shoaib Khan (MS Trading), backed by Hermes AI Dynamic Profit Armor and 5x Isolated Margin compounding controls.

- **Zero Retail Indicators:** Absolutely NO RSI, MACD, EMA, or Bollinger Bands.
- **Pure Order Flow & Price Action:** Evaluates 3-candle imbalance structures, liquidity sweeps, market structure shifts (BOS/MSS), and Inducement (IDM).
- **Dual Engine:** Operates as both an Automated TradingView Strategy (`strategy(...)`) for backtesting and a Visual HUD Indicator.

---

## 📐 The 7 Order Block Models Implemented

### 1. Base 5 Models:
1. **Type 1: Momentum Same-Color OB (🔴 WEAK):**
   - Bullish: Green base candle before expansion.
   - Bearish: Red base candle before drop.
   - *Rule:* 90% probability of being swept. Blind limit orders are **strictly prohibited**.
2. **Type 2: Classic Opposite-Color OB (🟢 STRONG):**
   - Bullish: Red base candle before impulsive up move.
   - Bearish: Green base candle before impulsive down move.
   - *Rule:* High institutional defense. Direct First Tap entry valid.
3. **Type 3: Outlier Displacement Candle 2 Breach (🔴 WEAK):**
   - Displacement candle wick pierces the base candle extreme.
   - *Rule:* Market hunts the extreme wick of Candle 2.
4. **Type 4: Swing Extreme Origin OB (🟢 STRONG):**
   - Base candle sits at the absolute swing origin with opposite color.
5. **Type 5: Mid-Leg Internal OB (🔴 WEAK):**
   - Formed midway inside an existing swing leg. Market treats it as internal inducement.

### 2. The 2 Conditional "STRONGEST" Models (Overrides Weak Status):
6. **Type 6: Sweep + BOS Leg OB (⚡ STRONGEST CONDITIONAL):**
   - The swing leg was initiated by a liquidity sweep of a prior swing point (wick sweep, no body close).
   - Any OB formed inside this leg is promoted to **STRONGEST OB**.
7. **Type 7: Post-IDM Decisional OB (⚡ STRONGEST CONDITIONAL):**
   - The OB resting at Inducement (IDM) is retail trap (Weak).
   - The unmitigated OB sitting **beyond/after the IDM sweep** is promoted to **STRONGEST OB**.

---

## 🛡️ Critical Institutional Nuances

1. **Shoaib Khan Invalidation Rule (Body Close vs Wick):**
   - An OB is broken **ONLY** when a candle **BODY closes** beyond the OB boundary on the same timeframe.
   - A wick past the OB is NOT invalidation—it is an **Institutional Liquidity Sweep**!
2. **Weak OB Sweep Execution Protocol:**
   - Weak OBs are monitored by the engine.
   - When price penetrates the Weak OB extreme with a wick and closes back inside with `>= 18% rejection wick`, an aggressive **Weak OB Swept Rejection** entry signal triggers.
3. **Dynamic Profit Armor:**
   - **Fast Breakeven:** Shift SL to Entry + Fee Shield at exactly `+1.0% profit` ($0.00 Risk).
   - **Trailing Lock:** Locks dynamic profits at `+1.8% profit`.
   - **Take Profit (TP):** Full profit booking at `+2.8%`.
   - **Stop Loss (SL):** Strict max risk `-2.8%`.

---

## 🚀 How to Run on TradingView
1. Open TradingView -> Open Pine Editor.
2. Create New Script -> Paste the entire contents of `HERMES_MS_TRADING_ORDER_BLOCK_SYSTEM.pine`.
3. Click **Add to Chart**.
4. Adjust settings in the Gear ⚙️ icon:
   - Select *Strategy Execution* to backtest or *Visual Indicator Only*.
   - Toggle *Trade Weak OB Wick Sweeps*.
   - Enable/Disable Institutional Dashboard HUD.


---

## 📦 Indicator vs Strategy Versions

Inside this folder, you have two dedicated versions:
1. **`HERMES_MS_TRADING_ORDER_BLOCK_INDICATOR.pine` (Pure Study / Indicator):**
   - Clean, zero simulated order fills, zero blue/red strategy boxes.
   - 6 Native TradingView `alertcondition()` alerts ready for smartphone/desktop notifications.
   - Plots clean targets (+2.8% TP, -2.8% SL, +1.0% Breakeven) and visual signals.
2. **`HERMES_MS_TRADING_ORDER_BLOCK_SYSTEM.pine` (Backtest Strategy):**
   - Includes full Pine Strategy backtesting engine with simulated fills, win rate tracking, and equity compounding curves.
