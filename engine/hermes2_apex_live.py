"""
HERMES 2.0 APEX: 24/7 Autonomous Live Streaming Forward-Test Engine
=====================================================================
Integrates the Unified Master Strategy Blueprint into the live cloud platform.
- Scans Top-22 Champion Crypto Assets across 1H and 4H timeframes.
- Enforces the 4 Sentry Guardians:
    1. Sentry 1 (Macro BTC Causal Brake): Prior 4H BTC >= 2.0% dump/pump veto.
    2. Sentry 2 (Institutional Floor): >= 5.0% Displacement wave + FVG footprint.
    3. Sentry 3 (Liquidity Sweep): IDM swept + >= 18% wick absorption + 50% MT.
    4. Sentry 4 (Freshness Guard): Retest tap strictly <= 28 bars.
- Autonomous Geometric Compounding:
    - Starting Capital: $50.00 USDT
    - Target Milestone: $2,000.00 USDT
    - Isolated 5x Perpetual Futures simulated leverage.
    - 85% net profit reinvested / 15% Cold Storage Vault stashed.
    - Strict 1-Trade Sequential Queue (Zero margin contagion).
- Real-Time Broadcast:
    - Instant Telegram alerts to @SMC_V17_Trigger_Bot.
    - Live WebSocket feeds to https://smc-ai-agent.onrender.com.
"""

import asyncio
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from database.db import (
    get_connection,
    get_paper_account,
    get_open_paper_trades,
    get_setting,
    set_metric
)
from feed.binance_feed import binance_feed
from alerts.telegram_service import telegram_service
from engine.chart_image_generator import render_smc_chart_image

logger = logging.getLogger("Hermes2ApexLive")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

IST = timezone(timedelta(hours=5, minutes=30))

