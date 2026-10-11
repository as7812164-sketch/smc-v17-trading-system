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
    get_open_paper_trades,
    update_paper_trade_mark_price,
    format_duration_str,
    get_paper_trade_sequence_num,
    get_setting,
    set_setting,
    set_metric,
    is_alert_sent,
    record_sent_alert,
    open_paper_trade
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
    HERMES_3_MAX_TAP_BARS
)

IST = timezone(timedelta(hours=5, minutes=30))

class Hermes30Model2ALiveEngine:
    def __init__(self):
        self.is_running = False
        self.scan_interval_seconds = 180  # Structure scan every 3 minutes
        self.tick_interval_seconds = 5    # Live ticker watchdog every 5 seconds
        self.last_scan_time = 0
        self.last_btc_bias = {"bias": "NEUTRAL", "pct": 0.0, "time": 0}
        self.active_position: Optional[Dict[str, Any]] = None
        self.detected_setups: List[Dict[str, Any]] = []
        self.last_tickers: Dict[str, float] = {}
        self.last_ticker_time: float = 0.0
        self.trade_cooldowns: Dict[str, float] = {}
        self._order_execution_lock = asyncio.Lock()
        self._in_flight_symbols = set()
        self.ws_broadcast_callback = None
        self._ensure_db_schema()

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

            # Update account mode to HERMES_3.0_MODEL_2A
            conn.execute("UPDATE paper_account SET mode = 'HERMES_3.0_MODEL_2A' WHERE id = 1")
            conn.commit()

    def get_hermes_account(self) -> Dict[str, Any]:
        """Retrieves live Hermes account state with compounding metrics."""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()
            if not row:
                self._ensure_db_schema()
                row = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()
            acc = dict(row)
            open_count = conn.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN'").fetchone()[0]
            acc["open_trades_count"] = open_count
            wins = acc.get("win_count", 0) or 0
            losses = acc.get("loss_count", 0) or 0
            total_closed = wins + losses
            acc["win_rate"] = round((wins / total_closed * 100), 1) if total_closed > 0 else 0.0
            init_b = float(acc.get("initial_balance", 50.0) or 50.0)
            curr_b = float(acc.get("current_balance", 50.0) or 50.0)
            vault_b = float(acc.get("vault_balance", 0.0) or 0.0)
            target = float(acc.get("milestone_target", 2000.0) or 2000.0)
            equity = curr_b + vault_b
            acc["equity"] = round(equity, 2)
            acc["return_pct"] = round(((equity - init_b) / init_b * 100), 2)
            acc["milestone_progress_pct"] = round(min(100.0, (equity / target) * 100.0), 2)
            acc["mode"] = "HERMES_3.0_MODEL_2A"
            return acc

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

                                        # First Tap Check at 50% MT
                                        if t_l <= mt and t_c >= mt:
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
                                                    "entry_price": mt,
                                                    "mean_threshold": mt,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "tp_price": tp_price,
                                                    "soft_sl_price": soft_sl_price,
                                                    "hard_sl_price": hard_sl_price,
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
                                                    "sentry_reasons": "Hermes 3.0 Model 2A | 50% MT Deep Entry | Rejection Wick >= 18% | Body Close SL"
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

                                        if t_h >= mt and t_c <= mt:
                                            c_range = t_h - t_l
                                            swept = any(float(candles[k]["high"]) > idm_high for k in range(low_idx, t + 1))
                                            w_ratio = (t_h - max(t_o, t_c)) / c_range if c_range > 0 else 0.0

                                            if swept and w_ratio >= HERMES_3_REJECTION_WICK_MIN:
                                                is_fresh = (t == n - 1 or t == n - 2)
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "SHORT",
                                                    "interval": interval,
                                                    "entry_price": mt,
                                                    "mean_threshold": mt,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "tp_price": tp_price,
                                                    "soft_sl_price": soft_sl_price,
                                                    "hard_sl_price": hard_sl_price,
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
                                                    "sentry_reasons": "Hermes 3.0 Model 2A | 50% MT Deep Entry | Rejection Wick >= 18% | Body Close SL"
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
            return

        # Check for immediate fresh trigger execution
        fresh = [s for s in all_setups if s.get("is_fresh_trigger")]
        if fresh and not self.active_position:
            # Check sequential queue
            open_trades = get_open_paper_trades()
            if not open_trades:
                asyncio.create_task(self.execute_apex_entry(fresh[0]))

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
        """Executes a qualified Model 2A trade under strict sequential compounding queue."""
        async with self._order_execution_lock:
            if self.is_kill_switch_active():
                logger.warning("🚨 EMERGENCY KILL SWITCH ACTIVE: Suppressing new trade entry.")
                return

            open_trades = get_open_paper_trades()
            if open_trades:
                return  # Strict sequential trade queue (0 margin contagion)

            symbol = setup["symbol"]
            side = setup["side"].upper()
            now_ts = time.time()

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

            acc = self.get_hermes_account()
            curr_balance = acc["current_balance"]
            if curr_balance < 5.0:
                return

            # Arm 1-hour cooldown immediately so coin cannot re-enter in a rapid loop
            self.trade_cooldowns[symbol] = now_ts + 3600
            set_setting(f"cooldown_{symbol}", str(now_ts + 3600))
            record_sent_alert(alert_key, symbol, side, "ENTRY", setup.get("tap_time", 0), None)

            # 5x Leverage Compounding
            leverage = 5
            margin = round(curr_balance, 2)
            position_size = round(margin * leverage, 2)

            ep = float(setup["entry_price"])
            tp = float(setup["tp_price"])
            soft_sl = float(setup["soft_sl_price"])
            hard_sl = float(setup["hard_sl_price"])
            timeframe = setup.get("interval", "4h")

            trade_record = open_paper_trade(setup)
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

            logger.info(f"🚀 HERMES 3.0 MODEL 2A TRADE OPENED: {symbol} {side} @ {ep} | TP: {tp} | Soft SL: {soft_sl} (Body Close) | Hard SL: {hard_sl}")

            # Send Telegram Alert with Live Chart Image
            try:
                alert_text = (
                    f"👑 <b>HERMES 3.0 MODEL 2A: NEW TRADE EXECUTED</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 <b>Pair</b>: #{symbol} ({timeframe.upper()})\n"
                    f"📈 <b>Action</b>: {'🟢 BUY (LONG)' if side == 'LONG' else '🔴 SELL (SHORT)'}\n"
                    f"🎯 <b>Entry Price</b>: {ep:.6f} (50% Mean Threshold)\n"
                    f"🏆 <b>Take Profit (+15% ROE)</b>: {tp:.6f}\n"
                    f"🛡️ <b>Soft Stop Loss (-7.5% ROE)</b>: {soft_sl:.6f} (Candle Body Close Only!)\n"
                    f"🛑 <b>Hard Circuit Breaker</b>: {hard_sl:.6f} (-3.00% Flash Dump Guard)\n"
                    f"🛡️ <b>Break-Even Armor</b>: Locks Risk-Free at {setup['be_armor_price']:.6f} (+1.50% Spot)\n"
                    f"🕯️ <b>Rejection Wick</b>: {setup.get('wick_ratio_pct', 24.5):.1f}% (Confirmed ≥ 18.0% Absorption)\n"
                    f"⚡ <b>Leverage</b>: {leverage}x Isolated | Margin: ${margin:.2f} USDT\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔬 <i>Wick sweeps below soft SL are absorbed! Position exits only on Bar Close confirmation.</i>"
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
        - Layer 1: +3.00% TP Hit -> Instant Exit
        - Layer 2: +1.50% Spot Move -> Break-Even Armor Lock (SL moved to entry)
        - Layer 3: -3.00% Hard Circuit Breaker -> Instant Emergency Exit
        - Layer 4: Soft -1.50% SL -> Checked ONLY on Candle Body Close!
        """
        open_trades = get_open_paper_trades()
        if not open_trades:
            return

        tickers = await binance_feed.fetch_all_tickers()
        if not tickers:
            return

        for trade in list(open_trades):
            sym = trade["symbol"]
            side = trade["side"].upper()
            entry_price = float(trade["entry_price"])
            tp_price = float(trade["tp_price"])
            soft_sl_price = float(trade["sl_price"])
            hard_sl_price = float(trade.get("hard_sl_price", 0.0) or (entry_price * 0.970 if side == "LONG" else entry_price * 1.030))
            be_locked = bool(trade.get("be_locked", 0))
            trade_id = trade["id"]
            tf = trade.get("timeframe", "4h")

            cur_price = tickers.get(sym)
            if not cur_price or cur_price <= 0:
                continue

            update_paper_trade_mark_price(trade_id, cur_price)

            exit_triggered = None
            exit_price = cur_price

            if side in ("BUY", "LONG"):
                # Break-Even Armor Trigger (+1.50% Spot Gain)
                if not be_locked and cur_price >= entry_price * (1.0 + HERMES_3_BE_TRIGGER_PCT):
                    be_locked = True
                    with get_connection() as conn:
                        conn.execute("UPDATE paper_trades SET be_locked = 1, sl_price = ? WHERE id = ?", (entry_price, trade_id))
                        conn.commit()
                    logger.info(f"🛡️ HERMES 3.0 BE ARMOR ACTIVE: {sym} LONG SL locked at {entry_price} (Risk-Free!)")

                # 1. Take Profit Touch
                if cur_price >= tp_price:
                    exit_triggered = "TP_HIT"
                    exit_price = tp_price
                # 2. Emergency Hard Circuit Breaker Touch (-3.00%)
                elif cur_price <= hard_sl_price:
                    exit_triggered = "EMERGENCY_HARD_SL_HIT"
                    exit_price = hard_sl_price
                # 3. Break-Even Touch if locked
                elif be_locked and cur_price <= entry_price:
                    exit_triggered = "BE_SAVE"
                    exit_price = entry_price
                # 4. Soft SL (-1.50%): Evaluated ONLY on Candle Body Close!
                else:
                    # Fetch latest completed candle to check body close
                    try:
                        k = await binance_feed.fetch_klines(sym, interval=tf, limit=2)
                        if k and len(k) >= 2:
                            last_closed_candle = k[-2]
                            if float(last_closed_candle["close"]) <= soft_sl_price:
                                exit_triggered = "STRUCTURAL_BODY_CLOSE_SL"
                                exit_price = float(last_closed_candle["close"])
                                logger.info(f"🛑 HERMES 3.0 STRUCTURAL BODY CLOSE SL: {sym} LONG closed below {soft_sl_price}")
                    except Exception:
                        pass

            else: # SELL / SHORT
                # Break-Even Armor Trigger (+1.50% Spot Drop)
                if not be_locked and cur_price <= entry_price * (1.0 - HERMES_3_BE_TRIGGER_PCT):
                    be_locked = True
                    with get_connection() as conn:
                        conn.execute("UPDATE paper_trades SET be_locked = 1, sl_price = ? WHERE id = ?", (entry_price, trade_id))
                        conn.commit()
                    logger.info(f"🛡️ HERMES 3.0 BE ARMOR ACTIVE: {sym} SHORT SL locked at {entry_price} (Risk-Free!)")

                # 1. Take Profit Touch
                if cur_price <= tp_price:
                    exit_triggered = "TP_HIT"
                    exit_price = tp_price
                # 2. Emergency Hard Circuit Breaker Touch (-3.00%)
                elif cur_price >= hard_sl_price:
                    exit_triggered = "EMERGENCY_HARD_SL_HIT"
                    exit_price = hard_sl_price
                # 3. Break-Even Touch if locked
                elif be_locked and cur_price >= entry_price:
                    exit_triggered = "BE_SAVE"
                    exit_price = entry_price
                # 4. Soft SL (-1.50%): Evaluated ONLY on Candle Body Close!
                else:
                    try:
                        k = await binance_feed.fetch_klines(sym, interval=tf, limit=2)
                        if k and len(k) >= 2:
                            last_closed_candle = k[-2]
                            if float(last_closed_candle["close"]) >= soft_sl_price:
                                exit_triggered = "STRUCTURAL_BODY_CLOSE_SL"
                                exit_price = float(last_closed_candle["close"])
                                logger.info(f"🛑 HERMES 3.0 STRUCTURAL BODY CLOSE SL: {sym} SHORT closed above {soft_sl_price}")
                    except Exception:
                        pass

            if exit_triggered:
                await self.resolve_trade_exit(trade, exit_triggered, exit_price)

    async def resolve_trade_exit(self, trade: Dict[str, Any], outcome: str, exit_price: float):
        """Resolves trade exit, compounds balance, and dispatches alert."""
        trade_id = trade["id"]
        sym = trade["symbol"]
        side = trade["side"].upper()
        entry_price = float(trade["entry_price"])
        margin = float(trade["margin"])
        leverage = int(trade["leverage"])

        if side in ("BUY", "LONG"):
            pnl_pct = (exit_price - entry_price) / entry_price * leverage
        else:
            pnl_pct = (entry_price - exit_price) / entry_price * leverage

        pnl_usdt = round(margin * pnl_pct, 2)
        close_time_ms = int(time.time() * 1000)

        with get_connection() as conn:
            conn.execute("""
            UPDATE paper_trades SET
                exit_price = ?,
                closed_at = ?,
                realized_pnl = ?,
                pnl_pct = ?,
                status = 'CLOSED',
                exit_reason = ?
            WHERE id = ?
            """, (exit_price, close_time_ms, pnl_usdt, pnl_pct * 100.0, outcome, trade_id))

            # Update paper account compounding balance
            acc = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()
            curr_b = float(acc["current_balance"])
            new_b = max(5.0, round(curr_b + pnl_usdt, 2))

            win_inc = 1 if outcome == "TP_HIT" else 0
            loss_inc = 1 if outcome in ("STRUCTURAL_BODY_CLOSE_SL", "EMERGENCY_HARD_SL_HIT") else 0

            conn.execute("""
            UPDATE paper_account SET
                current_balance = ?,
                total_pnl = total_pnl + ?,
                win_count = win_count + ?,
                loss_count = loss_count + ?
            WHERE id = 1
            """, (new_b, pnl_usdt, win_inc, loss_inc))
            conn.commit()

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
        logger.info(f"🏁 HERMES 3.0 TRADE CLOSED: {sym} {outcome} | PnL: ${pnl_usdt:+.2f} USDT ({pnl_pct*100:+.2f}%) | New Balance: ${new_b:.2f}")

        # Send Telegram notification
        try:
            tg_text = (
                f"{'🏆' if outcome == 'TP_HIT' else ('🛡️' if outcome == 'BE_SAVE' else '🛑')} "
                f"<b>HERMES 3.0 MODEL 2A: POSITION CLOSED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🪙 <b>Pair</b>: #{sym}\n"
                f"📋 <b>Result</b>: <b>{outcome}</b>\n"
                f"💵 <b>Realized PnL</b>: <b>{pnl_usdt:+.2f} USDT ({pnl_pct*100:+.2f}%)</b>\n"
                f"🚪 <b>Exit Price</b>: {exit_price:.6f}\n"
                f"💰 <b>Updated Compounding Equity</b>: <b>${new_b:.2f} USDT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 <i>Hermes 3.0 Model 2A Scanning 24/7 for next setup.</i>"
            )
            await telegram_service.send_raw_message(tg_text)
        except Exception as e:
            logger.warning(f"Telegram exit alert error: {e}")

    async def start(self):
        """Starts the 24/7 autonomous live loop for Model 2A."""
        self.is_running = True
        logger.info("👑 HERMES 3.0 MODEL 2A LIVE ENGINE ACTIVATED (24/7 AUTONOMOUS)")
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

            await asyncio.sleep(self.tick_interval_seconds)

    def stop(self):
        self.is_running = False

hermes30_live_engine = Hermes30Model2ALiveEngine()
hermes2_apex_engine = hermes30_live_engine
hermes35_live_engine = hermes30_live_engine
hermes35_engine = hermes30_live_engine
