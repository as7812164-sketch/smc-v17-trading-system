# Visual Atlas: Video 14
## CBDR Explained | Predict Day High & Day Low | SMC and ICT Trading Strategy

---

### Frame 01: The Daily Candle Anatomy & Institutional Objective

```
========================================================================================
THE 95% DAILY CANDLE DELIVERY CYCLE (BULLISH GREEN CANDLE EXAMPLE)
========================================================================================

                  [Day High]  <----+ Upper Wick: Price reaches target & pulls back slightly
                      |
                 +----+----+  <----+ Daily Close: Closes near the highs
                 |         |
                 |         |
                 |  BODY   |  <----+ The Main Expansion Leg (Capture this with CBDR!)
                 |         |
                 |         |
                 +----+----+  <----+ Daily Open: 00:00 UTC / 17:00 NY
                      |
                  [Day Low]   <----+ THE INSTITUTIONAL GOAL:
                                     Pinpoint this exact Low using CBDR Standard Deviations!
                                     Once MSS confirms Day Low, IT WILL NOT BE RETESTED!
```

---

### Frame 02: CBDR Time Window & 24-Hour Operational Horizon

```
========================================================================================
NEW YORK TIME (UTC-4) SESSION CHRONOLOGY & CBDR POSITIONING
========================================================================================

 14:00        20:00                 00:00        02:00        05:00        07:00        10:00
   |            |                     |            |            |            |            |
   +------------+                     +------------+            +------------+            +
   |    CBDR    |        ASIAN        |  DEAD ZONE |   LONDON   |  DEAD ZONE |  NEW YORK  |
   |   WINDOW   |       KILLZONE      |  NO TRADES |  KILLZONE  |  NO TRADES |  KILLZONE  |
   | (Body Box) |      (20:00-00:00)  |(00:00-02:00)|(02:00-05:00)|(05:00-07:00)|(07:00-10:00)
   +------------+                     +------------+            +------------+            +
         |
         +--> Measure 15m Bodies -> Project SD -1 to -4 and +1 to +4 -> Wait for Asia/London to tap!
```

---

### Frame 03: 15-Minute Body-to-Body Marking Law (Strict Wick Exclusion)

```
========================================================================================
BODY-TO-BODY MEASUREMENT PROTOCOL (15-MINUTE TIMEFRAME ONLY)
========================================================================================

        CANDLE 1      CANDLE 2      CANDLE 3      CANDLE 4      CANDLE 5
           |             |                           |             |
           |          +-----+                        |             |  <-- Upper Wicks IGNORED!
        +-----+       |     |       +-----+       +-----+          |
  ====  |     |  ===  |     |  ===  |     |  ===  |     |  ======  |  <== CBDR HIGH BODY LINE
        |     |       |     |       |     |       |     |       +-----+
        |     |       +-----+       |     |       +-----+       |     |
        +-----+          |          |     |          |          |     |
           |             |          +-----+          |          +-----+
  ====     |     ===     |     ===  |     |  ===     |     ===  |     |  <== CBDR LOW BODY LINE
        +-----+          |          +-----+          |          +-----+
        |     |          |                           |             |
        |     |          |                           |             |  <-- Lower Wicks IGNORED!
           |             |                           |             |

  *RULE: CBDR High = Highest Close or Open between 14:00 and 20:00 NY.
         CBDR Low  = Lowest Close or Open between 14:00 and 20:00 NY.
         Wicks represent noise; institutional ranges are priced from bodies!
```

---

### Frame 04: Standard Deviation Projection Matrix

```
========================================================================================
CBDR STANDARD DEVIATION PROJECTIONS (H = HighBody - LowBody)
========================================================================================

  ------------------------------------------------------------- +4.0 SD (Extreme Blow-Off High)
  ------------------------------------------------------------- +3.0 SD (Macro Target High)
  ------------------------------------------------------------- +2.0 SD (Primary Bearish Day High Zone)
  ------------------------------------------------------------- +1.0 SD (Primary Bearish Day High Zone)
  +===========================================================+
  |              CBDR HIGH BODY (14:00 - 20:00 NY)           |
  |                                                           |
  |              CBDR 15m BODY RANGE (H_CBDR)                 |  <-- Ideal: 100 - 150 Pips (Gold)
  |                                                           |
  |              CBDR LOW BODY (14:00 - 20:00 NY)            |
  +===========================================================+
  ------------------------------------------------------------- -1.0 SD (Primary Bullish Day Low Zone)
  ------------------------------------------------------------- -2.0 SD (Primary Bullish Day Low Zone)
  ------------------------------------------------------------- -3.0 SD (Macro Target Low)
  ------------------------------------------------------------- -4.0 SD (Extreme Blow-Off Low)
```

