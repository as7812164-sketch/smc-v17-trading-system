# 📑 PRD (Product Requirements Document)
## Project Name: SMC V17 Crypto Sniper Institutional Trading System
**Version**: 17.0.0-PRO  
**Timeframes**: 1H (Intraday Sniper & Fast Compounding) & 4H (Macro Trend & Swing Anchor)  
**Market**: Crypto Perpetual Futures (Binance & Bitget)  
**Primary Focus**: Smart Money Concepts (SMC), Institutional Order Flow (CVD + Open Interest), $50 Compounding Challenge

---

## 1. Executive Summary & Vision
The **SMC V17 Crypto Sniper Platform** is an institutional-grade, multi-page quantitative trading system designed for automated and semi-automated crypto futures trading. It pairs Smart Money Concepts (Order Blocks, Fair Value Gaps, Liquidity Sweeps) with deep Institutional Order Flow analysis (Cumulative Volume Delta absorption and Open Interest expansion).

The platform carries forward a battle-tested ledger of **238 historical audit trades** and powers a live **$50 to $1,000 Compounding Roadmap** across 1H and 4H timeframes.

---

## 2. Key Objectives & Scope
1. **Precision Sniper Execution**:
   - Strictly identify **2nd Order Blocks (Continuation OBs)** after market structure break (BOS/CHoCH).
   - Lock entry price to the exact outer boundary (Top Boundary `ob_high` for Longs, Bottom Boundary `ob_low` for Shorts).
2. **Order Flow Confirmation (Rocket Ignition)**:
   - Eliminate false breakouts by requiring real-time CVD reversal / absorption and Whale OI expansion ($\Delta OI > +0.5\%$).
3. **Dual Timeframe Synergy**:
   - **4H Macro Anchor**: Establishes high-timeframe directional bias and major liquidity pools.
   - **1H Intraday Sniper**: Captures rapid high-probability pullbacks for fast portfolio compounding.
4. **Data Preservation & Triple-Layer Persistence**:
   - Zero data loss: Preserves all 238 historical trades across Local SQLite (`smc_v17.db`), Master CSV (`trade_journal_ledger.csv`), and Cloud NoSQL (MongoDB Atlas Free Tier).
5. **Continuous Backup**:
   - Automated git backups to GitHub repository (`as7812164-sketch/smc-ai-agent`) and local desktop mirrors.

---

## 3. Core Target Personas & Use Cases
- **Crypto Futures Trader**: Executes high-probability setups with strict 5x leverage and asymmetric risk-reward ($R:R \ge 1:2$).
- **Compounding Portfolio Manager**: Grows small starting capital ($50) systematically into institutional scale ($1,000+) using disciplined dual-ladder compounding.
- **Quantitative Analyst / Auditor**: Reviews historical performance, win rates, post-mortem lessons, and coin-specific behaviors via persistent cognitive memory.

---

## 4. System Requirements & Functional Modules
| Module | Purpose | Priority |
| :--- | :--- | :--- |
| **Trading Terminal (`/`)** | Pro charting dock, 50-coin watchlist, HUD metrics, drawing tools | High |
| **Positions Cockpit (`/positions`)** | Live futures positions, 2nd OB limit orders, mini depth book, 5x order form | High |
| **Compounding & Journal (`/compounding`)** | $50 Growth roadmap, dual ladders, 238-trade ledger sheet, 1-click CSV export | Critical |
| **Mike AI Cognitive Brain (`/brain`)** | 5-agent council, dynamic factor weights, coin radar, lessons learned stream | High |
| **Signals & Zone Radar (`/signals`)** | Live signal feed, filterable 50-coin active zone radar table | High |
| **Settings & Security (`/settings`)** | Telegram bot alerts, Gemini AI config, Bitget auto-trade switch (PAUSED default) | Critical |

---

## 5. Non-Functional Requirements
- **Latency**: Signal detection within $\le 500\text{ ms}$ of candle close / WebSocket tick.
- **Availability**: 99.9% uptime on cloud deployment (Render + MongoDB Atlas).
- **Safety**: Auto-Trading mode must remain **STRICTLY PAUSED / OFF** by default. Zero real-capital execution without manual authorization.
