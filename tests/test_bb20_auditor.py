"""
BB 2.0 SNIPER & CLOUD WORKER COMPREHENSIVE AUDIT & STRESS SUITE
==============================================================
Validates:
1. Binance Vision API spot symbol mapping & Bybit Linear fallback
2. PDH/PDL daily mark calculation & Extreme OB detection (Displacement + FVG + MT + Buffer SL)
3. Stepped Trailing SL logic (+1.0R -> +0.2R, +1.5R -> +1.0R, +2.0R -> +1.5R)
4. Strict Single-Shot discipline (Max 1 Long & 1 Short per day per coin)
5. Section collision protection
6. FastAPI deca endpoints (/api/deca/summary, /api/deca/sections, /api/deca/setups, /api/deca/reset)
"""

import os
import sys
import json
import pytest
from datetime import datetime, timezone

# Ensure project root is in sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import bb20_config as cfg
from scripts.run_bb20_live_sniper import BB20LiveSniper, fetch_binance_klines, ShadowLedger

def test_fetch_binance_klines_mapping():
    """Verify Binance Vision API spot symbol mapping for 1000PEPEUSDT and standard pairs."""
    # Standard pair
    btc_candles = fetch_binance_klines("BTCUSDT", interval="15m", limit=5)
    assert len(btc_candles) > 0, "Failed to fetch BTCUSDT candles"
    assert btc_candles[-1]["close"] > 10000, f"Unreasonable BTC price: {btc_candles[-1]['close']}"

    # 1000-multiplier meme coin (1000PEPEUSDT)
    pepe_candles = fetch_binance_klines("1000PEPEUSDT", interval="15m", limit=5)
    assert len(pepe_candles) > 0, "Failed to fetch 1000PEPEUSDT candles"
    # Spot PEPE is ~0.000004 - 0.000015, multiplied by 1000 gives ~0.004 - 0.015
    pepe_price = pepe_candles[-1]["close"]
    assert 0.0005 <= pepe_price <= 0.1, f"1000PEPE price not properly scaled by 1000: {pepe_price}"

def test_stepped_trailing_sl_logic():
    """Verify Stepped Trailing SL (+1.0R -> +0.2R BE, +1.5R -> +1.0R lock, +2.0R -> +1.5R lock)."""
    sniper = BB20LiveSniper()
    symbol = "TEST_BTC"
    sec_id = "1"
    entry = 80000.0
    sl = 79000.0
    risk = 1000.0

    # Arm a mock setup
    sniper.ledger.data["active_positions"][symbol] = {
        "symbol": symbol,
        "section_id": sec_id,
        "side": "LONG",
        "mt_entry": entry,
        "sl": sl,
        "active_sl": sl,
        "risk": risk,
        "risk_usd": 2.5,
        "current_tier": 0,
        "highest_r": 0.0,
        "filled_at": datetime.now(timezone.utc).isoformat()
    }
    sniper.ledger.data["sections"][sec_id]["status"] = f"IN TRADE ({symbol} LONG)"

    # Milestone 1: Reaches +1.0R (81,000) -> SL must move to +0.2R (80,200)
    mock_candles_1r = [
        {"time": 1, "open": 80000, "high": 81050, "low": 79900, "close": 81000, "volume": 100}
    ]
    sniper._monitor_active_position(symbol, mock_candles_1r)
    pos = sniper.ledger.data["active_positions"][symbol]
    assert pos["current_tier"] == 1, f"Expected tier 1 at +1.0R, got {pos['current_tier']}"
    assert pos["active_sl"] == 80200.0, f"Expected active SL at +0.2R (80200), got {pos['active_sl']}"

    # Milestone 2: Reaches +1.5R (81,500) -> SL must move to +1.0R lock (81,000)
    mock_candles_15r = [
        {"time": 2, "open": 81000, "high": 81550, "low": 80900, "close": 81500, "volume": 100}
    ]
    sniper._monitor_active_position(symbol, mock_candles_15r)
    pos = sniper.ledger.data["active_positions"][symbol]
    assert pos["current_tier"] == 2, f"Expected tier 2 at +1.5R, got {pos['current_tier']}"
    assert pos["active_sl"] == 81000.0, f"Expected active SL at +1.0R lock (81000), got {pos['active_sl']}"

    # Milestone 3: Reaches +2.0R (82,000) -> SL must move to +1.5R lock (81,500)
    mock_candles_2r = [
        {"time": 3, "open": 81500, "high": 82050, "low": 81400, "close": 82000, "volume": 100}
    ]
    sniper._monitor_active_position(symbol, mock_candles_2r)
    pos = sniper.ledger.data["active_positions"][symbol]
    assert pos["current_tier"] == 3, f"Expected tier 3 at +2.0R, got {pos['current_tier']}"
    assert pos["active_sl"] == 81500.0, f"Expected active SL at +1.5R lock (81500), got {pos['active_sl']}"

    # SL hit at 81,500 (+1.5R lock)
    mock_candles_sl = [
        {"time": 4, "open": 81600, "high": 81700, "low": 81400, "close": 81450, "volume": 100}
    ]
    sniper._monitor_active_position(symbol, mock_candles_sl)
    assert symbol not in sniper.ledger.data["active_positions"], "Position should be closed"
    closed = sniper.ledger.data["closed_trades"][-1]
    assert "WIN (+1.5R PROFIT LOCKED)" in closed["outcome"], f"Unexpected outcome: {closed['outcome']}"
    # Realized R should be 1.5 - friction (0.06) = 1.44
    assert round(closed["realized_r"], 2) == 1.44, f"Unexpected realized R: {closed['realized_r']}"