---

### Frame 05: Bullish Daily Bias — Pinpointing the Absolute Day Low

```
========================================================================================
BULLISH DAILY BIAS: DAY LOW FORMS AT SD -1.0 OR SD -2.0
========================================================================================

                 +===========================================+
                 |                 CBDR BOX                  |
                 +===========================================+
                                       |
                                       |  [Asian / London Asian Sweep Dip]
                                       |  Price declines into institutional discount...
                                       v
  ------------------------------------------------------------- SD -1.0
             \
              \   OR price extends deeper...
               v
  ------------------------------------------------------------- SD -2.0
               |
               |  1. Price enters SD -1.0 or SD -2.0 zone
               |  2. Rejection wick prints (Absorption)
               |  3. Lower Timeframe (5m) Market Structure Shift (MSS) CONFIRMS!
               v
          [CONFIRMED DAY LOW LOCKED IN HERE!]
               |
               +----------------------------------------------------> Massive Daily Expansion!
                                                                      Target: CBDR High & +SD
```

---

### Frame 06: Bearish Daily Bias — Pinpointing the Absolute Day High

```
========================================================================================
BEARISH DAILY BIAS: DAY HIGH FORMS AT SD +1.0 OR SD +2.0
========================================================================================

          [CONFIRMED DAY HIGH LOCKED IN HERE!]
               ^
               |  1. Price spikes into SD +1.0 or SD +2.0 zone
               |  2. Rejection wick prints (Absorption)
               |  3. Lower Timeframe (5m) Market Structure Shift (MSS) CONFIRMS!
               |
  ------------------------------------------------------------- SD +2.0
               ^   OR price pauses at SD +1.0...
              /
  ------------------------------------------------------------- SD +1.0
                                       ^
                                       |  [Asian / London Buy-Stop Purge]
                                       |  Price rallies into institutional premium...
                 +===========================================+
                 |                 CBDR BOX                  |
                 +===========================================+
                                       |
                                       +----------------------------> Massive Daily Sell-Off!
                                                                      Target: CBDR Low & -SD
```

---

### Frame 07: Sentry Protocol — Rejection Alone vs Mandatory 5m MSS

```
========================================================================================
REJECTION WICK ALONE (INVALID) VS MANDATORY 5m MSS CONFIRMATION (VALID)
========================================================================================

  [THE RETAIL AMATEUR TRAP]:
  Price hits SD -1.0 -> Prints a tiny wick -> Retail Trader buys immediately on limit order.
  Price hesitates for 2 bars, then slices straight down into SD -2.0 or SD -3.0. Stop Out!

  [THE INSTITUTIONAL HERMES AUDIT]:
  SD -1.0 / -2.0 Level -------------------------------------------------+
                                                                        |
     Price dips into SD Level                                           |
           \                                                            |
            \                                                           |
             v                                                          |
            (Low) ----> Slight bounce                                   |
                          \                                             |
                           v                                            v
                         (Higher Low) ----> IMPULSIVE CANDLE BREAKS MINOR SWING HIGH!
                                            [5m MARKET STRUCTURE SHIFT (MSS)]
                                            + Leaves clean Displacement FVG!
                                                    |
                                                    v
                                    [ENTRY ON RETEST OF 5m FVG / OB]
                                    SL: Below Established Extreme
                                    Confidence: 99.9% Day Low Locked!
```

---

### Frame 08: Sniper Entry Execution on 5m Retest

```
========================================================================================
THE 5m SNIPER ENTRY ANATOMY AT CONFIRMED CBDR DAY LOW
========================================================================================

                             [5m MSS Breakout]
                                     |
                                  +-----+
                                  |     |
                                  |     |
                                  +-----+
                                     |
                        +-----+   [5m FVG]
                        |     |      |
                        +-----+      v
                           |      +-----+  <--- ENTRY EXECUTED HERE! (Retest of FVG / OB)
                  +-----+  |      |     |       Stop Loss: 0.5 ATR below Day Low
                  |     |  |      +-----+
                  +-----+  |
                     |     |
  -------------------+-----+------------------------------------ SD -1.0 / -2.0 Zone
                     |
                 (DAY LOW)  <--- Guaranteed lowest price of the entire daily candle!
```

---

### Frame 09: News Volatility Spike Absorption at SD -2.0

