# 📘 SMC V17 SYSTEM MASTER LEDGER & DISASTER RECOVERY MANUAL
**Last Updated:** 20 September 2026 • 22:46 PM IST  
**System Status:** 🟢 PRODUCTION LIVE ON RENDER CLOUD (WITH TELEGRAM MINI-APP & IN-PLACE AUTO-EDIT)  
**Architecture:** 24/7 Cloud Automated Crypto Trading Terminal & Autonomous Telegram Scanner  

---

## 1. 🌐 Master System Overview & Credentials Table

| Item | Details / Value | Purpose |
| :--- | :--- | :--- |
| **Project Name** | `SMC V17 Crypto Trading Terminal` | 4H Order Block Automated System |
| **Live Web Terminal** | [https://smc-ai-agent.onrender.com](https://smc-ai-agent.onrender.com) | Public live browser terminal |
| **Render Service ID** | `srv-d61q691r0fns73f4p720` | Render Web Service identifier |
| **Render Owner ID** | `tea-d61pqbogjchc738thce0` (`as7812164@gmail.com`) | Render Workspace Account |
| **Render API Key** | `[REDACTED_RENDER_KEY]` | Full API deployment access |
| **GitHub Repository** | `https://github.com/as7812164-sketch/smc-ai-agent` | Connected auto-deploy Git repo |
| **GitHub Token (PAT)** | `[REDACTED_TOKEN]` | Repo write & push access |
| **Telegram Bot** | `@SMC_V17_Trigger_Bot` | Signal alerts & live dashboard |
| **Telegram Bot Token** | `8593127726:AAGdudgSBU_krN-g42Cq_5ovc5DW2c6A-yY` | Bot API communication |
| **Telegram Chat ID** | `752247227` | Direct user alert destination |
| **Gemini AI API Key** | `AIzaSyDdAd6NelUiI-EO56igFNKkEPB0p1P_QPM` | AI Market Structure Analyst |
| **System Timezone** | `Asia/Kolkata` (IST, UTC+5:30) | Standard Indian Standard Time |
| **Keep-Alive Monitor** | [https://cron-job.org](https://cron-job.org) -> `/api/status` | Prevents Render 15-min free sleep |

---

## 2. 🧠 Strict SMC V17 Strategy Rulebook

All code in `engine/smc_v17.py` enforces these non-negotiable quantitative rules:

* **Timeframe:** `4H` (Binance USDT-M Futures).
* **Displacement Rule:** Candle body must be $\ge 1.5 \times$ the average body of the prior 10 candles.
* **True Origin Rule:** Origin candle is the latest opposite-colored candle within the prior 6 candles before the displacement.
* **7% Qualification Rule:** Price must expand at least $+7\%$ (BUY) or $-7\%$ (SELL) from the Order Block without retesting the OB. Any pre-retest invalidates the zone.
* **Entry Rule:** `FIRST_TAP_ONLY` at the Order Block boundary:
  - **BUY Entry:** At `OB High`
  - **SELL Entry:** At `OB Low`
* **Risk / Reward:**
  - **Take Profit (TP):** $+4.0\%$ from entry price.
  - **Stop Loss (SL):** $-3.0\%$ from entry price.
* **Capacity Constraints:** Maximum 3 active BUY zones and 3 active SELL zones per coin (up to 3 Order Blocks displayed).
* **Soft Confluence Tags:** Liquidity Sweep, FVG, BOS are tags only (soft filters) and do not reject zones.

---

## 3. 💼 100 USDT Paper Trading Engine Ledger

* **Initial Capital:** `100.00 USDT`
* **Allocation Policy:** `10% of dynamic balance` per trade (e.g. \$10.00 at \$100.00 balance).
* **Execution Mode:** 100% Autonomous.
  - Triggered immediately when live price touches a qualified 4H Order Block.
* **PnL Formulas:**
  $$\text{Gain on TP} = \text{Position Size} \times 0.04 = +\$0.40\text{ USDT}$$
  $$\text{Loss on SL} = \text{Position Size} \times 0.03 = -\$0.30\text{ USDT}$$
* **Database Tracking:**
  - `paper_account`: Tracks `initial_balance`, `current_balance`, `total_pnl`, `win_count`, `loss_count`.
  - `paper_trades`: Logs trade `id`, `symbol`, `side`, `entry_price`, `position_size_usdt`, `tp_price`, `sl_price`, `pnl_usdt`, `pnl_pct`.
* **API Access:** `GET https://smc-ai-agent.onrender.com/api/paper_trading`

---

## 4. 🗂️ Complete File & Component Architecture

```
smc_v17_trading_system/
├── app.py                      # FastAPI web server, WebSocket manager, REST API endpoints
├── main.py                     # Entrypoint wrapper for Render cloud (uvicorn launcher)
├── config.py                   # Central config: coins, risk params, timezones, API keys
├── scanner.py                  # Background scanner: scans 50 pairs every 10m & ticks every 5s
├── requirements.txt            # Python dependencies (fastapi, uvicorn, aiohttp, pillow, etc.)
├── Dockerfile                  # Container definition for cloud deployment
├── Procfile                    # Web service process declaration: "web: python app.py"
├── render.yaml                 # Infrastructure-as-code for Render deployment
├── ai/
│   ├── smart_money_analyzer.py # Algorithmic ICT/SMC Engine (BOS/CHoCH, Sweeps, FVGs, OTE, Confluence 0-100)
│   └── gemini_analyst.py       # Gemini 2.5 Flash institutional market structure Hinglish consultant
├── alerts/
│   └── telegram_service.py     # Telegram Bot: send_photo, send_raw_message, pinned status, /ai, /analyze
├── database/
│   ├── db.py                   # SQLite storage (WAL mode) for zones, signals, paper trading
│   └── smc_v17.db              # Active SQLite database file
├── engine/
│   ├── smc_v17.py              # Mathematical SMC V17 detection engine (7% qualification, true origin)
│   ├── tags.py                 # Soft tags analyzer: Liquidity Sweeps, FVGs, BOS
│   └── chart_image_generator.py# High-res TradingView dark theme chart renderer (Pillow)
├── feed/
│   └── binance_feed.py         # Universal multi-source feed (Vision + Bybit) bypassing US geo-blocks
└── static/
    ├── index.html              # Modern Trading Terminal UI layout with full screen
    ├── app.js                  # Frontend WebSocket client, Lightweight Charts integration
    └── style.css               # Futuristic dark TradingView theme styling
```

---

## 5. 🛠️ Disaster Recovery & Troubleshooting Runbook

### Case 1: Server Goes Offline / Sleeps
* **Cause:** Cron-job was paused or free tier 15-minute inactivity kicked in.
* **Fix:**
  1. Open [https://cron-job.org](https://cron-job.org), ensure the cronjob targeting `https://smc-ai-agent.onrender.com/api/status` is **Active** with 5-10 minute interval.
  2. Open `https://smc-ai-agent.onrender.com` in your browser to immediately wake up the container.

### Case 2: Telegram Bot Does Not Send Alerts
* **Cause:** Bot Token or Chat ID mismatch, or Telegram session timeout.
* **Fix:**
  1. Send `/status` in Telegram to `@SMC_V17_Trigger_Bot`.
  2. Test manually: Trigger `POST https://smc-ai-agent.onrender.com/api/telegram/test` via curl or browser.

### Case 3: Chart Data is Blank / Disconnected
* **Cause:** Binance US geoblock on direct futures API.
* **Fix:**
  - `feed/binance_feed.py` automatically falls back to `https://data-api.binance.vision` (which has 0 geoblocks) and Bybit for `KASUSDT`. Ensure this multi-source feed remains untouched.

### Case 4: Complete Fresh Redeployment (1-Click Restore)
If Render service is accidentally deleted or needs to be recreated from zero:
1. All files are permanently backed up on your Desktop at `Desktop\SMC_V17_COMPLETE_BACKUP`.
2. Push files to GitHub `https://github.com/as7812164-sketch/smc-ai-agent`.
3. In Render: New Web Service -> Select repository `smc-ai-agent` -> Branch `main`.
4. Build command: `pip install -r requirements.txt`, Start command: `python app.py`.
5. Environment Variables:
   - `TELEGRAM_BOT_TOKEN = 8593127726:AAGdudgSBU_krN-g42Cq_5ovc5DW2c6A-yY`
   - `TELEGRAM_CHAT_ID = 752247227`
   - `GEMINI_API_KEY = AIzaSyDdAd6NelUiI-EO56igFNKkEPB0p1P_QPM`
   - `TZ = Asia/Kolkata`
   - `PYTHONUNBUFFERED = 1`

### Case 5: Resetting Paper Trading Wallet
If you ever want to restart paper trading from fresh $100.00 USDT:
- Run this simple command:
  ```python
  from database.db import get_connection
  with get_connection() as conn:
      conn.execute("DELETE FROM paper_trades;")
      conn.execute("UPDATE paper_account SET current_balance = 100.0, total_pnl = 0.0, win_count = 0, loss_count = 0 WHERE id = 1;")
      conn.commit()
  ```

---

## 6. 🎨 TradingView Floating Drawing Toolbar Guide (Authentic 2-Click Engine)
Fully upgraded to replicate authentic TradingView behavior:
1. **2-Click Placement & Drag-and-Drop Hybrid**:
   - **Click 1**: Anchors Point 1 (shown with a pulsing anchor ring).
   - **Mouse Move**: Shows dynamic live preview following cursor (ghost line/rectangle/arrow/ruler).
   - **Click 2**: Anchors Point 2, locks the drawing, saves to `localStorage`, and deactivates tool.
   - Users who prefer holding and dragging can also drag & release smoothly!
2. **Tools Included**:
   - **Trend Line (`o—`)**: 2-click / drag placement with dual endpoint anchor handles.
   - **Rectangle / OB Box (`□`)**: 2-click / drag placement with 4 corner anchors.
   - **Price Range / Ruler (`↨`)**: Measures price delta, %, bar count, and time elapsed with styled badge.
   - **Date / Time Range (`|->|`)**: Measures bar count and elapsed time with boundary columns.
   - **Path / Polyline Zigzag (`o-o-o^`)**: Multi-point market structure path with vertex dots and final arrowhead. Double-click or Esc finishes.
   - **Long Position (`=L=`)**: 1-click placement; dynamically spans 18 bars (`logical + 18`), green TP (+4%) & red SL (-2%) boxes with 1:2 R:R metrics. Scales seamlessly on zoom/pan.
   - **Short Position (`=S=`)**: 1-click placement; dynamically spans 18 bars (`logical + 18`), red SL (+2%) & green TP (-4%) boxes with 1:2 R:R metrics.
   - **Trend Arrow (`↗`)**: 2-click / drag line with clean directional arrowhead.
   - **Callout Note (`⚑`)**: 1-click opens custom glass modal with quick SMC tags ("4H Origin OB", "Liquidity Sweep", "ChOCH", "BOS", "FVG", "EQH", "EQL") or custom text.
   - **Eraser Tool (`🧹`)**: Hovering over any drawing highlights it in red; clicking it deletes that drawing immediately!
   - **Undo (`Ctrl+Z`) & Trash (`🗑`)**: Instant undo or clear all drawings for current symbol.
3. **Continuous Coordinate Resolution**:
   - Stores `logical` (bar index), `time` (candle seconds), and `price` (float).
   - Uses `timeScale.logicalToCoordinate(pt.logical)` for flawless, non-breaking zoom, pan, and sub-bar rendering.
4. **Canvas Layering & Pointer Events**:
   - `tvOverlayCanvas` is set to `zIndex: 15` (above chart panes, below toolbar at `zIndex: 30`).
   - When no tool is active: `pointerEvents: 'none'` (100% chart pan/zoom smoothness).
   - When tool is active: `pointerEvents: 'auto'` with precision crosshair cursor.

---

## 7. 🛡️ Anti-Spam & Telegram Alert Deduplication System
Fixed recurring/old alert spam caused by 10-minute scan status reset:
1. **DB Status Preservation (`save_or_update_zone`)**:
   - `ON CONFLICT DO UPDATE` now checks `WHEN zones.status IN ('ACTIVE', 'TP_HIT', 'SL_HIT', 'INVALIDATED') AND excluded.status = 'QUALIFIED' THEN zones.status`.
   - Prevents the 10-minute 4H historical scan from downgrading active or completed trades back to `QUALIFIED`.
2. **`sent_alerts` Table**:
   - Stores `alert_key` = `{symbol}_{side}_{origin_time}_{signal_type}`.
   - Prevents `FIRST_TAP_ENTRY`, `TP_HIT`, or `SL_HIT` from ever being alerted twice in a zone's lifetime.
3. **Startup History Pre-Registration**:
   - On container boot, all historical `ACTIVE`, `TP_HIT`, and `SL_HIT` zones from historical candles are pre-registered into `sent_alerts`.
   - Prevents old trades from firing alerts when container restarts.
4. **Invalidation Check Before Entry**:
   - For BUY: If `current_price < ob_low * 0.97`, price already crashed through the OB. The zone is marked `INVALIDATED` and NO alert is sent.
   - For SELL: If `current_price > ob_high * 1.03`, price already spiked through the OB. The zone is marked `INVALIDATED` and NO alert is sent.
5. **Telegram Polling Backlog Purge**:
   - `start_polling` fetches `getUpdates(offset=-1)` on startup to drop stale queued updates and avoid replaying old commands.
6. **Proximity Warning Rate Limiting**:
   - Proximity warnings only edit existing messages in-place; new message creation is throttled to at most once every 2 hours.


