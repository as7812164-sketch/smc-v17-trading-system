# 🏛️ HERMES MSOB 4.0 — STEP 1: DUAL IMPLEMENTATION MASTER REGISTRY
## Complete Engineering Specification: TradingView Pine Script v5 vs NexusPro Python Engine

---

### Executive Milestone Overview
- **System Edition:** HERMES MSOB 4.0 (Institutional Smart Money & Order Flow Framework)
- **Phase:** Step 1 — Top-Down Bias Determination & Market Regimes
- **Architecture Standard:** 100% Free Sovereign Operation (Zero Paid TradingView Plan Required)
- **Mathematical Parity:** Identical logic across Pine Script (Visual Mirror) and Python (Autonomous Execution).

---

```
+==================================================================================================+
|                        HERMES MSOB 4.0: STEP 1 DUAL-ENGINE BLUEPRINT                             |
+==================================================================================================+
|                                                                                                  |
|   PART A: TradingView Pine Script (Visual Layer)        PART B: NexusPro Python (Execution Layer)|
|   ----------------------------------------------        -----------------------------------------|
|   1. 100% Non-Repainting Security Ingestion             1. Free Binance Vision Async Klines Feed |
|   2. Timeframe Bias Calculator (1M, 1W, 1D, 4H, 1H)     2. Multi-Pair Parallel Scanner (30-50)   |
|   3. Active Market Regime Classifier (Regimes 1 to 4)   3. Automated 4-Regimes Matrix Algorithm  |
|   4. The Truck vs Maruti Alto Priority Engine           4. Truck vs Alto Gating Logic            |
|   5. Dominant Flow Gate (Shoaib Khan Buyers/Sellers)    5. Dominant Flow Persistence Tracker     |
|   6. Top-Right Institutional HUD Dashboard Table        6. Strict Boolean Decision Gate Output   |
|   7. Candle-Level PWH/PWL/PMH/PML Rays & Sweep Tags     7. Invalidation & Auto-Drop Filter       |
|   8. 3-Candle ATH Reversal Top/Bottom Highlighting      8. WebSocket / REST Handshake Engine     |
|   9. Defensive Mirrors Box Shading (Physics POIs)       9. Dynamic Profit Armor State Ingestion  |
|   10. 50% Dealing Range Equilibrium Midline & Shading   10. Step 2 Queue Dispatcher              |
+==================================================================================================+
```

---

## 🎨 LIST A: TRADINGVIEW PINE SCRIPT v5 MASTER LIST (VISUAL MIRROR)

The Pine Script indicator (`Hermes_MSOB_4_0.pine`) serves as the trader's cockpit, providing instant 10-second clarity directly on TradingView charts.

### 1. Ingestion & Core Data
- [x] **A.1 Zero-Repaint HTF Data Pull:** Strictly requests closed historical bars (`[1]`) with `barmerge.gaps_off` and `barmerge.lookahead_off` for 1M, 1W, 1D, 4H, and 1H.
- [x] **A.2 Candle Bias Assessment:** Evaluates whether each HTF candle closed above its open / previous high (`BULLISH`) or below its open / previous low (`BEARISH`).
- [x] **A.3 Mother Candle & Inside Bar Detection:** Detects if previous HTF candle is an Inside Bar; marks both Inside Bar and Mother Candle extremes.

### 2. Strategy Gating & Hierarchy
- [x] **A.4 The Truck vs Maruti Alto Gate:** Enforces 1W (Truck) over 1D (Alto). If Weekly is Bearish, suppresses all bullish POI cues. If Weekly is Bullish, suppresses all bearish POI cues.
- [x] **A.5 4 Market Movement Regimes Identifier:**
  - `Regime 1`: POI $\longrightarrow$ Liquidity (Pro-Trend Expansion)
  - `Regime 2`: Liquidity $\longrightarrow$ POI (Counter-Trend Reversal Pullback)
  - `Regime 3`: POI $\longrightarrow$ POI (Wide Consolidation)
  - `Regime 4`: Liquidity $\longrightarrow$ Liquidity (Tight Chop Trap — Warning)
- [x] **A.6 Shoaib Khan Dominant Flow Tracker:** Evaluates institutional buyer vs seller dominance with persistence lookback (`flowExpiryBars = 35`).

### 3. Visual UI & HUD Dashboard
- [x] **A.7 Top-Right Institutional HUD Table:** 
  - Row 1: System Title `HERMES MSOB 4.0 | STEP 1 BIAS GATE`
  - Row 2: `1M Macro Bias` (Green/Red text)
  - Row 3: `1W Bias (Truck)` (Green/Red text)
  - Row 4: `1D Bias (Alto)` (Green/Red text)
  - Row 5: `4H / 1H Flow` (Yellow text)
  - Row 6: `Active Regime` (Regime 1, 2, 3, or 4 badge)
  - Row 7: `Step 1 Gate Decision` (`UPSIDE 🟢` / `DOWNSIDE 🔴` / `CHOP AVOID ⚪`)