```
========================================================================================
NEWS SPIKE ABSORPTION: NEWS IS MERELY THE DELIVERY CATALYST!
========================================================================================

  1. Normal Price Action hovers between CBDR Low and SD -1.0.
  2. 08:30 AM NY High-Impact News (CPI / NFP / PPI) releases.
  3. Violent 5-minute liquidity cascade plunges price directly into SD -2.0!
  4. Retail perceives "Catastrophic Breakdown" and enters panic market short orders.
  5. Central Bank institutional iceberg orders absorb the liquidity instantly:
     - 15m candle closes with a massive 60% lower rejection wick!
     - 5m MSS prints within 10 minutes of news release.
  6. Price rockets in the direction of the Daily Bias.
  7. Lesson: News never destroys structure; it accelerates delivery into SD 1 or 2!
```

---

### Frame 10: The Pip Range Filter — 100–150 Pips Ideal vs 380 Pips Blown Out

```
========================================================================================
CBDR PIP RANGE QUALIFICATION AUDIT (GOLD / XAUUSD BENCHMARK)
========================================================================================

  CASE A: IDEAL RANGE (100 - 150 PIPS)         CASE B: BLOWN OUT RANGE (380 PIPS)
  +==================================+         +==================================+
  | High Body: $2,580.00             |         | High Body: $2,595.00             |
  | Low Body:  $2,567.00             |         |                                  |
  | Range:     130 Pips              |         |                                  |
  +==================================+         |                                  |
  |                                  |         |                                  |
  | SD -1.0 is 130 pips away         |         |                                  |
  | SD -2.0 is 260 pips away         |         | Low Body:  $2,557.00             |
  |                                  |         | Range:     380 Pips!             |
  | Status: [QUALIFIED & ACTIVE]     |         +==================================+
  | Realistic daily ADR targets.     |         |                                  |
  | Clean institutional execution.   |         | SD -1.0 is 380 pips away!        |
  |                                  |         | Daily ADR is exhausted before    |
  |                                  |         | price can even reach SD 1!       |
  |                                  |         |                                  |
  |                                  |         | Status: [BLOWN OUT - ABORT CBDR] |
  |                                  |         | Trade normal session models!     |
  +----------------------------------+         +----------------------------------+
```

---

### Frame 11: Fail-over Protocol on Blown-Out CBDR Days

```
========================================================================================
ALGORITHMIC FAIL-OVER ARCHITECTURE: CBDR --> SESSION PURGE ENGINE
========================================================================================

                   [14:00 - 20:00 NY 15m CBDR Computed]
                                     |
                                     v
                       Is Range <= 200 Pips on Gold?
                                    / \
                                   /   \
                            YES   /     \   NO (>200 Pips, e.g. 380 Pips)
                                 /       \
                                v         v
             [ACTIVATE CBDR ENGINE]     [ABORT CBDR PROTOCOL]
             - Project SD -1 to -4      - Hide CBDR Projection Lines
             - Project SD +1 to +4      - Activate Ep 12 London Asian-Purge
             - Hunt Day Low/High at SD  - Activate Ep 12 NY Judas / Continuation
             - Target CBDR Opposing SD  - Zero ADR Exhaustion Risk!
```

---

### Frame 12: Complete 24-Hour Execution Blueprint

```
========================================================================================
THE FULL 24-HOUR CBDR INSTITUTIONAL WORKFLOW
========================================================================================

  1. 20:01 NY (Post-CBDR Close):
     - Identify Highest 15m Body & Lowest 15m Body from 14:00 to 20:00 NY.
     - Calculate Range (H_CBDR). If > 200 pips on Gold, disable CBDR for today.
     - Check Higher Timeframe Daily Bias (Bullish or Bearish).

  2. 20:00 - 00:00 NY (Asian Session):
     - Plot SD levels: -1.0, -2.0, -3.0, -4.0 and +1.0, +2.0, +3.0, +4.0.
     - Optional Ep 11 Asian Scalp (Target 1:3 RR), but keep macro focus on CBDR.

  3. 02:00 - 05:00 NY (London Killzone) OR 07:00 - 10:00 NY (New York Killzone):
     - Wait patiently for price to reach SD -1.0 or SD -2.0 (if Bullish Bias).
     - DO NOT enter blindly on limit order.
     - Drop to 5m chart -> Watch for Rejection Wick + 5m MSS Displacement.

  4. Post-MSS Execution:
     - Enter long on retest of 5m FVG / Order Block.
     - Stop Loss: Below the confirmed Day Low.
     - Lock Breakeven ($0.00 Risk) when price reaches CBDR Low / 1:1.2R.
     - Primary Target: CBDR High Body.
     - Extended Target: Upper Standard Deviation +1.0 or +2.0.
```
