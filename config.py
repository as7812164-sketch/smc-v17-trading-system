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

# --- HERMES 3.0 QUANTUM (UNIVERSAL PRODUCTION ENGINE) ---
STRATEGY_OPTIONS = ["HERMES_3.0_QUANTUM", "HERMES_2.5_APEX_HYBRID"]
STRATEGY_VERSION = "HERMES_3.0_QUANTUM"  # Universal Production Engine: 50% Mean Threshold Entry + Multi-Stage Profit Armor
HERMES_3_MEAN_THRESHOLD_ENTRY = True
HERMES_3_MULTI_STAGE_ARMOR = True
HERMES_3_BTC_EMERGENCY_SHIELD = True
HERMES_3_DYNAMIC_ATR_BUFFER = True
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

# Combined Master Priority Queue (Strictly Top 22 Champions)
TIER1_COINS = TOP_22_CHAMPIONS

# --- Configured Active Universe (Strictly Top 22 Champions Only) ---
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
BITGET_AUTO_TRADE = os.getenv("BITGET_AUTO_TRADE", "true").lower() == "true"
BITGET_DEFAULT_LEVERAGE = 5
BITGET_STARTING_MARGIN = 50.0  # $50 USDT compounding starting size
BITGET_COMPOUNDING_TARGET = 2000.0  # $2,000 USDT Milestone Target Goal
BITGET_ALLOWED_SIDES = ["BUY", "LONG", "SELL", "SHORT"]  # Both BUY & SHORT supported on Bitget
BITGET_MARGIN_MODE = "ISOLATED"
BITGET_4H_TP_PCT = 0.0280  # +2.80% price move (+14.00% ROE @ 5x)
BITGET_4H_SL_PCT = 0.0280  # -2.80% soft SL on 4H candle close
BITGET_HARD_DISASTER_SL_PCT = 0.0380  # 3.80% emergency disaster stop on exchange
BITGET_MIN_CONFLUENCE = int(os.getenv("BITGET_MIN_CONFLUENCE", "80"))

# --- Binance Real Auto-Trading Config (Challenge: 4H Macro Compounding) ---
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_AUTO_TRADE = os.getenv("BINANCE_AUTO_TRADE", "true").lower() == "true"
BINANCE_TIMEFRAME = "4h"
BINANCE_ALLOWED_SIDES = ["BUY", "LONG", "SELL", "SHORT"]  # Both LONG & SHORT enabled for Quad-Compounding
BINANCE_MARGIN_MODE = "ISOLATED"           # Strictly ISOLATED margin mode - CROSS mode prohibited
BINANCE_DEFAULT_LEVERAGE = 5
BINANCE_STARTING_MARGIN = 50.0  # $50 USDT compounding starting size
BINANCE_COMPOUNDING_TARGET = 2000.0  # $2,000 USDT Milestone Target Goal
BINANCE_4H_TP_PCT = 0.0280  # +2.80% price move (+14.00% ROE @ 5x)
BINANCE_4H_SL_PCT = 0.0280  # -2.80% soft SL on 4H candle close
BINANCE_HARD_DISASTER_SL_PCT = 0.0380  # +3.80% emergency disaster stop order on exchange
BINANCE_1H_TP_PCT = 0.0160  # +1.60% price move (+8.00% ROE @ 5x)
BINANCE_1H_SL_PCT = 0.0145  # -1.45% price move (-7.27% ROE @ 5x)

BITGET_1H_TP_PCT = 0.0160  # +1.60% price move (+8.00% ROE @ 5x)
BITGET_1H_SL_PCT = 0.0145  # -1.45% soft SL on 1H candle close
BITGET_1H_HARD_SL_PCT = 0.0300  # 3.00% emergency disaster stop on exchange

# --- Quad-Compounding Fortress Challenge Specifications ($50 x 4 Tracks) ---
QUAD_CHALLENGES = {
    "binance_4h": {
        "name": "Binance 4H Macro Compounding",
        "exchange": "Binance",
        "timeframe": "4h",
        "start_balance": 50.0,
        "target_balance": 2000.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "tp_pct": 0.0280,  # +2.80% price move (+14.00% ROE @ 5x)
        "sl_pct": 0.0280,  # -2.80% soft SL on 4H candle close
        "disaster_sl_pct": 0.0380,
        "description": "Binance 4H Macro Swing • 5x ISOLATED ($50 -> $2,000)"
    },
    "binance_1h": {
        "name": "Binance 1H Intraday Compounding",
        "exchange": "Binance",
        "timeframe": "1h",
        "start_balance": 50.0,
        "target_balance": 2000.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "tp_pct": 0.0160,  # +1.60% price move (+8.00% ROE @ 5x)
        "sl_pct": 0.0145,  # -1.45% soft SL on 1H candle close
        "disaster_sl_pct": 0.0300,
        "description": "Binance 1H Intraday Scalp • 5x ISOLATED ($50 -> $2,000)"
    },
    "bitget_4h": {
        "name": "Bitget 4H Macro Compounding",
        "exchange": "Bitget",
        "timeframe": "4h",
        "start_balance": 50.0,
        "target_balance": 2000.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "tp_pct": 0.0280,  # +2.80% price move (+14.00% ROE @ 5x)
        "sl_pct": 0.0280,  # -2.80% soft SL on 4H candle close
        "disaster_sl_pct": 0.0380,
        "description": "Bitget 4H Macro Swing • 5x ISOLATED ($50 -> $2,000)"
    },
    "bitget_1h": {
        "name": "Bitget 1H Intraday Compounding",
        "exchange": "Bitget",
        "timeframe": "1h",
        "start_balance": 50.0,
        "target_balance": 2000.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "tp_pct": 0.0160,  # +1.60% price move (+8.00% ROE @ 5x)
        "sl_pct": 0.0145,  # -1.45% soft SL on 1H candle close
        "disaster_sl_pct": 0.0300,
        "description": "Bitget 1H Intraday Scalp • 5x ISOLATED ($50 -> $2,000)"
    }
}
DUAL_CHALLENGES = QUAD_CHALLENGES  # Backward compatibility

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