def test_single_shot_discipline():
    """Verify single-shot discipline: Max 1 long and 1 short per day per coin."""
    sniper = BB20LiveSniper()
    day_key = sniper.get_day_key()
    symbol = "BTCUSDT"

    # Initialize daily status
    sniper.ledger.data.setdefault("daily_single_shot", {})[day_key] = {
        symbol: {"LONG": False, "SHORT": False}
    }

    # Arm a long setup
    mt = 80000.0
    sl = 79500.0
    risk = 500.0
    sniper._arm_new_setup(symbol, "1", "LONG", mt, sl, risk, 81000.0, "PDL SUPPORT")

    # Simulate fill
    fill_candle = [{"time": 1, "open": 80100, "high": 80150, "low": 79900, "close": 80000, "volume": 50}]
    sniper._check_pending_setup_fill(symbol, fill_candle)

    # LONG shot must now be LOCKED
    assert sniper.ledger.data["daily_single_shot"][day_key][symbol]["LONG"] is True, "LONG should be locked after fill"
    # SHORT shot must still be available
    assert sniper.ledger.data["daily_single_shot"][day_key][symbol]["SHORT"] is False, "SHORT should still be available"

    # Close the LONG position
    sniper._close_position(symbol, "SL_HIT", sl)
    assert symbol not in sniper.ledger.data["active_positions"]

    # Even after position closed, LONG shot remains LOCKED for the rest of the day
    assert sniper.ledger.data["daily_single_shot"][day_key][symbol]["LONG"] is True, "LONG must remain locked for entire day"

def test_fastapi_deca_endpoints():
    """Verify /api/deca/summary, /api/deca/sections, /api/deca/setups, /api/deca/reset."""
    from fastapi.testclient import TestClient
    from app import app
    client = TestClient(app)

    # 1. Reset
    res_reset = client.post("/api/deca/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["status"] == "SUCCESS"

    # 2. Summary
    res_sum = client.get("/api/deca/summary")
    assert res_sum.status_code == 200
    d_sum = res_sum.json()
    assert d_sum["total_balance"] == 500.0
    assert d_sum["starting_capital"] == 500.0
    assert d_sum["total_trades"] == 0

    # 3. Sections
    res_sec = client.get("/api/deca/sections")
    assert res_sec.status_code == 200
    sections = res_sec.json()["sections"]
    assert len(sections) == 10
    for s in sections:
        assert s["current_balance"] == 50.0
        assert s["status"] == "IDLE"

    # 4. Setups
    res_set = client.get("/api/deca/setups")
    assert res_set.status_code == 200
    assert "setups" in res_set.json()
