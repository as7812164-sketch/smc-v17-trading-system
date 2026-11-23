# 🏛️ HERMES MSOB 4.0 — PRACTICAL OPERATIONAL TRADING MANUAL
## From Chart Reading to Live Execution: The Complete Day-to-Day Playbook & Build Roadmap

---

## 📌 EXECUTIVE OVERVIEW: HOW THE SYSTEM ACTUALLY WORKS

Hermes MSOB 4.0 is not a collection of isolated indicators. It is a **closed-loop algorithmic decision pipeline**. You never stare at 1-minute candles wondering what to do. You follow an invariant, mechanical sequence:

```
[NIGHT BEFORE / MORNING]
  Daily Candle Audit ➔ Determine Directional Bias ➔ Identify 2 Targets (Target 1 & Final Target)
          │
          ▼
[1-HOUR TIMEFRAME]
  Locate 2 Institutional POIs (Decisional Post-IDM vs Extreme Base) ➔ Check 0.5 Discount/Premium Gate
          │
          ▼
[WAIT FOR POI TAP (ALERT TRIGGER)]
  Price travels towards POI ➔ DO NOT CHASE MID-AIR (Mountain Road Analogy)
          │
          ▼
[5-MINUTE / 1-MINUTE EXECUTION SENTINEL]
  Choose 1 of 4 Entry Models (Single Candle Sweep, 3 POI Triggers, or 4-Solution Split)
          │
          ▼
[DYNAMIC RISK ARMOR]
  Safe SL beyond Swing ➔ Shift to BE at +1.0% / Cost-to-Cost ➔ Book 50% at 1:3 RR (The Helmet Principle)
```

---

# 🕒 CHAPTER 1: THE PRACTICAL DAILY OPERATING PLAYBOOK (HOW TO USE IT)

### Step 1: The Morning Routine (6:00 AM – 8:00 AM)
1. **Open the Daily Chart (Gold / BTC / Forex):**
   - Did yesterday's Daily candle sweep a previous day's high or low?
   - Did it tap a Daily Fair Value Gap (FVG) or Daily Order Block?
   - **Formulate Bias:**
     - If previous high was swept and closed with rejection $\implies$ **Bearish Bias (Downside)**.
     - If previous low was swept and closed with rejection $\implies$ **Bullish Bias (Upside)**.
     - If price tapped a HTF POI with displacement $\implies$ **Follow HTF Direction**.
2. **Mark 2 Clear Targets:**
   - **Target 1:** The nearest internal swing liquidity or unfilled FVG.
   - **Target 2 (Final Target):** HTF Breakaway Gap, opposing Order Block, or major structural High/Low.

### Step 2: The 1-Hour POI Marking Protocol
1. Drop to the **1-Hour (1H) Chart**.
2. Find the active swing leg (from confirmed Swing Low to confirmed Swing High).
3. Identify **Inducement (IDM):** The first internal pullback to the left of the peak.
4. Mark strictly **TWO Order Blocks**:
   - **Decisional POI:** The first valid Order Block with FVG immediately after IDM is swept.
   - **Extreme Base POI:** The lowest valid Order Block with FVG at the origin of the impulse.
5. Apply the **0.5 Equilibrium Rule:**
   - If looking to Buy, both POIs must be below the 0.5 Fibonacci level (Discount).
   - Any POI in Premium is marked as a Trap / Inducement.
6. **Set TradingView Alerts** at the top/bottom of both POIs. **Close charts and walk away.**

### Step 3: Lower Timeframe Execution (When Alert Triggers)
When price touches the 1H POI, open the **5-Minute (5m)** chart:
- Look for **Market Structure Shift (MSS)**: A 5m swing high/low broken with a full candle body.
- Observe the **Velocity Differential:**
  - Did price crawl into the POI slowly over 10–12 candles? $\implies$ Counter-move is weak; trade with full confidence!
- Execute via one of the **Core Entry Models** (detailed below).

---

# 🎯 CHAPTER 2: THE 5 INSTITUTIONAL ENTRY MODELS (THE CORE)

---

### MODEL 1: The 15m / 1m (or 1H / 5m) Single Candle Liquidity Sweep Sniper
*The highest probability reversal model taught by Shoaib Khan.*
- **Step 1:** On 15m (or 1H), price sweeps a structural high/low or POI with a **wick rejection**.
- **Step 2:** Drop immediately to 1m (or 5m). Wait for a candle to close its **full body beyond the sweeping candle's close**.
- **Step 3:** Enter at the market close or on the 50% retest of that candle.
- **Stop Loss:** Strictly 1 pip beyond the extreme wick tip of the sweeping candle.
- **Risk-to-Reward:** Typically **1:6 to 1:12 RR**.

---

### MODEL 2: First POI vs Last POI 4-Solutions
*Eliminates the fear of missing out vs getting stopped out.*
- **Solution A (50/50 Risk Split):**
  - Allocate 0.5% risk at Decisional POI (First POI).
  - Allocate 0.5% risk at Extreme Base POI (Last POI).
  - If POI 1 runs, you make 1:5+ RR. If POI 1 fails, POI 2 catches the full 1:10+ RR move (net highly profitable).
