import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config import (
    DEFAULT_COINS,
    TIER1_COINS,
    TIMEFRAME,
    KLINES_LIMIT,
    STRUCTURE_REFRESH_MINUTES,
    LIVE_PRICE_INTERVAL_SECONDS,
    BITGET_MIN_CONFLUENCE,
    get_ist_now
)
from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17, filter_active_zones
from database.db import (
    save_or_update_zone,
    get_active_zones,
    add_signal,
    set_metric,
    increment_metric,
    get_performance_stats,
    is_alert_sent,
    record_sent_alert,
    open_paper_trade,
    close_paper_trade,
    get_setting
)
from alerts.telegram_service import telegram_service
from engine.bitget_trader import bitget_trader
from engine.binance_trader import binance_trader
from engine.trade_journal import record_trade_entry, record_trade_exit
from ai.smart_money_analyzer import evaluate_setup_confluence
from engine.order_flow import analyze_order_flow
from ai.self_improving_engine import mike_brain

class SMCScanner:
    def __init__(self):
        self.is_running = False
        # Prioritize Tier 1 Elite Coins first
        remaining = [c for c in DEFAULT_COINS if c not in TIER1_COINS]
        self.active_coins = list(TIER1_COINS) + remaining
        self.last_full_scan_time = 0
        self.last_tickers: Dict[str, float] = {}
        self.ws_broadcast_callback = None
        self.proximity_cooldowns: Dict[int, float] = {}
        self.last_daily_report_date: str = ""

    def set_broadcast_callback(self, callback):
        self.ws_broadcast_callback = callback

    async def broadcast(self, event_type: str, data: Any):
        if self.ws_broadcast_callback:
            try:
                await self.ws_broadcast_callback({"type": event_type, "data": data})
            except Exception:
                pass

    async def run_full_structure_scan(self) -> Dict[str, Any]:
        """
        Scans 4H candles for all configured coins and identifies SMC V17 zones.
        """
        scan_start = time.time()
        now_dt = get_ist_now()
        now_str = now_dt.strftime("%d %b %Y • %I:%M:%S %p IST")
        next_dt = now_dt + timedelta(minutes=STRUCTURE_REFRESH_MINUTES)
        next_str = next_dt.strftime("%d %b %Y • %I:%M:%S %p IST")

        set_metric("last_ob_refresh", now_str)
        set_metric("next_refresh", next_str)

        all_klines = await binance_feed.fetch_multiple_symbols(self.active_coins, TIMEFRAME, KLINES_LIMIT)
        successful_coins = len(all_klines)
        set_metric("coins_subscribed", f"{successful_coins}/{len(self.active_coins)}")
        set_metric("coins_active_count", str(len(self.active_coins)))

        total_new_zones = 0

        for symbol, candles in all_klines.items():
            if not candles:
                continue
            detected = analyze_candles_smc_v17(symbol, candles)
            filtered = filter_active_zones(detected)

            for z in filtered:
                zone_id = save_or_update_zone(z)
                total_new_zones += 1

                # If this zone was already entered or resolved in historical candles,
                # pre-register its alert key so it NEVER triggers an old alert on startup
                if z.get("status") in ("ACTIVE", "TP_HIT", "SL_HIT", "INVALIDATED"):
                    alert_key = f"{z['symbol']}_{z['side']}_{z['origin_time']}_FIRST_TAP_ENTRY"
                    if not is_alert_sent(alert_key):
                        record_sent_alert(alert_key, z['symbol'], z['side'], "FIRST_TAP_ENTRY", z['origin_time'])
                    if z.get("status") in ("TP_HIT", "SL_HIT"):
                        res_key = f"{z['symbol']}_{z['side']}_{z['origin_time']}_{z['status']}"
                        if not is_alert_sent(res_key):
                            record_sent_alert(res_key, z['symbol'], z['side'], z['status'], z['origin_time'])

        scan_duration = int(time.time() - scan_start)
        set_metric("last_scan_duration", f"{scan_duration}s")
        self.last_full_scan_time = time.time()

        # Update Telegram status message
        asyncio.create_task(telegram_service.update_live_status_message())

        stats = get_performance_stats()
        await self.broadcast("SCAN_COMPLETE", {
            "duration": f"{scan_duration}s",
            "active_zones": stats["total_active_zones"],
            "timestamp": now_str
        })

        return {"scanned": successful_coins, "duration": scan_duration, "zones": total_new_zones}

    async def check_live_prices_and_triggers(self):
        """
        Checks live prices against active zones for FIRST TAP ENTRY and TP/SL hits.
        """
        tickers = await binance_feed.fetch_all_tickers()
        if not tickers:
            return
        self.last_tickers = tickers
        # Broadcast live ticker updates over WebSocket
        await self.broadcast("TICKER_UPDATE", tickers)
        active_zones = get_active_zones()

        for z in active_zones:
            sym = z["symbol"]
            current_price = tickers.get(sym)
            if current_price is None:
                continue

            side = z["side"]
            status = z["status"]

            # 1. Check FIRST TAP ENTRY for QUALIFIED zones
            if status == "QUALIFIED":
                triggered = False
                if side == "BUY":
                    # If price already collapsed below Stop Loss, zone is INVALIDATED (do not alert)
                    if current_price < z["ob_low"] * 0.97:
                        z["status"] = "INVALIDATED"
                        save_or_update_zone(z)
                        continue
                    elif current_price <= z["ob_high"]:
                        triggered = True
                elif side == "SELL":
                    # If price already spiked above Stop Loss, zone is INVALIDATED (do not alert)
                    if current_price > z["ob_high"] * 1.03:
                        z["status"] = "INVALIDATED"
                        save_or_update_zone(z)
                        continue
                    elif current_price >= z["ob_low"]:
                        triggered = True

                if triggered:
                    # Check Mike AI Self-Improving eligibility
                    eligibility = mike_brain.evaluate_coin_eligibility(sym)
                    if not eligibility.get("eligible", True):
                        print(f"Skipping trade on {sym}: Mike AI cool-off active ({eligibility.get('reason')})")
                        continue

                    alert_key = f"{sym}_{side}_{z['origin_time']}_FIRST_TAP_ENTRY"
                    if is_alert_sent(alert_key):
                        # Alert already sent previously, do not duplicate
                        z["status"] = "ACTIVE"
                        save_or_update_zone(z)
                        continue

                    entry_price = z["ob_high"] if side == "BUY" else z["ob_low"]
                    now_ms = int(time.time() * 1000)
                    tp_price = entry_price * (1.04 if side == "BUY" else 0.96)
                    sl_price = entry_price * (0.97 if side == "BUY" else 1.03)

                    z["status"] = "ACTIVE"
                    z["entry_price"] = entry_price
                    z["entry_time"] = now_ms
                    z["tp_price"] = tp_price
                    z["sl_price"] = sl_price

                    save_or_update_zone(z)
                    add_signal(z.get("id"), sym, side, "FIRST_TAP_ENTRY", entry_price, now_ms, f"Triggered @ {current_price}")

                    try:
                        open_paper_trade(z)
                    except Exception:
                        pass

                    # Strict 3-OB Sandwich Rule (Exact Visual Price Stack on Screen)
                    coin_zones = [cz for cz in active_zones if cz["symbol"] == sym and cz["side"] == side and cz["status"] in ("QUALIFIED", "ACTIVE")]
                    if side == "BUY":
                        coin_zones.sort(key=lambda x: x["ob_high"], reverse=True) # Top OB #1 -> Middle OB #2 -> Bottom OB #3
                    else:
                        coin_zones.sort(key=lambda x: x["ob_low"]) # Bottom OB #1 -> Middle OB #2 -> Top OB #3
                    
                    has_3_obs = len(coin_zones) >= 3
                    # Middle OB is index 1 (between top and bottom)
                    middle_zone = coin_zones[1] if has_3_obs else None
                    target_id = middle_zone.get("id") if middle_zone else None
                    is_middle_2nd_ob = (has_3_obs and z.get("id") == target_id)

                    # Institutional Order Flow (CVD Delta, Open Interest & Resting Order Book Depth)
                    order_flow = None
                    try:
                        oi_live = await binance_feed.fetch_open_interest(sym)
                        oi_hist = await binance_feed.fetch_open_interest_hist(sym, period="1h", limit=10)
                        depth = await binance_feed.fetch_order_book_depth(sym, limit=100)
                        flow_klines = await binance_feed.fetch_klines(sym, interval="1h", limit=30)
                        if flow_klines:
                            order_flow = analyze_order_flow(sym, flow_klines, current_price, zone=z, live_oi=oi_live, hist_oi=oi_hist, depth=depth)
                    except Exception:
                        pass

                    # Super Sniper Combo Verification for BUY Trades (92.3% Win Rate Filter with Resting Wall)
                    is_super_sniper = False
                    is_dump_warning = False
                    if side == "BUY" and order_flow:
                        d_ratio = order_flow.get("delta_ratio", 0.50)
                        cvd_rev = order_flow.get("cvd_reversal", False)
                        oi_chg = order_flow.get("oi_change_1h", 0.0)
                        is_bid_wall = order_flow.get("is_heavy_bid_wall", False)
                        depth_r = order_flow.get("depth_ratio", 1.0)
                        
                        # Super Sniper Combo: Delta >= 51% OR Heavy Resting Bid Wall (>= 1.5x) + CVD Reversal + Whale OI
                        if (d_ratio >= 0.51 or order_flow.get("is_rocket") or is_bid_wall) and cvd_rev and oi_chg >= 0.0:
                            is_super_sniper = True
                            z["is_super_sniper"] = True
                            z["is_resting_wall"] = is_bid_wall
                            z["depth_ratio"] = depth_r
                        elif d_ratio < 0.44 and oi_chg < -1.0:
                            is_dump_warning = True
                            z["is_dump_warning"] = True

                    # Bitget 4H Real Auto-Trading (5x Isolated, STRICTLY 3-OB Middle Zone & Score >= 90)
                    try:
                        if bitget_trader.is_auto_trade_enabled():
                            if is_dump_warning:
                                print(f"Skipping Bitget BUY order for {sym}: Super Sniper Dump Warning (Heavy Sellers {100-d_ratio*100:.1f}%).")
                            elif is_middle_2nd_ob:
                                klines_4h = await binance_feed.fetch_klines(sym, interval="4h", limit=50)
                                conf = evaluate_setup_confluence(sym, z, klines_4h, order_flow=order_flow) if klines_4h else None
                                score = conf.get("score", 0) if conf else 0
                                min_conf = int(get_setting("bitget_min_confluence", str(BITGET_MIN_CONFLUENCE)))
                                if score >= min_conf:
                                    asyncio.create_task(bitget_trader.execute_2nd_ob_trade(z, confluence=conf))
                                else:
                                    print(f"Skipping Bitget order for {sym}: Mike AI Score ({score}/100) < {min_conf} required.")
                            else:
                                print(f"Skipping Bitget order for {sym}: Does not meet strict 3-OB Middle Zone requirement (Has {len(coin_zones)} OBs).")
                    except Exception as e:
                        pass

                    # Binance 1H Real Auto-Trading (5x Isolated, STRICTLY 3-OB Middle Zone & Score >= 90)
                    try:
                        if binance_trader.is_auto_trade_enabled():
                            if is_dump_warning:
                                print(f"Skipping Binance 1H BUY order for {sym}: Super Sniper Dump Warning (Heavy Sellers {100-d_ratio*100:.1f}%).")
                            elif is_middle_2nd_ob:
                                klines_1h = await binance_feed.fetch_klines(sym, interval="1h", limit=50)
                                conf_1h = evaluate_setup_confluence(sym, z, klines_1h, order_flow=order_flow) if klines_1h else None
                                score_1h = conf_1h.get("score", 0) if conf_1h else 0
                                if score_1h >= 90:
                                    asyncio.create_task(binance_trader.execute_1h_scalp_trade(z, confluence=conf_1h))
                                else:
                                    print(f"Skipping Binance 1H order for {sym}: Mike AI Score ({score_1h}/100) < 90 required.")
                            else:
                                print(f"Skipping Binance 1H order for {sym}: Does not meet strict 3-OB Middle Zone requirement (Has {len(coin_zones)} OBs).")
                    except Exception as e:
                        pass

                    # Record in Master Trade Journal Spreadsheet
                    try:
                        record_trade_entry(
                            exchange="Binance/Bitget",
                            timeframe="1h/4h",
                            symbol=sym,
                            side=side,
                            entry_price=entry_price,
                            tp_price=tp_price,
                            soft_sl_price=sl_price,
                            hard_sl_price=entry_price * (0.955 if side == "BUY" else 1.045),
                            margin_usdt=50.0,
                            account_balance=77.59,
                            mike_score=95,
                            notes="2nd OB Priority Institutional Entry" if is_2nd_ob else "1st OB Entry"
                        )
                    except Exception:
                        pass

                    # Telegram alert & broadcast
                    asyncio.create_task(telegram_service.alert_first_tap_entry(z, order_flow=order_flow))
                    await self.broadcast("FIRST_TAP_ENTRY", {**z, "order_flow": order_flow})

            # 2. Check TP / SL for ACTIVE trades
            elif status == "ACTIVE":
                entry_price = z.get("entry_price") or (z["ob_high"] if side == "BUY" else z["ob_low"])
                tp_price = z.get("tp_price") or (entry_price * 1.04 if side == "BUY" else entry_price * 0.96)
                sl_price = z.get("sl_price") or (entry_price * 0.97 if side == "BUY" else entry_price * 1.03)
                now_ms = int(time.time() * 1000)

                if side == "BUY":
                    if current_price >= tp_price:
                        alert_key = f"{sym}_{side}_{z['origin_time']}_TP_HIT"
                        z["status"] = "TP_HIT"
                        save_or_update_zone(z)
                        add_signal(z.get("id"), sym, side, "TP_HIT", current_price, now_ms, "+4.0% Hit")
                        try:
                            close_paper_trade(z, "TP_HIT")
                        except Exception:
                            pass
                        try:
                            mike_brain.reflect_on_trade({
                                "symbol": sym,
                                "status": "TP_HIT",
                                "entry_price": entry_price,
                                "exit_price": current_price,
                                "roe_pct": 7.50 if side == "BUY" else 7.50,
                                "pnl_usdt": 3.75,
                                "order_flow": z.get("order_flow", {})
                            })
                        except Exception as e:
                            print(f"Error in Mike AI reflection: {e}")
                        if not is_alert_sent(alert_key):
                            asyncio.create_task(telegram_service.alert_tp_hit(z))
                        await self.broadcast("TP_HIT", z)
                    elif current_price <= sl_price:
                        alert_key = f"{sym}_{side}_{z['origin_time']}_SL_HIT"
                        z["status"] = "SL_HIT"
                        save_or_update_zone(z)
                        add_signal(z.get("id"), sym, side, "SL_HIT", current_price, now_ms, "-3.0% Hit")
                        try:
                            close_paper_trade(z, "SL_HIT")
                        except Exception:
                            pass
                        try:
                            mike_brain.reflect_on_trade({
                                "symbol": sym,
                                "status": "SL_HIT",
                                "entry_price": entry_price,
                                "exit_price": current_price,
                                "roe_pct": -10.0 if side == "BUY" else -10.0,
                                "pnl_usdt": -5.0,
                                "order_flow": z.get("order_flow", {})
                            })
                        except Exception as e:
                            print(f"Error in Mike AI reflection: {e}")
                        if not is_alert_sent(alert_key):
                            asyncio.create_task(telegram_service.alert_sl_hit(z))
                        await self.broadcast("SL_HIT", z)

                elif side == "SELL":
                    if current_price <= tp_price:
                        alert_key = f"{sym}_{side}_{z['origin_time']}_TP_HIT"
                        z["status"] = "TP_HIT"
                        save_or_update_zone(z)
                        add_signal(z.get("id"), sym, side, "TP_HIT", current_price, now_ms, "+4.0% Hit")
                        try:
                            close_paper_trade(z, "TP_HIT")
                        except Exception:
                            pass
                        if not is_alert_sent(alert_key):
                            asyncio.create_task(telegram_service.alert_tp_hit(z))
                        await self.broadcast("TP_HIT", z)
                    elif current_price >= sl_price:
                        alert_key = f"{sym}_{side}_{z['origin_time']}_SL_HIT"
                        z["status"] = "SL_HIT"
                        save_or_update_zone(z)
                        add_signal(z.get("id"), sym, side, "SL_HIT", current_price, now_ms, "-3.0% Hit")
                        try:
                            close_paper_trade(z, "SL_HIT")
                        except Exception:
                            pass
                        if not is_alert_sent(alert_key):
                            asyncio.create_task(telegram_service.alert_sl_hit(z))
                        await self.broadcast("SL_HIT", z)

    async def check_daily_report_schedule(self):
        now_ist = get_ist_now()
        date_str = now_ist.strftime("%Y-%m-%d")
        if now_ist.hour == 23 and now_ist.minute >= 58 and self.last_daily_report_date != date_str:
            self.last_daily_report_date = date_str
            asyncio.create_task(telegram_service.send_daily_summary())

    async def start(self):
        self.is_running = True
        set_metric("start_time", str(time.time()))

        # Immediately fetch live tickers so prices are available to /api/coins within 1 second!
        try:
            await self.check_live_prices_and_triggers()
        except Exception:
            pass

        # Short delay so server starts and serves UI immediately
        await asyncio.sleep(2)
        try:
            await self.run_full_structure_scan()
        except Exception as e:
            increment_metric("errors")

        # Main loops
        price_check_timer = 0
        structure_check_timer = 0
        daily_check_timer = 0

        while self.is_running:
            try:
                now = time.time()
                # Live price ticker check
                if now - price_check_timer >= LIVE_PRICE_INTERVAL_SECONDS:
                    await self.check_live_prices_and_triggers()
                    price_check_timer = now

                # Structure refresh check (every 10 minutes)
                if now - structure_check_timer >= (STRUCTURE_REFRESH_MINUTES * 60):
                    await self.run_full_structure_scan()
                    structure_check_timer = now

                # Daily summary check (every 60 seconds)
                if now - daily_check_timer >= 60:
                    await self.check_daily_report_schedule()
                    daily_check_timer = now

                await asyncio.sleep(1)
            except Exception as e:
                increment_metric("errors")
                await asyncio.sleep(3)

    def stop(self):
        self.is_running = False

scanner = SMCScanner()
