# HERMES MSOB 4.0 — Step 2 Dual Implementation Registry
## Institutional Implementation Blueprint: Pine Script v5 (Visual Mirror + HUD) & NexusPro Python Engine (24/7 Autonomous Backend)

> **Milestone:** Step 2 — Bias Utilization, Intermediate Hurdles & The Core Entry Module  
> **Source Logic:** Masterclasses Video 19 (`3cgI90d_aqs`) & Video 20 (`m_IHo3SkQLY` — Shoaib Khan / MS Trading)  
> **Core Objective:** Eliminate lower-timeframe traps, map intermediate POI hurdles, execute the 3-point ITH/ITL Entry Module, and compress stop loss to deliver 1:11 to 1:15 RR setups.  
> **Dedicated Engineering Spec:** [HERMES_MSOB_4_ENTRY_MODULE_ENGINEERING_SPEC.md](file:///C:/Users/power/.gemini/antigravity/brain/cf8480f7-6fe5-4496-9c76-80211255c078/HERMES_MSOB_4_ENTRY_MODULE_ENGINEERING_SPEC.md)

---

## Part A: TradingView Pine Script v5 Visual Implementation

### 1. On-Chart Candlestick Visual Elements
- **1. 1H/4H Institutional Anchor POI Box:**
  - Drawn as a translucent shaded box across the Order Block / FVG boundaries.
  - Dynamically greys out and disables when a closed candle body violates the boundary (**Order Block Invalidation Law**).
- **2. 3-Point Fractal Markers (ITH & ITL):**
  - **Intermediate Term Low (ITL):** Cyan/Green circular marker below the 3-point fractal trough (Left Low > Center Low < Right Low).
    - Ray drawn horizontally from the Center Low: `🛡️ ITL: Protected Floor (Stop Loss Anchor)`.
  - **Intermediate Term High (ITH):** Crimson/Orange circular marker above the 3-point fractal peak (Left High < Center High > Right High).
    - Ray drawn horizontally from the Center High: `🎯 ITH: Dynamic Target (Take Profit)`.
- **3. Intermediate POI Hurdle Target Lines (TP1):**
  - Bold dashed Amber horizontal line marking opposing HTF Daily/4H supply/demand zones.
  - Label: `🎯 TP1: Intermediate Hurdle (Mandatory Partial)`.
- **4. Macro Draw on Liquidity (DOL) Line (TP2):**
  - Solid Bright Green horizontal ray at the Weekly/Daily extreme.
  - Label: `🚀 TP2: Macro Draw on Liquidity`.
- **5. 5m Market Structure Shift (MSS) Trigger Ray:**
  - Plotted upon a valid candle body close above/below the internal swing pivot.
  - Label: `⚡ 5m MSS Confirmed (Impulsive Displacement)`.
- **6. 5m "Last POI" Entry Box & Execution Bracket:**
  - Highlighted micro-box at the origin Order Block / lowest FVG of the 5m displacement leg.
  - Limit Entry line, tight SL line (below ITL / 5m extreme low), and dynamic RR badge: `RR: 1:12.8`.

---

### 2. Pine Script HUD Dashboard Extension (Step 2 Entry Module Metrics)
| Parameter | Display Format | Logic Trigger |
| :--- | :--- | :--- |
| **HTF Bias & Regime** | `BULLISH (Regime 1: Expansion)` | Step 1 Top-Down Daily/Weekly Calculation |
| **HTF Anchor Status** | `ACTIVE IN 1H POI (0.618 OTE)` | Price currently inside unmitigated Discount POI |
| **OB Boundary Integrity**| `🟢 INTACT (Zero Body Breach)` | Validated by candle body close check |
| **Intermediate Hurdle** | `DAILY OB @ $64,850 (TP1 Hurdle)` | Detected opposing Daily POI in path |
| **Active Structure** | `ITL PROTECTED @ $63,120` | Confirmed 3-point fractal floor |
| **Dynamic Target** | `ITH TARGET @ $64,480` | Confirmed 3-point fractal ceiling |
| **5m MSS State** | `🟢 TRIGGERED (Impulse Body)` | Confirmed 5m structural shift |
| **Entry Order Sizing** | `LIMIT @ 5m Last POI ($63,420)` | Base of 5m displacement leg |
| **Stop Loss Distance**| `240 Pips (-0.38%)` | Below Center Low of ITL |
| **Calculated RR (TP1)** | `1 : 11.5 RR` | Compressed institutional reward-to-risk |
| **Breakeven Shield** | `ARMED (+1.0% $\to$ Zero Risk)` | SL shifted to Entry + Fee Shield |

---

## Part B: NexusPro Autonomous Python Engine (24/7 Backend)

### 1. Data Pipeline & Multi-Timeframe Architecture
- **Free Binance Vision REST Endpoint:** `https://data-api.binance.vision/api/v3/klines` (100% free, zero IP block).
- **Timeframe Processing Hierarchy:**
  * Daily/4H Thread: Macro Bias & Intermediate Hurdle Detection.
  * 1H Thread: Anchor POI Monitoring & 3-Point Fractal Mapping (ITH/ITL).
  * 5m Watchdog Thread: Sub-second websocket / high-speed polling active inside 1H POIs.

---

### 2. Algorithmic Modules for Step 2

```python
# Algorithmic Logic Breakdown for Step 2 Modules

# Module 1: 3-Point Fractal Detector (ITH & ITL)
def detect_ith_itl(klines):
    """
    Computes 3-point fractal pivots on closed candles:
    ITL: klines[i-1].low > klines[i].low and klines[i+1].low > klines[i].low
    ITH: klines[i-1].high < klines[i].high and klines[i+1].high < klines[i].high
    Returns: active_itl (price, bar_index), active_ith (price, bar_index)
    """
    pass

# Module 2: Order Block Invalidation Gate
def is_ob_valid(ob_zone, latest_closed_kline, bias_direction):
    """
    Enforces Shoaib Khan's Order Block Invalidation Law:
    For Demand OB: If closed_candle.close < ob_zone.bottom -> RETURN FALSE (DEAD)
    For Supply OB: If closed_candle.close > ob_zone.top -> RETURN FALSE (DEAD)
    Wick breaches with body closing inside remain TRUE (Valid Liquidity Sweep).
    """
    pass

# Module 3: 3-Zone Discount Layer Selector
def evaluate_discount_zones(discount_zones, m5_klines):
    """
    Iterates through:
      1. Breaker Block
      2. OTE 0.618 - 0.79 FVG/OB
      3. Extreme Origin Last POI
    Executes on the FIRST zone that triggers 5m MSS + 5m ITL confirmation.
    Rejects zones that are sliced through without LTF reaction.
    """
    pass

# Module 4: Mechanical Bracket Generator
def build_trade_bracket(entry_price, itl_floor, ith_target, hurdle_tp1):
    """
    Stop Loss: itl_floor - fee_buffer
    TP1: hurdle_tp1 if hurdle_tp1 < ith_target else ith_target
    TP2: Macro DOL
    Enforces: RR >= 5.0 Gate
    """
    pass
```

---

## 3. End-to-End Execution Sequence

| Stage | Trigger Condition | Algorithmic Output |
| :--- | :--- | :--- |
| **1. Macro Bias** | Weekly/Daily Regime 1-4 determined | Direction Filter (Long/Short) |
| **2. POI Gating** | 1H Discount POI penetrated | Check OB Body Integrity; activate 5m Watchdog |
| **3. Hurdle Mapping**| Scan for opposing Daily/4H POIs | Set Mandatory TP1 at Nearest Hurdle |
| **4. Fractal Floor** | 5m 3-point ITL completes ($L > C < R$) | Set Protected SL at Center Low |
| **5. Entry Limit** | 5m MSS displacement creates "Last POI" | Limit Order at Last POI retest |
| **6. Exit & Shield** | Price reaches +1.0% or ITH Target | Shift SL to Entry + Fee; harvest at ITH |
