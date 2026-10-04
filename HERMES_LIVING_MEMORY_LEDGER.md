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
| **Sentry 1: Macro BTC Trend** | 4H BTC EMA50 Filter | If $BTC > EMA50$, market is Bullish $\rightarrow$ Alt Shorts are 100% FORBIDDEN. Alt Shorts only allowed if $BTC < EMA50$ or pair is BTCUSDT. |
| **Sentry 2: Institutional Floor** | Displacement $\ge 5.0\%$ + FVG | Requires clean structural impulse $\ge 5.0\%$ leaving an unmitigated 3-candle Fair Value Gap. |
| **Sentry 3: Inducement (IDM)** | Liquidity Sweep + $\ge 18\%$ Wick | Decisional swing low/high swept by price with candle rejection wick $\ge 18\%$ of total candle range. |
| **Entry Execution** | 50% Mean Threshold (MT) | Entry is STRICTLY placed at the 50% midpoint of the Decisional Order Block: $MT = \frac{OB_{top} + OB_{bot}}{2}$. Never at the outer edge! |
| **Sentry 4: Freshness Guard** | $\le 28$ Bars Tap Window | The order block must be mitigated within 28 bars of the swing high/low. |
| **Multi-Stage Profit Armor** | Dynamic Trailing Protection | **Stage 1:** At $+1.6\%$ gain $\rightarrow$ SL moved to Break-Even $+0.1\%$.<br>**Stage 2:** At $+2.2\%$ gain $\rightarrow$ SL locked in Trailing Profit at $+0.8\%$. |
| **Stop Loss Architecture** | Dynamic ATR Buffer SL | Structural SL placed beyond OB / tap wick with $0.20 \times ATR$ buffer, capped at Hard SL $3.8\%$. |
| **Take Profit** | Macro Target | Standard $2.8\%$ TP on 4H/3H ($2.2\%$ on 1H). |

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
