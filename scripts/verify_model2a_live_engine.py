import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import STRATEGY_VERSION, HERMES_3_MEAN_THRESHOLD_ENTRY, HERMES_3_CANDLE_BODY_CLOSE_SL
from engine.hermes30_apex_live import hermes30_live_engine
from database.db import get_paper_account

print(f"Verified Config STRATEGY_VERSION: {STRATEGY_VERSION}")
print(f"HERMES_3_MEAN_THRESHOLD_ENTRY: {HERMES_3_MEAN_THRESHOLD_ENTRY}")
print(f"HERMES_3_CANDLE_BODY_CLOSE_SL: {HERMES_3_CANDLE_BODY_CLOSE_SL}")

acc = hermes30_live_engine.get_hermes_account()
print(f"Account Mode: {acc.get('mode')}")
print(f"Current Balance: ${acc.get('current_balance'):.2f} USDT")

print("Engine instantiation & DB sync: 100% OK!")