class Hermes2ApexLiveEngine:
    def __init__(self):
        self.is_running = False
        self.scan_interval_seconds = 180  # Scan heavy structure every 3 minutes
        self.tick_interval_seconds = 5    # Real-time tap watchdog & exit monitor every 5 seconds
        self.last_scan_time = 0
        self.last_btc_bias = {"bias": "NEUTRAL", "pct": 0.0, "time": 0}
        self.active_position: Optional[Dict[str, Any]] = None
        self.detected_setups: List[Dict[str, Any]] = []
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
        """Ensures database tables and Hermes 2.0 Apex columns exist."""
        with get_connection() as conn:
            # Check paper_account columns
            cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_account)").fetchall()]
            if "vault_balance" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN vault_balance REAL DEFAULT 0.0")
            if "milestone_target" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN milestone_target REAL DEFAULT 2000.0")
            if "mode" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN mode TEXT DEFAULT 'HERMES_2.0_APEX'")

            # Check paper_trades columns
            trade_cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_trades)").fetchall()]
            if "timeframe" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN timeframe TEXT DEFAULT '1h'")
            if "hard_sl_price" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN hard_sl_price REAL DEFAULT 0.0")
            if "vault_stashed_usdt" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN vault_stashed_usdt REAL DEFAULT 0.0")
            if "sentry_reasons" not in trade_cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN sentry_reasons TEXT DEFAULT ''")

            # Seed starting paper balance to $50.00 if brand new or zero
            acc = conn.execute("SELECT * FROM paper_account WHERE id = 1").fetchone()
            if not acc:
                conn.execute("""
                INSERT OR IGNORE INTO paper_account 
                (id, initial_balance, current_balance, vault_balance, total_pnl, win_count, loss_count, milestone_target, mode)
                VALUES (1, 50.0, 50.0, 0.0, 0.0, 0, 0, 2000.0, 'HERMES_2.0_APEX');
                """)
            elif acc["current_balance"] <= 0.0 and acc["win_count"] == 0 and acc["loss_count"] == 0:
                conn.execute("""
                UPDATE paper_account SET
                    initial_balance = 50.0,
                    current_balance = 50.0,
                    vault_balance = 0.0,
                    total_pnl = 0.0,
                    win_count = 0,
                    loss_count = 0,
                    milestone_target = 2000.0,
                    mode = 'HERMES_2.0_APEX'
                WHERE id = 1
                """)
            conn.commit()

    def get_hermes_account(self) -> Dict[str, Any]:
        """Retrieves live Hermes 2.0 Apex account state with compounding metrics."""
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
            acc["mode"] = "HERMES_2.0_APEX"
            return acc

    async def evaluate_btc_macro_sentry(self) -> Dict[str, Any]:
        """
        Sentry 1: Evaluates the finalized prior 4H BTC bar for macro cascade risk.
        Vetoes longs if BTC dumped >= 2.0%.
        Vetoes shorts if BTC pumped >= 2.0%.
        """
        try:
            btc_candles = await binance_feed.fetch_klines("BTCUSDT", interval="4h", limit=10)
            if len(btc_candles) >= 2:
                # The last candle in list is current in-progress candle; previous candle is closed.
                closed_bar = btc_candles[-2]
                o = closed_bar["open"]
                c = closed_bar["close"]
                change_pct = (c - o) / o * 100.0
                dump_pct = (o - c) / o * 100.0
                pump_pct = (c - o) / o * 100.0

                long_veto = dump_pct >= 2.0
                short_veto = pump_pct >= 2.0

                bias = "NEUTRAL"
                if long_veto:
                    bias = "DUMP_VETO_ACTIVE"
                elif short_veto:
                    bias = "PUMP_VETO_ACTIVE"

                self.last_btc_bias = {
                    "bias": bias,
                    "change_pct": round(change_pct, 2),
                    "long_veto": long_veto,
                    "short_veto": short_veto,
                    "bar_time": closed_bar["time"],
                    "close_price": c
                }
                return self.last_btc_bias
        except Exception as e:
            logger.warning(f"BTC macro sentry check error: {e}")
        return {"bias": "NEUTRAL", "change_pct": 0.0, "long_veto": False, "short_veto": False}

    def detect_apex_setups_on_candles(
        self,
        symbol: str,
        candles: List[Dict[str, Any]],
        interval: str,
        btc_sentry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Pure algorithmic implementation of HERMES 2.0 APEX on live candle series.
        Applies Sentry 2 (Displacement >= 5%), Sentry 3 (IDM Sweep + Wick Rejection >= 18% + 50% MT),
        Sentry 4 (Tap window <= 28 bars), and Sentry 1 (Macro BTC Veto).
        """
        n = len(candles)
        if n < 40:
            return []

        tp_pct = 0.022 if interval == "1h" else 0.028
        soft_sl_pct = 0.025 if interval == "1h" else 0.028
        hard_sl_pct = 0.036 if interval == "1h" else 0.038
        min_displacement = 0.050
        max_tap_window = 28

        setups = []

        # We look back in the most recent 35 bars
        search_start = max(20, n - 40)
        for i in range(search_start, n - 2):
            # -------------------------------------------------------------
            # 1. BULLISH SETUP DETECTION
            # -------------------------------------------------------------
            if not btc_sentry.get("long_veto", False):
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= min_displacement:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid

                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False

                                if has_fvg:
                                    tapped_found = False
                                    # Check bars from high_idx to current candle
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        if tap_c["low"] <= dec_top * 1.0005:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            # Sentry 3: IDM Sweep + >=18% Wick Absorption + 50% MT
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                age = n - 1 - t
                                                is_fresh_trigger = (age <= 1)
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "LONG",
                                                    "interval": interval,
                                                    "entry_price": dec_top,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "tp_price": dec_top * (1.0 + tp_pct),
                                                    "soft_sl_price": dec_top * (1.0 - soft_sl_pct),
                                                    "hard_sl_price": dec_top * (1.0 - hard_sl_pct),
                                                    "tp_pct": tp_pct,
                                                    "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct,
                                                    "displacement_pct": round(gain * 100.0, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100.0, 1),
                                                    "tap_bar_age": age,
                                                    "tap_time": tap_c["time"],
                                                    "is_fresh_trigger": is_fresh_trigger,
                                                    "status": "FRESH_TRIGGERED" if is_fresh_trigger else "CONFIRMED_TAP",
                                                    "sentry_reasons": f"Sentry 1 Clean | Sentry 2 Disp: {gain*100:.1f}% + FVG | Sentry 3 Wick: {w_ratio*100:.1f}% & MT OK | Sentry 4 Fresh: Bar #{t - high_idx}"
                                                })
                                                tapped_found = True
                                            break

                                    if not tapped_found:
                                        bars_since_high = (n - 1) - high_idx
                                        if 1 <= bars_since_high <= max_tap_window:
                                            recent_bars = candles[high_idx + 1:n]
                                            broken = any(b["close"] < dec_bot for b in recent_bars)
                                            if not broken:
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "LONG",
                                                    "interval": interval,
                                                    "entry_price": dec_top,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "tp_price": dec_top * (1.0 + tp_pct),
                                                    "soft_sl_price": dec_top * (1.0 - soft_sl_pct),
                                                    "hard_sl_price": dec_top * (1.0 - hard_sl_pct),
                                                    "tp_pct": tp_pct,
                                                    "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct,
                                                    "displacement_pct": round(gain * 100.0, 2),
                                                    "wick_ratio_pct": 0.0,
                                                    "tap_bar_age": 0,
                                                    "tap_time": candles[-1]["time"],
                                                    "is_fresh_trigger": False,
                                                    "status": "ARMED_WAITING_TAP",
                                                    "sentry_reasons": f"Sentry 1 Clean | Sentry 2 Disp: {gain*100:.1f}% + FVG | Sentry 3 Armed IDM | Sentry 4 Fresh Window: {bars_since_high}/28 Bars"
                                                })

            # -------------------------------------------------------------
            # 2. BEARISH SETUP DETECTION
            # -------------------------------------------------------------
            if not btc_sentry.get("short_veto", False):
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= min_displacement:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid

                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False

                                if has_bear_fvg:
                                    tapped_found = False
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        if tap_c["high"] >= dec_bot * 0.9995:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                age = n - 1 - t
                                                is_fresh_trigger = (age <= 1)
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "SHORT",
                                                    "interval": interval,
                                                    "entry_price": dec_bot,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "tp_price": dec_bot * (1.0 - tp_pct),
                                                    "soft_sl_price": dec_bot * (1.0 + soft_sl_pct),
                                                    "hard_sl_price": dec_bot * (1.0 + hard_sl_pct),
                                                    "tp_pct": tp_pct,
                                                    "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct,
                                                    "displacement_pct": round(drop * 100.0, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100.0, 1),
                                                    "tap_bar_age": age,
                                                    "tap_time": tap_c["time"],
                                                    "is_fresh_trigger": is_fresh_trigger,
                                                    "status": "FRESH_TRIGGERED" if is_fresh_trigger else "CONFIRMED_TAP",
                                                    "sentry_reasons": f"Sentry 1 Clean | Sentry 2 Disp: {drop*100:.1f}% + Bear FVG | Sentry 3 Wick: {w_ratio*100:.1f}% & MT OK | Sentry 4 Fresh: Bar #{t - low_idx}"
                                                })
                                                tapped_found = True
                                            break

                                    if not tapped_found:
                                        bars_since_low = (n - 1) - low_idx
                                        if 1 <= bars_since_low <= max_tap_window:
                                            recent_bars = candles[low_idx + 1:n]
                                            broken = any(b["close"] > dec_top for b in recent_bars)
                                            if not broken:
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "SHORT",
                                                    "interval": interval,
                                                    "entry_price": dec_bot,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "tp_price": dec_bot * (1.0 - tp_pct),
                                                    "soft_sl_price": dec_bot * (1.0 + soft_sl_pct),
                                                    "hard_sl_price": dec_bot * (1.0 + hard_sl_pct),
                                                    "tp_pct": tp_pct,
                                                    "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct,
                                                    "displacement_pct": round(drop * 100.0, 2),
                                                    "wick_ratio_pct": 0.0,
                                                    "tap_bar_age": 0,
                                                    "tap_time": candles[-1]["time"],
                                                    "is_fresh_trigger": False,
                                                    "status": "ARMED_WAITING_TAP",
                                                    "sentry_reasons": f"Sentry 1 Clean | Sentry 2 Disp: {drop*100:.1f}% + Bear FVG | Sentry 3 IDM Level | Sentry 4 Armed Fresh ({bars_since_low}/28 Bars)"
                                                })

        return setups

    async def run_full_champion_scan(self) -> Dict[str, Any]:
        """Scans all Top-22 Champion crypto pairs across 1H and 4H timeframes."""
        scan_start = time.time()
        btc_sentry = await self.evaluate_btc_macro_sentry()

        found_setups: List[Dict[str, Any]] = []

        for sym in TOP_22_CHAMPIONS:
            # Check 1H timeframe
            try:
                klines_1h = await binance_feed.fetch_klines(sym, interval="1h", limit=80)
                if klines_1h and len(klines_1h) >= 40:
                    setups_1h = self.detect_apex_setups_on_candles(sym, klines_1h, "1h", btc_sentry)
                    found_setups.extend(setups_1h)
            except Exception as e:
                logger.debug(f"1H scan error on {sym}: {e}")

            # Check 4H timeframe
            try:
                klines_4h = await binance_feed.fetch_klines(sym, interval="4h", limit=80)
                if klines_4h and len(klines_4h) >= 40:
                    setups_4h = self.detect_apex_setups_on_candles(sym, klines_4h, "4h", btc_sentry)
                    found_setups.extend(setups_4h)
            except Exception as e:
                logger.debug(f"4H scan error on {sym}: {e}")

        self.detected_setups = found_setups
        self.last_scan_time = time.time()
        now_dt = datetime.now(IST)
        now_str = now_dt.strftime("%d %b %Y • %I:%M:%S %p IST")
        set_metric("hermes_last_scan", now_str)
        set_metric("hermes_setups_detected", str(len(found_setups)))

        # If no active position, check if any fresh setup should be entered
        open_trades = get_open_paper_trades()
        if not open_trades and found_setups:
            # Strictly enter ONLY fresh setups (tapped within latest candle, age <= 1)
            fresh = [s for s in found_setups if s.get("is_fresh_trigger")]
            if fresh:
                target_setup = fresh[0]
                await self.execute_apex_entry(target_setup)

        await self.broadcast("HERMES_SCAN_COMPLETE", {
            "timestamp": now_str,
            "setups_count": len(found_setups),
            "btc_bias": btc_sentry.get("bias", "NEUTRAL"),
            "btc_change": btc_sentry.get("change_pct", 0.0),
            "duration": round(time.time() - scan_start, 2)
        })

        return {
            "status": "ok",
            "setups_found": len(found_setups),
            "btc_bias": btc_sentry,
            "duration_s": round(time.time() - scan_start, 2)
        }

    async def execute_apex_entry(self, setup: Dict[str, Any]):
        """Executes a 5x Isolated Simulated Compounding position on a verified setup."""
        # Check if already in an open trade
        open_trades = get_open_paper_trades()
        if open_trades:
            return

        sym = setup["symbol"]
        entry_price = float(setup["entry_price"])

        # Live Proximity Check: Price must be within the Order Block zone or 0.50% range
        cur_price = entry_price
        try:
            tickers = await binance_feed.fetch_all_tickers()
            cur_p = tickers.get(sym)
            if cur_p and cur_p > 0:
                cur_price = cur_p
                ob_high = float(setup.get("ob_high", entry_price))
                ob_low = float(setup.get("ob_low", entry_price))
                diff_pct = abs(cur_price - entry_price) / entry_price * 100.0
                in_zone = (ob_low * 0.995) <= cur_price <= (ob_high * 1.005)
                if diff_pct > 0.50 and not in_zone:
                    logger.info(f"Skipping entry on {sym}: live price {cur_price} is {diff_pct:.2f}% away from entry limit {entry_price}")
                    return
        except Exception:
            pass

        acc = self.get_hermes_account()
        current_balance = float(acc.get("current_balance", 50.0) or 50.0)
        if current_balance < 1.0:
            current_balance = 50.0

        # Isolated 5x Leverage: 100% of available compounding margin
        margin = current_balance
        position_size = round(margin * 5.0, 2)
        now_ms = int(time.time() * 1000)

        sym = setup["symbol"]
        side = setup["side"]
        tf = setup["interval"]
        entry_price = cur_price

        tp_pct = float(setup.get("tp_pct", 0.028 if tf == "4h" else 0.022))
        soft_sl_pct = float(setup.get("soft_sl_pct", 0.028 if tf == "4h" else 0.025))
        hard_sl_pct = float(setup.get("hard_sl_pct", 0.038 if tf == "4h" else 0.036))

        if side in ("BUY", "LONG"):
            tp_price = round(entry_price * (1.0 + tp_pct), 6)
            sl_price = round(entry_price * (1.0 - soft_sl_pct), 6)
            hard_sl_price = round(entry_price * (1.0 - hard_sl_pct), 6)
        else:
            tp_price = round(entry_price * (1.0 - tp_pct), 6)
            sl_price = round(entry_price * (1.0 + soft_sl_pct), 6)
            hard_sl_price = round(entry_price * (1.0 + hard_sl_pct), 6)

        sentry_reasons = setup.get("sentry_reasons", "")

        with get_connection() as conn:
            cursor = conn.execute("""
            INSERT INTO paper_trades (
                symbol, side, entry_price, position_size_usdt,
                tp_price, sl_price, hard_sl_price, timeframe,
                status, entry_time, sentry_reasons
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
            """, (
                sym, side, entry_price, position_size,
                tp_price, sl_price, hard_sl_price, tf,
                now_ms, sentry_reasons
            ))
            conn.commit()
            trade_id = cursor.lastrowid

        trade_obj = {
            "id": trade_id,
            "symbol": sym,
            "side": side,
            "timeframe": tf,
            "entry_price": entry_price,
            "position_size_usdt": position_size,
            "margin_usdt": margin,
            "tp_price": tp_price,
            "sl_price": sl_price,
            "hard_sl_price": hard_sl_price,
            "status": "OPEN",
            "entry_time": now_ms,
            "sentry_reasons": sentry_reasons
        }
        self.active_position = trade_obj

        # Send Telegram Announcement to User's Bot WITH LIVE CANDLESTICK CHART
        try:
            tg_msg = (
                f"👑 <b>HERMES 2.0 APEX: NEW POSITION ENTERED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 <b>Pair</b>: <code>{sym}</code> (5x Isolated Perpetual)\n"
                f"⚡ <b>Action</b>: <b>{side}</b> | ⏱️ <b>Timeframe</b>: {tf.upper()}\n"
                f"💵 <b>Entry Limit</b>: ${entry_price:,.4f}\n"
                f"🎯 <b>Target TP (+{setup['tp_pct']*100:.1f}%)</b>: ${tp_price:,.4f} (+{setup['tp_pct']*500:.1f}% ROE)\n"
                f"🛡️ <b>Soft SL (-{setup['soft_sl_pct']*100:.1f}%)</b>: ${sl_price:,.4f} (-{setup['soft_sl_pct']*500:.1f}% ROE)\n"
                f"🚨 <b>Emergency Hard SL (-{setup['hard_sl_pct']*100:.1f}%)</b>: ${hard_sl_price:,.4f}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Active Margin</b>: ${margin:.2f} USDT (100% Compounding Queue)\n"
                f"📦 <b>Effective Position</b>: ${position_size:.2f} USDT (5x Isolated)\n"
                f"🔒 <b>Vault Reserve</b>: ${acc.get('vault_balance', 0.0):.2f} USDT\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🛡️ <b>4 SENTRIES VERIFIED</b>:\n"
                f"• {sentry_reasons}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚀 <i>24/7 Cloud Simulated Forward-Test: $50 ➔ $2,000 Milestone</i>"
            )

            # Generate chart with Entry, TP, and SL lines
            chart_sent = False
            try:
                candles = await binance_feed.fetch_klines(sym, interval=tf, limit=50)
                if candles:
                    zone_dict = {
                        "symbol": sym,
                        "side": side,
                        "entry_price": entry_price,
                        "tp_price": tp_price,
                        "sl_price": sl_price,
                        "ob_high": setup.get("ob_high", entry_price),
                        "ob_low": setup.get("ob_low", entry_price)
                    }
                    chart_bytes = render_smc_chart_image(sym, candles, zone_dict, timeframe=tf.upper())
                    resp = await telegram_service.send_photo(chart_bytes, tg_msg)
                    if resp and resp.get("ok"):
                        chart_sent = True
            except Exception as ce:
                logger.warning(f"Failed to render/send chart image: {ce}")

            if not chart_sent:
                await telegram_service.send_raw_message(tg_msg)
        except Exception as e:
            logger.warning(f"Telegram alert error on entry: {e}")

        await self.broadcast("HERMES_POSITION_OPENED", trade_obj)

    async def check_live_price_and_exits(self):
        """Monitors live Binance tickers against active position every few seconds, and triggers real-time Order Block taps."""
        open_trades = get_open_paper_trades()
        if open_trades:
            trade = open_trades[0]
            sym = trade["symbol"]
            side = trade["side"].upper()
            entry_price = float(trade["entry_price"])
            tp_price = float(trade["tp_price"])
            sl_price = float(trade["sl_price"])
            hard_sl_price = float(trade.get("hard_sl_price", 0.0) or (entry_price * 0.964 if side in ("BUY", "LONG") else entry_price * 1.036))
            pos_size = float(trade["position_size_usdt"])
            trade_id = trade["id"]

            tickers = await binance_feed.fetch_all_tickers()
            if tickers:
                self.last_tickers = tickers
                self.last_ticker_time = time.time()
                try:
                    await self.broadcast("TICKER_UPDATE", {"tickers": tickers})
                except Exception:
                    pass
            cur_price = tickers.get(sym) if tickers else None
            if not cur_price or cur_price <= 0:
                return

            exit_triggered = None
            exit_price = cur_price

            if side in ("BUY", "LONG"):
                if cur_price >= tp_price:
                    exit_triggered = "TP_HIT"
                    exit_price = tp_price
                elif cur_price <= hard_sl_price:
                    exit_triggered = "SL_HIT"
                    exit_price = hard_sl_price
            else: # SELL / SHORT
                if cur_price <= tp_price:
                    exit_triggered = "TP_HIT"
                    exit_price = tp_price
                elif cur_price >= hard_sl_price:
                    exit_triggered = "SL_HIT"
                    exit_price = hard_sl_price

            if exit_triggered:
                await self.resolve_trade_exit(trade, exit_triggered, exit_price)
            return

        # -------------------------------------------------------------
        # REAL-TIME TAP WATCHDOG (RUNS EVERY 5 SECONDS)
        # Evaluates armed setups against live Binance tickers between macro scans.
        # If price taps an Order Block zone right now, enters immediately!
        # -------------------------------------------------------------
        self.active_position = None
        if not self.detected_setups:
            return

        btc_sentry = self.last_btc_bias or {}

        try:
            tickers = await binance_feed.fetch_all_tickers()
            if not tickers:
                return
            self.last_tickers = tickers
            self.last_ticker_time = time.time()
            try:
                await self.broadcast("TICKER_UPDATE", {"tickers": tickers})
            except Exception:
                pass

            for setup in self.detected_setups:
                sym = setup.get("symbol")
                cur_price = tickers.get(sym)
                if not cur_price or cur_price <= 0:
                    continue

                side = setup.get("side", "LONG")
                if side in ("BUY", "LONG") and btc_sentry.get("long_veto"):
                    continue
                if side in ("SELL", "SHORT") and btc_sentry.get("short_veto"):
                    continue

                entry_p = float(setup["entry_price"])
                ob_high = float(setup.get("ob_high", entry_p))
                ob_low = float(setup.get("ob_low", entry_p))
                is_fresh = setup.get("is_fresh_trigger", False)

                tapped = False
                if side in ("BUY", "LONG"):
                    # Price has touched or dipped into the top of the Order Block zone
                    if (cur_price <= ob_high * 1.002) and (cur_price >= ob_low * 0.995):
                        tapped = True
                else: # SHORT / SELL
                    # Price has touched or pushed up into the bottom of the Order Block zone
                    if (cur_price >= ob_low * 0.998) and (cur_price <= ob_high * 1.005):
                        tapped = True

                diff_pct = abs(cur_price - entry_p) / entry_p * 100.0
                if tapped or (is_fresh and diff_pct <= 0.40):
                    logger.info(f"⚡ REAL-TIME TAP WATCHDOG TRIGGERED on {sym} ({side})! Live Price: {cur_price} tapped OB [{ob_low}, {ob_high}] (TF: {setup.get('interval')})")
                    await self.execute_apex_entry(setup)
                    break # Enforce strict 1-trade sequential compounding queue
        except Exception as e:
            logger.debug(f"Real-time tap watchdog error: {e}")

    async def resolve_trade_exit(self, trade: Dict[str, Any], outcome: str, exit_price: float):
        """Resolves trade exit, calculates fees, vault stashing (15%), and compounding reinvestment (85%)."""
        now_ms = int(time.time() * 1000)
        side = trade["side"].upper()
        entry_price = float(trade["entry_price"])
        pos_size = float(trade["position_size_usdt"])
        trade_id = trade["id"]
        sym = trade["symbol"]
        roundtrip_fee = pos_size * 0.0016 # 0.16% roundtrip exchange fee

        if side in ("BUY", "LONG"):
            gross_pnl_pct = (exit_price - entry_price) / entry_price * 100.0
        else:
            gross_pnl_pct = (entry_price - exit_price) / entry_price * 100.0

        gross_pnl_usdt = pos_size * (gross_pnl_pct / 100.0)
        net_pnl_usdt = gross_pnl_usdt - roundtrip_fee

        acc = self.get_hermes_account()
        current_balance = float(acc.get("current_balance", 50.0) or 50.0)
        vault_balance = float(acc.get("vault_balance", 0.0) or 0.0)
        win_count = int(acc.get("win_count", 0) or 0)
        loss_count = int(acc.get("loss_count", 0) or 0)
        total_pnl = float(acc.get("total_pnl", 0.0) or 0.0)

        vault_stash = 0.0
        if outcome == "TP_HIT" and net_pnl_usdt > 0:
            win_count += 1
            # 15% to Cold Storage Vault, 85% to Active Compounding Margin
            vault_stash = round(net_pnl_usdt * 0.15, 2)
            margin_reinvest = round(net_pnl_usdt * 0.85, 2)
            new_balance = round(current_balance + margin_reinvest, 2)
            new_vault = round(vault_balance + vault_stash, 2)
        else:
            loss_count += 1
            new_balance = round(max(1.0, current_balance + net_pnl_usdt), 2)
            new_vault = vault_balance # Cold storage vault remains 100% untouched!

        new_total_pnl = round(total_pnl + net_pnl_usdt, 2)

        with get_connection() as conn:
            conn.execute("""
            UPDATE paper_trades SET
                status = ?, exit_time = ?, exit_price = ?,
                pnl_usdt = ?, pnl_pct = ?, vault_stashed_usdt = ?
            WHERE id = ?
            """, (outcome, now_ms, exit_price, round(net_pnl_usdt, 2), round(gross_pnl_pct * 5.0, 2), vault_stash, trade_id))

            conn.execute("""
            UPDATE paper_account SET
                current_balance = ?,
                vault_balance = ?,
                total_pnl = ?,
                win_count = ?,
                loss_count = ?
            WHERE id = 1
            """, (new_balance, new_vault, new_total_pnl, win_count, loss_count))
            conn.commit()

        self.active_position = None
        total_equity = new_balance + new_vault
        completed = win_count + loss_count
        win_rate = round(win_count / completed * 100, 1) if completed > 0 else 0.0
        progress_pct = round(min(100.0, total_equity / 2000.0 * 100), 1)

        # Send Telegram Announcement to User's Bot
        try:
            if outcome == "TP_HIT":
                tg_msg = (
                    f"🎉 <b>HERMES 2.0 APEX: TAKE PROFIT HIT!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏆 <b>Asset</b>: <code>{sym}</code> {side}\n"
                    f"💵 <b>Exit Price</b>: ${exit_price:,.4f}\n"
                    f"📈 <b>Net Realized PnL</b>: <b>+${net_pnl_usdt:,.2f} USDT</b> (+{gross_pnl_pct * 5.0:.1f}% ROE)\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏦 <b>COMPOUNDING SPLIT (85 / 15)</b>:\n"
                    f"• 💰 <b>Reinvested to Margin (85%)</b>: +${net_pnl_usdt * 0.85:,.2f} USDT\n"
                    f"• 🔒 <b>Stashed to Vault Reserve (15%)</b>: +${vault_stash:,.2f} USDT\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>UPDATED PORTFOLIO LEDGER</b>:\n"
                    f"• 🚀 <b>Active Compounding Balance</b>: ${new_balance:,.2f} USDT\n"
                    f"• 🛡️ <b>Cold Storage Vault Total</b>: ${new_vault:,.2f} USDT\n"
                    f"• 🎯 <b>Total Portfolio Equity</b>: ${total_equity:,.2f} USDT\n"
                    f"• 🏁 <b>Goal Progress ($2,000 Milestone)</b>: <b>{progress_pct}%</b>\n"
                    f"• 📊 <b>Lifetime Win Rate</b>: <b>{win_rate}%</b> ({win_count}W / {loss_count}L)\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👑 <i>Hermes 2.0 Apex Autonomous Quant Engine</i>"
                )
            else:
                tg_msg = (
                    f"🛑 <b>HERMES 2.0 APEX: STOP LOSS HIT</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ <b>Asset</b>: <code>{sym}</code> {side}\n"
                    f"💵 <b>Exit Price</b>: ${exit_price:,.4f}\n"
                    f"📉 <b>Realized Net Loss</b>: <b>-${abs(net_pnl_usdt):,.2f} USDT</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>CAPITAL INTEGRITY</b>:\n"
                    f"• 🚀 <b>Remaining Margin</b>: ${new_balance:,.2f} USDT\n"
                    f"• 🛡️ <b>Cold Storage Vault (Preserved)</b>: ${new_vault:,.2f} USDT\n"
                    f"• 🎯 <b>Total Portfolio Equity</b>: ${total_equity:,.2f} USDT\n"
                    f"• 📊 <b>Win Rate</b>: <b>{win_rate}%</b> ({win_count}W / {loss_count}L)\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👑 <i>Hermes 2.0 Apex Autonomous Quant Engine</i>"
                )

            # Send exit chart photo if available
            chart_sent = False
            try:
                tf = trade.get("timeframe", "4h")
                candles = await binance_feed.fetch_klines(sym, interval=tf, limit=50)
                if candles:
                    zone_dict = {
                        "symbol": sym,
                        "side": side,
                        "entry_price": entry_price,
                        "tp_price": float(trade.get("tp_price", exit_price)),
                        "sl_price": float(trade.get("sl_price", exit_price)),
                        "ob_high": max(entry_price, exit_price),
                        "ob_low": min(entry_price, exit_price)
                    }
                    chart_bytes = render_smc_chart_image(sym, candles, zone_dict, timeframe=tf.upper())
                    resp = await telegram_service.send_photo(chart_bytes, tg_msg)
                    if resp and resp.get("ok"):
                        chart_sent = True
            except Exception as ce:
                logger.warning(f"Failed to render/send exit chart photo: {ce}")

            if not chart_sent:
                await telegram_service.send_raw_message(tg_msg)
        except Exception as e:
            logger.warning(f"Telegram exit alert error: {e}")

        await self.broadcast("HERMES_POSITION_CLOSED", {
            "symbol": sym,
            "outcome": outcome,
            "net_pnl": net_pnl_usdt,
            "new_balance": new_balance,
            "vault_balance": new_vault,
            "win_rate": win_rate
        })

    async def start(self):
        """Autonomous 24/7 background loop running on the cloud server."""
        self.is_running = True
        logger.info("👑 HERMES 2.0 APEX Live Streaming Simulated Engine Started 24/7.")
        set_metric("hermes_status", "ACTIVE_24_7")

        # Enforce 1-Trade Sequential Queue & Restore Active Position
        try:
            with get_connection() as conn:
                open_rows = conn.execute("SELECT * FROM paper_trades WHERE status = 'OPEN' ORDER BY id DESC").fetchall()
                if open_rows:
                    self.active_position = dict(open_rows[0])
                    logger.info(f"👑 Restored active Hermes position: {self.active_position.get('symbol')} {self.active_position.get('side')}")
                    if len(open_rows) > 1:
                        now_ms = int(time.time() * 1000)
                        for extra in open_rows[1:]:
                            conn.execute("UPDATE paper_trades SET status = 'CLOSED_LEGACY', exit_time = ?, exit_price = ? WHERE id = ?",
                                         (now_ms, extra['entry_price'], extra['id']))
                        conn.commit()
                        logger.info(f"🧹 Cleaned up {len(open_rows)-1} extra legacy open trades to strictly maintain 1-Trade Sequential Queue.")
        except Exception as e:
            logger.warning(f"Error restoring active position on boot: {e}")

        # Initial Telegram Heartbeat on Boot
        try:
            acc = self.get_hermes_account()
            boot_msg = (
                f"👑 <b>HERMES 2.0 APEX: 24/7 CLOUD ROBOT DEPLOYED & ONLINE!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌐 <b>Host</b>: 100% Free Render Cloud Server (24/7 Autonomous)\n"
                f"🎯 <b>Compounding Mission</b>: $50.00 ➔ $2,000.00 USDT Milestone\n"
                f"⚡ <b>Leverage</b>: 5x Isolated Perpetual Futures\n"
                f"🛡️ <b>Armor</b>: 4 Sentry Guardians Active (Macro BTC Brake + Institutional Floor 5% + IDM Sweep + Freshness 28-Bar)\n"
                f"📊 <b>Starting Compounding Margin</b>: ${acc['current_balance']:.2f} USDT\n"
                f"🔒 <b>Cold Storage Vault</b>: ${acc['vault_balance']:.2f} USDT\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📡 <b>Scanning</b>: Top-22 Champion Crypto Pairs (1H & 4H)\n"
                f"💻 <b>Live Terminal</b>: https://smc-ai-agent.onrender.com\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚀 <i>Your computer can be turned OFF now. Hermes 2.0 Apex operates 24/7 autonomously in the cloud!</i>"
            )
            await telegram_service.send_raw_message(boot_msg)
        except Exception as e:
            logger.warning(f"Boot notification error: {e}")

        scan_timer = 0
        while self.is_running:
            try:
                # 1. Price tick & exit monitor (runs every 8s)
                await self.check_live_price_and_exits()

                # 2. Structure scan (runs every 3 minutes)
                scan_timer += self.tick_interval_seconds
                if scan_timer >= self.scan_interval_seconds:
                    scan_timer = 0
                    await self.run_full_champion_scan()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Hermes Apex loop: {e}")

            await asyncio.sleep(self.tick_interval_seconds)

    def stop(self):
        self.is_running = False

hermes2_apex_engine = Hermes2ApexLiveEngine()
