# 🚀 SMC V17 Crypto Trading Terminal & AI Analyst (24x7 Scanner)

Ek complete, professional crypto trading system aur web dashboard jo aapke **SMC V17 Strategy** aur **Free Setup Roadmap** ke mutabik 100% zero recurring cost par Binance USDT-M Futures ke 50 coins scan karta hai.

---

## 🌟 Key Features

1. **Exact SMC V17 Strategy Engine**:
   - **4H Timeframe** analysis on Binance USDT-M Futures.
   - **Displacement**: 10-period Average Body $\times 1.5$ threshold filter.
   - **True Origin Candle**: Latest opposite candle (Red for BUY, Green for SELL) within previous 6 candles.
   - **Order Block Boundary**: Full origin candle High-Low range ($OB_{high}$ to $OB_{low}$).
   - **7% Qualification Target**:
     - BUY: $OB_{high} \times 1.07$ (+7% clean move)
     - SELL: $OB_{low} \times 0.93$ (-7% clean move)
   - **Pre-7% Invalidation**: Agar 7% move se pehle price OB ko touch ya retest karti hai $\rightarrow$ **PERMANENTLY INVALID**.
   - **Freshness & No Expiry**: Once qualified, zone stays active indefinitely until First Tap.
   - **First Tap Entry**: Pehla boundary touch (OB High for BUY, OB Low for SELL) triggers entry alert.
   - **Risk Management**: Target $TP = +4\%$, Stop Loss $SL = -3\%$.
   - **Max Active Zones**: Maximum 2 BUY + 2 SELL active zones per coin.
   - **Soft Tags**: Liquidity Sweep, Fair Value Gap (FVG), Break of Structure (BOS).

2. **Professional Dark Terminal UI (TradingView Lightweight Charts)**:
   - Real-time 4H candlestick chart with volume histogram.
   - Visual Order Block rectangles (Green for BUY, Red for SELL).
   - Dynamic 7% Qualification line, Entry line, TP line, and SL line.
   - Candle markers for True Origin, Displacement, and First Tap Entry.
   - KPI metrics: Total Signals, Overall Win Rate %, BUY WR %, SELL WR %, TP Hits, SL Hits, and Last Alert banner.
   - 50 Coins Watchlist with real-time prices, filters, and active zone badges.

3. **Gemini AI Chart & Setup Analyst**:
   - Integrated Google Gemini AI (supporting Hinglish / English).
   - On-demand setup explanations ("Why is this OB valid?", "Displacement strength", "Distance to entry").
   - Analyzes soft tags confluence (Sweep, FVG, BOS) and risk advice without violating strict strategy rules.

4. **Telegram Live Alert Bot**:
   - Sends the exact **🟢 SMC V17 LIVE** status dashboard shown in your screenshot.
   - Real-time instant alerts on **First Tap Entry**, **TP Hit (+4%)**, and **SL Hit (-3%)**.
   - Live pinned message updates every cycle.

5. **Zero Recurring Cost**:
   - Public Binance Futures REST API (Free, no API key needed for scanning).
   - Local SQLite database (WAL mode, fast, persistent).
   - Free Google Gemini API tier.

---

## 📂 Project Structure

```
smc_v17_trading_system/
│
├── config.py                 # 50 coins list, strategy constants (7%, 1.5x, 4% TP, 3% SL)
├── database/
│   └── db.py                 # SQLite database schema, zones, signals, and metrics
├── engine/
│   ├── smc_v17.py            # SMC V17 core mathematical detection & state machine
│   └── tags.py               # Soft tags: FVG, Liquidity Sweep, BOS
├── feed/
│   └── binance_feed.py       # Async Binance 4H klines & live ticker feed with cache
├── alerts/
│   └── telegram_service.py   # Telegram bot service matching exact live status layout
├── ai/
│   └── gemini_analyst.py     # Gemini AI assistant with Hinglish explanation & fallback
├── scanner.py                # 24x7 background scanner & live price watcher
├── app.py                    # FastAPI server & WebSocket streaming
├── static/
│   ├── index.html            # Dark-theme trading terminal dashboard
│   ├── style.css             # High-contrast terminal styling
│   └── app.js                # TradingView charts renderer, live WebSocket handler
├── run.bat                   # 1-Click Windows Launcher
├── requirements.txt          # Minimal Python dependencies
└── test_smc_v17.py           # Automated unit tests
```

---

## 🚀 Quick Start Guide

### 1. Run with 1-Click:
Windows terminal mein `run.bat` par double click karein, ya run karein:
```bash
python app.py
```

### 2. Open Web Dashboard:
Apne browser me open karein:
👉 **[http://localhost:8000](http://localhost:8000)**

### 3. Configure Telegram & Gemini (Settings Button ⚙️):
Dashboard ke top right me **Settings (Gear Icon)** par click karein:
- **Telegram Bot Token**: BotFather se generate kiya hua token.
- **Telegram Chat ID**: Aapki chat ya channel ID jisme alerts chahiye.
- **Gemini API Key** (Optional): Google AI Studio ka free API key deep AI reasoning ke liye.
- Click **"Test Telegram"** to verify connection instantly!

---

## 🧪 Testing

Automated tests run karne ke liye:
```bash
python test_smc_v17.py
python test_endpoints.py
```