- **Solution B (Safe SL Cushion):**
  - Enter at the Decisional POI, but place the Stop Loss safely below the Extreme Base POI.
  - Gives 1:4 to 1:6 RR with near-zero premature whip-outs.
- **Solution C (Extreme-Only Filter):**
  - Ignore the Decisional POI entirely. Enter only at Extreme POI.
  - Gives ultra-compressed SL with 1:11 to 1:15 RR.
- **Solution D (First POI High Break Confirmation):**
  - Do not place a blind limit at First POI. Wait for price to tap First POI and produce an internal 5m body break before entering.

---

### MODEL 3: The 3 Operational Triggers Inside POIs
1. **Trigger 1 (Full MSS Retest - Conservative):**
   - Price taps POI $\to$ prints 5m MSS body close $\to$ creates fresh 5m POI $\to$ retests fresh POI $\to$ enter on rejection candle.
2. **Trigger 2 (Pre-MSS Displacement FVG - Momentum):**
   - Price inside POI explodes with a massive candle leaving an FVG before breaking structural MSS.
   - Enter immediately at 50% fill of that FVG with SL below impulse candle.
3. **Trigger 3 (Decisional First POI CISD - Sniper):**
   - Change in State of Delivery. Candle closes beyond the opening price of the prior opposite candle inside POI.

---

### MODEL 4: Second Leg Re-Entry (Missed Trade Protocol)
*What to do when you miss the initial entry (Shoaib's Wednesday Trade).*
- **Rule 1:** NEVER chase price mid-air with a market order.
- **Rule 2:** Wait for the first lower-timeframe Break of Structure (BOS).
- **Rule 3:** A fresh displacement candle must form leaving an internal FVG/OB.
- **Rule 4:** Enter on retest or candle departure with SL above/below the fresh swing.
- **Rule 5:** Maximum **1 to 2 re-entries** per trending leg. Re-entering on leg 3 or 4 is strictly forbidden.

---

### MODEL 5: All Time High (ATH) 3-Candle Confirmation Dip-Buy
*For Gold or Bitcoin in price discovery.*
- **Absolute Rule:** NEVER short an All-Time High!
- **3-Candle Formation:**
  - Candle 1: Makes new ATH peak.
  - Candle 2: Wicks above Candle 1, but closes weak.
  - Candle 3: Closes its full candle body below Candle 2's close.
- **Action:** This signals the start of a healthy pullback. Wait for price to dip into the nearest 1H Demand POI and **BUY THE DIP**.

---

# 🛡️ CHAPTER 3: DYNAMIC RISK ARMOR & TRADE MANAGEMENT

1. **The Helmet Principle (1:3 RR Partial + BE):**
   - When price reaches **1:3 Risk-to-Reward**, automatically book **50% of position size**.
   - Simultaneously shift Stop Loss to **Breakeven (Entry + Fee Shield)**.
   - The remaining 50% is a 100% risk-free trade riding to HTF targets.
2. **The Fast Breakeven Gate:**
   - At $+1.0\%$ net profit, shift SL to cost-to-cost.
3. **The Same-Timeframe Invalidation Rule:**
   - If a candle closes its full body beyond your POI boundary, the setup is **DEAD**. Do not re-enter or hold hoping for a bounce.
4. **The Cost-to-Cost Cut Rule:**
   - If price reaches your target zone early (e.g., Daily OB tapped overnight like Shoaib's Thursday), immediately cut any counter-trend trades at Entry-SL.

---

# 🚀 CHAPTER 4: THE 6-PHASE SYSTEM BUILD ROADMAP

```
Phase 1: Valid Pullback & Left-Side Inducement (IDM) Engine
   │
Phase 2: Confirmed Swings (HH/LL) & Strict Candle Body BOS / CHoCH Engine
   │
Phase 3: Institutional POIs (Color-Independent OBs, FVG Shift & 0.5 Discount Gate)
   │
Phase 4: 3-Tier Structural Hierarchy (STH/STL ➔ ITH/ITL) & Dynamic Trailing Stop
   │
Phase 5: Master Entry Module (Single Candle Sweep, 3 Triggers & First/Last POI Engine)
   │
Phase 6: Full Dual Integration & Verification (TradingView Pine Script v5 + Python Backend)
```

### Detailed Phase Milestones:
- **Phase 1:** Code 2-candle sweeping pullback detector and strictly left-side IDM locator.
- **Phase 2:** Code swing peak confirmation upon IDM sweep + strict candle body close BOS/CHoCH logic.
- **Phase 3:** Code color-independent Order Blocks, FVG backward shift search, dynamic Fibonacci equilibrium gate.
- **Phase 4:** Code 3-candle STH/STL fractals, ITL/ITH hierarchy, and sequential trailing stop rules.
- **Phase 5:** Code 15m/1m single candle sweep detector, First vs Last POI logic, and 3 operational entry triggers.
- **Phase 6:** Build complete Pine Script v5 indicator for TradingView chart visual mirror + Python engine running via Binance Vision API.
