"""
BB 2.0 SNIPER CONFIGURATION (DEDICATED & ISOLATED)
==================================================
This file is 100% separate from the production engine.
It connects only to the new dedicated Telegram Bot and local shadow ledger.
"""

# Dedicated Telegram Bot Credentials
BB20_TELEGRAM_BOT_TOKEN = "8685685362:AAFWkKvRIs6cJ70gegcJVFyKB5soDtEttbU"
BB20_TELEGRAM_CHAT_ID = "752247227"

# Deca Compounding Parameters
TOTAL_STARTING_CAPITAL = 500.0  # USDT
TOTAL_DECA_SECTIONS = 10
STARTING_BALANCE_PER_SECTION = 50.0  # USDT
SECTION_RISK_FRACTION = 0.05  # 5% Risk per Section (Compounding Mode)
FRICTION_R = 0.06  # 0.06 R (Taker fee + adverse slippage deduction)
SL_ANTI_HUNT_BUFFER = 0.0015  # 0.15% Buffer beyond extreme wick

# Asset Universe & Dedicated Pairing (3 Proven Champions per Isolated Section = 30 Champions)
PAIR_MAPPING = {
    "BTCUSDT": 1, "ETHUSDT": 1, "BCHUSDT": 1,
    "SOLUSDT": 2, "BNBUSDT": 2, "SEIUSDT": 2,
    "AVAXUSDT": 3, "DOGEUSDT": 3, "KAVAUSDT": 3,
    "DOTUSDT": 4, "LINKUSDT": 4, "ENSUSDT": 4,
    "LTCUSDT": 5, "NEARUSDT": 5, "DYDXUSDT": 5,
    "OPUSDT": 6, "RENDERUSDT": 6, "WLDUSDT": 6,
    "SUIUSDT": 7, "TIAUSDT": 7, "TRBUSDT": 7,
    "UNIUSDT": 8, "XRPUSDT": 8, "SNXUSDT": 8,
    "1000PEPEUSDT": 9, "APTUSDT": 9, "ARKMUSDT": 9,
    "ARBUSDT": 10, "FETUSDT": 10, "ONDOUSDT": 10
}

CHAMPIONS = list(PAIR_MAPPING.keys())

# Storage
SHADOW_LEDGER_FILE = "bb20_shadow_ledger.json"
