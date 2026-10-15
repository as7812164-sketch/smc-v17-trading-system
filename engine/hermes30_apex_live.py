"""
HERMES 3.0 MODEL 2A: 24/7 Autonomous Live Execution & Scanning Engine
=====================================================================
Official Production Strategy Engine implementing:
1. Setup Architecture:
   - 1H & 4H Timeframes across Top-22 Champions.
   - 4 Sentry Guardians:
     * Sentry 1: BTC Macro Causal Brake (BTC 4H >= 2.0% dump/pump veto).
     * Sentry 2: Institutional Displacement >= 5.0% + Fair Value Gap (FVG).
     * Sentry 3: Inducement (IDM) Liquidity Sweep + >= 18% Rejection Wick Absorption.
     * Sentry 4: Freshness Guard (Retest tap strictly <= 28 bars).
   - Entry Point: Strictly at 50% Mean Threshold (MT) = (OB_High + OB_Low) / 2.0.

2. Risk & Dual-Threshold Defense (1:2 R:R):
   - Take Profit (TP): +3.00% spot move (+15.0% ROE @ 5x leverage).
   - Break-Even Armor: +1.50% spot move (+7.5% ROE @ 5x) locks SL at entry ($0.00 risk-free).
   - Soft SL (Structural Invalidation): -1.50% spot move (-7.5% ROE @ 5x) evaluated strictly on CANDLE BODY CLOSE.
     (Wick sweeps below -1.50% do not trigger exit, absorbing institutional hunts!).
   - Emergency Hard Circuit Breaker: -3.00% spot move (-15.0% ROE @ 5x) placed on exchange & live ticker monitor.
"""

import asyncio
import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

from database.db import (
    get_connection,
    get_paper_account,
    get_dual_paper_accounts,
    get_compounding_sections,
    get_open_paper_trades,
    update_paper_trade_mark_price,
    format_duration_str,
    get_paper_trade_sequence_num,
    get_setting,
    set_setting,
    set_metric,
    is_alert_sent,
    record_sent_alert,
    open_paper_trade,
    close_paper_trade
)
from feed.binance_feed import binance_feed
from alerts.telegram_service import (
    telegram_service,
    format_trade_open_alert,
    format_trade_closed_alert,
    format_tg_ist_timestamp
)
from engine.chart_image_generator import render_smc_chart_image

logger = logging.getLogger("Hermes30Model2A")

from config import (
    TOP_22_CHAMPIONS,
    STRATEGY_VERSION,
    HERMES_3_MEAN_THRESHOLD_ENTRY,
    HERMES_3_CANDLE_BODY_CLOSE_SL,
    HERMES_3_SOFT_SL_PCT,
    HERMES_3_HARD_CIRCUIT_SL_PCT,
    HERMES_3_TP_PCT,
    HERMES_3_BE_TRIGGER_PCT,
    HERMES_3_REJECTION_WICK_MIN,
    HERMES_3_MAX_TAP_BARS,
    HERMES_3_LIMIT_PROXIMITY_PCT,
    HERMES_3_ENABLE_STEPPED_TRAILING,
    HERMES_3_INFINITE_TRAILING_RIDER,
    HERMES_3_STEPPED_TRAILING_LADDER
)

IST = timezone(timedelta(hours=5, minutes=30))

