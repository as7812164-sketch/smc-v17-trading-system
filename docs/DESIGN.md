# 🎨 DESIGN: SMC V17 Multi-Page Institutional Platform Design

Yeh document frontend UI/UX design specifications, typography, color palette aur 6 dedicated pages ke architecture ko outline karta hai.

---

## 1. Visual Theme & Institutional Palette

Platform institutional Bloomberg/Binance Pro dark theme follow karta hai:

| Color Role | Hex Code | Purpose |
| :--- | :--- | :--- |
| **Deep Background** | `#080b11` | Primary platform canvas |
| **Surface Dark** | `#0f172a` | Card & dock backgrounds |
| **Border Slate** | `#1e293b` | Clean structural dividing borders |
| **Accent Emerald** | `#10b981` | Long / Buy zones, positive PnL, bullish CVD |
| **Accent Rose** | `#ef4444` | Short / Sell zones, negative delta, stop loss |
| **Cyan Glow** | `#06b6d4` | 2nd OB primary boundary highlights |
| **Amber Warning** | `#f59e0b` | Confluence alerts & pending limit triggers |
| **Text Primary** | `#f8fafc` | Headings and high-contrast numerical metrics |
| **Text Muted** | `#94a3b8` | Subtitles, labels, and metadata |

---

## 2. Global Navigation & 24H Ticker Strip

Every page features a persistent, unified header:
1. **Brand & Version**: `SMC V17 PRO` with neon pulse indicator.
2. **Page Navigation Links**:
   - `📊 Terminal` (`/`)
   - `💼 Positions` (`/positions`)
   - `🏆 Compounding` (`/compounding`)
   - `🧠 Mike Brain` (`/brain`)
   - `⚡ Signals` (`/signals`)
   - `⚙️ Settings` (`/settings`)
3. **Master 24H Ticker Strip**:
   - Live BTC/USDT Mark Price & 24h % change.
   - Real-time Bitget Account Equity (`$77.59 USDT`).
   - Compounding Stage 1 Progress Pill (`$77.59 / $100` $\rightarrow 77.6\%$).
   - Quick Manual Scan button and Telegram broadcast status.

---

## 3. Dedicated Pages Architecture

```
        ┌────────────────────────────────────────────────────────┐
        │               MASTER NAVBAR & 24H TICKER               │
        └───────────────────────────┬────────────────────────────┘
                                    │
    ┌──────────────┬────────────────┼──────────────┬─────────────┴────────────┐
    ▼              ▼                ▼              ▼                          ▼
┌────────┐   ┌───────────┐   ┌─────────────┐   ┌─────────┐   ┌─────────┐   ┌──────────┐
│Terminal│   │ Positions │   │ Compounding │   │  Brain  │   │ Signals │   │ Settings │
│  (/)   │   │(/positions│   │(/compounding│   │ (/brain)│   │(/signals│   │(/settings│
└────────┘   └───────────┘   └─────────────┘   └─────────┘   └─────────┘   └──────────┘
```

### 3.1 Terminal (`/`)
* **Left Dock**: 50-Coin Crypto Watchlist with live price, 24h change, and 2nd OB trigger tags.
* **Center Stage**: TradingView Lightweight Charts v4 with interactive candlestick rendering, OB boundary boxes, and floating drawing toolbar.
* **Bottom Dock**: Pro positions and recent trade logs.

### 3.2 Positions & Cockpit (`/positions`)
* **Live Futures Position Cards**: Mark price, unrealized PnL, liquidation buffer distance, 1-click market close.
* **2nd OB Pending Limit Orders**: Visual list of pending orders with distance % to 2nd OB boundary.
* **Mini Depth Book & Order Form**: Isolated 5x leverage order ticket directly synced to Bitget Pro.

### 3.3 Compounding & Journal (`/compounding`)
* **Dual Compounding Ladders**: 4H Macro ladder ($77.59 $\rightarrow$ $1,000) and 1H Fast Scalp ladder.
* **Growth Simulator**: Interactive compounding calculator with custom starting capital and win-rate inputs.
* **Master Trade Journal Ledger**: Filterable table showing all **238 historical audit trades** with search, exchange filter, status filter, and **1-Click CSV Export**.

### 3.4 Mike AI Cognitive Brain (`/brain`)
* **Metrics Radar**: 69.3% Lifetime Win Rate, 98.7% Capital Safety Rate.
* **Adaptive Factor Weights**: Visual sliders showing dynamic weights for 2nd OB, CVD, OI, and Turtle Soup sweeps.
* **5-Agent Council**: Mike (Lead Manager), Alex (Quant Engineer), David (Risk Guard), Liam (Chartist), Sarah (Macro Analyst).

### 3.5 Signals & Radar (`/signals`)
* **Live Stream**: WebSocket/Polling execution feed showing real-time 1H and 4H triggers.
* **50-Coin Zone Radar Table**: Comprehensive table showing coin, timeframe (1H/4H), zone type, 2nd OB top/bottom boundaries, distance %, and confluence score.

### 3.6 Settings & Pine Script (`/settings`)
* **API Credentials**: Telegram Bot token, Gemini AI API key.
* **Safety Toggle**: Bitget Auto-Trade switch (strictly PAUSED by default).
* **Pine Script v5 Studio**: Full Pine Script v5 codebox with 1-click clipboard copy and TradingView installation guide.
