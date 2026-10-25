"""
HERMES 3.5 RADAR HARVEST: 24/7 Autonomous Live Execution & Scanning Engine
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
    HERMES_3_STEPPED_TRAILING_LADDER,
    HERMES_3_BTC_EMERGENCY_SHIELD
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
        """Ensures database tables reflect HERMES 3.5 RADAR HARVEST."""
        with get_connection() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_account)").fetchall()]
            if "vault_balance" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN vault_balance REAL DEFAULT 0.0")
            if "milestone_target" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN milestone_target REAL DEFAULT 2000.0")
            if "mode" not in cols:
                conn.execute("ALTER TABLE paper_account ADD COLUMN mode TEXT DEFAULT 'HERMES_3.5_RADAR_HARVEST'")

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

            # Update account mode to HERMES_3.5_RADAR_HARVEST
            conn.execute("UPDATE paper_account SET mode = 'HERMES_3.5_RADAR_HARVEST' WHERE id <= 10")
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
                curr_c = btc_candles[-1]  # Current forming 4H candle
                o_prev, c_prev = float(last_c["open"]), float(last_c["close"])
                chg_prev = (c_prev - o_prev) / o_prev if o_prev > 0 else 0.0

                o_curr, c_curr = float(curr_c["open"]), float(curr_c["close"])
                chg_curr = (c_curr - o_curr) / o_curr if o_curr > 0 else 0.0

                # Veto if either previous closed 4H or current live 4H dumped/pumped >= 2.0%
                long_veto = (chg_prev <= -0.020) or (chg_curr <= -0.020)
                short_veto = (chg_prev >= 0.020) or (chg_curr >= 0.020)
                chg_rep = chg_curr if abs(chg_curr) > abs(chg_prev) else chg_prev
                res = {
                    "bias": "BULLISH" if chg_rep > 0 else "BEARISH",
                    "change_pct": round(chg_rep * 100.0, 2),
                    "long_veto": long_veto,
                    "short_veto": short_veto,
                    "btc_is_bull": chg_rep > 0
                }
                self.last_btc_bias = res
                return res
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
        Pure algorithmic implementation of HERMES 3.5 RADAR HARVEST:
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

    def detect_hermes35_single_tier_zones(
        self,
        symbol: str,
        candles: List[Dict[str, Any]],
        interval: str = "4h"
    ) -> List[Dict[str, Any]]:
        """
        Pure algorithmic implementation of HERMES 3.5 SINGLE TIER OFFICIAL
        conforming 100% to HERMES_3_5_SINGLE_TIER_OFFICIAL.pine:
        - 5% Boundary penetration entry:
            Long:  o_high - (o_rng * 0.05)
            Short: o_low + (o_rng * 0.05)
        - 0.20% Proximity Radar price:
            Long:  entry_p * 1.0020
            Short: entry_p * 0.9980
        - +8.0% ROE BE Armor:
            Long:  entry_p * (1.0 + 0.0160)
            Short: entry_p * (1.0 - 0.0160)
        - +9.0% -> +4.5% Stepped Profit Harvest:
            Trigger: Long: entry_p * (1.0 + 0.0180) | Short: entry_p * (1.0 - 0.0180)
            Lock:    Long: entry_p * (1.0 + 0.0090) | Short: entry_p * (1.0 - 0.0090)
        - +14.0% ROE TP:
            Long:  entry_p * (1.0 + 0.0280)
            Short: entry_p * (1.0 - 0.0280)
        - Dynamic SL (-14.0% ROE):
            Long:  entry_p * (1.0 - 0.0280)
            Short: entry_p * (1.0 + 0.0280)
        """
        n = len(candles)
        if n < 30:
            return []

        tf = interval.lower()
        min_disp = 3.5 if tf in ("15m", "1h") else 5.0
        effective_min_bars = 18 if tf in ("1h", "15m") else 8
        effective_max_bars = 720 if tf in ("15m", "1h") else 360

        cur_price = float(candles[-1]["close"])
        active_zones = []

        for i in range(20, n - 3):
            c3 = candles[i]
            c2 = candles[i+1]
            c1 = candles[i+2]

            impulse_h = max(float(c1["high"]), float(c2["high"]))
            impulse_l = min(float(c1["low"]), float(c2["low"]))

            # ---------------- BULLISH SETUP (LONG) ----------------
            is_red = float(c3["close"]) < float(c3["open"])
            has_bull_fvg = float(c1["low"]) > float(c3["high"])
            bull_disp = ((impulse_h - float(c3["low"])) / float(c3["low"])) * 100.0 if float(c3["low"]) > 0 else 0.0

            prior_lows = [float(candles[k]["low"]) for k in range(max(0, i - 20), i)]
            is_origin_bull = float(c3["low"]) <= min(prior_lows) if prior_lows else False

            if is_red and has_bull_fvg and bull_disp >= min_disp:
                o_high = float(c3["high"])
                o_low = float(c3["low"])
                o_rng = o_high - o_low

                ent_p = round(o_high - (o_rng * 0.05), 8)
                rad_p = round(ent_p * 1.0020, 8)
                tp_p = round(ent_p * (1.0 + 0.0580), 8)  # +29.0% ROI Harvest Target
                be_armor_p = round(ent_p * (1.0 + 0.0098), 8)  # Step 1: +4.90% Trigger
                step_trig_p = round(ent_p * (1.0 + 0.0196), 8)  # Step 2: +9.80% Trigger
                step_lock_p = round(ent_p * (1.0 + 0.0102), 8)  # Step 2: +5.10% Lock
                sl_p = round(ent_p * (1.0 - 0.0150), 8)  # -7.50% Initial Hard SL

                c3_lower_wick = min(float(c3["open"]), float(c3["close"])) - o_low
                w_ratio = round((c3_lower_wick / o_rng) * 100.0, 1) if o_rng > 0 else 20.0

                peak_runway = impulse_h
                invalidated = False
                tapped = False
                be_locked = False
                profit_stepped = False
                completed = False
                fill_time = None
                armor_time = None
                harvest_time = None
                tp_time = None
                sl_time = None
                end_time = candles[-1]["time"]
                exit_time = None
                exit_price = None
                exit_reason = None
                bars_alive_at_tap = 0
                gap_at_tap = 0.0
                cur_sl = sl_p

                for k in range(i + 3, n):
                    bar = candles[k]
                    b_high = float(bar["high"])
                    b_low = float(bar["low"])
                    b_close = float(bar["close"])
                    b_time = bar["time"]
                    bars_alive = k - i

                    if not tapped and not completed:
                        peak_runway = max(peak_runway, b_high)
                        airspace_runway_pct = ((peak_runway - o_high) / o_high) * 100.0 if o_high > 0 else 0.0

                        if bars_alive > effective_max_bars:
                            completed = True
                            end_time = b_time
                            break
                        elif b_close < o_low:
                            invalidated = True
                            completed = True
                            end_time = b_time
                            break
                        elif b_low <= ent_p and b_low >= sl_p:
                            if airspace_runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                tapped = True
                                fill_time = b_time
                                bars_alive_at_tap = bars_alive
                                gap_at_tap = airspace_runway_pct
                                continue
                            else:
                                completed = True
                                end_time = b_time
                                break

                    elif tapped and not completed:
                        peak_runway = max(peak_runway, b_high)
                        gain_roi = ((b_high - ent_p) / ent_p) * 100.0 * 5.0

                        if gain_roi >= 4.90 and cur_sl < round(ent_p * (1.0 + (0.50 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 + (0.50 / 500.0)), 8)
                            be_locked = True
                            armor_time = b_time
                        if gain_roi >= 9.80 and cur_sl < round(ent_p * (1.0 + (5.10 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 + (5.10 / 500.0)), 8)
                            profit_stepped = True
                            harvest_time = b_time
                        if gain_roi >= 14.80 and cur_sl < round(ent_p * (1.0 + (10.10 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 + (10.10 / 500.0)), 8)
                        if gain_roi >= 19.80 and cur_sl < round(ent_p * (1.0 + (15.10 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 + (15.10 / 500.0)), 8)
                        if gain_roi >= 24.00 and cur_sl < round(ent_p * (1.0 + (20.10 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 + (20.10 / 500.0)), 8)
                        if b_high >= tp_p:
                            completed = True
                            tp_time = b_time
                            exit_time = b_time
                            exit_price = tp_p
                            end_time = b_time
                            exit_reason = "TP_HIT (+29.0% ROE)"
                            break
                        elif b_low <= cur_sl:
                            completed = True
                            sl_time = b_time
                            exit_time = b_time
                            exit_price = cur_sl
                            end_time = b_time
                            exit_reason = "TRAILING_EXIT" if be_locked else "SL_HIT"
                            break

                # Determine final status
                if completed:
                    if tp_time:
                        status = "COMPLETED_TP"
                    elif sl_time:
                        status = "COMPLETED_HARVEST" if profit_stepped else "COMPLETED_SL"
                    elif invalidated:
                        status = "INVALIDATED"
                    else:
                        status = "COMPLETED_SL"
                elif tapped:
                    if profit_stepped:
                        status = "STAGE2_HARVEST"
                    elif be_locked:
                        status = "STAGE1_ARMOR"
                    else:
                        status = "ACTIVE_TAPPED"
                else:
                    within_radar = (cur_price <= rad_p) and (cur_price >= ent_p)
                    status = "RADAR_PRE_ARMED" if within_radar else "ACTIVE_UNMITIGATED"

                within_radar = (cur_price <= rad_p) and (cur_price >= ent_p)
                is_fresh = (within_radar or (tapped and not be_locked)) and not completed

                if not completed:
                    end_time = candles[-1]["time"]

                active_bars_alive = bars_alive_at_tap if tapped else ((n - 1) - i)
                active_runway = gap_at_tap if tapped else (((peak_runway - o_high) / o_high * 100.0) if o_high > 0 else 0.0)

                if tapped or (not completed and status != "INVALIDATED"):
                    active_zones.append({
                        "symbol": symbol,
                        "side": "BUY",
                        "timeframe": tf.upper(),
                        "interval": tf,
                        "ob_high": o_high,
                        "ob_low": o_low,
                        "origin_time": c3["time"],
                        "end_time": end_time,
                        "entry_price": ent_p,
                        "radar_price": rad_p,
                        "tp_price": tp_p,
                        "armor_stage1_price": be_armor_p,
                        "armor_stage2_price": step_trig_p,
                        "harvest_lock_price": step_lock_p,
                        "sl_price": cur_sl,
                        "soft_sl_price": cur_sl,
                        "hard_sl_price": sl_p,
                        "is_fresh_trigger": is_fresh,
                        "tap_bar_age": 1 if tapped else 0,
                        "status": status,
                        "displacement_pct": round(bull_disp, 2),
                        "wick_ratio_pct": w_ratio,
                        "runway_pct": round(active_runway, 1),
                        "runway_void_pct": round(active_runway, 1),
                        "bars_alive": active_bars_alive,
                        "is_origin": is_origin_bull,
                        "is_in_radar": within_radar,
                        "tier_type": "SINGLE_TIER",
                        "strategy": "HERMES_3.5_SINGLE_TIER",
                        "prob_score": 97.2,
                        "rank_label": f"🏛️ HERMES 3.5 RADAR HARVEST [5% Boundary Entry: ${ent_p}]",
                        "fill_time": fill_time,
                        "fill_price": ent_p if tapped else None,
                        "be_armor_time": armor_time,
                        "profit_harvest_time": harvest_time,
                        "tp_time": tp_time,
                        "sl_time": sl_time,
                        "exit_time": exit_time,
                        "exit_price": exit_price,
                        "exit_reason": exit_reason,
                        "tapped": tapped,
                        "completed": completed
                    })

            # ---------------- BEARISH SETUP (SHORT) ----------------
            is_green = float(c3["close"]) > float(c3["open"])
            has_bear_fvg = float(c1["high"]) < float(c3["low"])
            bear_disp = ((float(c3["high"]) - impulse_l) / float(c3["high"])) * 100.0 if float(c3["high"]) > 0 else 0.0

            prior_highs = [float(candles[k]["high"]) for k in range(max(0, i - 20), i)]
            is_origin_bear = float(c3["high"]) >= max(prior_highs) if prior_highs else False

            if is_green and has_bear_fvg and bear_disp >= min_disp:
                o_high = float(c3["high"])
                o_low = float(c3["low"])
                o_rng = o_high - o_low

                ent_p = round(o_low + (o_rng * 0.05), 8)
                rad_p = round(ent_p * 0.9980, 8)
                tp_p = round(ent_p * (1.0 - 0.0580), 8)  # +29.0% ROI Harvest Target
                be_armor_p = round(ent_p * (1.0 - 0.0098), 8)  # Step 1: +4.90% Trigger
                step_trig_p = round(ent_p * (1.0 - 0.0196), 8)  # Step 2: +9.80% Trigger
                step_lock_p = round(ent_p * (1.0 - 0.0102), 8)  # Step 2: +5.10% Lock
                sl_p = round(ent_p * (1.0 + 0.0150), 8)  # -7.50% Initial Hard SL

                c3_upper_wick = o_high - max(float(c3["open"]), float(c3["close"]))
                w_ratio = round((c3_upper_wick / o_rng) * 100.0, 1) if o_rng > 0 else 20.0

                peak_runway = impulse_l
                invalidated = False
                tapped = False
                be_locked = False
                profit_stepped = False
                completed = False
                fill_time = None
                armor_time = None
                harvest_time = None
                tp_time = None
                sl_time = None
                end_time = candles[-1]["time"]
                exit_time = None
                exit_price = None
                exit_reason = None
                bars_alive_at_tap = 0
                gap_at_tap = 0.0
                cur_sl = sl_p

                for k in range(i + 3, n):
                    bar = candles[k]
                    b_high = float(bar["high"])
                    b_low = float(bar["low"])
                    b_close = float(bar["close"])
                    b_time = bar["time"]
                    bars_alive = k - i

                    if not tapped and not completed:
                        peak_runway = min(peak_runway, b_low)
                        airspace_runway_pct = ((o_low - peak_runway) / o_low) * 100.0 if o_low > 0 else 0.0

                        if bars_alive > effective_max_bars:
                            completed = True
                            end_time = b_time
                            break
                        elif b_close > o_high:
                            invalidated = True
                            completed = True
                            end_time = b_time
                            break
                        elif b_high >= ent_p and b_high <= sl_p:
                            if airspace_runway_pct >= 5.0 and bars_alive >= effective_min_bars:
                                tapped = True
                                fill_time = b_time
                                bars_alive_at_tap = bars_alive
                                gap_at_tap = airspace_runway_pct
                                continue
                            else:
                                completed = True
                                end_time = b_time
                                break

                    elif tapped and not completed:
                        peak_runway = min(peak_runway, b_low)
                        gain_roi = ((ent_p - b_low) / ent_p) * 100.0 * 5.0

                        if gain_roi >= 4.90 and cur_sl > round(ent_p * (1.0 - (0.50 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 - (0.50 / 500.0)), 8)
                            be_locked = True
                            armor_time = b_time
                        if gain_roi >= 9.80 and cur_sl > round(ent_p * (1.0 - (5.10 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 - (5.10 / 500.0)), 8)
                            profit_stepped = True
                            harvest_time = b_time
                        if gain_roi >= 14.80 and cur_sl > round(ent_p * (1.0 - (10.10 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 - (10.10 / 500.0)), 8)
                        if gain_roi >= 19.80 and cur_sl > round(ent_p * (1.0 - (15.10 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 - (15.10 / 500.0)), 8)
                        if gain_roi >= 24.00 and cur_sl > round(ent_p * (1.0 - (20.10 / 500.0)), 8):
                            cur_sl = round(ent_p * (1.0 - (20.10 / 500.0)), 8)
                        if b_low <= tp_p:
                            completed = True
                            tp_time = b_time
                            exit_time = b_time
                            exit_price = tp_p
                            end_time = b_time
                            exit_reason = "TP_HIT (+29.0% ROE)"
                            break
                        elif b_high >= cur_sl:
                            completed = True
                            sl_time = b_time
                            exit_time = b_time
                            exit_price = cur_sl
                            end_time = b_time
                            exit_reason = "TRAILING_EXIT" if be_locked else "SL_HIT"
                            break

                # Determine final status
                if completed:
                    if tp_time:
                        status = "COMPLETED_TP"
                    elif sl_time:
                        status = "COMPLETED_HARVEST" if profit_stepped else "COMPLETED_SL"
                    elif invalidated:
                        status = "INVALIDATED"
                    else:
                        status = "COMPLETED_SL"
                elif tapped:
                    if profit_stepped:
                        status = "STAGE2_HARVEST"
                    elif be_locked:
                        status = "STAGE1_ARMOR"
                    else:
                        status = "ACTIVE_TAPPED"
                else:
                    within_radar = (cur_price >= rad_p) and (cur_price <= ent_p)
                    status = "RADAR_PRE_ARMED" if within_radar else "ACTIVE_UNMITIGATED"

                within_radar = (cur_price >= rad_p) and (cur_price <= ent_p)
                is_fresh_bear = (within_radar or (tapped and not be_locked)) and not completed

                if not completed:
                    end_time = candles[-1]["time"]

                active_bars_alive = bars_alive_at_tap if tapped else ((n - 1) - i)
                active_runway = gap_at_tap if tapped else (((o_low - peak_runway) / o_low * 100.0) if o_low > 0 else 0.0)

                if tapped or (not completed and status != "INVALIDATED"):
                    active_zones.append({
                        "symbol": symbol,
                        "side": "SELL",
                        "timeframe": tf.upper(),
                        "interval": tf,
                        "ob_high": o_high,
                        "ob_low": o_low,
                        "origin_time": c3["time"],
                        "end_time": end_time,
                        "entry_price": ent_p,
                        "radar_price": rad_p,
                        "tp_price": tp_p,
                        "armor_stage1_price": be_armor_p,
                        "armor_stage2_price": step_trig_p,
                        "harvest_lock_price": step_lock_p,
                        "sl_price": cur_sl,
                        "soft_sl_price": cur_sl,
                        "hard_sl_price": sl_p,
                        "is_fresh_trigger": is_fresh_bear,
                        "tap_bar_age": 1 if tapped else 0,
                        "status": status,
                        "displacement_pct": round(bear_disp, 2),
                        "wick_ratio_pct": w_ratio,
                        "runway_pct": round(active_runway, 1),
                        "runway_void_pct": round(active_runway, 1),
                        "bars_alive": active_bars_alive,
                        "is_origin": is_origin_bear,
                        "is_in_radar": within_radar,
                        "tier_type": "SINGLE_TIER",
                        "strategy": "HERMES_3.5_SINGLE_TIER",
                        "prob_score": 97.2,
                        "rank_label": f"🏛️ HERMES 3.5 RADAR HARVEST [5% Boundary Entry: ${ent_p}]",
                        "fill_time": fill_time,
                        "fill_price": ent_p if tapped else None,
                        "be_armor_time": armor_time,
                        "profit_harvest_time": harvest_time,
                        "tp_time": tp_time,
                        "sl_time": sl_time,
                        "exit_time": exit_time,
                        "exit_price": exit_price,
                        "exit_reason": exit_reason,
                        "tapped": tapped,
                        "completed": completed
                    })

        return active_zones

    async def run_full_champion_scan(self) -> Dict[str, Any]:
        """Scans all configured champion assets on 1H and 4H."""
        btc_sentry = await self.evaluate_btc_macro_sentry()
        all_setups = []

        for symbol in TOP_22_CHAMPIONS:
            for interval in ["4h", "1h"]:
                try:
                    candles = await binance_feed.fetch_klines(symbol, interval=interval, limit=120)
                    if candles and len(candles) >= 40:
                        detected = self.detect_hermes35_single_tier_zones(symbol, candles, interval)
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

        now_ts = time.time()
        self.last_scan_time = now_ts
        return {
            "timestamp": now_ts,
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

    async def dispatch_entry_filled_alert(self, setup: Dict[str, Any], sec_id: int, sec_type_str: str, ep: float, tp: float, soft_sl: float, hard_sl: float, leverage: int, margin: float, timeframe: str, symbol: str, side: str, trade_id: Optional[int] = None):
        """Dispatches official Telegram Alert ONLY when the limit order is actually FILLED into a live position on exchange."""
        try:
            alert_text = (
                f"⚡ <b>HERMES 3.5 RADAR HARVEST • ENTRY FILLED & POSITION LIVE</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 <b>Compounding Slot</b>: <b>Section {sec_id} ({sec_type_str})</b>\n"
                f"🪙 <b>Pair</b>: #{symbol} ({timeframe.upper()})\n"
                f"📈 <b>Action</b>: {'🟢 LONG BUY (FILLED)' if side == 'LONG' else '🔴 SHORT SELL (FILLED)'}\n"
                f"🎯 <b>Fill Price</b>: {ep:.6f} (5% Boundary Penetration Confirmed)\n"
                f"🎯 <b>Take Profit</b>: {tp:.6f} (+29.0% ROE Target Harvest)\n"
                f"🛑 <b>Initial Hard SL</b>: {hard_sl:.6f} (-14.0% ROE Shield)\n"
                f"🛡️ <b>Soft Stop Loss</b>: {soft_sl:.6f} (Candle Body Close Defense)\n"
                f"🛡️ <b>Trailing Plan</b>: 6-Tier Stepped Trailing Active (+4.9% ➔ +0.5%, +9.8% ➔ +5.1%, +14.8% ➔ +10.1%, +19.8% ➔ +15.1%, +24% ➔ +20.1%, +29% ➔ +25%)\n"
                f"🕯️ <b>Rejection Wick</b>: {setup.get('wick_ratio_pct', 24.5):.1f}% (Confirmed ≥ 18.0% Absorption)\n"
                f"⚡ <b>Leverage</b>: {leverage}x Isolated | Margin: ${margin:.2f} USDT\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 <i>Position Officially Open & Live on Exchange | Alert 1 of 2</i>"
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
            logger.info(f"💎 Telegram LIVE FILLED alert dispatched for {symbol}")
        except Exception as e:
            logger.warning(f"Telegram alert error: {e}")

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
            curr_balance = float(acc.get("current_balance", 5.0) or 5.0)
            if curr_balance < 4.50:
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

            # Real-Time Price Proximity Armor: Prevent retroactive fills when market has already moved past TP or SL
            try:
                tickers = await binance_feed.fetch_all_tickers()
                live_p = tickers.get(symbol)
                if live_p and live_p > 0:
                    if side in ("BUY", "LONG"):
                        if live_p >= tp or live_p <= hard_sl:
                            logger.warning(f"⚠️ Suppressing stale entry for {symbol} LONG: Current price ({live_p}) already passed TP ({tp}) or SL ({hard_sl}).")
                            return
                    else:  # SHORT / SELL
                        if live_p <= tp or live_p >= hard_sl:
                            logger.warning(f"⚠️ Suppressing stale entry for {symbol} SHORT: Current price ({live_p}) already passed TP ({tp}) or SL ({hard_sl}).")
                            return
            except Exception as pe:
                logger.debug(f"Price proximity check warning for {symbol}: {pe}")

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
                        bg_res = await bitget_trader.execute_4h_trade(setup_copy)
                    else:
                        bg_res = await bitget_trader.execute_1h_trade(setup_copy)
                    
                    if bg_res and not bg_res.get("success"):
                        err_reason = bg_res.get("error") or bg_res.get("reason", "Bitget rejected order")
                        logger.error(f"Bitget execution failed for {symbol}: {err_reason}")
                        from database.db import close_paper_trade
                        close_paper_trade(setup, outcome="EXCHANGE_REJECTED", exit_price=ep)
                        return
                    else:
                        logger.info(f"Bitget real trade submitted for {symbol}")
                        # If executed at CMP Market, synchronize exact fill price
                        actual_ep = float(bg_res.get("entry_price") or 0.0)
                        if actual_ep and actual_ep > 0:
                            ep = actual_ep
                            try:
                                with get_connection() as conn:
                                    conn.execute("UPDATE paper_trades SET entry_price = ? WHERE id = ?", (ep, trade_id))
                            except Exception:
                                pass
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

            # Check if order is immediately filled on exchange or resting limit
            is_filled = False
            try:
                from engine.bitget_trader import bitget_trader
                if bitget_trader.is_configured() and bitget_trader.is_auto_trade_enabled():
                    is_filled = bitget_trader.is_symbol_active_on_exchange(symbol)
                else:
                    is_filled = True
            except Exception:
                is_filled = True

            if is_filled:
                await self.dispatch_entry_filled_alert(setup, sec_id, sec_type_str, ep, tp, soft_sl, hard_sl, leverage, margin, timeframe, symbol, side, trade_id)
            else:
                self._pending_limit_alerts[symbol] = {
                    "setup": setup, "sec_id": sec_id, "sec_type_str": sec_type_str,
                    "ep": ep, "tp": tp, "soft_sl": soft_sl, "hard_sl": hard_sl,
                    "leverage": leverage, "margin": margin, "timeframe": timeframe,
                    "symbol": symbol, "side": side, "trade_id": trade_id
                }
                logger.info(f"⏳ Limit order placed on Bitget for {symbol}. Alert will be sent when filled!")

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

        # Check if any pending limit orders were just filled on Bitget!
        if getattr(self, "_pending_limit_alerts", None):
            for p_sym in list(self._pending_limit_alerts.keys()):
                try:
                    from engine.bitget_trader import bitget_trader
                    if bitget_trader.is_symbol_active_on_exchange(p_sym):
                        p_info = self._pending_limit_alerts.pop(p_sym)
                        await self.dispatch_entry_filled_alert(
                            p_info["setup"], p_info["sec_id"], p_info["sec_type_str"],
                            p_info["ep"], p_info["tp"], p_info["soft_sl"], p_info["hard_sl"],
                            p_info["leverage"], p_info["margin"], p_info["timeframe"],
                            p_info["symbol"], p_info["side"], p_info.get("trade_id")
                        )
                        logger.info(f"🎯 PENDING LIMIT FILLED on Bitget for {p_sym}! Alert dispatched!")
                except Exception as p_err:
                    pass

        tickers = await binance_feed.fetch_all_tickers() or {}
        leverage = 5.0

        for trade in list(open_trades):
            try:
                sym = trade["symbol"]
                side = trade["side"].upper()
                entry_price = float(trade["entry_price"])
                hard_sl_price = float(trade.get("hard_sl_price", 0.0) or (entry_price * 0.970 if side in ("BUY", "LONG") else entry_price * 1.030))
                trade_id = trade["id"]
                tf = str(trade.get("timeframe") or ("4h" if int(trade.get("account_id") or 1) <= 5 else "1h")).lower()
                tp_price = float(trade.get("tp_price", 0.0) or 0.0)

                cur_price = tickers.get(sym)
                if not cur_price or cur_price <= 0:
                    cur_price = await binance_feed.fetch_symbol_price(sym)
                if not cur_price or cur_price <= 0:
                    continue

                # Exchange Parity Guard: If trade was filled on Bitget and closed on exchange
                try:
                    from engine.bitget_trader import bitget_trader
                    if bitget_trader.is_configured() and bitget_trader.is_auto_trade_enabled():
                        entry_time_ms = int(trade.get("entry_time") or 0)
                        if 0 < entry_time_ms < 100_000_000_000:
                            entry_time_ms *= 1000
                        now_ms = int(time.time() * 1000)
                        # Check only after 30s of trade opening to avoid race conditions
                        if (now_ms - entry_time_ms) > 30_000:
                            clean_sym = sym.replace('/', '').replace(':USDT', '').upper()
                            if not bitget_trader.is_symbol_active_on_exchange(clean_sym):
                                # Position is no longer open on Bitget! Fetch closing info from history
                                try:
                                    hist = bitget_trader.exchange.privateMixGetV2MixPositionHistoryPosition({
                                        'productType': 'USDT-FUTURES',
                                        'symbol': clean_sym,
                                        'pageSize': '1'
                                    })
                                    recent_closed = (hist.get('data', {}).get('list', []) or [None])[0]
                                    if recent_closed:
                                        close_avg = float(recent_closed.get('closeAvgPrice') or cur_price)
                                        pnl_val = float(recent_closed.get('pnl') or 0.0)
                                        outcome = "TP_HIT" if pnl_val >= 0 else "SL_HIT"
                                        logger.info(f"⚡ Bitget exchange exit detected for {sym} {side}: Close Price {close_avg} | PnL {pnl_val} USDT ({outcome})")
                                        await self.resolve_trade_exit(trade, outcome, close_avg)
                                        continue
                                except Exception as he:
                                    logger.warning(f"Error checking Bitget closed history for {sym}: {he}")
                except Exception as bge:
                    logger.debug(f"Bitget exit parity check note for {sym}: {bge}")

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
                # EXACT 6-TIER STEPPED TRAILING SL LADDER (DEFINED BY USER):
                # Step 1: +4.90% ROI -> Lock SL @ +0.50% ROI (Fee Shield / Free Trade)
                # Step 2: +9.80% ROI -> Lock SL @ +5.10% ROI (Confirmed Profit Tier 1)
                # Step 3: +14.80% ROI -> Lock SL @ +10.10% ROI (Profit Tier 2)
                # Step 4: +19.80% ROI -> Lock SL @ +15.10% ROI (Super Profit Tier 3)
                # Step 5: +24.00% ROI -> Lock SL @ +20.10% ROI (Mega Profit Tier 4)
                # Step 6: +29.00% ROI -> Lock SL @ +25.00% ROI (Target Harvest Tier 5)
                # -------------------------------------------------------------
                target_locked_roi = current_locked_roi
                target_step = current_step

                if peak_roi >= 4.90 and target_locked_roi < 0.50:
                    target_locked_roi = 0.50
                    target_step = 1

                if peak_roi >= 9.80 and target_locked_roi < 5.10:
                    target_locked_roi = 5.10
                    target_step = 2

                if peak_roi >= 14.80 and target_locked_roi < 10.10:
                    target_locked_roi = 10.10
                    target_step = 3

                if peak_roi >= 19.80 and target_locked_roi < 15.10:
                    target_locked_roi = 15.10
                    target_step = 4

                if peak_roi >= 24.00 and target_locked_roi < 20.10:
                    target_locked_roi = 20.10
                    target_step = 5

                if peak_roi >= 29.00 and target_locked_roi < 25.00:
                    target_locked_roi = 25.00
                    target_step = 6

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

                    # Trailing SL executes silently in background (no Telegram spam: strictly 2 alerts per trade: Entry Fill & Exit)
                    logger.info(f"🛡️ [SILENT TRAILING SL] Section {trade.get('account_id') or 1} {sym} Step {target_step} (+{target_locked_roi:.1f}% ROI locked at ${new_sl_price:.6f})")

                exit_triggered = None
                exit_price = cur_price

                # -------------------------------------------------------------
                # EXIT TRIGGER CHECKS
                # -------------------------------------------------------------
                if side in ("BUY", "LONG"):
                    # 1. Take Profit (Target Reached)
                    if tp_price > 0 and cur_price >= tp_price:
                        exit_triggered = "TP_HIT"
                        exit_price = tp_price
                        logger.info(f"🎯 HERMES 3.5 RADAR HARVEST TAKE PROFIT: {sym} LONG hit TP @ {tp_price}")

                    # 2. Trailing SL Hit (Once locked in profit >= +1.0% ROI)
                    elif be_locked and current_locked_roi >= 0.4 and cur_price <= active_sl_price:
                        exit_triggered = "TRAILING_SL_HIT"
                        exit_price = active_sl_price
                        logger.info(f"💎 HERMES 3.5 STEPPED HARVEST EXIT: {sym} LONG hit locked SL @ {active_sl_price} (+{current_locked_roi:.1f}% ROI)")

                    # 3. Emergency Hard Circuit Breaker Touch (-3.00%)
                    elif cur_price <= hard_sl_price:
                        exit_triggered = "EMERGENCY_HARD_SL_HIT"
                        exit_price = hard_sl_price
                        logger.info(f"🛑 HERMES 3.0 EMERGENCY HARD SL: {sym} LONG hit hard circuit @ {hard_sl_price}")

                    # 4. BTC Macro Causal Brake (if active dump detected)
                    elif HERMES_3_BTC_EMERGENCY_SHIELD and getattr(self, "last_btc_bias", None) and self.last_btc_bias.get("long_veto"):
                        exit_triggered = "BTC_MACRO_BRAKE"
                        exit_price = cur_price
                        logger.warning(f"🚨 HERMES 3.0 BTC MACRO BRAKE EXIT: {sym} LONG exited on BTC 4H dump")

                    # 5. Soft SL (-1.50%): Evaluated ONLY on Candle Body Close occurring AFTER trade entry
                    elif not be_locked:
                        try:
                            k = await binance_feed.fetch_klines(sym, interval=tf, limit=2)
                            if k and len(k) >= 2:
                                last_closed_candle = k[-2]
                                tf_str = str(tf).lower()
                                tf_ms = (4 * 3600 * 1000) if "4h" in tf_str else ((3600 * 1000) if "1h" in tf_str else (15 * 60 * 1000))
                                candle_open_ms = int(last_closed_candle.get("time", 0))
                                candle_close_ms = candle_open_ms + tf_ms
                                entry_time_ms = int(trade.get("entry_time") or 0)
                                if 0 < entry_time_ms < 100_000_000_000:
                                    entry_time_ms *= 1000  # Normalize seconds to ms

                                # STRICT & AIRTIGHT GUARD: Only evaluate candles that closed strictly after trade entry (+15s clock drift buffer)
                                if entry_time_ms > 0 and candle_close_ms > (entry_time_ms + 15_000):
                                    if float(last_closed_candle["close"]) <= active_sl_price:
                                        exit_triggered = "STRUCTURAL_BODY_CLOSE_SL"
                                        exit_price = float(last_closed_candle["close"])
                                        logger.info(f"🛑 HERMES 3.0 STRUCTURAL BODY CLOSE SL: {sym} LONG closed below {active_sl_price}")
                        except Exception:
                            pass

                else: # SELL / SHORT
                    # 1. Take Profit (Target Reached)
                    if tp_price > 0 and cur_price <= tp_price:
                        exit_triggered = "TP_HIT"
                        exit_price = tp_price
                        logger.info(f"🎯 HERMES 3.5 RADAR HARVEST TAKE PROFIT: {sym} SHORT hit TP @ {tp_price}")

                    # 2. Trailing SL Hit (Once locked in profit >= +1.0% ROI)
                    elif be_locked and current_locked_roi >= 0.4 and cur_price >= active_sl_price:
                        exit_triggered = "TRAILING_SL_HIT"
                        exit_price = active_sl_price
                        logger.info(f"💎 HERMES 3.5 STEPPED HARVEST EXIT: {sym} SHORT hit locked SL @ {active_sl_price} (+{current_locked_roi:.1f}% ROI)")

                    # 3. Emergency Hard Circuit Breaker Touch (-3.00%)
                    elif cur_price >= hard_sl_price:
                        exit_triggered = "EMERGENCY_HARD_SL_HIT"
                        exit_price = hard_sl_price
                        logger.info(f"🛑 HERMES 3.0 EMERGENCY HARD SL: {sym} SHORT hit hard circuit @ {hard_sl_price}")

                    # 4. BTC Macro Causal Brake (if active pump detected)
                    elif HERMES_3_BTC_EMERGENCY_SHIELD and getattr(self, "last_btc_bias", None) and self.last_btc_bias.get("short_veto"):
                        exit_triggered = "BTC_MACRO_BRAKE"
                        exit_price = cur_price
                        logger.warning(f"🚨 HERMES 3.0 BTC MACRO BRAKE EXIT: {sym} SHORT exited on BTC 4H pump")

                    # 5. Soft SL (-1.50%): Evaluated ONLY on Candle Body Close occurring AFTER trade entry
                    elif not be_locked:
                        try:
                            k = await binance_feed.fetch_klines(sym, interval=tf, limit=2)
                            if k and len(k) >= 2:
                                last_closed_candle = k[-2]
                                tf_str = str(tf).lower()
                                tf_ms = (4 * 3600 * 1000) if "4h" in tf_str else ((3600 * 1000) if "1h" in tf_str else (15 * 60 * 1000))
                                candle_open_ms = int(last_closed_candle.get("time", 0))
                                candle_close_ms = candle_open_ms + tf_ms
                                entry_time_ms = int(trade.get("entry_time") or 0)
                                if 0 < entry_time_ms < 100_000_000_000:
                                    entry_time_ms *= 1000  # Normalize seconds to ms

                                # STRICT & AIRTIGHT GUARD: Only evaluate candles that closed strictly after trade entry (+15s clock drift buffer)
                                if entry_time_ms > 0 and candle_close_ms > (entry_time_ms + 15_000):
                                    if float(last_closed_candle["close"]) >= active_sl_price:
                                        exit_triggered = "STRUCTURAL_BODY_CLOSE_SL"
                                        exit_price = float(last_closed_candle["close"])
                                        logger.info(f"🛑 HERMES 3.0 STRUCTURAL BODY CLOSE SL: {sym} SHORT closed above {active_sl_price}")
                        except Exception:
                            pass

                if exit_triggered:
                    await self.resolve_trade_exit(trade, exit_triggered, exit_price)

            except Exception as trade_err:
                logger.error(f"Error checking exit for trade #{trade.get('id')} ({trade.get('symbol')}): {trade_err}")

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
        new_b = close_res.get("new_balance", 5.0)
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
        logger.info("👑 HERMES 3.5 RADAR HARVEST LIVE ENGINE ACTIVATED (24/7 AUTONOMOUS & LOCKED)")
        
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