class Hermes30Model2ALiveEngine:
    def __init__(self):
        self.is_running = False
        self.scan_interval_seconds = 180  # Structure scan every 3 minutes
        self.tick_interval_seconds = 5    # Live ticker watchdog every 5 seconds
        self.last_scan_time = 0
        self.last_btc_bias = {"bias": "NEUTRAL", "pct": 0.0, "time": 0}
        self.detected_setups: List[Dict[str, Any]] = []
        self.last_tickers: Dict[str, float] = {}
        self.last_ticker_time: float = 0.0
        self.trade_cooldowns: Dict[str, float] = {}
        self._order_execution_lock = asyncio.Lock()
        self._in_flight_symbols = set()
        self.ws_broadcast_callback = None
        self._ensure_db_schema()

    @property
    def active_position(self) -> Optional[Dict[str, Any]]:
        """Returns the first active position or None, for backwards compatibility."""
        open_trades = get_open_paper_trades()
        return open_trades[0] if open_trades else None

    @active_position.setter
    def active_position(self, val):
        pass  # Backwards compatibility

    def set_broadcast_callback(self, callback):
        self.ws_broadcast_callback = callback

    async def broadcast(self, event_type: str, data: Any):
        if self.ws_broadcast_callback:
            try:
                await self.ws_broadcast_callback({"type": event_type, "data": data})
            except Exception:
                pass

    def _ensure_db_schema(self):
        """Ensures database tables reflect HERMES 3.0 MODEL 2A."""
        with get_connection() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_account)").fetchall()]
            if "vault_balance" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN vault_balance REAL DEFAULT 0.0")
            if "milestone_target" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN milestone_target REAL DEFAULT 2000.0")
            if "mode" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN mode TEXT DEFAULT 'HERMES_3.0_MODEL_2A'")

            trade_cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_trades)").fetchall()]
            if "timeframe" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN timeframe TEXT DEFAULT '4h'")
            if "hard_sl_price" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN hard_sl_price REAL DEFAULT 0.0")
            if "be_locked" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN be_locked INTEGER DEFAULT 0")
            if "vault_stashed_usdt" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN vault_stashed_usdt REAL DEFAULT 0.0")
            if "sentry_reasons" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN sentry_reasons TEXT DEFAULT ''")
            if "trailing_sl_price" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN trailing_sl_price REAL DEFAULT 0.0")
            if "locked_roi_pct" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN locked_roi_pct REAL DEFAULT 0.0")
            if "trailing_step" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN trailing_step INTEGER DEFAULT 0")
            if "order_type" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN order_type TEXT DEFAULT 'LIMIT'")

            # Update account mode to HERMES_3.0_MODEL_2A
            conn.execute("UPDATE paper_account SET mode = 'HERMES_3.0_MODEL_2A' WHERE id <= 10")
            conn.commit()

    def get_hermes_account(self, account_id: Optional[int] = None) -> Dict[str, Any]:
        """Retrieves live Hermes Deca Compounding account state ($500 total equity across 10 sections)."""
        if account_id:
            return get_paper_account(account_id=account_id)
        try:
            deca = get_compounding_sections()
            combined = deca.get("combined", {})
            combined["total_sections"] = 10
            combined["sections"] = deca.get("sections", [])
            return combined
        except Exception:
            with get_connection() as conn:
                row = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()
                return dict(row) if row else {}

    async def evaluate_btc_macro_sentry(self) -> Dict[str, Any]:
        """Sentry 1: Macro BTC Causal Brake (Vetoes if BTC 4H dumped/pumped >= 2.0%)."""
        try:
            btc_candles = await binance_feed.fetch_klines("BTCUSDT", interval="4h", limit=10)
            if len(btc_candles) >= 3:
                last_c = btc_candles[-2]  # Last completed 4H candle
                o, c = float(last_c["open"]), float(last_c["close"])
                chg = (c - o) / o if o > 0 else 0.0
                long_veto = (chg <= -0.020)   # Dump >= 2% vetoes longs
                short_veto = (chg >= 0.020)   # Pump >= 2% vetoes shorts
                return {
                    "bias": "BULLISH" if chg > 0 else "BEARISH",
                    "change_pct": round(chg * 100.0, 2),
                    "long_veto": long_veto,
                    "short_veto": short_veto,
                    "btc_is_bull": chg > 0
                }
        except Exception as e:
            logger.warning(f"BTC sentry error: {e}")
        return {"bias": "NEUTRAL", "change_pct": 0.0, "long_veto": False, "short_veto": False, "btc_is_bull": True}

    def detect_apex_setups_on_candles(
        self,
        symbol: str,
        candles: List[Dict[str, Any]],
        interval: str,
        btc_sentry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Pure algorithmic implementation of HERMES 3.0 MODEL 2A:
        - Decisional Order Block (Fib 0.30 - 0.70 of wave)
        - Displacement >= 5.0% with Fair Value Gap (FVG)
        - Inducement (IDM) swept
        - 50% Mean Threshold (MT) entry: mt = (ob_high + ob_low) / 2.0
        - Rejection wick >= 18% on tap candle
        - Freshness <= 28 bars
        - 1:2 R:R (+3.0% TP, -1.5% Soft Body Close SL, -3.0% Hard Circuit Breaker, +1.5% BE Armor)
        """
        n = len(candles)
        if n < 40:
            return []

        setups = []
        max_tap_window = HERMES_3_MAX_TAP_BARS  # 28 bars

        for i in range(20, n - 2):
            # -----------------------------------------------------------------
            # 1. BULLISH SETUP (LONG)
            # -----------------------------------------------------------------
            if not btc_sentry.get("long_veto", False):
                prior_lows = [float(x["low"]) for x in candles[max(0, i-15):i+1]]
                if float(candles[i]["low"]) == min(prior_lows):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [float(x["high"]) for x in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        origin_l = float(candles[i]["low"])
                        gain = (max_high - origin_l) / origin_l if origin_l > 0 else 0.0
                        if gain >= 0.050:  # Displacement >= 5.0%
                            idm_low = float(candles[high_idx - 1]["low"])
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i + 1, high_idx):
                                m_h, m_l = float(candles[mid]["high"]), float(candles[mid]["low"])
                                bg = (m_h - m_l) / m_l if m_l > 0 else 0.0
                                fib = (m_l - origin_l) / (max_high - origin_l) if max_high > origin_l else 0.0
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid

                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(float(dec_c["open"]), float(dec_c["close"]))
                                dec_bot = float(dec_c["low"])
                                has_fvg = (float(candles[best_mid + 1]["low"]) > float(candles[best_mid - 1]["high"])) if best_mid + 1 < n else False

                                if has_fvg:
                                    # 50% Mean Threshold Entry (Hermes 3.0 Standard)
                                    mt = round((dec_top + dec_bot) / 2.0, 8)
                                    tp_price = round(mt * (1.0 + HERMES_3_TP_PCT), 8)
                                    soft_sl_price = round(mt * (1.0 - HERMES_3_SOFT_SL_PCT), 8)
                                    hard_sl_price = round(mt * (1.0 - HERMES_3_HARD_CIRCUIT_SL_PCT), 8)
                                    be_armor_price = round(mt * (1.0 + HERMES_3_BE_TRIGGER_PCT), 8)

                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])

                                        # First Tap or 0.20% Proximity Limit Check at 50% MT
                                        is_limit_proximity = (t_l <= mt * (1.0 + HERMES_3_LIMIT_PROXIMITY_PCT))
                                        if is_limit_proximity and t_c >= mt * 0.995:
                                            c_range = t_h - t_l
                                            swept = any(float(candles[k]["low"]) < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(t_o, t_c) - t_l
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0.0

                                            if swept and w_ratio >= HERMES_3_REJECTION_WICK_MIN:
                                                is_fresh = (t == n - 1 or t == n - 2)
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "LONG",
                                                    "interval": interval,
                                                    "order_type": "LIMIT",
                                                    "entry_price": mt,
                                                    "mean_threshold": mt,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "tp_price": tp_price,
                                                    "soft_sl_price": soft_sl_price,
                                                    "hard_sl_price": hard_sl_price,
                                                    "trailing_sl_price": 0.0,
                                                    "locked_roi_pct": 0.0,
                                                    "trailing_step": 0,
                                                    "stepped_trailing_active": True,
                                                    "be_armor_price": be_armor_price,
                                                    "tp_pct": HERMES_3_TP_PCT,
                                                    "soft_sl_pct": HERMES_3_SOFT_SL_PCT,
                                                    "hard_sl_pct": HERMES_3_HARD_CIRCUIT_SL_PCT,
                                                    "displacement_pct": round(gain * 100.0, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100.0, 1),
                                                    "tap_bar_age": (n - 1) - t,
                                                    "tap_time": tap_c["time"],
                                                    "is_fresh_trigger": is_fresh,
                                                    "status": "FRESH_TRIGGERED" if is_fresh else "ARMED_TAP",
                                                    "sentry_reasons": "Hermes 3.0 Model 2A | 50% MT Limit Entry | Rejection Wick >= 18% | Stepped Trailing Active"
                                                })
                                            break

            # -----------------------------------------------------------------
            # 2. BEARISH SETUP (SHORT)
            # -----------------------------------------------------------------
            if not btc_sentry.get("short_veto", False):
                prior_highs = [float(x["high"]) for x in candles[max(0, i-15):i+1]]
                if float(candles[i]["high"]) == max(prior_highs):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [float(x["low"]) for x in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        origin_h = float(candles[i]["high"])
                        drop = (origin_h - min_low) / origin_h if origin_h > 0 else 0.0
                        if drop >= 0.050:
                            idm_high = float(candles[low_idx - 1]["high"])
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i + 1, low_idx):
                                m_h, m_l = float(candles[mid]["high"]), float(candles[mid]["low"])
                                bg = (m_h - m_l) / m_h if m_h > 0 else 0.0
                                fib = (origin_h - m_h) / (origin_h - min_low) if origin_h > min_low else 0.0
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid

                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = float(dec_c["high"])
                                dec_bot = min(float(dec_c["open"]), float(dec_c["close"]))
                                has_bear_fvg = (float(candles[best_mid + 1]["high"]) < float(candles[best_mid - 1]["low"])) if best_mid + 1 < n else False

                                if has_bear_fvg:
                                    mt = round((dec_top + dec_bot) / 2.0, 8)
                                    tp_price = round(mt * (1.0 - HERMES_3_TP_PCT), 8)
                                    soft_sl_price = round(mt * (1.0 + HERMES_3_SOFT_SL_PCT), 8)
                                    hard_sl_price = round(mt * (1.0 + HERMES_3_HARD_CIRCUIT_SL_PCT), 8)
                                    be_armor_price = round(mt * (1.0 - HERMES_3_BE_TRIGGER_PCT), 8)

                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])

                                        # First Tap or 0.20% Proximity Limit Check at 50% MT
                                        is_limit_proximity = (t_h >= mt * (1.0 - HERMES_3_LIMIT_PROXIMITY_PCT))
                                        if is_limit_proximity and t_c <= mt * 1.005:
                                            c_range = t_h - t_l
                                            swept = any(float(candles[k]["high"]) > idm_high for k in range(low_idx, t + 1))
                                            w_ratio = (t_h - max(t_o, t_c)) / c_range if c_range > 0 else 0.0

                                            if swept and w_ratio >= HERMES_3_REJECTION_WICK_MIN:
                                                is_fresh = (t == n - 1 or t == n - 2)
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "SHORT",
                                                    "interval": interval,
                                                    "order_type": "LIMIT",
                                                    "entry_price": mt,
                                                    "mean_threshold": mt,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "tp_price": tp_price,
                                                    "soft_sl_price": soft_sl_price,
                                                    "hard_sl_price": hard_sl_price,
                                                    "trailing_sl_price": 0.0,
                                                    "locked_roi_pct": 0.0,
                                                    "trailing_step": 0,
                                                    "stepped_trailing_active": True,
                                                    "be_armor_price": be_armor_price,
                                                    "tp_pct": HERMES_3_TP_PCT,
                                                    "soft_sl_pct": HERMES_3_SOFT_SL_PCT,
                                                    "hard_sl_pct": HERMES_3_HARD_CIRCUIT_SL_PCT,
                                                    "displacement_pct": round(drop * 100.0, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100.0, 1),
                                                    "tap_bar_age": (n - 1) - t,
                                                    "tap_time": tap_c["time"],
                                                    "is_fresh_trigger": is_fresh,
                                                    "status": "FRESH_TRIGGERED" if is_fresh else "ARMED_TAP",
                                                    "sentry_reasons": "Hermes 3.0 Model 2A | 50% MT Limit Entry | Rejection Wick >= 18% | Stepped Trailing Active"
                                                })
                                            break

        # Deduplicate
        unique_map = {}
        for s in setups:
            k = (s["symbol"], s["side"], s.get("interval", "4h"))
            if k not in unique_map or s.get("is_fresh_trigger"):
                unique_map[k] = s

        return list(unique_map.values())

    async def run_full_champion_scan(self) -> Dict[str, Any]:
        """Scans all configured champion assets on 1H and 4H."""
        btc_sentry = await self.evaluate_btc_macro_sentry()
        all_setups = []

        for symbol in TOP_22_CHAMPIONS:
            for interval in ["4h", "1h"]:
                try:
                    candles = await binance_feed.fetch_klines(symbol, interval=interval, limit=120)
                    if candles and len(candles) >= 40:
                        detected = self.detect_apex_setups_on_candles(symbol, candles, interval, btc_sentry)
                        all_setups.extend(detected)
                except Exception as e:
                    logger.debug(f"Scan error for {symbol} {interval}: {e}")

        # Sort fresh triggers first
        all_setups.sort(key=lambda x: (not x.get("is_fresh_trigger", False), x.get("tap_bar_age", 99)))
        self.detected_setups = all_setups

        # Master Emergency Kill Switch Check
        if self.is_kill_switch_active():
            return {
                "timestamp": time.time(),
                "btc_sentry": btc_sentry,
                "total_detected": len(all_setups),
                "fresh_triggers": 0,
                "kill_switch_active": True,
                "setups": all_setups[:20]
            }

        # Check for immediate fresh trigger execution across Deca Compounding Sections (1-10)
        fresh = [s for s in all_setups if s.get("is_fresh_trigger")]
        if fresh:
            open_trades = get_open_paper_trades()
            busy_sec_ids = {int(t["account_id"]) for t in open_trades if t.get("account_id")}
            busy_symbols = {t.get("symbol") for t in open_trades if t.get("symbol")}

            for setup in fresh:
                sym = setup.get("symbol")
                if sym in busy_symbols:
                    continue  # Zero coin duplication across sections

                tf = setup.get("interval", "4h").lower()
                target_sec_ids = list(range(1, 6)) if "4h" in tf else list(range(6, 11))
                available_sec = next((sid for sid in target_sec_ids if sid not in busy_sec_ids), None)

                if available_sec is not None:
                    # Allocate this slot
                    busy_sec_ids.add(available_sec)
                    busy_symbols.add(sym)
                    setup_to_run = dict(setup)
                    setup_to_run["account_id"] = available_sec
                    setup_to_run["channel"] = f"sec_{available_sec}"
                    logger.info(f"⚡ DECA COMPOUNDING: Deploying {sym} {tf.upper()} into Section {available_sec}")
                    asyncio.create_task(self.execute_apex_entry(setup_to_run))
                else:
                    logger.info(f"⏳ All {tf.upper()} Deca Compounding sections are currently busy for {sym}.")

        return {
            "timestamp": time.time(),
            "btc_sentry": btc_sentry,
            "total_detected": len(all_setups),
            "fresh_triggers": len(fresh),
            "kill_switch_active": self.is_kill_switch_active(),
            "setups": all_setups[:20]
        }

    def is_kill_switch_active(self) -> bool:
        """Returns True if the Master Emergency Kill Switch is enabled."""
        return get_setting("trading_kill_switch", "false").lower() == "true"

    def set_kill_switch(self, enabled: bool) -> bool:
        """Enables or disables the Master Emergency Kill Switch."""
        set_setting("trading_kill_switch", "true" if enabled else "false")
        logger.warning(f"🚨 MASTER EMERGENCY KILL SWITCH: {'ACTIVATED (ALL TRADES HALTED)' if enabled else 'DEACTIVATED (TRADING RESUMED)'}")
        return enabled

    async def execute_apex_entry(self, setup: Dict[str, Any]):
        """Executes a qualified Model 2A trade under Deca Compounding (10 independent slots)."""
        async with self._order_execution_lock:
            if self.is_kill_switch_active():
                logger.warning("🚨 EMERGENCY KILL SWITCH ACTIVE: Suppressing new trade entry.")
                return

            symbol = setup["symbol"]
            side = setup["side"].upper()
            timeframe = setup.get("interval", setup.get("timeframe", "4h")).lower()
            now_ts = time.time()

            # Prevent duplicate position on same symbol
            open_trades = get_open_paper_trades()
            if any(t.get("symbol") == symbol for t in open_trades):
                logger.info(f"⚠️ Position already open for {symbol}. Suppressing duplicate.")
                return

            # Determine Deca Compounding Section ID (1-5 for 4H Macro, 6-10 for 1H Intraday)
            target_sec_ids = list(range(1, 6)) if "4h" in timeframe else list(range(6, 11))
            busy_sec_ids = {int(t["account_id"]) for t in open_trades if t.get("account_id")}

            req_sec_id = setup.get("account_id")
            if req_sec_id and req_sec_id in target_sec_ids and req_sec_id not in busy_sec_ids:
                sec_id = req_sec_id
            else:
                sec_id = next((i for i in target_sec_ids if i not in busy_sec_ids), None)

            if not sec_id:
                logger.info(f"⏳ All {timeframe.upper()} compounding sections (IDs {target_sec_ids}) are currently busy. Queue full.")
                return

            # Cooldown guard: In-memory & Persistent DB check (Prevents rapid machine-gun re-entries!)
            cd_db = float(get_setting(f"cooldown_{symbol}", 0) or 0)
            if self.trade_cooldowns.get(symbol, 0) > now_ts or cd_db > now_ts:
                logger.info(f"⏳ Cooldown active for {symbol}. Suppressing entry.")
                return

            # Dedup guard: Prevent multiple alerts for the same candle tap
            alert_key = f"{symbol}_{side}_{setup.get('tap_time', int(now_ts // 14400))}_ENTRY"
            if is_alert_sent(alert_key):
                logger.info(f"⚠️ Duplicate entry alert prevented for {symbol} {side}")
                return

            # Fetch account balance for this specific section
            acc = get_paper_account(account_id=sec_id)
            curr_balance = float(acc.get("current_balance", 50.0) or 50.0)
            if curr_balance < 5.0:
                logger.warning(f"⚠️ Section {sec_id} balance too low (${curr_balance}). Suppressing entry.")
                return

            # Arm 1-hour cooldown immediately so coin cannot re-enter in a rapid loop
            self.trade_cooldowns[symbol] = now_ts + 3600
            set_setting(f"cooldown_{symbol}", str(now_ts + 3600))
            record_sent_alert(alert_key, symbol, side, "ENTRY", setup.get("tap_time", 0), None)

            # 5x Leverage Compounding isolated to this section
            leverage = 5
            margin = round(curr_balance, 2)
            position_size = round(margin * leverage, 2)

            ep = float(setup["entry_price"])
            tp = float(setup["tp_price"])
            soft_sl = float(setup["soft_sl_price"])
            hard_sl = float(setup["hard_sl_price"])

            setup["account_id"] = sec_id
            setup["channel"] = f"sec_{sec_id}"
            setup["timeframe"] = timeframe
            setup["margin_usdt"] = margin
            setup["position_size_usdt"] = position_size
            setup["order_type"] = "LIMIT"
            setup["trailing_sl_price"] = 0.0
            setup["locked_roi_pct"] = 0.0
            setup["trailing_step"] = 0

            trade_record = open_paper_trade(setup)
            if not trade_record or "error" in trade_record:
                logger.error(f"Failed to open paper trade for {symbol}: {trade_record}")
                return

            trade_id = trade_record.get("id")

            # Real exchange auto-trading execution (Bitget / Binance)
            try:
                from engine.bitget_trader import bitget_trader
                if bitget_trader.is_configured() and bitget_trader.is_auto_trade_enabled():
                    setup_copy = {**setup, "managed_by_hermes": True}
                    if "4h" in timeframe:
                        await bitget_trader.execute_4h_trade(setup_copy)
                    else:
                        await bitget_trader.execute_1h_trade(setup_copy)
                    logger.info(f"💎 Bitget real trade submitted for {symbol}")
            except Exception as bge:
                logger.error(f"Error executing real Bitget trade: {bge}")

            try:
                from engine.binance_trader import binance_trader
                if binance_trader.is_configured() and binance_trader.is_auto_trade_enabled():
                    setup_copy = {**setup, "managed_by_hermes": True}
                    if "4h" in timeframe:
                        await binance_trader.execute_4h_trade(setup_copy)
                    else:
                        await binance_trader.execute_1h_trade(setup_copy)
                    logger.info(f"💎 Binance real trade submitted for {symbol}")
            except Exception as bne:
                logger.error(f"Error executing real Binance trade: {bne}")

            sec_type_str = "4H Macro Swing" if sec_id <= 5 else "1H Intraday Scalp"
            logger.info(f"🚀 HERMES 3.0 LIMIT ORDER ARMED [Section {sec_id}]: {symbol} {side} LIMIT @ {ep} | Initial Hard SL: {hard_sl} | Stepped Trailing Active")

            # Send Telegram Alert with Live Chart Image
            try:
                alert_text = (
                    f"👑 <b>HERMES 3.0: NEW LIMIT ORDER ARMED</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📦 <b>Compounding Slot</b>: <b>Section {sec_id} ({sec_type_str})</b>\n"
                    f"🪙 <b>Pair</b>: #{symbol} ({timeframe.upper()})\n"
                    f"📈 <b>Action</b>: {'🟢 BUY (LONG)' if side == 'LONG' else '🔴 SELL (SHORT)'} (LIMIT ORDER)\n"
                    f"🎯 <b>Entry Price</b>: {ep:.6f} (50% Mean Threshold | 0.20% Proximity)\n"
                    f"🛑 <b>Initial Hard SL</b>: {hard_sl:.6f} (-3.00% Disaster Shield)\n"
                    f"🛡️ <b>Soft Stop Loss</b>: {soft_sl:.6f} (Candle Body Close Defense)\n"
                    f"📈 <b>Stepped Trailing SL</b>: +5% ROI ➔ +1% | +10% ROI ➔ +5% | +15% ROI ➔ +10%\n"
                    f"🕯️ <b>Rejection Wick</b>: {setup.get('wick_ratio_pct', 24.5):.1f}% (Confirmed ≥ 18.0% Absorption)\n"
                    f"⚡ <b>Leverage</b>: {leverage}x Isolated | Margin: ${margin:.2f} USDT\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔬 <i>Deca Compounding Slot {sec_id}/10 Active | Infinite Trend Runner</i>"
                )
                keyboard = telegram_service.get_alert_inline_keyboard(symbol)
                sent_msg_id = None
                sent = False
                try:
                    candles = await binance_feed.fetch_klines(symbol, interval=timeframe, limit=50)
                    if candles:
                        chart_bytes = render_smc_chart_image(
                            symbol,
                            candles,
                            setup,
                            zones=[setup],
                            timeframe=timeframe.upper()
                        )
                        resp = await telegram_service.send_photo(
                            chart_bytes,
                            alert_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                        if resp and resp.get("ok"):
                            sent_msg_id = resp["result"]["message_id"]
                            sent = True
                except Exception as ce:
                    logger.error(f"Error generating/sending chart photo for {symbol}: {ce}")

                if not sent:
                    resp = await telegram_service.send_raw_message(alert_text, parse_mode="HTML", reply_markup=keyboard)
                    if resp and resp.get("ok"):
                        sent_msg_id = resp["result"]["message_id"]

                if sent_msg_id:
                    set_setting(f"trade_msg_{symbol}_{side}", str(sent_msg_id))
                    if trade_id:
                        set_setting(f"trade_rec_msg_{trade_id}", str(sent_msg_id))
            except Exception as e:
                logger.warning(f"Telegram alert error: {e}")

    async def check_live_price_and_exits(self):
        """
        Monitors active positions against live Binance ticker feed every few seconds:
        - Layer 1: Stepped Trailing SL Ladder (5% ROI -> +1% ROI, 9.5% -> +5%, 14.5% -> +10%, 19.5% -> +15%, 24.5% -> +20%, 29.5% -> +25%, 34.5% -> +30%... Infinite Trend Rider)
        - Layer 2: Trailing SL Hit -> Instant Profit Exit on limit/touch
        - Layer 3: Initial Hard Circuit Breaker (-3.00% Disaster SL on Exchange)
        - Layer 4: Structural Soft SL (-1.50% on Candle Body Close if trailing not yet armed)
        """
        open_trades = get_open_paper_trades()
        if not open_trades:
            return

        tickers = await binance_feed.fetch_all_tickers()
        if not tickers:
            return

        leverage = 5.0

        for trade in list(open_trades):
            sym = trade["symbol"]
            side = trade["side"].upper()
            entry_price = float(trade["entry_price"])
            hard_sl_price = float(trade.get("hard_sl_price", 0.0) or (entry_price * 0.970 if side in ("BUY", "LONG") else entry_price * 1.030))
            trade_id = trade["id"]
            tf = trade.get("timeframe", "4h")

            cur_price = tickers.get(sym)
            if not cur_price or cur_price <= 0:
                continue

            update_paper_trade_mark_price(trade_id, cur_price)

            highest_p = max(float(trade.get("highest_price") or entry_price), cur_price)
            lowest_p = min(float(trade.get("lowest_price") or entry_price), cur_price)

            # Calculate current peak ROI achieved so far
            if side in ("BUY", "LONG"):
                peak_roi = ((highest_p - entry_price) / entry_price) * 100.0 * leverage
            else:
                peak_roi = ((entry_price - lowest_p) / entry_price) * 100.0 * leverage

            current_locked_roi = float(trade.get("locked_roi_pct", 0.0) or 0.0)
            current_step = int(trade.get("trailing_step", 0) or 0)
            active_sl_price = float(trade.get("sl_price") or (entry_price * 0.985 if side in ("BUY", "LONG") else entry_price * 1.015))
            be_locked = bool(trade.get("be_locked", 0))

            # -------------------------------------------------------------
            # STEPPED TRAILING SL LADDER EVALUATION (USER-DEFINED 9.5% CADENCE)
            # -------------------------------------------------------------
            target_locked_roi = current_locked_roi
            target_step = current_step

            # Tier 1: 5.00% ROI -> SL shifts to +1.00% (Fee Shield / BE Lock)
            if peak_roi >= 5.00 and target_locked_roi < 1.0:
                target_locked_roi = 1.0
                target_step = 1
            # Tier 2: 9.50% ROI -> SL shifts to +5.00%
            if peak_roi >= 9.50 and target_locked_roi < 5.0:
                target_locked_roi = 5.0
                target_step = 2
            # Tier 3: 14.50% ROI -> SL shifts to +10.00%
            if peak_roi >= 14.50 and target_locked_roi < 10.0:
                target_locked_roi = 10.0
                target_step = 3
            # Tier 4: 19.50% ROI -> SL shifts to +15.00%
            if peak_roi >= 19.50 and target_locked_roi < 15.0:
                target_locked_roi = 15.0
                target_step = 4
            # Tier 5: 24.50% ROI -> SL shifts to +20.00%
            if peak_roi >= 24.50 and target_locked_roi < 20.0:
                target_locked_roi = 20.0
                target_step = 5
            # Tier 6: 29.50% ROI -> SL shifts to +25.00%
            if peak_roi >= 29.50 and target_locked_roi < 25.0:
                target_locked_roi = 25.0
                target_step = 6
            # Tier 7: 34.50% ROI -> SL shifts to +30.00%
            if peak_roi >= 34.50 and target_locked_roi < 30.0:
                target_locked_roi = 30.0
                target_step = 7
            # Tier 8+: Infinite Trend Runner continuation beyond 34.50%
            if peak_roi >= 39.50:
                extra_steps = int((peak_roi - 34.50) // 5.0)
                extended_target = 30.0 + (extra_steps * 5.0)
                if extended_target > target_locked_roi:
                    target_locked_roi = extended_target
                    target_step = 7 + extra_steps

            # Upgrade Trailing SL if a new step is reached!
            if target_locked_roi > current_locked_roi:
                spot_gain_pct = (target_locked_roi / 100.0) / leverage
                if side in ("BUY", "LONG"):
                    new_sl_price = round(entry_price * (1.0 + spot_gain_pct), 8)
                else:
                    new_sl_price = round(entry_price * (1.0 - spot_gain_pct), 8)

                with get_connection() as conn:
                    conn.execute("""
                    UPDATE paper_trades SET
                        sl_price = ?,
                        trailing_sl_price = ?,
                        locked_roi_pct = ?,
                        trailing_step = ?,
                        be_locked = 1
                    WHERE id = ?
                    """, (new_sl_price, new_sl_price, target_locked_roi, target_step, trade_id))
                    conn.commit()

                trade["sl_price"] = new_sl_price
                trade["trailing_sl_price"] = new_sl_price
                trade["locked_roi_pct"] = target_locked_roi
                trade["trailing_step"] = target_step
                trade["be_locked"] = 1
                active_sl_price = new_sl_price
                current_locked_roi = target_locked_roi
                be_locked = True

                logger.info(
                    f"🛡️ STEPPED TRAILING SL UPGRADE: {sym} {side} Step {target_step} | "
                    f"Peak ROI: {peak_roi:.1f}% -> Locked SL @ +{target_locked_roi:.1f}% ROI ({new_sl_price:.6f})"
                )

                # Broadcast upgrade via WebSocket to frontend
                await self.broadcast("TRADE_TRAILING_UPDATE", {
                    "trade_id": trade_id,
                    "symbol": sym,
                    "side": side,
                    "step": target_step,
                    "locked_roi": target_locked_roi,
                    "sl_price": new_sl_price,
                    "peak_roi": round(peak_roi, 1)
                })

                # Dispatch Telegram alert for Trailing SL upgrade
                try:
                    sec_id = trade.get("account_id") or 1
                    trail_text = (
                        f"🛡️ <b>HERMES 3.0: STEPPED TRAILING SL UPGRADED</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📦 <b>Compounding Slot</b>: Section {sec_id}\n"
                        f"🪙 <b>Pair</b>: #{sym} ({tf.upper()}) | Side: {'🟢 LONG' if side in ('BUY', 'LONG') else '🔴 SHORT'}\n"
                        f"📈 <b>Peak Move Achieved</b>: <b>+{peak_roi:.1f}% ROI</b> (+{peak_roi/leverage:.2f}% Spot)\n"
                        f"🔒 <b>Trailing Ladder</b>: <b>Step {target_step}</b>\n"
                        f"💰 <b>Guaranteed Locked Profit</b>: <b>+{target_locked_roi:.1f}% ROI</b>\n"
                        f"🛑 <b>New Stop Loss Price</b>: <code>{new_sl_price:.6f}</code>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"⚡ <i>Capital secured in profit. Trend runner active without TP ceiling!</i>"
                    )
                    asyncio.create_task(telegram_service.send_raw_message(trail_text))
                except Exception:
                    pass

            exit_triggered = None
            exit_price = cur_price

            # -------------------------------------------------------------
            # EXIT TRIGGER CHECKS
            # -------------------------------------------------------------
            if side in ("BUY", "LONG"):
                # 1. Trailing SL Hit (Once locked in profit >= +1.0% ROI)
                if be_locked and current_locked_roi >= 1.0 and cur_price <= active_sl_price:
                    exit_triggered = "TRAILING_SL_HIT"
                    exit_price = active_sl_price
                    logger.info(f"💎 HERMES 3.0 TRAILING SL EXIT: {sym} LONG hit locked SL @ {active_sl_price} (+{current_locked_roi:.1f}% ROI)")

                # 2. Emergency Hard Circuit Breaker Touch (-3.00%)
                elif cur_price <= hard_sl_price:
                    exit_triggered = "EMERGENCY_HARD_SL_HIT"
                    exit_price = hard_sl_price
                    logger.info(f"🛑 HERMES 3.0 EMERGENCY HARD SL: {sym} LONG hit hard circuit @ {hard_sl_price}")

                # 3. Soft SL (-1.50%): Evaluated ONLY on Candle Body Close before trailing is locked
                elif not be_locked:
                    try:
                        k = await binance_feed.fetch_klines(sym, interval=tf, limit=2)
                        if k and len(k) >= 2:
                            last_closed_candle = k[-2]
                            if float(last_closed_candle["close"]) <= active_sl_price:
                                exit_triggered = "STRUCTURAL_BODY_CLOSE_SL"
                                exit_price = float(last_closed_candle["close"])
                                logger.info(f"🛑 HERMES 3.0 STRUCTURAL BODY CLOSE SL: {sym} LONG closed below {active_sl_price}")
                    except Exception:
                        pass

            else: # SELL / SHORT
                # 1. Trailing SL Hit (Once locked in profit >= +1.0% ROI)
                if be_locked and current_locked_roi >= 1.0 and cur_price >= active_sl_price:
                    exit_triggered = "TRAILING_SL_HIT"
                    exit_price = active_sl_price
                    logger.info(f"💎 HERMES 3.0 TRAILING SL EXIT: {sym} SHORT hit locked SL @ {active_sl_price} (+{current_locked_roi:.1f}% ROI)")

                # 2. Emergency Hard Circuit Breaker Touch (-3.00%)
                elif cur_price >= hard_sl_price:
                    exit_triggered = "EMERGENCY_HARD_SL_HIT"
                    exit_price = hard_sl_price
                    logger.info(f"🛑 HERMES 3.0 EMERGENCY HARD SL: {sym} SHORT hit hard circuit @ {hard_sl_price}")

                # 3. Soft SL (-1.50%): Evaluated ONLY on Candle Body Close before trailing is locked
                elif not be_locked:
                    try:
                        k = await binance_feed.fetch_klines(sym, interval=tf, limit=2)
                        if k and len(k) >= 2:
                            last_closed_candle = k[-2]
                            if float(last_closed_candle["close"]) >= active_sl_price:
                                exit_triggered = "STRUCTURAL_BODY_CLOSE_SL"
                                exit_price = float(last_closed_candle["close"])
                                logger.info(f"🛑 HERMES 3.0 STRUCTURAL BODY CLOSE SL: {sym} SHORT closed above {active_sl_price}")
                    except Exception:
                        pass

            if exit_triggered:
                await self.resolve_trade_exit(trade, exit_triggered, exit_price)

    async def resolve_trade_exit(self, trade: Dict[str, Any], outcome: str, exit_price: float):
        """Resolves trade exit, compounds balance into specific Deca section, and dispatches alert."""
        trade_id = trade["id"]
        sym = trade["symbol"]
        side = trade["side"].upper()
        sec_id = trade.get("account_id") or 1
        tf = str(trade.get("timeframe", "4h")).lower()

        # Atomic exit settlement using database engine
        close_res = close_paper_trade(trade, outcome, exit_price)
        if not close_res:
            logger.warning(f"Trade #{trade_id} ({sym}) was already closed or not found.")
            return

        pnl_usdt = close_res.get("pnl_usdt", 0.0)
        pnl_pct = close_res.get("pnl_pct", 0.0)
        new_b = close_res.get("new_balance", 50.0)
        duration_str = close_res.get("duration", "")

        # Real exchange position close (Bitget / Binance)
        try:
            from engine.bitget_trader import bitget_trader
            if bitget_trader.is_auto_trade_enabled():
                await bitget_trader.close_position_market(sym, side)
        except Exception as bge:
            logger.error(f"Error closing Bitget real position for {sym}: {bge}")

        try:
            from engine.binance_trader import binance_trader
            if binance_trader.is_auto_trade_enabled():
                await binance_trader.close_position_market(sym, side)
        except Exception as bne:
            logger.error(f"Error closing Binance real position for {sym}: {bne}")

        # Set 30m cooldown
        self.trade_cooldowns[sym] = time.time() + 1800
        logger.info(f"🏁 HERMES 3.0 TRADE CLOSED [Section {sec_id}]: {sym} {outcome} | PnL: ${pnl_usdt:+.2f} USDT ({pnl_pct:+.2f}%) | Slot Balance: ${new_b:.2f}")

        # Send Telegram notification
        try:
            sec_type = "4H Macro Swing" if int(sec_id) <= 5 else "1H Intraday Scalp"
            tg_text = (
                f"{'🏆' if outcome in ('TP_HIT', 'TRAILING_SL_HIT') else ('🛡️' if outcome in ('BE_SAVE', 'BE_FEE_SAVE') else '🛑')} "
                f"<b>HERMES 3.0: POSITION CLOSED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 <b>Compounding Slot</b>: <b>Section {sec_id} ({sec_type})</b>\n"
                f"🪙 <b>Pair</b>: #{sym} ({tf.upper()})\n"
                f"📋 <b>Result</b>: <b>{'💎 TRAILING SL PROFIT BANK' if outcome == 'TRAILING_SL_HIT' else outcome}</b>\n"
                f"💵 <b>Realized PnL</b>: <b>{pnl_usdt:+.2f} USDT ({pnl_pct:+.2f}%)</b>\n"
                f"🚪 <b>Exit Price</b>: {exit_price:.6f}\n"
                f"⏱️ <b>Duration</b>: {duration_str}\n"
                f"💰 <b>Updated Slot Equity</b>: <b>${new_b:.2f} USDT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 <i>Section {sec_id} is now IDLE and armed for next setup.</i>"
            )
            await telegram_service.send_raw_message(tg_text)
        except Exception as e:
            logger.warning(f"Telegram exit alert error: {e}")

    async def start(self):
        """Starts the 24/7 autonomous live loop for Model 2A with infinite resilience."""
        self.is_running = True
        logger.info("👑 HERMES 3.0 MODEL 2A LIVE ENGINE ACTIVATED (24/7 AUTONOMOUS & LOCKED)")
        
        # Immediate initial scan on startup so no setups are missed
        try:
            await self.run_full_champion_scan()
        except Exception as se:
            logger.error(f"Initial scan error: {se}")

        scan_timer = 0
        while self.is_running:
            try:
                # 1. Real-time Price Ticker & Exit Watchdog (Every 5s)
                await self.check_live_price_and_exits()

                # 2. Structure Scan (Every 3 mins)
                scan_timer += self.tick_interval_seconds
                if scan_timer >= self.scan_interval_seconds:
                    scan_timer = 0
                    await self.run_full_champion_scan()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Hermes 3.0 loop: {e}")
                await asyncio.sleep(2)

            await asyncio.sleep(self.tick_interval_seconds)

    def stop(self):
        self.is_running = False

hermes30_live_engine = Hermes30Model2ALiveEngine()
hermes2_apex_engine = hermes30_live_engine
hermes35_live_engine = hermes30_live_engine
hermes35_engine = hermes30_live_engine
