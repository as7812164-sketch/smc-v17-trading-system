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
    get_ist_now
)
from feed.binance_feed import binance_feed
from database.db import (
    get_setting
)
from alerts.telegram_service import telegram_service

class SMCScanner:
    """
    Hermes 3.5 Single Tier Radar Harvest Scanner Gateway.
    All scanning, setup detection, orderflow verification, and execution 
    are handled by hermes35_live_engine.
    """
    def __init__(self):
        self.is_running = False
        remaining = [c for c in DEFAULT_COINS if c not in TIER1_COINS]
        self.active_coins = list(TIER1_COINS) + remaining
        self.last_full_scan_time = 0
        self.last_tickers: Dict[str, float] = {}
        self.ws_broadcast_callback = None
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
        Structure scan delegated completely to HERMES 3.5 SINGLE TIER RADAR HARVEST.
        """
        from engine.hermes35_live import hermes35_live_engine
        return await hermes35_live_engine.run_full_champion_scan()

    async def check_live_prices_and_triggers(self):
        """
        Broadcasts live tickers and delegates real-time execution to Hermes 3.5 engine.
        """
        tickers = await binance_feed.fetch_all_tickers()
        if not tickers:
            return
        self.last_tickers = tickers
        await self.broadcast("TICKER_UPDATE", tickers)
        return

    async def check_daily_report_schedule(self):
        now_ist = get_ist_now()
        date_str = now_ist.strftime("%Y-%m-%d")
        if now_ist.hour == 23 and now_ist.minute >= 58 and self.last_daily_report_date != date_str:
            self.last_daily_report_date = date_str
            asyncio.create_task(telegram_service.send_daily_summary())

    async def start(self):
        """Hermes 3.5 operates 24/7 autonomously."""
        self.is_running = False
        return

    def stop(self):
        self.is_running = False

scanner = SMCScanner()