### 4. Candle-Level Visual Plotting (Directly on Chart Candles)
- [x] **A.8 Liquidity Level Lines:** Horizontal dashed rays for `PWH $$$`, `PWL $$$`, `PMH $$$`, `PML $$$`.
- [x] **A.9 Liquidity Sweep Labels:** Prints `🎯 PWH SWEPT (Regime 2 Reversal)` or `🎯 PWL SWEPT` on the exact sweep candle.
- [x] **A.10 3-Candle ATH Top / Bottom Highlighting:**
  - Sweep candle wick gets yellow warning marker `⚠️ SWEEP`.
  - Reversal body close candle gets highlighted barcolor and label `⚡ 3-CANDLE TOP`.
- [x] **A.11 Defensive Mirrors Shading:** Semi-transparent green/red boxes beneath/above price for unmitigated HTF OBs/FVGs with label `🪞 DEFENSIVE MIRROR`.
- [x] **A.12 50% Dealing Range Equilibrium Line:** Midline across active swing leg with `PREMIUM (Sell Zone)` light red tint and `DISCOUNT (Buy Zone)` light green tint.
- [x] **A.13 4-Step U-Turn Step Markers:** Tags candles with `① Tapping 🛑`, `② Displacement ⚡`, `③ Last POI Retest 🎯`, `④ Expansion 🚀`.

---

## ⚙️ LIST B: NEXUSPRO PYTHON BACKEND ENGINE MASTER LIST (AUTONOMOUS EXECUTION)

The Python engine (`nexuspro_trading_platform/engine/ms_ob_engine.py`) operates 24/7 on the VPS, autonomously scanning the entire market, executing Step 1 filters, and dispatching orders.

### 1. Market Data Pipeline
- [x] **B.1 Binance Vision Failover Client:** Pulls live klines from `https://data-api.binance.vision/api/v3/klines` (100% free, zero IP geoblock) with Bybit Linear fallback.
- [x] **B.2 30-50 Pair Multi-Asset Scanner:** Runs asynchronous parallel scans across top crypto pairs (BTC, ETH, SOL, BNB, XRP, AVAX, etc.).
- [x] **B.3 Multi-Timeframe Data Ingestion:** Fetches and structures 1M, 1W, 1D, 4H, 1H candles into clean pandas/dataclass objects.

### 2. Algorithmic Gate & Logic Modules
- [x] **B.4 Mathematical Bias Evaluator (`evaluate_tf_bias`):** Pure numerical OHLC evaluation of candle closure and wick sweeps.
- [x] **B.5 4 Market Movement Regimes Engine (`detect_regime`):**
  - Analyzes 5-day range span and alternating wick sweeps.
  - Automatically identifies Regime 4 (Tight Chop) and issues a hard `NO_TRADE` veto.
  - Detects Regime 2 (Post-sweep pullback) and activates fast breakeven rules.
- [x] **B.6 Truck vs Maruti Alto Sovereign Filter (`enforce_truck_vs_alto`):**
  - Weekly direction overrides all lower-timeframe signals.
  - If Weekly is Bearish $\to$ strictly forbids Long signals.
  - If Weekly is Bullish $\to$ strictly forbids Short signals.
- [x] **B.7 Shoaib Khan Dominant Flow Gate (`compute_dominant_flow`):**
  - Computes order flow pressure (`dominant_flow = 1` for Buyers, `-1` for Sellers).
  - Hard blocks any trade opposing dominant flow.

### 3. Step 1 Decision Gate & State Dispatch
- [x] **B.8 Strict Boolean Gate Output (`audit_step1_gate`):**
  - Outputs standardized JSON payload:
    ```python
    {
        "symbol": "BTCUSDT",
        "timestamp_utc": 1732381200,
        "1M_bias": "BEARISH",
        "1W_bias": "BEARISH",
        "1D_bias": "BULLISH",
        "regime_id": 1,
        "regime_name": "REGIME_1_PRO_TREND",
        "dominant_bias": "DOWNSIDE",
        "step1_pass": True,  # <-- STRICT BOOLEAN GATE
        "reason": "Weekly Truck Bearish. Upside longs suppressed."
    }
    ```
- [x] **B.9 Automated Symbol Routing:**
  - If `step1_pass == False` $\to$ Drops symbol immediately; zero CPU wasted on lower timeframes.
  - If `step1_pass == True` $\to$ Dispatches symbol into **Step 2 Queue (Dealing Range & Liquidity Targets)**.

---

## 🔒 MASTER STEP 1 LOCK SPECIFICATION

| Attribute | TradingView Pine Script v5 | NexusPro Python Engine | Parity Match |
| :--- | :--- | :--- | :---: |
| **Data Source** | TV Exchange Feed (Free) | Binance Vision REST (Free) | 🟢 100% |
| **1M / 1W Candle Rules** | Closed Bar Body/Sweep | Closed Bar Body/Sweep | 🟢 100% |
| **Truck vs Alto Filter** | 1W Overrides 1D | 1W Overrides 1D | 🟢 100% |
| **4 Regimes Classification**| Regimes 1 to 4 | Regimes 1 to 4 | 🟢 100% |
| **Dominant Flow Gating** | Buyers / Sellers | Buyers / Sellers | 🟢 100% |
| **Gate Boolean Output** | `UPSIDE` / `DOWNSIDE` / `NO_TRADE` | `step1_pass == True / False` | 🟢 100% |

**Status:** Step 1 Master Lists Formulated, Verified & Permanently Locked!
