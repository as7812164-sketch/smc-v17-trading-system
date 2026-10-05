# 🧠 HERMES 3.5: PERMANENT LIVING MEMORY & SYSTEM STATE LEDGER
> **CRITICAL DIRECTIVE:** This ledger is the single source of truth for the Hermes trading system. Even if context compaction or memory truncation occurs in the conversation, this document preserves all core strategies, user mandates, deployed architecture, and operational rules.

---

## 📌 1. CURRENT ACTIVE PRODUCTION PROFILE

* **Active Strategy Engine:** **HERMES 3.5 SINGLE TIER** (Institutional Smart Money Concepts / ICT)
* **Active Compounding Structure:** **10-Section Deca Compounding Matrix**
  * **Total Capital:** **$500.00 USDT** ($50.00 starting balance per isolated section)
  * **Sections:** Section 1 to Section 10 (`section_1` through `section_10`)
  * **Leverage:** 5x Isolated Futures
  * **Compounding Rule (100% PURE COMPOUNDING):** **ZERO AMOUNT SPLIT**. 100% of the section balance is deployed as margin into each trade. (Example: $50 balance makes +10% profit -> next trade opens with full $55 margin, compounding 100% geometrically across all 10 sections!).
  * **Milestone Target:** $50 ➔ $2,000.00 per section ($500 ➔ $20,000.00 cumulative deca portfolio)
* **Live Server Deployment URL:** `https://smc-ai-agent.onrender.com`
* **Telegram WebApp URL:** `https://smc-ai-agent.onrender.com/?v=350_deca`
* **Service Worker Cache Key:** `hermes-35-deca-v3`

---

## 🚫 2. ABSOLUTE MANDATES & FORBIDDEN PATTERNS

1. **PROHIBITED HEADER:**
   * **NEVER** output or use the header: `### 🏛️ HERMES 3.5 AI QUANT VERDICT & SUGGESTION (LIVE PULSE)` under any circumstances.
2. **ZERO CONCURRENT TRADE COLLISIONS:**
   * No two compounding sections may ever enter the same coin in the same direction simultaneously.
   * Dedicated slot isolation must be strictly enforced.
3. **ZERO LOOPHOLE PRINCIPLE (SMG v17 Prevention):**
   * Never deploy code without automated verification and cross-checking.
   * Every fix must be logged, verified against live endpoints, and certified.
4. **LEGACY ARCHIVING:**
   * Obsolete, superseded, or scratch scripts from older iterations (SMG v17, Hermes 2.0, Hermes 2.5, Quad $200) must remain archived in `archive/` to keep the active production tree clean.

---

## 📐 3. HERMES 3.5 SINGLE TIER: MATHEMATICAL CORE RULES

| Sentry / Rule | Technical Formulation | Verification Criteria |
| :--- | :--- | :--- |
| **Sentry 1: Macro BTC Sentry** | Multi-EMA Trend Anchor | Trend Cross ($EMA20 \ge EMA50$) OR Macro Anchor ($Close \ge EMA200$). Emergency dump brake ($\ge 1.5\%$ drop) vetos longs. |
| **Sentry 2: Institutional Floor** | Displacement $\ge 5.0\%$ + FVG | Requires clean structural impulse $\ge 5.0\%$ leaving an unmitigated 3-candle Fair Value Gap. |
| **Sentry 3: Inducement (IDM)** | Liquidity Sweep + $\ge 18\%$ Wick | Decisional swing swept with candle rejection wick $\ge 18\%$ defending Mean Threshold ($MT$). |
| **Entry Execution** | 5% Boundary Penetration | Entry placed at $OB_{high} - 0.05 \times \text{range}$ (Long) / $OB_{low} + 0.05 \times \text{range}$ (Short) with 0.20% Proximity Radar pre-arm. |
| **Sentry 4: Retest Maturation** | 18h Intraday / 32h Macro | Order block must mature $\ge 18$ bars (1H) or $\ge 8$ bars (4H) before first tap is armed, eliminating early chop. |
| **Multi-Stage Profit Harvest** | Stepped Profit Armor | **Stage 1:** $+8.0\%$ ROE ($+1.6\%$ move) $\rightarrow$ BE Lock $+0.1\%$.<br>**Stage 2:** $+9.0\%$ ROE ($+1.8\%$ move) $\rightarrow$ Locks $+4.5\%$ ROE cash profit.<br>**Final TP:** $+14.0\%$ ROE ($+2.8\%$ move). |
| **Stop Loss Architecture** | Dynamic ATR Buffer SL | Structural SL placed beyond OB / tap wick with $0.20 \times ATR$ buffer, capped at Hard SL $3.8\%$. |

---

## 🧪 4. SCIENTIFIC MULTI-TIMEFRAME QUANT RESULTS

Tested on 6-Month High-Resolution 15m dataset (20 coins | 360,000 candles) and 2-Year Continuous dataset (22 coins | 385,440 candles):

* **3H (180m):** **92.38% Win Rate** (OOS: 92.15%), Profit Factor 4.96. Milestone $1K reached at Trade #42, $2K at Trade #48. 🥇 *Highest accuracy, outperforming standard 4H.*
* **4H (240m):** **90.33% Win Rate** (OOS: 90.49%), Profit Factor 4.63. Milestone $1K reached at Trade #39, $2K at Trade #77. 🥈 *Robust macro anchor.*
* **1H (60m):** **83.82% Win Rate** (OOS: 85.39%), Profit Factor 2.50. Milestone $1K at Trade #147. 🥉 *Reliable intraday anchor.*
* **1.5H (90m):** **76.98% Win Rate**, Profit Factor 1.78. ⚠️ *Misaligned session closes degrade accuracy by ~10%.*
* **45m (45min):** **74.20% (Strict) / 67.49% (Calibrated) Win Rate**. ❌ *High retail noise and liquidity chop.*

