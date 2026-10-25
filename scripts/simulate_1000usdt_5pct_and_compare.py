"""
SIMULATE $1,000 USDT (5% CAPITAL DEPLOYED PER TRADE) 1-YEAR OOS TEST
=====================================================================
Uses the exact same 168 candidate signals from the 1-Year OOS continuous dataset:
- Capital: $1,000.00 USDT
- Margin per Trade: 5.0% of current account equity (at 5x Isolated Leverage)
- Max Concurrent Trades: 10 (Max 50% capital deployed, 50% cash buffer)
- Strategy: Hermes 3.5 Single Tier (5% Boundary Penetration, +1.6% BE, +1.8% Trailing Lock, +2.8% TP)
- Timeframes: 1H & 4H
=====================================================================
"""

import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "historical_data")

from run_oos_1year_deca_compounding import run_oos_backtest

# Load pre-computed deca results to inspect
with open("oos_1year_deca_compounding_results.json", "r", encoding="utf-8") as f:
    deca_data = json.load(f)

print("Deca Results loaded successfully.")
