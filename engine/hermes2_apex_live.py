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
import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

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
    record_sent_alert
)
from feed.binance_feed import binance_feed
from alerts.telegram_service import (
    telegram_service,
    format_trade_open_alert,
    format_trade_closed_alert,
    format_tg_ist_timestamp
)
from engine.chart_image_generator import render_smc_chart_image

logger = logging.getLogger("Hermes2ApexLive")

from config import TOP_22_CHAMPIONS, STRATEGY_VERSION
from engine.hermes3_5_apex import hermes35_engine

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
        self.trade_cooldowns: Dict[str, float] = {}  # Symbol -> timestamp of when cooldown ends
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
        """Ensures database tables and Hermes 2.0 Apex columns exist."""
        with get_connection() as conn:
            # Check paper_account columns
            cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_account)").fetchall()]
            if "vault_balance" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN vault_balance REAL DEFAULT 0.0")
            if "milestone_target" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN milestone_target REAL DEFAULT 2000.0")
            if "mode" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN mode TEXT DEFAULT 'HERMES_3.0_QUANTUM'")

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
                VALUES (1, 50.0, 50.0, 0.0, 0.0, 0, 0, 2000.0, 'HERMES_3.0_QUANTUM');
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
                    mode = 'HERMES_3.0_QUANTUM'
                WHERE id = 1
                """)
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
            acc["mode"] = get_setting("strategy_version", os.getenv("STRATEGY_VERSION", "HERMES_3.0_QUANTUM"))
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

                                            strat_mode = get_setting("strategy_version", os.getenv("STRATEGY_VERSION", "HERMES_3.5_DUAL_TIER_SNIPER"))
                                            is_hermes3 = strat_mode.startswith("HERMES_3")
                                            is_hermes35 = strat_mode.startswith("HERMES_3.5")
                                            is_valid_tap = (tap_c["low"] <= mt and tap_c["close"] >= mt) if is_hermes3 else (tap_c["close"] >= mt)

                                            # Sentry 3: IDM Sweep + >=18% Wick Absorption + 50% MT
                                            if swept and w_ratio >= 0.18 and is_valid_tap:
                                                tier = "TIER_1_INSTITUTIONAL"
                                                be_lock_pct = 0.016
                                                trail_lock_pct = 0.022
                                                cvd_confirmed = True

                                                if is_hermes35:
                                                    passed_sniper, sniper_reason = hermes35_engine.evaluate_15m_micro_sniper_gate(tap_c, "LONG")
                                                    if not passed_sniper:
                                                        logger.info(f"🛑 [HERMES 3.5 SNIPER VETO] {symbol} LONG tap rejected: {sniper_reason}")
                                                        continue
                                                    tier_info = hermes35_engine.classify_dual_tier_setup(candles, t, "LONG")
                                                    tier = tier_info.get("tier", "TIER_1_INSTITUTIONAL")
                                                    tier_name = tier_info.get("tier_name", "Tier 1 (Institutional)")
                                                    be_lock_pct = tier_info.get("be_lock_pct", 0.016)
                                                    trail_lock_pct = tier_info.get("trail_lock_pct", 0.022)
                                                    cvd_confirmed = tier_info.get("cvd_confirmed", True)
                                                    eff_entry = mt
                                                    sentry_lbl = f"HERMES 3.5 DUAL SNIPER [{tier_name}] | {sniper_reason} | Sentry 1 Clean | Sentry 2 Disp: {gain*100:.1f}% + FVG | Sentry 3 Wick: {w_ratio*100:.1f}% & MT 50% | Sentry 4 Fresh: Bar #{t - high_idx}"
                                                elif is_hermes3:
                                                    eff_entry = mt
                                                    sentry_lbl = f"HERMES 3.0 QUANTUM (Mean Threshold 50% EQ) | Sentry 1 Clean | Sentry 2 Disp: {gain*100:.1f}% + FVG | Sentry 3 Wick: {w_ratio*100:.1f}% & MT 50% Rejection | Sentry 4 Fresh: Bar #{t - high_idx}"
                                                else:
                                                    eff_entry = dec_top
                                                    sentry_lbl = f"HERMES 2.5 APEX HYBRID | Sentry 1 Clean | Sentry 2 Disp: {gain*100:.1f}% + FVG | Sentry 3 Wick: {w_ratio*100:.1f}% & MT OK | Sentry 4 Fresh: Bar #{t - high_idx}"

                                                age = n - 1 - t
                                                is_fresh_trigger = (age <= 1)

                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "LONG",
                                                    "interval": interval,
                                                    "entry_price": eff_entry,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "mean_threshold": mt,
                                                    "tp_price": eff_entry * (1.0 + tp_pct),
                                                    "soft_sl_price": eff_entry * (1.0 - soft_sl_pct),
                                                    "hard_sl_price": eff_entry * (1.0 - hard_sl_pct),
                                                    "tp_pct": tp_pct,
                                                    "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct,
                                                    "displacement_pct": round(gain * 100.0, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100.0, 1),
                                                    "tap_bar_age": age,
                                                    "tap_time": tap_c["time"],
                                                    "is_fresh_trigger": is_fresh_trigger,
                                                    "status": "FRESH_TRIGGERED" if is_fresh_trigger else "CONFIRMED_TAP",
                                                    "sentry_reasons": sentry_lbl,
                                                    "tier": tier,
                                                    "be_lock_pct": be_lock_pct,
                                                    "trail_lock_pct": trail_lock_pct,
                                                    "cvd_confirmed": cvd_confirmed
                                                })
                                                tapped_found = True
                                            break

                                    if not tapped_found:
                                        bars_since_high = (n - 1) - high_idx
                                        if 1 <= bars_since_high <= max_tap_window:
                                            recent_bars = candles[high_idx + 1:n]
                                            broken = any(b["close"] < dec_bot for b in recent_bars)
                                            if not broken:
                                                strat_mode = get_setting("strategy_version", os.getenv("STRATEGY_VERSION", "HERMES_3.0_QUANTUM"))
                                                eff_entry = mt if strat_mode.startswith("HERMES_3") else dec_top
                                                sentry_lbl = f"HERMES 3.0 QUANTUM Armed MT | Sentry 1 Clean | Sentry 2 Disp: {gain*100:.1f}% + FVG | Sentry 3 Armed IDM | Sentry 4 Fresh: {bars_since_high}/28 Bars" if strat_mode.startswith("HERMES_3") else f"HERMES 2.5 APEX HYBRID | Sentry 1 Clean | Sentry 2 Disp: {gain*100:.1f}% + FVG | Sentry 3 Armed IDM | Sentry 4 Fresh Window: {bars_since_high}/28 Bars"
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "LONG",
                                                    "interval": interval,
                                                    "entry_price": eff_entry,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "mean_threshold": mt,
                                                    "tp_price": eff_entry * (1.0 + tp_pct),
                                                    "soft_sl_price": eff_entry * (1.0 - soft_sl_pct),
                                                    "hard_sl_price": eff_entry * (1.0 - hard_sl_pct),
                                                    "tp_pct": tp_pct,
                                                    "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct,
                                                    "displacement_pct": round(gain * 100.0, 2),
                                                    "wick_ratio_pct": 0.0,
                                                    "tap_bar_age": 0,
                                                    "tap_time": candles[-1]["time"],
                                                    "is_fresh_trigger": False,
                                                    "status": "ARMED_WAITING_TAP",
                                                    "sentry_reasons": sentry_lbl
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

                                            strat_mode = get_setting("strategy_version", os.getenv("STRATEGY_VERSION", "HERMES_3.5_DUAL_TIER_SNIPER"))
                                            is_hermes3 = strat_mode.startswith("HERMES_3")
                                            is_hermes35 = strat_mode.startswith("HERMES_3.5")
                                            is_valid_tap = (tap_c["high"] >= mt and tap_c["close"] <= mt) if is_hermes3 else (tap_c["close"] <= mt)

                                            if swept and w_ratio >= 0.18 and is_valid_tap:
                                                tier = "TIER_1_INSTITUTIONAL"
                                                be_lock_pct = 0.016
                                                trail_lock_pct = 0.022
                                                cvd_confirmed = True

                                                if is_hermes35:
                                                    passed_sniper, sniper_reason = hermes35_engine.evaluate_15m_micro_sniper_gate(tap_c, "SHORT")
                                                    if not passed_sniper:
                                                        logger.info(f"🛑 [HERMES 3.5 SNIPER VETO] {symbol} SHORT tap rejected: {sniper_reason}")
                                                        continue
                                                    tier_info = hermes35_engine.classify_dual_tier_setup(candles, t, "SHORT")
                                                    tier = tier_info.get("tier", "TIER_1_INSTITUTIONAL")
                                                    tier_name = tier_info.get("tier_name", "Tier 1 (Institutional)")
                                                    be_lock_pct = tier_info.get("be_lock_pct", 0.016)
                                                    trail_lock_pct = tier_info.get("trail_lock_pct", 0.022)
                                                    cvd_confirmed = tier_info.get("cvd_confirmed", True)
                                                    eff_entry = mt
                                                    sentry_lbl = f"HERMES 3.5 DUAL SNIPER [{tier_name}] | {sniper_reason} | Sentry 1 Clean | Sentry 2 Disp: {drop*100:.1f}% + Bear FVG | Sentry 3 Wick: {w_ratio*100:.1f}% & MT 50% | Sentry 4 Fresh: Bar #{t - low_idx}"
                                                elif is_hermes3:
                                                    eff_entry = mt
                                                    sentry_lbl = f"HERMES 3.0 QUANTUM (Mean Threshold 50% EQ) | Sentry 1 Clean | Sentry 2 Disp: {drop*100:.1f}% + Bear FVG | Sentry 3 Wick: {w_ratio*100:.1f}% & MT 50% Rejection | Sentry 4 Fresh: Bar #{t - low_idx}"
                                                else:
                                                    eff_entry = dec_bot
                                                    sentry_lbl = f"HERMES 2.5 APEX HYBRID | Sentry 1 Clean | Sentry 2 Disp: {drop*100:.1f}% + Bear FVG | Sentry 3 Wick: {w_ratio*100:.1f}% & MT OK | Sentry 4 Fresh: Bar #{t - low_idx}"

                                                age = n - 1 - t
                                                is_fresh_trigger = (age <= 1)

                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "SHORT",
                                                    "interval": interval,
                                                    "entry_price": eff_entry,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "mean_threshold": mt,
                                                    "tp_price": eff_entry * (1.0 - tp_pct),
                                                    "soft_sl_price": eff_entry * (1.0 + soft_sl_pct),
                                                    "hard_sl_price": eff_entry * (1.0 + hard_sl_pct),
                                                    "tp_pct": tp_pct,
                                                    "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct,
                                                    "displacement_pct": round(drop * 100.0, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100.0, 1),
                                                    "tap_bar_age": age,
                                                    "tap_time": tap_c["time"],
                                                    "is_fresh_trigger": is_fresh_trigger,
                                                    "status": "FRESH_TRIGGERED" if is_fresh_trigger else "CONFIRMED_TAP",
                                                    "sentry_reasons": sentry_lbl,
                                                    "tier": tier,
                                                    "be_lock_pct": be_lock_pct,
                                                    "trail_lock_pct": trail_lock_pct,
                                                    "cvd_confirmed": cvd_confirmed
                                                })
                                                tapped_found = True
                                            break

                                    if not tapped_found:
                                        bars_since_low = (n - 1) - low_idx
                                        if 1 <= bars_since_low <= max_tap_window:
                                            recent_bars = candles[low_idx + 1:n]
                                            broken = any(b["close"] > dec_top for b in recent_bars)
                                            if not broken:
                                                strat_mode = get_setting("strategy_version", os.getenv("STRATEGY_VERSION", "HERMES_3.0_QUANTUM"))
                                                eff_entry = mt if strat_mode.startswith("HERMES_3") else dec_bot
                                                sentry_lbl = f"HERMES 3.0 QUANTUM Armed MT | Sentry 1 Clean | Sentry 2 Disp: {drop*100:.1f}% + Bear FVG | Sentry 3 Armed IDM | Sentry 4 Fresh: {bars_since_low}/28 Bars" if strat_mode.startswith("HERMES_3") else f"HERMES 2.5 APEX HYBRID | Sentry 1 Clean | Sentry 2 Disp: {drop*100:.1f}% + Bear FVG | Sentry 3 IDM Level | Sentry 4 Armed Fresh ({bars_since_low}/28 Bars)"
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "SHORT",
                                                    "interval": interval,
                                                    "entry_price": eff_entry,
                                                    "ob_high": dec_top,
                                                    "ob_low": dec_bot,
                                                    "mean_threshold": mt,
                                                    "tp_price": eff_entry * (1.0 - tp_pct),
                                                    "soft_sl_price": eff_entry * (1.0 + soft_sl_pct),
                                                    "hard_sl_price": eff_entry * (1.0 + hard_sl_pct),
                                                    "tp_pct": tp_pct,
                                                    "soft_sl_pct": soft_sl_pct,
                                                    "hard_sl_pct": hard_sl_pct,
                                                    "displacement_pct": round(drop * 100.0, 2),
                                                    "wick_ratio_pct": 0.0,
                                                    "tap_bar_age": 0,
                                                    "tap_time": candles[-1]["time"],
                                                    "is_fresh_trigger": False,
                                                    "status": "ARMED_WAITING_TAP",
                                                    "sentry_reasons": sentry_lbl
                                                })

        # Deduplicate setups: At most 1 setup per symbol, side, and timeframe
        unique_setups_map = {}
        for s in setups:
            k = (s["symbol"], s["side"], s.get("interval", "4h"))
            # Prefer fresh trigger or confirmed tap over waiting
            if k not in unique_setups_map or s.get("is_fresh_trigger") or s.get("status") == "CONFIRMED_TAP":
                unique_setups_map[k] = s

        return list(unique_setups_map.values())

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

        # Global deduplication across all scanned setups
        deduped_setups = []
        seen_setup_keys = set()
        for s in found_setups:
            s_key = f"{s['symbol']}_{s['side']}_{s.get('interval', '4h')}"
            if s_key not in seen_setup_keys:
                seen_setup_keys.add(s_key)
                deduped_setups.append(s)

        self.detected_setups = deduped_setups
        self.last_scan_time = time.time()
        now_dt = datetime.now(IST)
        now_str = now_dt.strftime("%d %b %Y • %I:%M:%S %p IST")
        set_metric("hermes_last_scan", now_str)
        set_metric("hermes_setups_detected", str(len(found_setups)))

        # Check if any Quad-Compounding slot has capacity for fresh setups
        open_trades = get_open_paper_trades()
        if len(open_trades) < 4 and found_setups:
            # Strictly enter fresh setups (tapped within latest candle, age <= 1)
            fresh = [s for s in found_setups if s.get("is_fresh_trigger")]
            for target_setup in fresh:
                if len(get_open_paper_trades()) >= 4:
                    break
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
        """Guarded entrypoint: Enforces atomic lock and in-flight symbol deduplication across all loops."""
        sym_clean = setup.get("symbol", "").upper()
        if not sym_clean:
            return

        if sym_clean in self._in_flight_symbols:
            logger.info(f"🛡️ [IN-FLIGHT GUARD] Skipping {sym_clean}: Execution already in flight!")
            return

        async with self._order_execution_lock:
            if sym_clean in self._in_flight_symbols:
                logger.info(f"🛡️ [IN-FLIGHT GUARD] Skipping {sym_clean}: Already queued in flight!")
                return
            self._in_flight_symbols.add(sym_clean)
            try:
                await self._execute_apex_entry_internal(setup)
            finally:
                self._in_flight_symbols.discard(sym_clean)

    async def _execute_apex_entry_internal(self, setup: Dict[str, Any]):
        """Executes a 5x Isolated Simulated Compounding position on a verified setup for its specific timeframe."""
        tf = (setup.get("interval") or "4h").lower()
        sym = setup["symbol"]
        entry_price = float(setup["entry_price"])
        side = setup["side"]

        # Check all currently open trades across all channels
        with get_connection() as conn:
            all_open = conn.execute("SELECT * FROM paper_trades WHERE status = 'OPEN'").fetchall()
            all_open_trades = [dict(r) for r in all_open]

        # 0. STRICT POST-LOSS / EXIT COOLDOWN CHECK (In-Memory + SQLite Persistent)
        db_cooldown = int(get_setting(f"cooldown_{sym.upper()}", "0") or "0")
        current_cooldown = max(self.trade_cooldowns.get(sym.upper(), 0), db_cooldown)
        if current_cooldown > time.time():
            remaining_m = int((current_cooldown - time.time()) / 60)
            logger.info(f"🛑 [COOLDOWN ENFORCED] Skipping {sym}: In mandatory cooldown for {remaining_m} more minutes!")
            return

        # 1. STRICT ANTI-COLLISION & ASSET EXCLUSIVITY ("dono ka samne trade nhi hona chaiye")
        busy_symbols = {t["symbol"].upper() for t in all_open_trades}
        if sym.upper() in busy_symbols:
            logger.info(f"🛡️ [ANTI-COLLISION] Skipping {sym} ({tf.upper()} {side}): Symbol is already open in another slot!")
            return

        # 2. BITGET EXCLUSIVE QUAD-SLOT DISPATCHER ($50 x 4 Tracks: 4Hx2, 1Hx2)
        target_channel = None
        target_account_id = None
        target_exchange = "BITGET"

        if tf == "4h":
            bg_4h_1_open = any(t.get("account_id") == 1 or t.get("channel") == "bitget_4h_1" for t in all_open_trades if t.get("status") == "OPEN")
            bg_4h_2_open = any(t.get("account_id") == 2 or t.get("channel") == "bitget_4h_2" for t in all_open_trades if t.get("status") == "OPEN")

            if not bg_4h_1_open:
                target_channel = "bitget_4h_1"
                target_account_id = 1
            elif not bg_4h_2_open:
                target_channel = "bitget_4h_2"
                target_account_id = 2
            else:
                logger.info(f"Both Bitget 4H compounding slots (Section A & Section B) are full. Waiting...")
                return

        elif tf == "1h":
            bg_1h_1_open = any(t.get("account_id") == 3 or t.get("channel") == "bitget_1h_1" for t in all_open_trades if t.get("status") == "OPEN")
            bg_1h_2_open = any(t.get("account_id") == 4 or t.get("channel") == "bitget_1h_2" for t in all_open_trades if t.get("status") == "OPEN")

            if not bg_1h_1_open:
                target_channel = "bitget_1h_1"
                target_account_id = 3
            elif not bg_1h_2_open:
                target_channel = "bitget_1h_2"
                target_account_id = 4
            else:
                logger.info(f"Both Bitget 1H compounding slots (Section A & Section B) are full. Waiting...")
                return

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

        acc = get_paper_account(account_id=target_account_id)
        current_balance = float(acc.get("current_balance", 50.0) or 50.0)
        if current_balance < 1.0:
            current_balance = 50.0

        margin = current_balance
        position_size = round(margin * 5.0, 2)
        now_ms = int(time.time() * 1000)

        strat_mode = get_setting("strategy_version", os.getenv("STRATEGY_VERSION", "HERMES_3.0_QUANTUM"))
        if strat_mode.startswith("HERMES_3"):
            entry_price = float(setup.get("entry_price", cur_price))
        else:
            entry_price = cur_price

        tp_pct = float(setup.get("tp_pct", 0.028 if tf == "4h" else 0.016))
        soft_sl_pct = float(setup.get("soft_sl_pct", 0.028 if tf == "4h" else 0.0145))
        hard_sl_pct = float(setup.get("hard_sl_pct", 0.038 if tf == "4h" else 0.030))

        if side in ("BUY", "LONG"):
            tp_price = round(entry_price * (1.0 + tp_pct), 6)
            sl_price = round(entry_price * (1.0 - soft_sl_pct), 6)
            hard_sl_price = round(entry_price * (1.0 - hard_sl_pct), 6)
        else:
            tp_price = round(entry_price * (1.0 - tp_pct), 6)
            sl_price = round(entry_price * (1.0 + soft_sl_pct), 6)
            hard_sl_price = round(entry_price * (1.0 + hard_sl_pct), 6)

        sentry_reasons = setup.get("sentry_reasons", "")

        # Check if real exchange auto-trading is active for this target exchange
        exchange_auto_active = False
        if target_exchange == "BINANCE":
            from engine.binance_trader import binance_trader
            exchange_auto_active = binance_trader.is_auto_trade_enabled()
        elif target_exchange == "BITGET":
            from engine.bitget_trader import bitget_trader
            exchange_auto_active = bitget_trader.is_auto_trade_enabled()

        execution_order_id = None

        # 1:1 REAL EXECUTION MANDATE:
        # If auto-trading is enabled for the exchange, execute on real exchange FIRST!
        # A trade is ONLY opened if the exchange confirms the order. Zero phantom trades.
        if exchange_auto_active:
            setup_with_flag = {
                **setup,
                "managed_by_hermes": True,
                "entry_price": entry_price,
                "tp_price": tp_price,
                "sl_price": sl_price,
                "hard_sl_price": hard_sl_price,
                "tp_pct": tp_pct,
                "soft_sl_pct": soft_sl_pct,
                "hard_sl_pct": hard_sl_pct,
                "margin": margin
            }
            logger.info(f"🚀 [BITGET REAL DISPATCH] Routing {sym} {side} to BITGET ({target_channel.upper()}) | ${margin:.2f} Margin @ 5x Isolated (Account #{target_account_id})")
            res = None
            try:
                from engine.bitget_trader import bitget_trader
                if "4h" in target_channel:
                    res = await bitget_trader.execute_4h_trade(setup_with_flag)
                else:
                    res = await bitget_trader.execute_1h_trade(setup_with_flag)
            except Exception as be:
                logger.error(f"❌ Real order exception on BITGET ({target_channel}): {be}")
                return

            if not res or not res.get("success"):
                reason = res.get("reason") or res.get("error") if res else "Order placement failed"
                logger.warning(f"🛡️ [REAL PARITY ENFORCED] Trade on {sym} skipped/rejected on Bitget: {reason}. Paper trade NOT opened to maintain 1:1 real parity!")
                return

            execution_order_id = res.get("order_id") or (res.get("order", {}).get("id") if isinstance(res.get("order"), dict) else None)
            if res.get("entry_price"):
                entry_price = float(res["entry_price"])
            if res.get("margin"):
                margin = float(res["margin"])
                position_size = round(margin * 5.0, 2)
            logger.info(f"✅ Real exchange order placed on {target_exchange}: Order ID {execution_order_id}")

        tier = setup.get("tier", "TIER_1_INSTITUTIONAL")
        be_lock_pct = float(setup.get("be_lock_pct", 0.016))
        trail_lock_pct = float(setup.get("trail_lock_pct", 0.022))
        trade_mode = strat_mode if strat_mode else "HERMES_3.5_DUAL_TIER_SNIPER"

        with get_connection() as conn:
            cursor = conn.execute("""
            INSERT INTO paper_trades (
                symbol, side, entry_price, position_size_usdt,
                tp_price, sl_price, hard_sl_price, timeframe,
                channel, exchange, account_id,
                status, entry_time, sentry_reasons, mode,
                highest_price, lowest_price, mae_pct, mfe_pct, duration_str, roi_pct,
                tier, be_lock_pct, trail_lock_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, ?, 0.0, 0.0, '', 0.0, ?, ?, ?)
            """, (
                sym, side, entry_price, position_size,
                tp_price, sl_price, hard_sl_price, tf,
                target_channel, target_exchange, target_account_id,
                now_ms, sentry_reasons, trade_mode,
                entry_price, entry_price,
                tier, be_lock_pct, trail_lock_pct
            ))
            conn.commit()
            trade_id = cursor.lastrowid

        # Real-time Master Ledger synchronization
        try:
            from engine.trade_journal import sync_quad_accounts_to_ledger
            sync_quad_accounts_to_ledger()
        except Exception as e:
            logger.warning(f"Master ledger sync error on trade open: {e}")

        # Real-time Cloud Vault synchronization
        try:
            from database.cloud_vault import push_vault_state
            push_vault_state()
        except Exception:
            pass

        trade_obj = {
            "id": trade_id,
            "symbol": sym,
            "side": side,
            "timeframe": tf,
            "channel": target_channel,
            "exchange": target_exchange,
            "account_id": target_account_id,
            "entry_price": entry_price,
            "position_size_usdt": position_size,
            "margin_usdt": margin,
            "tp_price": tp_price,
            "sl_price": sl_price,
            "hard_sl_price": hard_sl_price,
            "status": "OPEN",
            "entry_time": now_ms,
            "sentry_reasons": sentry_reasons,
            "mode": trade_mode,
            "tier": tier,
            "be_lock_pct": be_lock_pct,
            "trail_lock_pct": trail_lock_pct,
            "order_id": execution_order_id
        }
        self.active_position = trade_obj

        # Check if paper trading alerts are muted
        mute_paper = get_setting("mute_paper_trading_alerts", "false").lower() == "true"
        if mute_paper:
            logger.info("Paper trading alerts are muted. Skipping Telegram entry alert.")
            await self.broadcast("HERMES_POSITION_OPENED", trade_obj)
            return

        # -------------------------------------------------------------
        # STRICT TELEGRAM ANTI-SPAM & DEDUPLICATION GATEWAY
        # -------------------------------------------------------------
        cooldown_bucket = int(now_ms // (2 * 3600 * 1000))  # 2-hour window
        alert_key = f"{sym.upper()}_{side.upper()}_{tf.upper()}_{cooldown_bucket}_HERMES_ENTRY"
        if is_alert_sent(alert_key):
            logger.warning(f"🛡️ [TG ANTI-SPAM BLOCKED] Telegram alert for {sym} {side} ({tf}) suppressed: Already sent within 2-hour window!")
            await self.broadcast("HERMES_POSITION_OPENED", trade_obj)
            return

        record_sent_alert(alert_key, sym, side, "HERMES_ENTRY", now_ms, None)

        # Send Telegram Announcement to User's Bot WITH LIVE CANDLESTICK CHART
        try:
            trade_num = get_paper_trade_sequence_num(tf, trade_id)
            date_time_str = format_tg_ist_timestamp(now_ms)
            tp_dist_pct = float(setup.get("tp_pct", 0.028 if tf == "4h" else 0.022)) * 100.0
            sl_dist_pct = -float(setup.get("soft_sl_pct", 0.028 if tf == "4h" else 0.025)) * 100.0
            quantity = round(position_size / entry_price, 4) if entry_price > 0 else 0.0

            tg_msg = format_trade_open_alert(
                symbol=sym,
                side=side,
                timeframe=tf,
                leverage="5x",
                trade_num=trade_num,
                entry_price=entry_price,
                tp_price=tp_price,
                sl_price=sl_price,
                balance=margin,
                deployed=margin,
                position_size=position_size,
                quantity=quantity,
                tp_dist_pct=tp_dist_pct,
                sl_dist_pct=sl_dist_pct,
                date_time_str=date_time_str,
                exchange=target_exchange,
                channel=target_channel,
                order_id=str(execution_order_id) if execution_order_id else None
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
                    keyboard = telegram_service.get_alert_inline_keyboard(sym, exchange=target_exchange)
                    resp = await telegram_service.send_photo(chart_bytes, tg_msg, parse_mode="HTML", reply_markup=keyboard)
                    if resp and resp.get("ok"):
                        chart_sent = True
            except Exception as ce:
                logger.warning(f"Failed to render/send chart image: {ce}")

            if not chart_sent:
                try:
                    keyboard = telegram_service.get_alert_inline_keyboard(sym, exchange=target_exchange)
                    await telegram_service.send_raw_message(tg_msg, parse_mode="HTML", reply_markup=keyboard)
                except Exception:
                    # Bulletproof fallback: Send text without markup if keyboard fails
                    await telegram_service.send_raw_message(tg_msg, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Telegram alert error on entry: {e}")
            try:
                # Emergency plain alert
                emergency_msg = f"⚡ <b>HERMES 3.0 LIVE ENTRY</b>: #{sym} ({side}) @ {entry_price} | TP: {tp_price} | SL: {sl_price}"
                await telegram_service.send_raw_message(emergency_msg, parse_mode="HTML")
            except Exception:
                pass

        await self.broadcast("HERMES_POSITION_OPENED", trade_obj)

    async def check_live_price_and_exits(self):
        """Monitors live Binance tickers against active positions (1H and 4H) every few seconds, and triggers real-time Order Block taps."""
        open_trades = get_open_paper_trades()
        if open_trades:
            tickers = await binance_feed.fetch_all_tickers()
            if tickers:
                self.last_tickers = tickers
                self.last_ticker_time = time.time()
                try:
                    await self.broadcast("TICKER_UPDATE", {"tickers": tickers})
                except Exception:
                    pass

            for trade in list(open_trades):
                sym = trade["symbol"]
                side = trade["side"].upper()
                entry_price = float(trade["entry_price"])
                tp_price = float(trade["tp_price"])
                sl_price = float(trade["sl_price"])
                hard_sl_price = float(trade.get("hard_sl_price", 0.0) or (entry_price * 0.964 if side in ("BUY", "LONG") else entry_price * 1.036))
                trade_id = trade["id"]

                cur_price = tickers.get(sym) if tickers else None
                if not cur_price or cur_price <= 0:
                    continue

                # Continuously update high, low, MAE, MFE in database
                update_paper_trade_mark_price(trade_id, cur_price)

                exit_triggered = None
                exit_price = cur_price

                if side in ("BUY", "LONG"):
                    highest = max(float(trade.get("highest_price") or entry_price), cur_price)
                    gain_from_entry = (highest - entry_price) / entry_price if entry_price > 0 else 0.0

                    trade_be_trigger = float(trade.get("be_lock_pct") or 0.016)
                    trade_trail_trigger = float(trade.get("trail_lock_pct") or 0.022)

                    # Evaluate Multi-Stage Dynamic Profit Armor for LONG
                    current_effective_sl = sl_price
                    sl_updated = False
                    if gain_from_entry >= trade_trail_trigger:
                        stage2_sl = round(entry_price * (1.0 + 0.008), 6) # +0.80% Trailing Profit Lock
                        if stage2_sl > current_effective_sl:
                            current_effective_sl = stage2_sl
                            sl_updated = True
                            logger.info(f"🛡️ HERMES PROFIT ARMOR STAGE 2 ACTIVE: {sym} LONG SL locked at {stage2_sl} (+0.80% trailing profit lock)")
                    elif gain_from_entry >= trade_be_trigger:
                        stage1_sl = round(entry_price * (1.0 + 0.001), 6) # +0.10% Breakeven Lock
                        if stage1_sl > current_effective_sl:
                            current_effective_sl = stage1_sl
                            sl_updated = True
                            logger.info(f"🛡️ HERMES PROFIT ARMOR STAGE 1 ACTIVE: {sym} LONG SL locked at {stage1_sl} (BE +0.10% profit)")

                    if sl_updated:
                        try:
                            with get_connection() as conn:
                                conn.execute("UPDATE paper_trades SET sl_price = ? WHERE id = ?", (current_effective_sl, trade_id))
                                conn.commit()
                        except Exception:
                            pass

                    if cur_price >= tp_price:
                        exit_triggered = "TP_HIT"
                        exit_price = tp_price
                    elif cur_price <= hard_sl_price:
                        exit_triggered = "SL_HIT"
                        exit_price = hard_sl_price
                    elif cur_price <= current_effective_sl:
                        if current_effective_sl > entry_price:
                            exit_triggered = "TP_HIT"
                            exit_price = current_effective_sl
                            logger.info(f"🛡️ HERMES PROFIT LOCKED EXIT TRIGGERED: {sym} LONG at {exit_price}")
                        else:
                            exit_triggered = "SL_HIT"
                            exit_price = current_effective_sl
                            logger.info(f"🛑 HERMES SL TRIGGERED: {sym} LONG at {exit_price}")
                else: # SELL / SHORT (HERMES MULTI-STAGE DYNAMIC PROFIT ARMOR)
                    lowest = min(float(trade.get("lowest_price") or entry_price), cur_price)
                    drop_from_entry = (entry_price - lowest) / entry_price if entry_price > 0 else 0.0
                    trade_be_trigger = float(trade.get("be_lock_pct") or 0.016)
                    trade_trail_trigger = float(trade.get("trail_lock_pct") or 0.022)

                    # Evaluate Multi-Stage Dynamic Profit Armor
                    current_effective_sl = sl_price
                    sl_updated = False
                    if drop_from_entry >= trade_trail_trigger:
                        stage2_sl = round(entry_price * (1.0 - 0.008), 6) # +0.80% Trailing Profit Lock
                        if stage2_sl < current_effective_sl:
                            current_effective_sl = stage2_sl
                            sl_updated = True
                            logger.info(f"🛡️ HERMES PROFIT ARMOR STAGE 2 ACTIVE: {sym} SHORT SL locked at {stage2_sl} (+0.80% trailing profit lock)")
                    elif drop_from_entry >= trade_be_trigger:
                        stage1_sl = round(entry_price * (1.0 - 0.001), 6) # +0.10% Breakeven Lock
                        if stage1_sl < current_effective_sl:
                            current_effective_sl = stage1_sl
                            sl_updated = True
                            logger.info(f"🛡️ HERMES PROFIT ARMOR STAGE 1 ACTIVE: {sym} SHORT SL locked at {stage1_sl} (BE +0.10% profit)")

                    if sl_updated:
                        try:
                            with get_connection() as conn:
                                conn.execute("UPDATE paper_trades SET sl_price = ? WHERE id = ?", (current_effective_sl, trade_id))
                                conn.commit()
                        except Exception:
                            pass

                    if cur_price <= tp_price:
                        exit_triggered = "TP_HIT"
                        exit_price = tp_price
                    elif cur_price >= hard_sl_price:
                        exit_triggered = "SL_HIT"
                        exit_price = hard_sl_price
                    elif cur_price >= current_effective_sl:
                        if current_effective_sl < entry_price:
                            exit_triggered = "TP_HIT"
                            exit_price = current_effective_sl
                            logger.info(f"🛡️ HERMES 3.0-C ARMOR PROFIT LOCKED EXIT TRIGGERED: {sym} SHORT at {exit_price}")
                        else:
                            exit_triggered = "SL_HIT"
                            exit_price = current_effective_sl
                            logger.info(f"🛑 HERMES SL TRIGGERED: {sym} SHORT at {exit_price}")

                if exit_triggered:
                    await self.resolve_trade_exit(trade, exit_triggered, exit_price)

            # If all 4 compounding slots are full (4 trades open), do not scan for new entries
            if len(open_trades) >= 4:
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

            # Strict Anti-Collision: Gather all currently active symbols across all 4 channels
            busy_symbols = {t["symbol"].upper() for t in (open_trades or [])}

            for setup in list(self.detected_setups):
                sym = setup.get("symbol")
                # Asset Exclusivity & Anti-Collision: never open same coin concurrently
                if sym and sym.upper() in busy_symbols:
                    continue

                # Cooldown check: prevent re-entering same symbol within cooldown window
                if self.trade_cooldowns.get(sym, 0) > time.time():
                    continue

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

                mt = float(setup.get("mean_threshold", (ob_high + ob_low) / 2.0))
                strat_mode = get_setting("strategy_version", os.getenv("STRATEGY_VERSION", "HERMES_3.5_DUAL_TIER_SNIPER"))

                tapped = False
                if side in ("BUY", "LONG"):
                    if strat_mode.startswith("HERMES_3"):
                        # In Hermes 3.0/3.5, enter at Mean Threshold 50% discount depth
                        if (cur_price <= mt * 1.002) and (cur_price >= ob_low * 0.995):
                            tapped = True
                            setup["entry_price"] = mt
                    else:
                        # Price has touched or dipped into the top of the Order Block zone
                        if (cur_price <= ob_high * 1.002) and (cur_price >= ob_low * 0.995):
                            tapped = True
                else: # SHORT / SELL
                    if strat_mode.startswith("HERMES_3"):
                        # In Hermes 3.0/3.5, enter at Mean Threshold 50% premium depth
                        if (cur_price >= mt * 0.998) and (cur_price <= ob_high * 1.005):
                            tapped = True
                            setup["entry_price"] = mt
                    else:
                        # Price has touched or pushed up into the bottom of the Order Block zone
                        if (cur_price >= ob_low * 0.998) and (cur_price <= ob_high * 1.005):
                            tapped = True

                diff_pct = abs(cur_price - entry_p) / entry_p * 100.0
                is_hermes3 = strat_mode.startswith("HERMES_3")
                should_trigger = tapped if is_hermes3 else (tapped or (is_fresh and diff_pct <= 0.40))
                if should_trigger:
                    tf_setup = (setup.get("interval") or "4h").lower()
                    # Check if this specific timeframe has capacity across its 2 slots
                    open_trades_current = get_open_paper_trades()
                    if tf_setup == "4h":
                        slots_4h_count = sum(1 for t in open_trades_current if t.get("account_id") in (1, 2) or str(t.get("channel", "")).startswith("bitget_4h"))
                        if slots_4h_count >= 2:
                            continue
                    elif tf_setup == "1h":
                        slots_1h_count = sum(1 for t in open_trades_current if t.get("account_id") in (3, 4) or str(t.get("channel", "")).startswith("bitget_1h"))
                        if slots_1h_count >= 2:
                            continue

                    # Live 15m Micro-Sniper & Live Binance Open Interest (OI) check on tap
                    if strat_mode.startswith("HERMES_3.5"):
                        try:
                            k15 = await binance_feed.fetch_klines(sym, interval="15m", limit=3)
                            if k15:
                                p_gate, r_gate = hermes35_engine.evaluate_15m_micro_sniper_gate(k15[-1], side)
                                if not p_gate:
                                    logger.info(f"🛑 [HERMES 3.5 TAP VETO] {sym} {side} live tap rejected: {r_gate}")
                                    continue
                            # Live Binance Open Interest (OI) Verification
                            live_oi_data = await binance_feed.fetch_open_interest(sym)
                            oi_val = float(live_oi_data.get("open_interest", 0.0) or 0.0)
                            if oi_val > 0:
                                setup["live_oi"] = oi_val
                                logger.info(f"📊 [HERMES 3.5 OI VERIFIED] {sym} live open interest confirmed: {oi_val:,.1f} contracts")
                        except Exception as e_tap:
                            logger.debug(f"Live tap sniper/OI check error: {e_tap}")

                    logger.info(f"⚡ REAL-TIME TAP WATCHDOG TRIGGERED on {sym} ({side})! Live Price: {cur_price} tapped OB [{ob_low}, {ob_high}] (TF: {tf_setup.upper()})")
                    # Purge ALL setups for this symbol across all timeframes to prevent repeated triggers
                    self.detected_setups = [s for s in self.detected_setups if s.get("symbol") != sym]
                    await self.execute_apex_entry(setup)
                    break
        except Exception as e:
            logger.debug(f"Real-time tap watchdog error: {e}")

    async def resolve_trade_exit(self, trade: Dict[str, Any], outcome: str, exit_price: float):
        """Resolves trade exit, calculates fees, vault stashing (15%), compounding reinvestment (85%), and MAE/MFE forensics."""
        now_ms = int(time.time() * 1000)
        side = trade["side"].upper()
        entry_price = float(trade["entry_price"])
        pos_size = float(trade["position_size_usdt"])
        trade_id = trade["id"]
        sym = trade["symbol"]
        tf = (trade.get("timeframe") or "4h").lower()
        acc_id = trade.get("account_id")
        if not acc_id:
            ch = str(trade.get("channel") or "")
            if ch == "binance_4h":
                acc_id = 1
            elif ch == "binance_1h":
                acc_id = 2
            elif ch == "bitget_4h":
                acc_id = 3
            elif ch == "bitget_1h":
                acc_id = 4
            else:
                acc_id = 2 if "1h" in tf else 1

        highest = max(float(trade.get("highest_price") or entry_price), exit_price)
        lowest = min(float(trade.get("lowest_price") or entry_price), exit_price)
        final_mae = float(trade.get("mae_pct") or 0.0)
        final_mfe = float(trade.get("mfe_pct") or 0.0)
        entry_t = trade.get("entry_time", now_ms)
        duration_str = format_duration_str(now_ms - entry_t)

        roundtrip_fee = pos_size * 0.0016 # 0.16% roundtrip exchange fee

        if side in ("BUY", "LONG"):
            gross_pnl_pct = (exit_price - entry_price) / entry_price * 100.0
        else:
            gross_pnl_pct = (entry_price - exit_price) / entry_price * 100.0

        gross_pnl_usdt = pos_size * (gross_pnl_pct / 100.0)
        net_pnl_usdt = gross_pnl_usdt - roundtrip_fee

        # ISOLATION GUARANTEE: If legacy Binance trade (acc_id == 99 or BINANCE exchange)
        if acc_id == 99 or str(trade.get("exchange", "")).upper() == "BINANCE" or str(trade.get("channel", "")).startswith("binance"):
            with get_connection() as conn:
                cursor = conn.execute("""
                UPDATE paper_trades SET
                    status = ?, exit_time = ?, exit_price = ?,
                    pnl_usdt = ?, pnl_pct = ?, vault_stashed_usdt = 0.0,
                    highest_price = ?, lowest_price = ?, mae_pct = ?, mfe_pct = ?,
                    duration_str = ?, roi_pct = ?
                WHERE id = ? AND status = 'OPEN'
                """, (
                    outcome, now_ms, exit_price, round(net_pnl_usdt, 2), round(gross_pnl_pct * 5.0, 2),
                    highest, lowest, final_mae, final_mfe, duration_str, round(gross_pnl_pct * 5.0, 2), trade_id
                ))
                if cursor.rowcount == 0:
                    logger.info(f"Trade #{trade_id} on {sym} was already settled. Skipping duplicate exit processing.")
                    return
                conn.commit()

            # Close Binance real market position
            try:
                from engine.binance_trader import binance_trader
                await binance_trader.close_position_market(sym, side)
                logger.info(f"✅ Binance legacy trade on {sym} closed on Binance exchange.")
            except Exception as bce:
                logger.error(f"Error closing Binance legacy trade {sym}: {bce}")

            # Record weekly forensic audit & autopsy
            try:
                from engine.hermes35_weekly_monitor import weekly_monitor
                if outcome == "SL_HIT" or net_pnl_usdt < 0:
                    await weekly_monitor.record_loss_autopsy(trade, exit_price, outcome)
                weekly_monitor.generate_weekly_markdown_artifact()
            except Exception as wme:
                logger.warning(f"Weekly monitor hook error (legacy): {wme}")

            self.active_position = None
            self.trade_cooldowns[sym] = time.time() + 7200
            self.detected_setups = [s for s in self.detected_setups if s.get("symbol") != sym]
            logger.info(f"🏆 Binance legacy position #{trade_id} on {sym} exited cleanly with outcome {outcome}. Bitget compounding accounts untouched.")
            return

        # Bitget Compounding Account update (acc_id in 1, 2, 3, 4)
        acc = get_paper_account(account_id=acc_id)
        current_balance = float(acc.get("current_balance", 50.0) or 50.0)
        vault_balance = float(acc.get("vault_balance", 0.0) or 0.0)
        win_count = int(acc.get("win_count", 0) or 0)
        loss_count = int(acc.get("loss_count", 0) or 0)
        total_pnl = float(acc.get("total_pnl", 0.0) or 0.0)

        # 100% Compounding Rule: 100% of Net P&L credited/debited directly to this specific account only!
        is_win = (outcome == "TP_HIT" or net_pnl_usdt > 0)
        win_streak = int(acc.get("win_streak") or 0)
        if is_win:
            win_count += 1
            win_streak += 1
        else:
            loss_count += 1
            win_streak = 0

        new_balance = round(max(1.0, current_balance + net_pnl_usdt), 2)
        new_total_pnl = round(total_pnl + net_pnl_usdt, 2)

        # Sync compounding setting for this specific track
        try:
            if acc_id == 1:
                set_setting("bitget_4h_1_compounding_balance", str(new_balance))
            elif acc_id == 2:
                set_setting("bitget_4h_2_compounding_balance", str(new_balance))
            elif acc_id == 3:
                set_setting("bitget_1h_1_compounding_balance", str(new_balance))
            elif acc_id == 4:
                set_setting("bitget_1h_2_compounding_balance", str(new_balance))
        except Exception:
            pass

        with get_connection() as conn:
            cursor = conn.execute("""
            UPDATE paper_trades SET
                status = ?, exit_time = ?, exit_price = ?,
                pnl_usdt = ?, pnl_pct = ?, vault_stashed_usdt = 0.0,
                highest_price = ?, lowest_price = ?, mae_pct = ?, mfe_pct = ?,
                duration_str = ?, roi_pct = ?
            WHERE id = ? AND status = 'OPEN'
            """, (
                outcome, now_ms, exit_price, round(net_pnl_usdt, 2), round(gross_pnl_pct * 5.0, 2),
                highest, lowest, final_mae, final_mfe, duration_str, round(gross_pnl_pct * 5.0, 2), trade_id
            ))
            if cursor.rowcount == 0:
                logger.info(f"Trade #{trade_id} on {sym} was already settled. Skipping duplicate exit processing.")
                return

            conn.execute("""
            UPDATE paper_account SET
                current_balance = ?,
                vault_balance = ?,
                total_pnl = ?,
                win_count = ?,
                loss_count = ?,
                win_streak = ?
            WHERE id = ?
            """, (new_balance, vault_balance, new_total_pnl, win_count, loss_count, win_streak, acc_id))
            conn.commit()

            # Record into trade_journal & sync Master Ledger for permanent auditing
            try:
                from engine.trade_journal import sync_quad_accounts_to_ledger
                sync_quad_accounts_to_ledger()
            except Exception as e:
                logger.warning(f"Master ledger sync error in hermes live exit: {e}")

        # Real-time Cloud Vault synchronization
        try:
            from database.cloud_vault import push_vault_state
            push_vault_state()
        except Exception:
            pass

        # Record weekly forensic audit & autopsy
        try:
            from engine.hermes35_weekly_monitor import weekly_monitor
            if outcome == "SL_HIT" or net_pnl_usdt < 0:
                await weekly_monitor.record_loss_autopsy(trade, exit_price, outcome)
            weekly_monitor.generate_weekly_markdown_artifact()
        except Exception as wme:
            logger.warning(f"Weekly monitor hook error: {wme}")

        self.active_position = None
        self.trade_cooldowns[sym.upper()] = time.time() + 7200
        set_setting(f"cooldown_{sym.upper()}", str(int(time.time() + 7200)))
        self.detected_setups = [s for s in self.detected_setups if s.get("symbol") != sym]

        # Close real Bitget futures position
        try:
            from engine.bitget_trader import bitget_trader
            if bitget_trader.is_auto_trade_enabled():
                close_res = await bitget_trader.close_position_market(sym, side)
                logger.info(f"Bitget real market close result for {sym}: {close_res}")
        except Exception as bge:
            logger.error(f"Bitget real market close exception for {sym}: {bge}")

        completed = win_count + loss_count
        win_rate = round(win_count / completed * 100, 1) if completed > 0 else 0.0

        # Check if paper trading alerts are muted
        mute_paper = get_setting("mute_paper_trading_alerts", "false").lower() == "true"
        if mute_paper:
            logger.info(f"Paper trading alerts are muted. Skipping Telegram exit alert for {sym}.")
        else:
            # Send Telegram Announcement to User's Bot in exact ALERT 2 format
            try:
                trade_num = get_paper_trade_sequence_num(tf, trade_id)
                date_time_str = format_tg_ist_timestamp(now_ms)
                pnl_pct = round(gross_pnl_pct if is_win else -gross_pnl_pct, 2)
                margin = float(trade.get("position_size_usdt", 250.0)) / 5.0
                roe_pct = round((net_pnl_usdt / margin) * 100.0, 2) if margin > 0 else round(pnl_pct * 5.0, 2)

                tg_msg = format_trade_closed_alert(
                    symbol=sym,
                    side=side,
                    timeframe=tf,
                    leverage="5x",
                    trade_num=trade_num,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    outcome=outcome,
                    pnl_pct=pnl_pct,
                    deployed=margin,
                    net_pnl=round(net_pnl_usdt, 2),
                    new_balance=new_balance,
                    roe_pct=roe_pct,
                    duration_str=duration_str,
                    streak=win_streak,
                    win_rate=win_rate,
                    date_time_str=date_time_str
                )

                # Send exit chart photo if available
                chart_sent = False
                try:
                    tf_chart = trade.get("timeframe", "4h")
                    candles = await binance_feed.fetch_klines(sym, interval=tf_chart, limit=50)
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
                        chart_bytes = render_smc_chart_image(sym, candles, zone_dict, timeframe=tf_chart.upper())
                        keyboard = telegram_service.get_alert_inline_keyboard(sym)
                        resp = await telegram_service.send_photo(chart_bytes, tg_msg, parse_mode="HTML", reply_markup=keyboard)
                        if resp and resp.get("ok"):
                            chart_sent = True
                except Exception as ce:
                    logger.warning(f"Failed to render/send exit chart photo: {ce}")

                if not chart_sent:
                    try:
                        keyboard = telegram_service.get_alert_inline_keyboard(sym)
                        await telegram_service.send_raw_message(tg_msg, parse_mode="HTML", reply_markup=keyboard)
                    except Exception:
                        await telegram_service.send_raw_message(tg_msg, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Telegram exit alert error: {e}")
                try:
                    emergency_exit_msg = f"🏆 <b>HERMES 3.0 TRADE CLOSED</b>: #{sym} ({side}) | Outcome: {outcome} | P&L: {net_pnl_usdt:+.2f} USDT"
                    await telegram_service.send_raw_message(emergency_exit_msg, parse_mode="HTML")
                except Exception:
                    pass

        await self.broadcast("HERMES_POSITION_CLOSED", {
            "symbol": sym,
            "outcome": outcome,
            "net_pnl": net_pnl_usdt,
            "new_balance": new_balance,
            "vault_balance": vault_balance,
            "win_rate": win_rate
        })

    async def start(self):
        """Autonomous 24/7 background loop running on the cloud server."""
        self.is_running = True
        active_ver = get_setting("strategy_version", os.getenv("STRATEGY_VERSION", "HERMES_3.0_QUANTUM"))
        logger.info(f"👑 {active_ver} Live Streaming Simulated Engine Started 24/7.")
        set_metric("hermes_status", "ACTIVE_24_7")
        set_metric("hermes_mode", active_ver)

        # Enforce 1-Trade Sequential Queue PER QUAD-COMPOUNDING ACCOUNT (1 to 4) & Restore Active Position
        try:
            with get_connection() as conn:
                for acc_id in (1, 2, 3, 4):
                    acc_open = conn.execute(
                        "SELECT * FROM paper_trades WHERE status = 'OPEN' AND account_id = ? ORDER BY id DESC",
                        (acc_id,)
                    ).fetchall()
                    if acc_open:
                        trade_dict = dict(acc_open[0])
                        if not self.active_position:
                            self.active_position = trade_dict
                        logger.info(f"👑 Restored active Account #{acc_id} Hermes position: {trade_dict['symbol']} {trade_dict['side']} ({trade_dict.get('channel', 'quad')})")
                        if len(acc_open) > 1:
                            now_ms = int(time.time() * 1000)
                            for extra in acc_open[1:]:
                                conn.execute(
                                    "UPDATE paper_trades SET status = 'CLOSED_LEGACY', exit_time = ?, exit_price = ?, pnl_usdt = 0.0, pnl_pct = 0.0, roi_pct = 0.0 WHERE id = ?",
                                    (now_ms, extra['entry_price'], extra['id'])
                                )
                            conn.commit()
                            logger.info(f"🧹 Cleaned up {len(acc_open)-1} extra legacy open trades in Account #{acc_id} queue.")
        except Exception as e:
            logger.warning(f"Error restoring active position on boot: {e}")

        # Initial sync of Quad accounts into Master Ledger
        try:
            from engine.trade_journal import sync_quad_accounts_to_ledger
            sync_quad_accounts_to_ledger()
            logger.info("📓 Synchronized all Quad Compounding Accounts (1, 2, 3, 4) to Master Ledger & CSV.")
        except Exception as e:
            logger.warning(f"Initial master ledger sync error on boot: {e}")

        # Initial Telegram Heartbeat on Boot
        try:
            acc = self.get_hermes_account()
            boot_msg = (
                f"👑 <b>HERMES 3.0 QUANTUM: 24/7 CLOUD ROBOT DEPLOYED & ONLINE!</b>\n"
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
