import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Indian Standard Time (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now() -> datetime:
    """Returns current datetime in Indian Standard Time (IST)."""
    return datetime.now(IST)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- HERMES STRATEGY OPTIONS (PRODUCTION & EXPERIMENTAL) ---
STRATEGY_OPTIONS = ["HERMES_3.0_QUANTUM", "HERMES_3.5_DUAL_TIER_SNIPER", "HERMES_2.5_APEX_HYBRID"]
STRATEGY_VERSION = os.getenv("STRATEGY_VERSION", "HERMES_3.5_DUAL_TIER_SNIPER")  # Dual-Tier Sizing + 15m Micro-Sniper
HERMES_3_MEAN_THRESHOLD_ENTRY = True
HERMES_3_MULTI_STAGE_ARMOR = True
HERMES_3_BTC_EMERGENCY_SHIELD = True
HERMES_3_DYNAMIC_ATR_BUFFER = True
HERMES_3_5_DUAL_TIER_SIZING = True   # Pillar 1: Full Size Tier 1, Half Size Tier 2 with fast BE
HERMES_3_5_15M_SNIPER_GATE = True    # Pillar 2: 15m Rejection Gate (rejects runaway knives/rockets)
HERMES_3_5_CVD_DELTA_FILTER = True   # Pillar 3: Cumulative Volume Delta & OI Alignment
TIMEFRAME = "4h"
KLINES_LIMIT = 200

# Average candle body period & displacement multiplier
AVG_BODY_PERIOD = 10
DISPLACEMENT_MULT = 1.5

# Lookback to find True Origin candle (opposite color)
ORIGIN_LOOKBACK = 6

# 7% Qualification Rule
QUALIFICATION_PCT = 0.07  # +7% for BUY, -7% for SELL

# Risk / Reward Rules
TP_PCT = 0.04  # +4%
SL_PCT = 0.03  # -3%

# Active Zone Constraints (Strict 3 OB Sandwich Rule per user specification)
MAX_ACTIVE_BUY_PER_COIN = 3
MAX_ACTIVE_SELL_PER_COIN = 3
REQUIRED_OB_COUNT_FOR_TRADE = 3  # Must have 3 unmitigated OBs to trigger setup (Mode A)
TRADE_ONLY_MIDDLE_2ND_OB = True  # Strictly trade ONLY the 2nd (middle) OB
ENTRY_MODE = "FIRST_TAP_ONLY"
ZONE_EXPIRY = "NONE"

# --- Hermes Institutional V17.5 Upgrades (Forensic Sweet Spots) ---
ENABLE_DUAL_MODE_ENGINE = True    # Mode A (Classic 3-OB) + Mode B (2-OB Dynamic Expansion + IDM + FVG)
AIRSPACE_REQ_15M = 0.015          # 1.50% Airspace for 15m Scalps (98.3% Safety)
AIRSPACE_REQ_1H = 0.025           # 2.50% Airspace for 1H Intraday (82.7% WR, 98.1% Safety)
AIRSPACE_REQ_4H = 0.035           # 3.50% Airspace for 4H Macro Swing (80.5% WR, 97.6% Safety)
ENABLE_KING_BITCOIN_SHIELD = True # Disqualify altcoin entries during BTC dumps (> -1.5% or < EMA50)
ENABLE_1400_UTC_JUDAS_GATE = True # Protect against 14:00 UTC US economic Judas swings
REJECTION_WICK_MIN_PCT_1H = 0.35  # Require >= 35% rejection wick on 1H entries (eliminates falling knives)

# Institutional Microstructure & Execution Parameters (Points 1, 3, 4, 5, 6, 7)
MIN_QUAL_DISTANCE_1H = 0.025   # +2.50% min expansion before 1H 1st tap is valid
MIN_QUAL_DISTANCE_4H = 0.040   # +4.00% min expansion before 4H 1st tap is valid
MAX_HOLD_HOURS_1H = 16         # 16-hour Time-Stop exit on 1H
MAX_HOLD_HOURS_4H = 48         # 48-hour Time-Stop exit on 4H
MAX_SPREAD_PCT = 0.0008        # Max 0.08% bid-ask spread
ENFORCE_ISOLATED_MARGIN = True # Strictly ISOLATED margin mode
MAX_CLIMAX_VOLUME_RATIO = 3.5  # Max 3.5x volume displacement (rejects blow-offs)

# Timers
STRUCTURE_REFRESH_MINUTES = 10
LIVE_PRICE_INTERVAL_SECONDS = 5

# --- Tier 1 Elite Priority Coins (Win Rate >= 80% on 4H First-Tap) ---
# Category 1: High Win-Rate Swing Precision (>80% to 90% Win Rate)
TIER1_SWING_COINS = [
    "ARBUSDT", "STXUSDT", "LTCUSDT", "ETHUSDT", "BNBUSDT",
    "1000BONKUSDT", "DOTUSDT", "SUIUSDT", "JUPUSDT", "1000PEPEUSDT",
    "AAVEUSDT", "AVAXUSDT", "UNIUSDT", "CRVUSDT", "SOLUSDT", "DOGEUSDT"
]

# Category 2: Quick Profit Fast Bounce Snipers (Fastest Time to TP: 4-7 Hours)
TIER1_QUICK_SNIPERS = [
    "ZECUSDT", "ONEUSDT", "PENDLEUSDT", "ETHFIUSDT", "ONGUSDT",
    "LDOUSDT", "PEOPLEUSDT", "AEROUSDT", "INJUSDT", "SUSDT"
]

# --- HERMES 2.0 APEX: TOP 22 VETTED INSTITUTIONAL CHAMPIONS ---
TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

# --- HERMES 3.5 APEX: TOP 45 EXTENDED LIQUID INSTITUTIONAL CHAMPIONS ---
TOP_45_CHAMPIONS = [
    # Top-22 Core Champions
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT",
    # 23 Extended High-Volume Institutional Movers
    "SOLUSDT", "ETHUSDT", "BNBUSDT", "LINKUSDT", "INJUSDT", "TIAUSDT", "SEIUSDT", "ARBUSDT",
    "PEPEUSDT", "WIFUSDT", "BONKUSDT", "DOTUSDT", "ADAUSDT", "PENDLEUSDT", "KASUSDT", "JUPUSDT",
    "ENAUSDT", "ONDOUSDT", "TAOUSDT", "CRVUSDT", "LTCUSDT", "STXUSDT", "PEOPLEUSDT"
]

# Combined Master Priority Queue
TIER1_COINS = TOP_22_CHAMPIONS
DEFAULT_COINS = TOP_22_CHAMPIONS

# --- Database ---
DB_PATH = BASE_DIR / "database" / "smc_v17.db"

# --- Telegram Settings ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_STATUS_MSG_ID = os.getenv("TELEGRAM_STATUS_MSG_ID", "")

# --- AI Integration (Mike AI - Flash Low Engine) ---
AI_AGENT_NAME = "Mike"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

# --- Bitget Real Auto-Trading Config (Challenge: 4H Macro Compounding) ---
BITGET_API_KEY = os.getenv("BITGET_API_KEY", "")
BITGET_SECRET = os.getenv("BITGET_SECRET", "")
BITGET_PASSPHRASE = os.getenv("BITGET_PASSPHRASE", "")
BITGET_AUTO_TRADE = False  # LIVE AUTO-TRADING OFF: Preserving capital for strategy R&D & Copy-Trading mode
BITGET_DEFAULT_LEVERAGE = 5
BITGET_STARTING_MARGIN = 50.0  # $50 USDT compounding starting size
BITGET_COMPOUNDING_TARGET = 2000.0  # $2,000 USDT Milestone Target Goal
BITGET_ALLOWED_SIDES = ["BUY", "LONG", "SELL", "SHORT"]  # Both BUY & SHORT supported on Bitget
BITGET_MARGIN_MODE = "ISOLATED"
BITGET_4H_TP_PCT = 0.0280  # +2.80% price move (+14.00% ROE @ 5x)
BITGET_4H_SL_PCT = 0.0280  # -2.80% soft SL on 4H candle close
BITGET_HARD_DISASTER_SL_PCT = 0.0380  # 3.80% emergency disaster stop on exchange
BITGET_MIN_CONFLUENCE = int(os.getenv("BITGET_MIN_CONFLUENCE", "80"))

# --- Binance Real Auto-Trading Config (Decommissioned - Waiting for TP exit on open positions) ---
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_AUTO_TRADE = False  # PERMANENTLY DISABLED: All new compounding trades execute exclusively on Bitget
BINANCE_TIMEFRAME = "4h"
BINANCE_ALLOWED_SIDES = ["BUY", "LONG", "SELL", "SHORT"]
BINANCE_MARGIN_MODE = "ISOLATED"
BINANCE_DEFAULT_LEVERAGE = 5
BINANCE_STARTING_MARGIN = 50.0
BINANCE_COMPOUNDING_TARGET = 2000.0
BINANCE_4H_TP_PCT = 0.0280
BINANCE_4H_SL_PCT = 0.0280
BINANCE_HARD_DISASTER_SL_PCT = 0.0380
BINANCE_1H_TP_PCT = 0.0160
BINANCE_1H_SL_PCT = 0.0145

BITGET_1H_TP_PCT = 0.0160  # +1.60% price move (+8.00% ROE @ 5x)
BITGET_1H_SL_PCT = 0.0145  # -1.45% soft SL on 1H candle close
BITGET_1H_HARD_SL_PCT = 0.0300  # 3.00% emergency disaster stop on exchange

# --- Bitget Exclusive Quad-Compounding Fortress ($50 x 4 Tracks: 4Hx2, 1Hx2) ---
QUAD_CHALLENGES = {
    "bitget_4h_1": {
        "name": "Bitget 4H Macro (Section A)",
        "exchange": "Bitget",
        "timeframe": "4h",
        "section": "A",
        "account_id": 1,
        "channel": "bitget_4h_1",
        "start_balance": 50.0,
        "target_balance": 2000.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "tp_pct": 0.0280,  # +2.80% price move (+14.00% ROE @ 5x)
        "sl_pct": 0.0280,  # -2.80% soft SL on 4H candle close
        "disaster_sl_pct": 0.0380,
        "description": "Bitget 4H Macro Swing (Section A) • 5x ISOLATED ($50 -> $2,000)"
    },
    "bitget_4h_2": {
        "name": "Bitget 4H Macro (Section B)",
        "exchange": "Bitget",
        "timeframe": "4h",
        "section": "B",
        "account_id": 2,
        "channel": "bitget_4h_2",
        "start_balance": 50.0,
        "target_balance": 2000.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "tp_pct": 0.0280,  # +2.80% price move (+14.00% ROE @ 5x)
        "sl_pct": 0.0280,  # -2.80% soft SL on 4H candle close
        "disaster_sl_pct": 0.0380,
        "description": "Bitget 4H Macro Swing (Section B) • 5x ISOLATED ($50 -> $2,000)"
    },
    "bitget_1h_1": {
        "name": "Bitget 1H Intraday (Section A)",
        "exchange": "Bitget",
        "timeframe": "1h",
        "section": "A",
        "account_id": 3,
        "channel": "bitget_1h_1",
        "start_balance": 50.0,
        "target_balance": 2000.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "tp_pct": 0.0160,  # +1.60% price move (+8.00% ROE @ 5x)
        "sl_pct": 0.0145,  # -1.45% soft SL on 1H candle close
        "disaster_sl_pct": 0.0300,
        "description": "Bitget 1H Fast Scalp (Section A) • 5x ISOLATED ($50 -> $2,000)"
    },
    "bitget_1h_2": {
        "name": "Bitget 1H Intraday (Section B)",
        "exchange": "Bitget",
        "timeframe": "1h",
        "section": "B",
        "account_id": 4,
        "channel": "bitget_1h_2",
        "start_balance": 50.0,
        "target_balance": 2000.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "tp_pct": 0.0160,  # +1.60% price move (+8.00% ROE @ 5x)
        "sl_pct": 0.0145,  # -1.45% soft SL on 1H candle close
        "disaster_sl_pct": 0.0300,
        "description": "Bitget 1H Fast Scalp (Section B) • 5x ISOLATED ($50 -> $2,000)"
    }
}
# Backward compatibility aliases:
QUAD_CHALLENGES["binance_4h"] = QUAD_CHALLENGES["bitget_4h_1"]
QUAD_CHALLENGES["binance_1h"] = QUAD_CHALLENGES["bitget_4h_2"]
QUAD_CHALLENGES["bitget_4h"] = QUAD_CHALLENGES["bitget_1h_1"]
QUAD_CHALLENGES["bitget_1h"] = QUAD_CHALLENGES["bitget_1h_2"]
DUAL_CHALLENGES = QUAD_CHALLENGES

# --- Advanced Hybrid Stop-Loss (Candle-Close Confirmation + Disaster Hard Stop) ---
CANDLE_CLOSE_SL_ENABLED = True
HARD_DISASTER_SL_PCT = 0.045  # 4.5% price emergency circuit-breaker on exchange (Zero liquidation risk)
SOFT_SL_1H_PCT = 0.020        # 2.0% soft SL confirmed only on 1H candle close
SOFT_SL_4H_PCT = 0.025        # 2.5% soft SL confirmed only on 4H candle close
BREAKEVEN_TRIGGER_1H = 0.0075  # Lock entry at +0.75% price gain (+3.75% ROE)
BREAKEVEN_TRIGGER_4H = 0.0102  # Lock entry at +1.02% price gain (+5.10% ROE)

# --- Real vs Paper Trading Alerts (Active: Broadcasts with Charts to Telegram) ---
MUTE_PAPER_TRADING_ALERTS = os.getenv("MUTE_PAPER_TRADING_ALERTS", "false").lower() == "true"
# --- Locked Universal Strategy ---
CURRENT_STRATEGY_NAME = "HERMES 3.0 QUANTUM"
CURRENT_STRATEGY_MODE = "HERMES_3.0_QUANTUM"
HERMES_HYBRID_BUY_ENGINE = "HERMES_3.0_QUANTUM"
HERMES_HYBRID_SELL_ENGINE = "HERMES_3.0_QUANTUM"

# --- Server Config ---
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8000))



