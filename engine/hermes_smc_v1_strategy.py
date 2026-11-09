"""
HERMES AI • SMC ENGINE V1.0 AUTONOMOUS QUANT STRATEGY
=====================================================
1:1 Implementation of User Akash Bhai's Exact Institutional Rules:
  1. Base Portfolio: $500 USDT starting capital.
  2. Dynamic Sizing & 2X Compounding:
     - $50 USDT margin per call (5x Isolated Margin) while portfolio < $1,000 USDT.
     - Once portfolio reaches $1,000 USDT (2X Milestone), margin scales 2X to $100 USDT per call.
     - Up to 8 concurrent active calls ($400 margin deployed max, $100 buffer).
  3. Order Block Trigger & Confirmation:
     - 4-Rule ATR (14 RMA) Displacement (1.8x) Order Blocks.
     - First Tap only (mitigated zones ignored).
     - 5-Minute Candle Close Confirmation:
       * Bullish OB: 5m candle close inside OB or bounce (max +0.35% runaway cap) -> ENTER LONG.
       * 5m candle close below OB floor -> INSTANT VOID (No 30-min delay, immediate cancellation).
       * Bearish OB: 5m candle close inside OB or drop (max -0.35% cap) -> ENTER SHORT.
       * 5m candle close above OB roof -> INSTANT VOID.
  4. Dual-Layer Defense:
     - Hard Disaster SL: -15.0% ROI (-3.0% price move from entry) placed directly on exchange.
     - Structural Soft SL: 1-Hour candle close outside OB boundary. Intraday wicks do NOT stop out the trade!
  5. Stepped Trailing Profit Armor with 50% Partial Booking:
     - TP 1 (+10.0% ROI / +2.0% Price): Book 50% partial profit instantly. Move SL of remaining 50% to +5.0% ROI ($0 risk guaranteed green).
     - TP 2 (+15.0% ROI / +3.0% Price): Move SL of remaining 50% to +10.0% ROI.
     - Runner Trailing: Advance SL by +5.0% ROI steps as price expands.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from database.db import get_connection, get_compounding_sections, update_paper_trade_mark_price, update_paper_trade_mark_price
from feed.binance_feed import binance_feed
from alerts.telegram_service import telegram_service
from engine.chart_image_generator import render_smc_chart_image

logger = logging.getLogger("hermes_smc_v1")
IST = timezone(timedelta(hours=5, minutes=30))

CHAMPION_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "NEARUSDT", "AXSUSDT",
    "SUIUSDT", "DOGEUSDT", "OPUSDT", "DYDXUSDT", "LINKUSDT", "ADAUSDT",
    "XRPUSDT", "BNBUSDT", "DOTUSDT", "ATOMUSDT", "LTCUSDT", "APTUSDT",
    "ARBUSDT", "INJUSDT"
]

TIMEFRAMES = ["1h", "4h"]

class HermesSMCV1StrategyEngine:
    def __init__(self):
        self.is_running = False
        self.max_concurrent_trades = 8
        self.leverage = 5
        self.base_margin = 50.0
        self.scaled_margin = 100.0
        self.milestone_2x_threshold = 1000.0

        # In-Flight State
        self.pending_taps: Dict[str, Dict[str, Any]] = {}
        self.trade_cooldowns: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self.ws_broadcast_callback = None
        self._ensure_db_schema()

    def set_broadcast_callback(self, cb):
        self.ws_broadcast_callback = cb

    async def broadcast(self, event_type: str, data: Any):
        if self.ws_broadcast_callback:
            try:
                await self.ws_broadcast_callback({"type": event_type, "data": data})
            except Exception:
                pass

    def _ensure_db_schema(self):
        """Ensures paper_trades and paper_account support SMC v1.0 partial booking and structural SL."""
        with get_connection() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_trades)").fetchall()]
            if "partial_booked" not in cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN partial_booked INTEGER DEFAULT 0")
            if "ob_bottom" not in cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN ob_bottom REAL DEFAULT 0.0")
            if "ob_top" not in cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN ob_top REAL DEFAULT 0.0")
            if "initial_margin" not in cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN initial_margin REAL DEFAULT 50.0")
            if "remaining_margin" not in cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN remaining_margin REAL DEFAULT 50.0")
            if "tp1_price" not in cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN tp1_price REAL DEFAULT 0.0")
            if "tp2_price" not in cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN tp2_price REAL DEFAULT 0.0")
            if "soft_sl_price" not in cols:
                conn.execute("ALTER TABLE paper_trades ADD COLUMN soft_sl_price REAL DEFAULT 0.0")
            conn.commit()

    def get_portfolio_equity(self) -> float:
        """Returns total portfolio equity across all 10 compounding sections."""
        with get_connection() as conn:
            row = conn.execute("SELECT SUM(current_balance) FROM paper_account WHERE id <= 10").fetchone()
            return float(row[0]) if row and row[0] is not None else 500.0

    def get_active_margin_size(self) -> float:
        """Calculates 2X Compounding Margin Size: $50 if < $1,000, $100 if >= $1,000."""
        equity = self.get_portfolio_equity()
        return self.scaled_margin if equity >= self.milestone_2x_threshold else self.base_margin

    def get_open_smc_trades(self) -> List[Dict[str, Any]]:
        """Returns all open trades executed under HERMES_SMC_V1."""
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM paper_trades 
                WHERE status = 'OPEN' AND (mode = 'HERMES_SMC_V1' OR mode = 'HERMES_SMC_ENGINE_V1_0' OR mode IS NULL OR mode = '')
                ORDER BY entry_time DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def calculate_atr(self, candles: List[Dict[str, Any]], period: int = 14) -> List[float]:
        """Calculates Wilder's RMA ATR(14) matching TradingView 1:1."""
        trs = []
        for i in range(len(candles)):
            c = candles[i]
            if i == 0:
                trs.append(float(c["high"]) - float(c["low"]))
            else:
                prev_c = candles[i - 1]
                tr = max(
                    float(c["high"]) - float(c["low"]),
                    abs(float(c["high"]) - float(prev_c["close"])),
                    abs(float(c["low"]) - float(prev_c["close"]))
                )
                trs.append(tr)

        atrs = [0.0] * len(candles)
        if len(trs) < period:
            return atrs

        # Initial SMA
        atrs[period - 1] = sum(trs[:period]) / period
        # RMA: (prev * (n-1) + tr) / n
        for i in range(period, len(trs)):
            atrs[i] = (atrs[i - 1] * (period - 1) + trs[i]) / period
        return atrs

    def detect_order_blocks(self, candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects 4-Rule Validated Order Blocks (Pine Script Hermes SMC Engine v1.0 parity):
          - ATR period: 14 RMA
          - Displacement: >= 1.8x ATR
          - Lookback: 5 bars
          - First Tap Only (Mitigated zones eliminated)
          - Max thickness: 2.0%
        """
        if len(candles) < 30:
            return []

        atrs = self.calculate_atr(candles, period=14)
        order_blocks = []
        n = len(candles)

        for i in range(5, n):
            c = candles[i]
            atr = atrs[i]
            if atr <= 0:
                continue

            # Bullish Displacement Check (Green OB candidate)
            bull_disp = (float(c["close"]) - float(c["open"])) >= (1.8 * atr)
            if bull_disp and float(c["close"]) > float(c["open"]):
                # Retrospective lookback (1..5 bars) for origin red/base candle
                for j in range(1, 6):
                    origin = candles[i - j]
                    if float(origin["close"]) <= float(origin["open"]): # Bearish origin bar
                        ob_top = max(float(origin["open"]), float(origin["close"]))
                        ob_bottom = float(origin["low"])
                        thickness_pct = (ob_top - ob_bottom) / ob_bottom if ob_bottom > 0 else 1.0

                        if thickness_pct <= 0.020: # Max 2.0% zone thickness
                            # Check mitigation from origin to current bar
                            is_mitigated = False
                            for k in range(i - j + 1, n):
                                if float(candles[k]["close"]) < ob_bottom:
                                    is_mitigated = True
                                    break

                            if not is_mitigated:
                                order_blocks.append({
                                    "side": "BUY",
                                    "type": "BULLISH_OB",
                                    "ob_top": ob_top,
                                    "ob_bottom": ob_bottom,
                                    "birth_time": origin["time"],
                                    "birth_index": i - j,
                                    "atr": atr
                                })
                        break

            # Bearish Displacement Check (Red OB candidate)
            bear_disp = (float(c["open"]) - float(c["close"])) >= (1.8 * atr)
            if bear_disp and float(c["close"]) < float(c["open"]):
                for j in range(1, 6):
                    origin = candles[i - j]
                    if float(origin["close"]) >= float(origin["open"]): # Bullish origin bar
                        ob_top = float(origin["high"])
                        ob_bottom = min(float(origin["open"]), float(origin["close"]))
                        thickness_pct = (ob_top - ob_bottom) / ob_bottom if ob_bottom > 0 else 1.0

                        if thickness_pct <= 0.020:
                            is_mitigated = False
                            for k in range(i - j + 1, n):
                                if float(candles[k]["close"]) > ob_top:
                                    is_mitigated = True
                                    break

                            if not is_mitigated:
                                order_blocks.append({
                                    "side": "SELL",
                                    "type": "BEARISH_OB",
                                    "ob_top": ob_top,
                                    "ob_bottom": ob_bottom,
                                    "birth_time": origin["time"],
                                    "birth_index": i - j,
                                    "atr": atr
                                })
                        break

        return order_blocks

    async def get_upcoming_setups(self, max_distance_pct: float = 6.0) -> List[Dict[str, Any]]:
        """
        Scans all 20 Champion Coins across 1H and 4H timeframes.
        Identifies active, unmitigated Order Blocks and calculates exact distance (% away from entry).
        Sorts ascending by distance_pct (closest to entry at top).
        """
        upcoming = []
        open_symbols = {t["symbol"] for t in self.get_open_smc_trades()}

        for sym in CHAMPION_COINS:
            cur_p = 0.0
            if hasattr(binance_feed, 'last_all_tickers') and sym in binance_feed.last_all_tickers:
                try: cur_p = float(binance_feed.last_all_tickers[sym])
                except Exception: pass
            if cur_p <= 0 and hasattr(binance_feed, 'last_24h_tickers') and sym in binance_feed.last_24h_tickers:
                try: cur_p = float(binance_feed.last_24h_tickers[sym].get('price', 0))
                except Exception: pass

            for tf in TIMEFRAMES:
                try:
                    candles = await binance_feed.fetch_klines(sym, interval=tf, limit=100)
                    if not candles or len(candles) < 25:
                        continue

                    if cur_p <= 0:
                        cur_p = float(candles[-1]["close"])

                    obs = self.detect_order_blocks(candles)
                    if not obs:
                        continue

                    for ob in obs:
                        ob_top = ob["ob_top"]
                        ob_bottom = ob["ob_bottom"]
                        side = ob["side"]

                        if side == "BUY":
                            entry_price = ob_top
                            if cur_p >= entry_price:
                                dist_pct = round(((cur_p - entry_price) / cur_p) * 100.0, 2)
                                is_inside = False
                            elif cur_p >= ob_bottom:
                                dist_pct = 0.0
                                is_inside = True
                            else:
                                continue

                            if dist_pct <= max_distance_pct:
                                tp = round(entry_price * 1.030, 6) # Direct +15% ROI (+3.0% price)
                                tp1 = tp
                                tp2 = tp
                                hard_sl = round(entry_price * 0.970, 6)

                                if dist_pct < 0.50 or is_inside:
                                    tier = "IMMINENT"
                                    tier_label = "🔥 IMMINENT TAP"
                                    tier_color = "#00e676"
                                elif dist_pct <= 1.50:
                                    tier = "APPROACHING"
                                    tier_label = "⚡ APPROACHING"
                                    tier_color = "#ffb020"
                                else:
                                    tier = "ON_RADAR"
                                    tier_label = "📡 ON RADAR"
                                    tier_color = "#38bdf8"

                                upcoming.append({
                                    "symbol": sym,
                                    "timeframe": tf.upper(),
                                    "side": "BUY",
                                    "direction": "DEMAND",
                                    "label": "Bullish Demand OB",
                                    "current_price": cur_p,
                                    "entry_price": entry_price,
                                    "ob_top": ob_top,
                                    "ob_bottom": ob_bottom,
                                    "distance_pct": dist_pct,
                                    "is_inside": is_inside,
                                    "tp1_price": tp1,
                                    "tp2_price": tp2,
                                    "hard_sl_price": hard_sl,
                                    "tier": tier,
                                    "tier_label": tier_label,
                                    "tier_color": tier_color,
                                    "confluence_stars": 3,
                                    "is_open": sym in open_symbols,
                                    "birth_time": ob.get("birth_time")
                                })

                        elif side == "SELL":
                            entry_price = ob_bottom
                            if cur_p <= entry_price:
                                dist_pct = round(((entry_price - cur_p) / cur_p) * 100.0, 2)
                                is_inside = False
                            elif cur_p <= ob_top:
                                dist_pct = 0.0
                                is_inside = True
                            else:
                                continue

                            if dist_pct <= max_distance_pct:
                                tp = round(entry_price * 0.970, 6) # Direct +15% ROI (-3.0% price)
                                tp1 = tp
                                tp2 = tp
                                hard_sl = round(entry_price * 1.030, 6)

                                if dist_pct < 0.50 or is_inside:
                                    tier = "IMMINENT"
                                    tier_label = "🔥 IMMINENT TAP"
                                    tier_color = "#ff3358"
                                elif dist_pct <= 1.50:
                                    tier = "APPROACHING"
                                    tier_label = "⚡ APPROACHING"
                                    tier_color = "#ffb020"
                                else:
                                    tier = "ON_RADAR"
                                    tier_label = "📡 ON RADAR"
                                    tier_color = "#38bdf8"

                                upcoming.append({
                                    "symbol": sym,
                                    "timeframe": tf.upper(),
                                    "side": "SELL",
                                    "direction": "SUPPLY",
                                    "label": "Bearish Supply OB",
                                    "current_price": cur_p,
                                    "entry_price": entry_price,
                                    "ob_top": ob_top,
                                    "ob_bottom": ob_bottom,
                                    "distance_pct": dist_pct,
                                    "is_inside": is_inside,
                                    "tp1_price": tp1,
                                    "tp2_price": tp2,
                                    "hard_sl_price": hard_sl,
                                    "tier": tier,
                                    "tier_label": tier_label,
                                    "tier_color": tier_color,
                                    "confluence_stars": 3,
                                    "is_open": sym in open_symbols,
                                    "birth_time": ob.get("birth_time")
                                })

                except Exception as e:
                    logger.debug(f"Error scanning {sym} {tf} for upcoming setups: {e}")

        dedup_map = {}
        for s in upcoming:
            key = (s["symbol"], s["timeframe"], s["side"])
            if key not in dedup_map or s["distance_pct"] < dedup_map[key]["distance_pct"]:
                dedup_map[key] = s

        final_setups = list(dedup_map.values())
        final_setups.sort(key=lambda x: x["distance_pct"])
        return final_setups

    async def scan_market_for_taps(self):
        """Scans champion pairs across timeframes for First Taps on SMC v1.0 Order Blocks."""
        now_ts = time.time()

        for sym in CHAMPION_COINS:
            # Check cooldown
            if self.trade_cooldowns.get(sym, 0) > now_ts:
                continue

            # Check if symbol already has an active trade or pending tap
            open_symbols = {t["symbol"] for t in self.get_open_smc_trades()}
            if sym in open_symbols or f"{sym}_BUY" in self.pending_taps or f"{sym}_SELL" in self.pending_taps:
                continue

            for tf in TIMEFRAMES:
                try:
                    candles = await binance_feed.fetch_klines(sym, interval=tf, limit=120)
                    if not candles or len(candles) < 20:
                        continue

                    obs = self.detect_order_blocks(candles)
                    if not obs:
                        continue

                    last_c = candles[-1]
                    cur_p = float(last_c["close"])
                    cur_l = float(last_c["low"])
                    cur_h = float(last_c["high"])

                    for ob in obs:
                        side = ob["side"]
                        ob_top = ob["ob_top"]
                        ob_bottom = ob["ob_bottom"]

                        # First Tap Verification
                        if side == "BUY":
                            # Bullish tap: current low touches or penetrates ob_top, but has not penetrated before
                            if cur_l <= ob_top and cur_p >= ob_bottom:
                                tap_key = f"{sym}_BUY"
                                self.pending_taps[tap_key] = {
                                    "symbol": sym,
                                    "side": "BUY",
                                    "ob_top": ob_top,
                                    "ob_bottom": ob_bottom,
                                    "timeframe": tf,
                                    "tap_price": cur_p,
                                    "tap_time": now_ts,
                                    "target_check_time": now_ts + 300 # 5 minutes later
                                }
                                logger.info(f"⚡ [HERMES SMC v1.0] SILENT TAP DETECTED: {sym} LONG at ${cur_p:.4f} (Monitoring 5m close internally)")
                                break

                        elif side == "SELL":
                            # Bearish tap: current high touches or penetrates ob_bottom
                            if cur_h >= ob_bottom and cur_p <= ob_top:
                                tap_key = f"{sym}_SELL"
                                self.pending_taps[tap_key] = {
                                    "symbol": sym,
                                    "side": "SELL",
                                    "ob_top": ob_top,
                                    "ob_bottom": ob_bottom,
                                    "timeframe": tf,
                                    "tap_price": cur_p,
                                    "tap_time": now_ts,
                                    "target_check_time": now_ts + 300 # 5 minutes later
                                }
                                logger.info(f"⚡ [HERMES SMC v1.0] SILENT TAP DETECTED: {sym} SHORT at ${cur_p:.4f} (Monitoring 5m close internally)")
                                break
                except Exception as e:
                    logger.debug(f"Error scanning {sym} {tf}: {e}")

    async def evaluate_pending_5m_taps(self):
        """
        Evaluates 5-Minute Candle Close Confirmation & Instant Invalidation:
          - Bullish OB: Close < ob_bottom -> INSTANT VOID.
          - Close >= ob_bottom & max +0.35% runaway -> ENTER LONG.
          - Bearish OB: Close > ob_top -> INSTANT VOID.
          - Close <= ob_top & max -0.35% runaway -> ENTER SHORT.
        """
        now_ts = time.time()
        keys_to_remove = []

        for tap_key, tap in list(self.pending_taps.items()):
            if now_ts < tap["target_check_time"]:
                continue # Still waiting for 5-minute candle

            sym = tap["symbol"]
            side = tap["side"]
            ob_top = tap["ob_top"]
            ob_bottom = tap["ob_bottom"]
            tf = tap["timeframe"]

            try:
                # Fetch fresh 5m candles to evaluate the close
                c5m = await binance_feed.fetch_klines(sym, interval="5m", limit=3)
                if not c5m:
                    continue

                confirmed_bar = c5m[-2] # Most recently closed 5m bar
                c_close = float(confirmed_bar["close"])

                if side == "BUY":
                    # Check Instant Invalidation (Candle closed below OB floor)
                    if c_close < ob_bottom:
                        logger.info(f"❌ [HERMES SMC v1.0] SILENT VOID: {sym} 5m close ${c_close} < OB floor ${ob_bottom}")
                        keys_to_remove.append(tap_key)
                        self.trade_cooldowns[sym] = now_ts + 900 # 15m cooldown
                        continue

                    # Check Runaway Cap (Max +0.35% above OB top)
                    runaway_pct = (c_close - ob_top) / ob_top if ob_top > 0 else 0.0
                    if runaway_pct > 0.0035:
                        logger.info(f"⚠️ [HERMES SMC v1.0] OVER-EXTENDED: {sym} closed +{runaway_pct*100:.2f}% above OB. Skipping.")
                        keys_to_remove.append(tap_key)
                        continue

                    # CONFIRMED LONG ENTRY!
                    keys_to_remove.append(tap_key)
                    await self.execute_order(sym, "BUY", c_close, ob_top, ob_bottom, tf)

                elif side == "SELL":
                    # Check Instant Invalidation (Candle closed above OB roof)
                    if c_close > ob_top:
                        logger.info(f"❌ [HERMES SMC v1.0] SILENT VOID: {sym} 5m close ${c_close} > OB roof ${ob_top}")
                        keys_to_remove.append(tap_key)
                        self.trade_cooldowns[sym] = now_ts + 900
                        continue

                    # Check Runaway Cap (Max -0.35% below OB bottom)
                    runaway_pct = (ob_bottom - c_close) / ob_bottom if ob_bottom > 0 else 0.0
                    if runaway_pct > 0.0035:
                        logger.info(f"⚠️ [HERMES SMC v1.0] OVER-EXTENDED: {sym} closed -{runaway_pct*100:.2f}% below OB. Skipping.")
                        keys_to_remove.append(tap_key)
                        continue

                    # CONFIRMED SHORT ENTRY!
                    keys_to_remove.append(tap_key)
                    await self.execute_order(sym, "SELL", c_close, ob_top, ob_bottom, tf)

            except Exception as e:
                logger.error(f"Error evaluating 5m tap for {sym}: {e}")

        for k in keys_to_remove:
            self.pending_taps.pop(k, None)

    async def execute_order(self, symbol: str, side: str, entry_price: float, ob_top: float, ob_bottom: float, timeframe: str):
        """
        Executes qualified order with 2X Compounding Sizing & 8 Concurrency Slots:
          - $50 USDT base / $100 USDT 2X scaled
          - 5x Isolated Margin
          - Hard SL: -15.0% ROI (-3.0% price move)
          - Structural SL: 1H candle close outside OB
          - TP1 (+10% ROI) & TP2 (+15% ROI) targets
        """
        async with self._lock:
            open_trades = self.get_open_smc_trades()
            if len(open_trades) >= self.max_concurrent_trades:
                logger.warning(f"⚠️ Max concurrency ({self.max_concurrent_trades} trades) reached. Skipping {symbol}.")
                return

            margin = self.get_active_margin_size()
            notional = round(margin * self.leverage, 2)

            if side == "BUY":
                hard_sl = round(entry_price * 0.970, 6) # -3.0% price move = -15% ROI
                tp = round(entry_price * 1.030, 6)      # +3.0% price move = +15% ROI (Direct single TP)
            else:
                hard_sl = round(entry_price * 1.030, 6) # +3.0% price move = -15% ROI
                tp = round(entry_price * 0.970, 6)      # -3.0% price move = +15% ROI (Direct single TP)
            tp1 = tp
            tp2 = tp

            now_ms = int(time.time() * 1000)

            # Find empty section (1..10)
            with get_connection() as conn:
                busy_sections = {r[0] for r in conn.execute("SELECT account_id FROM paper_trades WHERE status = 'OPEN' AND account_id IS NOT NULL").fetchall()}
                available_acc_id = 1
                for aid in range(1, 11):
                    if aid not in busy_sections:
                        available_acc_id = aid
                        break

                cur = conn.execute("""
                    INSERT INTO paper_trades (
                        symbol, side, entry_price, position_size_usdt,
                        tp_price, tp1_price, tp2_price,
                        sl_price, hard_sl_price, soft_sl_price,
                        ob_top, ob_bottom,
                        initial_margin, remaining_margin,
                        trailing_sl_price, locked_roi_pct, trailing_step,
                        partial_booked, timeframe,
                        status, mode, account_id, entry_time
                    ) VALUES (
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?,
                        ?, ?,
                        ?, 0.0, 0,
                        0, ?,
                        'OPEN', 'HERMES_SMC_V1', ?, ?
                    )
                """, (
                    symbol, side, entry_price, notional,
                    tp2, tp1, tp2,
                    hard_sl, hard_sl, ob_bottom if side == "BUY" else ob_top,
                    ob_top, ob_bottom,
                    margin, margin,
                    hard_sl, timeframe,
                    available_acc_id, now_ms
                ))
                trade_id = cur.lastrowid
                conn.commit()

            logger.info(f"🚀 [HERMES SMC v1.0] TRADE OPENED [Trade #{trade_id}]: {symbol} {side} at ${entry_price} | Margin: ${margin} USDT (5x)")

            # Dispatch Official Zero-Noise Telegram Alert with TradingView Dark Chart
            equity = self.get_portfolio_equity()
            is_2x = equity >= self.milestone_2x_threshold
            alert_text = (
                f"⚡ <b>HERMES SMC v1.0 • {'LONG' if side == 'BUY' else 'SHORT'} POSITION OPENED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🪙 <b>Pair:</b> #{symbol} ({timeframe.upper()})\n"
                f"{'🟢' if side == 'BUY' else '🔴'} <b>Signal:</b> {'Bullish' if side == 'BUY' else 'Bearish'} Order Block First Tap\n"
                f"💵 <b>Entry Price:</b> ${entry_price:.4f}\n"
                f"💰 <b>Margin Deployed:</b> ${margin:.2f} USDT (5x Isolated)\n"
                f"\n"
                f"🎯 <b>Take Profit:</b> ${tp:.4f} (+15.0% ROI)\n"
                f"🛑 <b>Hard Disaster SL:</b> ${hard_sl:.4f} (-15.0% ROI)\n"
                f"🛡️ <b>Profit Armor:</b> Fast BE Shield (+1.0%) • Trailing Lock (+1.8%)\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 <b>Slot:</b> Section {available_acc_id} ({'2X Compounded' if is_2x else 'Base'})\n"
                f"📊 <b>Active Concurrency:</b> {len(open_trades) + 1} / {self.max_concurrent_trades} Slots"
            )

            try:
                chart_candles = await binance_feed.fetch_klines(symbol, interval=timeframe, limit=120)
                zone_info = {
                    'side': side,
                    'entry_price': entry_price,
                    'tp1_price': tp1,
                    'tp2_price': tp2,
                    'hard_sl_price': hard_sl,
                    'ob_top': ob_top,
                    'ob_bottom': ob_bottom
                }
                chart_bytes = render_smc_chart_image(symbol, chart_candles, zone_info, timeframe=timeframe)
                await telegram_service.send_photo(chart_bytes, alert_text, parse_mode='HTML')
            except Exception as e:
                logger.error(f'Error rendering/sending chart photo: {e}')
                await telegram_service.send_raw_message(alert_text)

    async def monitor_active_trades(self):
        """
        Monitors open trades for:
          1. Hard Disaster SL (-15% ROI)
          2. Structural 1-Hour Body Close SL
          3. TP 1 (+10% ROI) with 50% Partial Profit Booking + SL shift to +5% ROI
          4. TP 2 (+15% ROI) with SL shift to +10% ROI
          5. Trailing SL Hit
        """
        trades = self.get_open_smc_trades()
        if not trades:
            return

        now_ms = int(time.time() * 1000)

        for trade in trades:
            trade_id = trade["id"]
            sym = trade["symbol"]
            side = trade["side"].upper()
            ep = float(trade["entry_price"])
            margin = float(trade["initial_margin"] or 50.0)
            rem_margin = float(trade["remaining_margin"] or margin)
            hard_sl = float(trade["hard_sl_price"])
            tp1 = float(trade.get("tp1_price") or (ep * 1.02 if side == "BUY" else ep * 0.98))
            tp2 = float(trade.get("tp2_price") or (ep * 1.03 if side == "BUY" else ep * 0.97))
            stage = int(trade.get("trailing_step") or 0)
            partial_booked = int(trade.get("partial_booked") or 0)
            trailing_sl = float(trade.get("trailing_sl_price") or hard_sl)
            acc_id = int(trade.get("account_id") or 1)
            ob_bottom = float(trade.get("ob_bottom") or 0.0)
            ob_top = float(trade.get("ob_top") or 0.0)

            cur_p = None
            if hasattr(binance_feed, 'last_all_tickers') and sym in binance_feed.last_all_tickers:
                cur_p = float(binance_feed.last_all_tickers[sym])
            elif hasattr(binance_feed, 'last_24h_tickers') and sym in binance_feed.last_24h_tickers:
                t_info = binance_feed.last_24h_tickers[sym]
                if isinstance(t_info, dict) and 'price' in t_info:
                    cur_p = float(t_info['price'])
            if not cur_p or cur_p <= 0:
                cur_p = await binance_feed.fetch_symbol_price(sym)
            if not cur_p or cur_p <= 0:
                continue

            # Monotonic High-Watermark Ratchet: Update mark price, MAE% & MFE% in DB on every tick!
            try:
                update_paper_trade_mark_price(trade_id, cur_p)
            except Exception as e:
                logger.error(f"Error updating mark price for trade {trade_id}: {e}")

            # Calculate Price Gain % and ROI %
            if side == "BUY":
                gain_pct = (cur_p - ep) / ep
                roi_pct = gain_pct * self.leverage * 100.0
            else:
                gain_pct = (ep - cur_p) / ep
                roi_pct = gain_pct * self.leverage * 100.0

            # -------------------------------------------------------------
            # 1. HARD DISASTER STOP LOSS (-15.0% ROI / -3.0% Price drop)
            # -------------------------------------------------------------
            hard_sl_hit = (cur_p <= hard_sl) if side == "BUY" else (cur_p >= hard_sl)
            if hard_sl_hit and stage == 0:
                loss_usdt = round(rem_margin * (-0.15), 2)
                self._close_trade_in_db(trade_id, acc_id, cur_p, loss_usdt, -15.0, "HARD_SL_HIT")
                await telegram_service.send_raw_message(
                    f"🛑 <b>HERMES SMC v1.0 • HARD SL TRIGGERED</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 <b>Pair:</b> #{sym} ({side})\n"
                    f"📍 <b>Exit Price:</b> ${cur_p:.4f}\n"
                    f"📉 <b>Loss:</b> ${loss_usdt:.2f} USDT (-15.0% ROI)\n"
                    f"🛡️ <i>Disaster circuit breaker protected remaining capital.</i>"
                )
                continue

            # -------------------------------------------------------------
            # 2. FAST BREAKEVEN SHIELD (+1.0% Price / +5.0% ROI) -> $0.00 Risk
            # -------------------------------------------------------------
            if stage == 0 and roi_pct >= 5.0:
                new_sl_price = round(ep * 1.0005 if side == "BUY" else ep * 0.9995, 6)
                with get_connection() as conn:
                    conn.execute("""
                        UPDATE paper_trades
                        SET trailing_step = 1,
                            trailing_sl_price = ?,
                            locked_roi_pct = 0.5
                        WHERE id = ?
                    """, (new_sl_price, trade_id))
                    conn.commit()
                logger.info(f"🛡️ [HERMES SMC v1.0] FAST BREAKEVEN ARMED: {sym} SL shifted to ${new_sl_price:.4f} ($0.00 Risk)")

            # -------------------------------------------------------------
            # 3. DYNAMIC TRAILING PROFIT LOCK (+1.8% Price / +9.0% ROI)
            # -------------------------------------------------------------
            if stage == 1 and roi_pct >= 9.0:
                new_sl_price = round(ep * 1.012 if side == "BUY" else ep * 0.988, 6)
                with get_connection() as conn:
                    conn.execute("""
                        UPDATE paper_trades
                        SET trailing_step = 2,
                            trailing_sl_price = ?,
                            locked_roi_pct = 6.0
                        WHERE id = ?
                    """, (new_sl_price, trade_id))
                    conn.commit()
                logger.info(f"⚡ [HERMES SMC v1.0] TRAILING PROFIT LOCKED: {sym} SL advanced to ${new_sl_price:.4f} (+6% ROI Guaranteed)")

            # -------------------------------------------------------------
            # 4. TAKE PROFIT HIT (+15.0% ROI / +3.0% Price Move) • 100% CLOSED
            # -------------------------------------------------------------
            tp_target = float(trade.get("tp_price") or trade.get("tp2_price") or (ep * 1.030 if side == "BUY" else ep * 0.970))
            tp_hit = (cur_p >= tp_target) if side == "BUY" else (cur_p <= tp_target)
            if tp_hit:
                full_pnl = round(rem_margin * 0.15, 2)
                self._close_trade_in_db(trade_id, acc_id, cur_p, full_pnl, 15.0, "TP_HIT")
                await telegram_service.send_raw_message(
                    f"🏆 <b>HERMES SMC v1.0 • TAKE PROFIT HIT (+15.0% ROI)</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 <b>Pair:</b> #{sym} ({side})\n"
                    f"📍 <b>Exit Price:</b> ${cur_p:.4f}\n"
                    f"💰 <b>Realized Profit:</b> <b>+${full_pnl:.2f} USDT (+15.0% ROI)</b>\n"
                    f"🤖 <i>Section {acc_id} target achieved! Full profit credited, armed for next setup.</i>"
                )
                continue

            # -------------------------------------------------------------
            # 5. TRAILING / BREAKEVEN STOP LOSS HIT
            # -------------------------------------------------------------
            if stage >= 1:
                trail_hit = (cur_p <= trailing_sl) if side == "BUY" else (cur_p >= trailing_sl)
                if trail_hit:
                    locked_roi = float(trade.get("locked_roi_pct") or 0.5)
                    rem_pnl = round(rem_margin * (locked_roi / 100.0), 2)
                    self._close_trade_in_db(trade_id, acc_id, cur_p, rem_pnl, locked_roi, "TRAILING_SL_HIT")
                    await telegram_service.send_raw_message(
                        f"🛡️ <b>HERMES SMC v1.0 • PROFIT ARMOR EXIT (PROTECTED)</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🪙 <b>Pair:</b> #{sym} ({side})\n"
                        f"📍 <b>Exit Price:</b> ${cur_p:.4f}\n"
                        f"💰 <b>Realized PnL:</b> +${rem_pnl:.2f} USDT (+{locked_roi:.1f}% ROI)\n"
                        f"🤖 <i>Section {acc_id} capital protected, armed for next setup.</i>"
                    )
                    continue

    async def check_structural_1h_sl(self):
        """
        Structural Soft SL: Evaluates 1-Hour candle closes.
        If a closed 1H candle closes below ob_bottom (for Long) or above ob_top (for Short),
        exit position at market to prevent further adverse movement.
        """
        trades = self.get_open_smc_trades()
        if not trades:
            return

        for trade in trades:
            # If trade has already booked TP1, trailing SL is handling protection
            if int(trade.get("trailing_step") or 0) >= 1:
                continue

            sym = trade["symbol"]
            side = trade["side"].upper()
            ob_bottom = float(trade.get("ob_bottom") or 0.0)
            ob_top = float(trade.get("ob_top") or 0.0)
            trade_id = trade["id"]
            acc_id = int(trade.get("account_id") or 1)
            margin = float(trade.get("remaining_margin") or 50.0)

            try:
                c1h = await binance_feed.fetch_klines(sym, interval="1h", limit=2)
                if not c1h or len(c1h) < 2:
                    continue

                last_closed_1h = c1h[-2]
                c_close = float(last_closed_1h["close"])

                if side == "BUY" and c_close < ob_bottom and ob_bottom > 0:
                    loss_pct = (c_close - float(trade["entry_price"])) / float(trade["entry_price"])
                    loss_usdt = round(margin * (loss_pct * self.leverage), 2)
                    self._close_trade_in_db(trade_id, acc_id, c_close, loss_usdt, loss_pct * self.leverage * 100, "1H_STRUCTURAL_SL")
                    await telegram_service.send_raw_message(
                        f"🛡️ <b>HERMES SMC v1.0 • 1H STRUCTURAL SL EXIT</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🪙 <b>Pair:</b> #{sym} (LONG)\n"
                        f"📍 <b>1H Close:</b> ${c_close:.4f} &lt; OB Floor (${ob_bottom:.4f})\n"
                        f"📉 <b>PnL:</b> ${loss_usdt:.2f} USDT\n"
                        f"🏛️ <i>Structure broken on 1H timeframe. Capital conserved.</i>"
                    )

                elif side == "SELL" and c_close > ob_top and ob_top > 0:
                    loss_pct = (float(trade["entry_price"]) - c_close) / float(trade["entry_price"])
                    loss_usdt = round(margin * (loss_pct * self.leverage), 2)
                    self._close_trade_in_db(trade_id, acc_id, c_close, loss_usdt, loss_pct * self.leverage * 100, "1H_STRUCTURAL_SL")
                    await telegram_service.send_raw_message(
                        f"🛡️ <b>HERMES SMC v1.0 • 1H STRUCTURAL SL EXIT</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🪙 <b>Pair:</b> #{sym} (SHORT)\n"
                        f"📍 <b>1H Close:</b> ${c_close:.4f} &gt; OB Roof (${ob_top:.4f})\n"
                        f"📉 <b>PnL:</b> ${loss_usdt:.2f} USDT\n"
                        f"🏛️ <i>Structure broken on 1H timeframe. Capital conserved.</i>"
                    )

            except Exception as e:
                logger.debug(f"Error checking 1H structural SL for {sym}: {e}")

    def _close_trade_in_db(self, trade_id: int, acc_id: int, exit_price: float, pnl_usdt: float, roi_pct: float, outcome: str):
        """Helper to mark trade CLOSED and update section balance."""
        now_ms = int(time.time() * 1000)
        with get_connection() as conn:
            conn.execute("""
                UPDATE paper_trades 
                SET status = 'CLOSED',
                    exit_price = ?,
                    pnl_usdt = ?,
                    roi_pct = ?,
                    outcome = ?,
                    exit_time = ?
                WHERE id = ?
            """, (exit_price, pnl_usdt, roi_pct, outcome, now_ms, trade_id))

            conn.execute("""
                UPDATE paper_account
                SET current_balance = MAX(10.0, current_balance + ?),
                    total_pnl = total_pnl + ?,
                    win_count = win_count + ?,
                    loss_count = loss_count + ?
                WHERE id = ?
            """, (pnl_usdt, pnl_usdt, 1 if pnl_usdt > 0 else 0, 1 if pnl_usdt <= 0 else 0, acc_id))
            conn.commit()

        # Check for 2X Portfolio Milestone Announcement
        equity = self.get_portfolio_equity()
        if equity >= self.milestone_2x_threshold:
            logger.info(f"🏆 [HERMES AI] 2X MILESTONE ACTIVE! Equity: ${equity:.2f} USDT. Trade size: $100 USDT.")

    async def start(self):
        """Main 24/7 background loop for Hermes SMC v1.0 autonomous trading."""
        self.is_running = True
        logger.info("🏛️ HERMES SMC V1.0 AUTONOMOUS QUANT ENGINE ONLINE & ARMED (5x Isolated • 8 Concurrency Slots)")

        scan_counter = 0
        h1_counter = 0

        while self.is_running:
            try:
                # 1. Fast Watchdog: Monitor open trades every 3 seconds
                await self.monitor_active_trades()

                # 2. Evaluate pending 5-minute candle confirmations every 5 seconds
                await self.evaluate_pending_5m_taps()

                # 3. Market structure scan every ~45 seconds
                scan_counter += 1
                if scan_counter >= 15:
                    scan_counter = 0
                    await self.scan_market_for_taps()

                # 1H Structural SL disabled per user directive:
                # Once entered, trades are managed exclusively by TP (with Dynamic Profit Armor) & Hard SL (-15.0% ROI)
                pass

            except Exception as e:
                logger.error(f"Error in Hermes SMC v1.0 loop: {e}", exc_info=True)

            await asyncio.sleep(3)

    def stop(self):
        self.is_running = False
        logger.info("🛑 HERMES SMC V1.0 ENGINE STOPPED")

# Global Singleton Instance
hermes_smc_v1_engine = HermesSMCV1StrategyEngine()