---

## 🏗️ 5. ACTIVE PRODUCTION DIRECTORY MAP

* `app.py`: FastAPI backend, background scanner loops, Deca compounding endpoints (`/api/paper/sections`), WebSocket broadcaster.
* `config.py`: System configuration, Top-22 vetted coins, feature flags (`HERMES_35_DECA_COMPOUNDING = True`).
* `engine/hermes2_apex_live.py`: Real-time orderflow scanner, 50% MT order placement, Multi-stage profit armor watchdog.
* `database/db.py`: SQLite ledger storing `paper_sections`, `paper_trades`, and system configuration.
* `alerts/telegram_service.py`: Telegram Bot alerts, WebApp URL routing (`/?v=350_deca`), interactive menu buttons.
* `static/index.html`: Desktop trading terminal, Deca Portfolio ($500.00) and Section 1-10 selector cards.
* `static/mobile.html`: Mobile responsive terminal with persistent cache-busting.
* `static/sw.js`: Service worker managing PWA caching with version `hermes-35-deca-v3`.
* `archive/`: Storage folder for obsolete and legacy scripts (SMG v17, Hermes 2.0/2.5).

---

## 🔭 6. USER STRUCTURAL DISCOVERIES: ROCKET GAP & 2-DAY MATURATION CYCLE

Formulated from User's TradingView visual chart discoveries (OPUSDT, ICPUSDT, MANAUSDT) and verified across 1-Year Continuous OOS data (`user_discoveries_backtest_results.json`):

1. **"The Rocket Gap" (Banning Late-Cycle Top OBs):**
   * **Rule:** Bullish OBs must satisfy $\Phi_{\text{leg}} \le 0.70$ (vetoes late-cycle distribution traps in upper 30% of rally) and $\text{Airspace}_{\%} \ge 3.0\%$ (clean unmitigated liquidity void / "Red Gap" between OB base and origin pivot).
   * **Result:** Eliminates false breakout tops, surges 4H Direct Win Rate to **64.52%** (PF 9.99, only 14 losses in 1 year across Top 25).
2. **"The 2-Day Maturation Cycle" (Institutional Breathing Window):**
   * **Rule:** Retest tap must satisfy $36 \le \text{bars\_since\_ob} \le 144$ on 1H ($9 \le \text{bars} \le 36$ on 4H).
   * **Result:** Replaces obsolete `max_tap_window = 28` (which prematurely expired 60-bar winners like OPUSDT) and prevents premature noise stop-outs ($bars < 36$). Empirically verified average maturation: OPUSDT = **63.3 bars**, ICPUSDT = **63.1 bars**, MANAUSDT = **54.5 bars**.

---

## ⚡ 7. HERMES 3.5 RADAR HARVEST (5% BOUNDARY) PRODUCTION RULES

Live in production across `engine/hermes35_live.py`, `app.py`, and `HERMES_3_5_SINGLE_TIER_OFFICIAL.pine`:

1. **5% Boundary Entry:**
   - Bullish: $\text{Entry} = \text{OB}_{\text{high}} - 0.05 \times (\text{OB}_{\text{high}} - \text{OB}_{\text{low}})$
   - Bearish: $\text{Entry} = \text{OB}_{\text{low}} + 0.05 \times (\text{OB}_{\text{high}} - \text{OB}_{\text{low}})$
2. **0.20% Proximity Radar Pre-Arm:**
   - Bullish Radar: $\text{Entry} \times 1.0020$. Triggers limit order pre-arming before the 5% boundary touch.
   - Bearish Radar: $\text{Entry} \times 0.9980$.
3. **Stepped Profit Harvest (Guaranteed Cash Returns):**
   - **Stage 1 (+8.0% ROE / +1.60% price gain at 5x):** SL moved to Break-Even ($\text{Entry} \times 1.0010$).
   - **Stage 2 (+9.0% ROE / +1.80% price gain at 5x):** SL shifted to $+4.50\%$ ROE ($\text{Entry} \times 1.0090$ Long, $\text{Entry} \times 0.9910$ Short), locking guaranteed cash profit!
   - **Final TP (+14.0% ROE / +2.80% price gain at 5x):** Full position exit.
4. **Rocket Airspace Runway Void:** $\ge 5.0\%$ displacement clearance void away from OB before returning.
5. **2-Day Maturation Horizon:** Retest occurs after $\ge 48$ bars on 1H / $\ge 12$ bars on 4H (max 720 bars 1H / 360 bars 4H).
6. **Origin Bedrock Floor/Ceiling:** OB candle is the extreme lowest/highest of prior 25 bars.
7. **Zero Legacy SMC v17:** All legacy `analyze_candles_smc_v17` code purged from `/api/klines`, helper scripts, and scanner loops.
8. **Real-Time Tap Watchdog Strict Parity:** Evaluates live ticks against 5% Boundary Penetration (`eff_entry`) and 0.20% Proximity Radar (`radar_price`) every 5 seconds, preserving dynamic ATR structural SL/TP with zero fallback to 50% MT or 0% boundary.

