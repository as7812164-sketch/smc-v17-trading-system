import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import time
import json
from database.db import (
    init_db,
    get_connection,
    open_paper_trade,
    get_open_paper_trades,
    close_paper_trade,
    update_paper_trade_mark_price
)
from engine.hermes30_apex_live import hermes30_live_engine

def run_comprehensive_unit_test():
    print("======================================================================")
    print("RUNNING COMPREHENSIVE STEPPED TRAILING SL & LIMIT ORDER ENGINE AUDIT")
    print("======================================================================")
    
    init_db()
    
    # 1. Test Long Setup with Limit Order
    long_setup = {
        "id": 99901,
        "symbol": "TESTBTCUSDT",
        "side": "LONG",
        "timeframe": "4h",
        "channel": "sec_1",
        "account_id": 1,
        "entry_price": 50000.0,
        "order_type": "LIMIT",
        "soft_sl_price": 49250.0,   # -1.5% soft
        "hard_sl_price": 48500.0,   # -3.0% disaster
        "tp_price": 51500.0,
        "wick_ratio_pct": 28.5
    }
    
    # Clean any prior test record
    with get_connection() as conn:
        conn.execute("DELETE FROM paper_trades WHERE symbol = 'TESTBTCUSDT'")
        conn.commit()
        
    trade = open_paper_trade(long_setup)
    trade_id = trade["id"]
    print(f"✅ Trade #{trade_id} Opened: TESTBTCUSDT LONG @ ${trade['entry_price']} | Order Type: {trade.get('order_type')}")
    assert trade.get("order_type") == "LIMIT", "Order type must be LIMIT!"
    
    # 2. Simulate Price Progression at 5x leverage
    # Leverage = 5x
    # +5% ROI = +1.0% spot = $50,500.0
    # +10% ROI = +2.0% spot = $51,000.0
    # +15% ROI = +3.0% spot = $51,500.0
    
    leverage = 5.0
    ep = 50000.0
    
    # Step A: Price moves to $50,600 (+6% ROI)
    p_a = 50600.0
    update_paper_trade_mark_price(trade_id, p_a)
    
    with get_connection() as conn:
        row = dict(conn.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,)).fetchone())
    
    peak_roi = ((float(row["highest_price"]) - ep) / ep) * 100.0 * leverage
    print(f"📊 Mark Price: ${p_a} | Peak ROI: {peak_roi:.2f}%")
    
    # Mock ticker feed in hermes30_live_engine
    mock_tickers = {"TESTBTCUSDT": p_a}
    
    # Run one pass of check_live_price_and_exits with mock feed
    async def test_pass_1():
        # Temporarily mock binance_feed.fetch_all_tickers
        from feed.binance_feed import binance_feed
        orig_fetch = binance_feed.fetch_all_tickers
        binance_feed.fetch_all_tickers = lambda: asyncio.sleep(0, result=mock_tickers)
        try:
            await hermes30_live_engine.check_live_price_and_exits()
        finally:
            binance_feed.fetch_all_tickers = orig_fetch
            
    asyncio.run(test_pass_1())
    
    with get_connection() as conn:
        row1 = dict(conn.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,)).fetchone())
    print(f"🛡️ Step 1 Check -> Locked ROI: {row1['locked_roi_pct']}%, Trailing Step: {row1['trailing_step']}, SL Price: ${row1['sl_price']}")
    assert row1["locked_roi_pct"] == 1.0, "Step 1 locked ROI must be +1.0%!"
    assert row1["trailing_step"] == 1, "Step 1 trailing_step must be 1!"
    expected_sl_1 = round(ep * (1.0 + (0.01 / 5.0)), 8) # $50,100
    assert abs(row1["sl_price"] - expected_sl_1) < 0.01, f"SL must be {expected_sl_1}"
    print(f"   >>> PASS: Step 1 (+5% ROI touch -> SL moved to +1% ROI @ ${expected_sl_1}) verified!")
    
    # Step B: Price surges to $51,100 (+11% ROI)
    p_b = 51100.0
    update_paper_trade_mark_price(trade_id, p_b)
    mock_tickers["TESTBTCUSDT"] = p_b
    
    async def test_pass_2():
        from feed.binance_feed import binance_feed
        orig_fetch = binance_feed.fetch_all_tickers
        binance_feed.fetch_all_tickers = lambda: asyncio.sleep(0, result=mock_tickers)
        try:
            await hermes30_live_engine.check_live_price_and_exits()
        finally:
            binance_feed.fetch_all_tickers = orig_fetch
            
    asyncio.run(test_pass_2())
    
    with get_connection() as conn:
        row2 = dict(conn.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,)).fetchone())
    print(f"🛡️ Step 2 Check -> Locked ROI: {row2['locked_roi_pct']}%, Trailing Step: {row2['trailing_step']}, SL Price: ${row2['sl_price']}")
    assert row2["locked_roi_pct"] == 5.0, "Step 2 locked ROI must be +5.0%!"
    assert row2["trailing_step"] == 2, "Step 2 trailing_step must be 2!"
    expected_sl_2 = round(ep * (1.0 + (0.05 / 5.0)), 8) # $50,500
    assert abs(row2["sl_price"] - expected_sl_2) < 0.01, f"SL must be {expected_sl_2}"
    print(f"   >>> PASS: Step 2 (+10% ROI touch -> SL moved to +5% ROI @ ${expected_sl_2}) verified!")
    
    # Step C: Price surges to $51,600 (+16% ROI)
    p_c = 51600.0
    update_paper_trade_mark_price(trade_id, p_c)
    mock_tickers["TESTBTCUSDT"] = p_c
    
    async def test_pass_3():
        from feed.binance_feed import binance_feed
        orig_fetch = binance_feed.fetch_all_tickers
        binance_feed.fetch_all_tickers = lambda: asyncio.sleep(0, result=mock_tickers)
        try:
            await hermes30_live_engine.check_live_price_and_exits()
        finally:
            binance_feed.fetch_all_tickers = orig_fetch
            
    asyncio.run(test_pass_3())
    
    with get_connection() as conn:
        row3 = dict(conn.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,)).fetchone())
    print(f"🛡️ Step 3 Check -> Locked ROI: {row3['locked_roi_pct']}%, Trailing Step: {row3['trailing_step']}, SL Price: ${row3['sl_price']}")
    assert row3["locked_roi_pct"] == 10.0, "Step 3 locked ROI must be +10.0%!"
    assert row3["trailing_step"] == 3, "Step 3 trailing_step must be 3!"
    expected_sl_3 = round(ep * (1.0 + (0.10 / 5.0)), 8) # $51,000
    assert abs(row3["sl_price"] - expected_sl_3) < 0.01, f"SL must be {expected_sl_3}"
    print(f"   >>> PASS: Step 3 (+15% ROI touch -> SL moved to +10% ROI @ ${expected_sl_3}) verified!")
    
    # Step D: Price retraces back down to $50,950 (Below $51,000 Trailing SL!)
    # Should trigger TRAILING_SL_HIT exit!
    p_d = 50950.0
    mock_tickers["TESTBTCUSDT"] = p_d
    
    async def test_pass_exit():
        from feed.binance_feed import binance_feed
        orig_fetch = binance_feed.fetch_all_tickers
        binance_feed.fetch_all_tickers = lambda: asyncio.sleep(0, result=mock_tickers)
        try:
            await hermes30_live_engine.check_live_price_and_exits()
        finally:
            binance_feed.fetch_all_tickers = orig_fetch
            
    asyncio.run(test_pass_exit())
    
    with get_connection() as conn:
        closed_row = dict(conn.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,)).fetchone())
    print(f"🏁 Exit Check -> Status: {closed_row['status']}, Exit Price: ${closed_row['exit_price']}, PnL: ${closed_row['pnl_usdt']}")
    assert closed_row["status"] == "TRAILING_SL_HIT", "Status must be TRAILING_SL_HIT!"
    assert abs(closed_row["exit_price"] - expected_sl_3) < 0.01, "Exit price must equal trailing SL!"
    assert closed_row["pnl_usdt"] > 0, "Realized PnL must be strictly positive!"
    print(f"   >>> PASS: Trailing SL triggered cleanly at ${closed_row['exit_price']} with strictly positive PnL: ${closed_row['pnl_usdt']}!")
    
    # Clean up test trade
    with get_connection() as conn:
        conn.execute("DELETE FROM paper_trades WHERE symbol = 'TESTBTCUSDT'")
        conn.commit()

    # 3. Test Short Setup with Limit Order
    print("\n----------------------------------------------------------------------")
    print("TESTING SHORT SIDE STEPPED TRAILING SL & LIMIT ORDER")
    print("----------------------------------------------------------------------")
    short_setup = {
        "id": 99902,
        "symbol": "TESTSHORTUSDT",
        "side": "SHORT",
        "timeframe": "1h",
        "channel": "sec_6",
        "account_id": 6,
        "entry_price": 1000.0,
        "order_type": "LIMIT",
        "soft_sl_price": 1015.0,
        "hard_sl_price": 1030.0,
        "tp_price": 970.0,
        "wick_ratio_pct": 25.0
    }
    with get_connection() as conn:
        conn.execute("DELETE FROM paper_trades WHERE symbol = 'TESTSHORTUSDT'")
        conn.commit()

    trade_s = open_paper_trade(short_setup)
    s_id = trade_s["id"]
    print(f"✅ Trade #{s_id} Opened: TESTSHORTUSDT SHORT @ ${trade_s['entry_price']} | Order Type: {trade_s.get('order_type')}")
    assert trade_s.get("order_type") == "LIMIT", "Order type must be LIMIT!"

    # Short: Drop to $988.0 (+6% ROI)
    p_s1 = 988.0
    update_paper_trade_mark_price(s_id, p_s1)
    mock_tickers["TESTSHORTUSDT"] = p_s1

    async def test_short_pass_1():
        from feed.binance_feed import binance_feed
        orig = binance_feed.fetch_all_tickers
        binance_feed.fetch_all_tickers = lambda: asyncio.sleep(0, result=mock_tickers)
        try:
            await hermes30_live_engine.check_live_price_and_exits()
        finally:
            binance_feed.fetch_all_tickers = orig

    asyncio.run(test_short_pass_1())

    with get_connection() as conn:
        s_row1 = dict(conn.execute("SELECT * FROM paper_trades WHERE id = ?", (s_id,)).fetchone())
    print(f"🛡️ Short Step 1 Check -> Locked ROI: {s_row1['locked_roi_pct']}%, Trailing Step: {s_row1['trailing_step']}, SL Price: ${s_row1['sl_price']}")
    assert s_row1["locked_roi_pct"] == 1.0, "Short Step 1 locked ROI must be 1.0%!"
    expected_s_sl_1 = round(1000.0 * (1.0 - (0.01 / 5.0)), 8) # $998.0
    assert abs(s_row1["sl_price"] - expected_s_sl_1) < 0.01
    print(f"   >>> PASS: Short Step 1 (+5% ROI touch -> SL moved to +1% ROI @ ${expected_s_sl_1}) verified!")

    # Short: Price bounces back up to $999.0 (Breaches $998.0 Trailing SL!)
    p_s_exit = 999.0
    mock_tickers["TESTSHORTUSDT"] = p_s_exit

    async def test_short_exit():
        from feed.binance_feed import binance_feed
        orig = binance_feed.fetch_all_tickers
        binance_feed.fetch_all_tickers = lambda: asyncio.sleep(0, result=mock_tickers)
        try:
            await hermes30_live_engine.check_live_price_and_exits()
        finally:
            binance_feed.fetch_all_tickers = orig

    asyncio.run(test_short_exit())

    with get_connection() as conn:
        s_closed = dict(conn.execute("SELECT * FROM paper_trades WHERE id = ?", (s_id,)).fetchone())
    print(f"🏁 Short Exit Check -> Status: {s_closed['status']}, Exit Price: ${s_closed['exit_price']}, PnL: ${s_closed['pnl_usdt']}")
    assert s_closed["status"] == "TRAILING_SL_HIT", "Status must be TRAILING_SL_HIT!"
    assert abs(s_closed["exit_price"] - expected_s_sl_1) < 0.01
    print(f"   >>> PASS: Short Trailing SL triggered cleanly at ${s_closed['exit_price']} with strictly positive PnL: ${s_closed['pnl_usdt']}!")

    # Clean up test trade
    with get_connection() as conn:
        conn.execute("DELETE FROM paper_trades WHERE symbol = 'TESTSHORTUSDT'")
        conn.commit()

    print("\n======================================================================")
    print("🎉 BOTH LONG & SHORT STEPPED TRAILING SL TESTS PASSED 100%!")
    print("======================================================================\n")

if __name__ == "__main__":
    run_comprehensive_unit_test()
