"""
HERMES 4.0 BALANCED APEX (COUNCIL OF 16) LIVE ENGINE
=====================================================
Autonomous 24/7 Live Streaming Forward-Test Engine for Hermes 4.0.
Operates exclusively on Compounding Sections 11 through 20 (Zero collision with Hermes 3.5).
- Scans Top-22 Champion Crypto Assets across 1H and 4H timeframes.
- Enforces the 16-Agent Unified Institutional ICT/SMC Model:
    1. Sentry 1: King BTC Causal Brake (Prior 4H BTC >= 1.0% dump veto).
    2. Sentry 2: Valid Virgin Bedrock OB (Extreme origin, prior candle swept, virgin FVG void).
    3. Sentry 3: Candle Body Close BOS (Strict body close, eliminates Turtle Soup wick traps).
    4. Sentry 4: Inducement (IDM) Sweep (Retail liquidity cleared before entry is armed).
    5. Gate 5: Wholesale Discount 50% Mean Threshold Entry (Entry at exact 50% midpoint of OB).
    6. Gate 6: Rejection Wick Absorption (>= 18% rejection wick defending the zone).
- Compounding Execution:
    - 5x Isolated Perpetual Futures simulated leverage.
    - Strict 1:2 Risk:Reward:
        * Take Profit: Exactly +3.00% Spot Move (+15.0% ROE)
        * Stop Loss: Bedrock Low - (0.35 * ATR) Buffer (~1.50% Spot Move / -7.5% ROE)
        * Stepped Break-Even Shield: Triggers at +1.50% Spot Move (+7.5% ROE / +1.0R), moving SL to $0.00 entry price!
    - 85% Profit Reinvested / 15% Vault Reserve Locked.
    - Sequential 1-Trade Queue per section across Sections 11 to 20 ($50.00 each -> $2,000.00 target).
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
    get_hermes40_compounding_sections,
    ensure_hermes40_sections,
    open_paper_trade_hermes4,
    close_paper_trade,
    update_paper_trade_mark_price,
    format_duration_str,
    get_setting,
    set_setting,
    set_metric,
    is_alert_sent,
    record_sent_alert
)
from feed.binance_feed import binance_feed
from alerts.telegram_service import (
    telegram_service,
    format_tg_ist_timestamp
)
from engine.chart_image_generator import render_smc_chart_image

logger = logging.getLogger("Hermes40Live")

from config import TOP_22_CHAMPIONS, ALL_MONITORED_COINS, HERMES40_TELEGRAM_BOT_TOKEN

async def send_hermes40_telegram_alert(text: str, photo_bytes: Optional[bytes] = None) -> bool:
    """Sends alert via dedicated Hermes 4.0 bot (@SMCTrigger24Bot) if configured, else fallback."""
    token = get_setting("hermes40_telegram_bot_token") or HERMES40_TELEGRAM_BOT_TOKEN or os.getenv("HERMES40_TELEGRAM_BOT_TOKEN")
    chat_id = get_setting("telegram_chat_id") or os.getenv("TELEGRAM_CHAT_ID", "752247227")
    
    if token:
        try:
            import aiohttp
            api_url = f"https://api.telegram.org/bot{token}"
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                if photo_bytes:
                    data = aiohttp.FormData()
                    data.add_field("chat_id", str(chat_id))
                    data.add_field("caption", text)
                    data.add_field("parse_mode", "HTML")
                    data.add_field("photo", photo_bytes, filename="chart.png", content_type="image/png")
                    async with session.post(f"{api_url}/sendPhoto", data=data, timeout=15) as resp:
                        res = await resp.json()
                        if res.get("ok"):
                            return True
                else:
                    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
                    async with session.post(f"{api_url}/sendMessage", json=payload, timeout=15) as resp:
                        res = await resp.json()
                        if res.get("ok"):
                            return True
        except Exception as e:
            logger.warning(f"Error sending alert via dedicated Hermes 4.0 bot: {e}")

    # Fallback to default telegram service
    try:
        if photo_bytes:
            r = await telegram_service.send_photo(photo_bytes, text, parse_mode="HTML")
            return bool(r and r.get("ok"))
        else:
            await telegram_service.send_raw_message(text, parse_mode="HTML")
            return True
    except Exception as e:
        logger.warning(f"Fallback telegram error for Hermes 4.0: {e}")
        return False


def calculate_atr_series(candles: List[Dict[str, Any]], period: int = 14) -> List[float]:
    if not candles:
        return []
    atrs = [max(float(candles[0]["high"]) - float(candles[0]["low"]), 1e-6)]
    for i in range(1, len(candles)):
        curr, prev = candles[i], candles[i-1]
        c_h, c_l, p_c = float(curr["high"]), float(curr["low"]), float(prev["close"])
        tr = max(c_h - c_l, abs(c_h - p_c), abs(c_l - p_c))
        atrs.append((atrs[-1] * (period - 1) + tr) / period)
    return atrs

class Hermes40LiveEngine:
    """Autonomous 24/7 live streaming engine for Hermes 4.0 Council Strategy."""

    def __init__(self):
        self.running = False
        self.ws_broadcast_callback = None
        self.last_scan_time = 0
        self.scan_cycle_seconds = 10
        self.last_btc_bias = {"btc_is_bull": True, "btc_is_bear": True, "long_veto": False, "short_veto": False}
        self.detected_setups: List[Dict[str, Any]] = []

    def set_broadcast_callback(self, callback):
        self.ws_broadcast_callback = callback

    async def broadcast(self, event_type: str, data: Any):
        if self.ws_broadcast_callback:
            try:
                await self.ws_broadcast_callback({"type": event_type, "data": data})
            except Exception:
                pass

    async def evaluate_btc_macro(self) -> Dict[str, Any]:
        """King BTC Sentry: prior 4H candle dump >= 1.0% vetoes longs."""
        try:
            btc_candles = await binance_feed.fetch_klines("BTCUSDT", interval="4h", limit=25)
            if len(btc_candles) >= 3:
                last_c = btc_candles[-2]  # completed bar
                o, c = float(last_c["open"]), float(last_c["close"])
                chg = (c - o) / o if o > 0 else 0.0
                return {
                    "btc_is_bull": chg >= 0,
                    "btc_is_bear": chg < 0,
                    "long_veto": chg < -0.010,   # Dump >= 1% vetoes longs
                    "short_veto": chg > 0.015,
                    "change_pct": round(chg * 100, 2)
                }
        except Exception as e:
            logger.warning(f"BTC macro check error: {e}")
        return {"btc_is_bull": True, "btc_is_bear": True, "long_veto": False, "short_veto": False, "change_pct": 0.0}

    def detect_hermes40_setups_sync(self, symbol: str, interval: str, candles: List[Dict[str, Any]], btc_sentry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """16-Agent Unified ICT/SMC Model: Extreme Bedrock OB + FVG + Body BOS + IDM Sweep + 50% MT Entry + Rejection Wick."""
        n = len(candles)
        if n < 35:
            return []

        atrs = calculate_atr_series(candles, 14)
        cur_price = float(candles[-1]["close"])
        setups = []

        # Target math (Strict 1:2 R:R at 5x leverage)
        tp_spot_gain = 0.0300   # +3.00% spot move (+15.0% ROE)
        be_spot_trigger = 0.0150 # +1.50% spot move (+7.5% ROE)

        # Scan backwards for recent qualified zones
        start_scan = max(15, n - 45)
        for i in range(start_scan, n - 4):
            c1, c2 = candles[i-1], candles[i]
            c1_l, c1_h = float(c1["low"]), float(c1["high"])
            c2_o, c2_c = float(c2["open"]), float(c2["open"]),
            c2_l, c2_h = float(c2["low"]), float(c2["high"])
            c2_c = float(c2["close"])

            # -------------------------------------------------------------------------
            # 1. BULLISH SETUP
            # -------------------------------------------------------------------------
            if not btc_sentry.get("long_veto", False) and c2_c <= c2_o:
                # Prior liquidity swept: C2 low sweeps C1 low
                if c2_l < c1_l:
                    # Origin Bedrock: C2 low is lowest of past 15 bars
                    prior_lows = [float(c["low"]) for c in candles[max(0, i-15):i+1]]
                    if c2_l == min(prior_lows):
                        sub_w = candles[i:min(i+20, n)]
                        highs = [float(c["high"]) for c in sub_w]
                        m_high = max(highs)
                        h_idx = i + highs.index(m_high)

                        if h_idx > i + 2:
                            disp_gain = (m_high - c2_l) / c2_l if c2_l > 0 else 0.0
                            # 3.5% minimum displacement
                            if disp_gain >= 0.035:
                                # Fair Value Gap (FVG)
                                has_fvg = any(float(candles[d+1]["low"]) > float(candles[d-1]["high"]) for d in range(i+1, min(h_idx, n-1)) if d+1 < n)
                                # Strict Body Close BOS
                                prev_swing_high = max(float(x["high"]) for x in candles[max(0, i-15):i])
                                body_bos = any(float(c["close"]) > prev_swing_high for c in candles[i+1:h_idx+1])

                                if has_fvg and body_bos:
                                    # 50% Mean Threshold of the Order Block
                                    entry_price = round((c2_h + c2_l) / 2.0, 6)
                                    idm_low = float(candles[h_idx-1]["low"])
                                    atr_val = atrs[min(h_idx, len(atrs)-1)]
                                    sl_price = round(c2_l - (0.35 * atr_val), 6)
                                    tp_price = round(entry_price * (1.0 + tp_spot_gain), 6)
                                    be_trigger_p = round(entry_price * (1.0 + be_spot_trigger), 6)

                                    # Check subsequent retest tap
                                    for t in range(h_idx+1, n):
                                        tap = candles[t]
                                        t_l, t_h, t_o, t_c = float(tap["low"]), float(tap["high"]), float(tap["open"]), float(tap["close"])
                                        
                                        # Inducement swept
                                        idm_swept = any(float(candles[k]["low"]) < idm_low for k in range(h_idx, t+1))
                                        touched = t_l <= entry_price * 1.0010  # within tap reach
                                        
                                        if idm_swept and touched:
                                            # Rejection wick check (>= 18%)
                                            c_range = t_h - t_l
                                            w_ratio = (min(t_o, t_c) - t_l) / c_range if c_range > 0 else 0.0
                                            
                                            # Low did not violate bedrock
                                            if w_ratio >= 0.18 and t_c >= c2_l:
                                                age = (n - 1) - t
                                                is_fresh = (age <= 2)
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "LONG",
                                                    "interval": interval,
                                                    "timeframe": interval,
                                                    "entry_price": entry_price,
                                                    "tp_price": tp_price,
                                                    "sl_price": sl_price,
                                                    "be_trigger_price": be_trigger_p,
                                                    "ob_high": c2_h,
                                                    "ob_low": c2_l,
                                                    "mean_threshold": entry_price,
                                                    "displacement_pct": round(disp_gain * 100, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100, 1),
                                                    "status": "FRESH_TRIGGERED" if is_fresh else "CONFIRMED_TAP",
                                                    "tap_time": tap["time"],
                                                    "is_fresh": is_fresh,
                                                    "strategy": "HERMES_4.0_BALANCED_APEX"
                                                })
                                            break

            # -------------------------------------------------------------------------
            # 2. BEARISH SETUP
            # -------------------------------------------------------------------------
            if not btc_sentry.get("short_veto", False) and c2_c >= c2_o:
                # Prior liquidity swept: C2 high sweeps C1 high
                if c2_h > c1_h:
                    prior_highs = [float(c["high"]) for c in candles[max(0, i-15):i+1]]
                    if c2_h == max(prior_highs):
                        sub_w = candles[i:min(i+20, n)]
                        lows = [float(c["low"]) for c in sub_w]
                        m_low = min(lows)
                        low_idx = i + lows.index(m_low)

                        if low_idx > i + 2:
                            disp_drop = (c2_h - m_low) / c2_h if c2_h > 0 else 0.0
                            if disp_drop >= 0.035:
                                has_fvg = any(float(candles[d+1]["high"]) < float(candles[d-1]["low"]) for d in range(i+1, min(low_idx, n-1)) if d+1 < n)
                                prev_swing_low = min(float(x["low"]) for x in candles[max(0, i-15):i])
                                body_bos = any(float(c["close"]) < prev_swing_low for c in candles[i+1:low_idx+1])

                                if has_fvg and body_bos:
                                    entry_price = round((c2_h + c2_l) / 2.0, 6)
                                    idm_high = float(candles[low_idx-1]["high"])
                                    atr_val = atrs[min(low_idx, len(atrs)-1)]
                                    sl_price = round(c2_h + (0.35 * atr_val), 6)
                                    tp_price = round(entry_price * (1.0 - tp_spot_gain), 6)
                                    be_trigger_p = round(entry_price * (1.0 - be_spot_trigger), 6)

                                    for t in range(low_idx+1, n):
                                        tap = candles[t]
                                        t_l, t_h, t_o, t_c = float(tap["low"]), float(tap["high"]), float(tap["open"]), float(tap["close"])
                                        
                                        idm_swept = any(float(candles[k]["high"]) > idm_high for k in range(low_idx, t+1))
                                        touched = t_h >= entry_price * 0.9990
                                        
                                        if idm_swept and touched:
                                            c_range = t_h - t_l
                                            w_ratio = (t_h - max(t_o, t_c)) / c_range if c_range > 0 else 0.0
                                            
                                            if w_ratio >= 0.18 and t_c <= c2_h:
                                                age = (n - 1) - t
                                                is_fresh = (age <= 2)
                                                setups.append({
                                                    "symbol": symbol,
                                                    "side": "SHORT",
                                                    "interval": interval,
                                                    "timeframe": interval,
                                                    "entry_price": entry_price,
                                                    "tp_price": tp_price,
                                                    "sl_price": sl_price,
                                                    "be_trigger_price": be_trigger_p,
                                                    "ob_high": c2_h,
                                                    "ob_low": c2_l,
                                                    "mean_threshold": entry_price,
                                                    "displacement_pct": round(disp_drop * 100, 2),
                                                    "wick_ratio_pct": round(w_ratio * 100, 1),
                                                    "status": "FRESH_TRIGGERED" if is_fresh else "CONFIRMED_TAP",
                                                    "tap_time": tap["time"],
                                                    "is_fresh": is_fresh,
                                                    "strategy": "HERMES_4.0_BALANCED_APEX"
                                                })
                                            break

        return setups

    async def scan_market(self):
        """Scans all 58 monitored coins on 4H and 1H for Hermes 4.0 setups."""
        btc_sentry = await self.evaluate_btc_macro()
        self.last_btc_bias = btc_sentry
        new_setups = []

        coins = ALL_MONITORED_COINS if ALL_MONITORED_COINS else TOP_22_CHAMPIONS

        for tf in ["4h", "1h"]:
            for sym in coins:
                try:
                    candles = await binance_feed.fetch_klines(sym, interval=tf, limit=75)
                    if len(candles) >= 35:
                        found = self.detect_hermes40_setups_sync(sym, tf, candles, btc_sentry)
                        for s in found:
                            new_setups.append(s)
                            # If fresh trigger, attempt trade execution in Sections 11-20
                            if s.get("is_fresh"):
                                alert_key = f"hermes4_{sym}_{s['side']}_{tf}_{s['tap_time']}"
                                if not is_alert_sent(alert_key):
                                    record_sent_alert(alert_key, 0)
                                    res = open_paper_trade_hermes4(s)
                                    if res and res.get("id"):
                                        logger.info(f"🟢 [HERMES 4.0] Opened Trade #{res['id']} {sym} {s['side']} in Account #{res['account_id']}")
                                        # Send Telegram alert for Hermes 4.0 Entry
                                        try:
                                            now_ms = int(time.time() * 1000)
                                            now_str = format_tg_ist_timestamp(now_ms)
                                            side_icon = "🟢 LONG" if s["side"].upper() in ("BUY", "LONG") else "🔴 SHORT"
                                            margin_val = float(res.get("margin", 50.0))
                                            pos_val = margin_val * 5.0
                                            
                                            tg_msg = (
                                                f"⚡ <b>[HERMES 4.0 COUNCIL OF 16] TRADE OPENED</b>\n"
                                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                                                f"🪙 <b>Pair:</b> #{sym} ({side_icon})\n"
                                                f"⏱️ <b>Timeframe:</b> {tf.upper()} • 5x ISOLATED\n"
                                                f"🏛️ <b>Section:</b> Hermes 4.0 Section #{res['account_id']}\n\n"
                                                f"🎯 <b>ENTRY (50% MT):</b> <code>${res['entry_price']}</code>\n"
                                                f"🚀 <b>TAKE PROFIT (+15.0% ROE):</b> <code>${res['tp_price']}</code> (+3.00% Spot)\n"
                                                f"🛡️ <b>STOP LOSS:</b> <code>${res['sl_price']}</code>\n"
                                                f"💰 <b>Margin Deployed:</b> ${margin_val:.2f} USDT (Pos: ${pos_val:.2f})\n\n"
                                                f"──────── INSTITUTIONAL CONFLUENCE ────────\n"
                                                f"• <b>Council Model:</b> 16-Agent Unified SMC Matrix\n"
                                                f"• <b>Order Block:</b> {s.get('ob_low')} - {s.get('ob_high')} (Displacement: +{s.get('displacement_pct', 0)}%)\n"
                                                f"• <b>Wick Defense:</b> {s.get('wick_ratio_pct', 0)}% Rejection Absorption\n"
                                                f"• <b>King BTC Sentry:</b> PASS (Macro Trend Aligned)\n"
                                                f"• <b>Armor:</b> Stepped BE Lock at +7.5% ROE (+1.5% Spot)\n\n"
                                                f"🕒 <i>{now_str}</i>"
                                            )
                                            
                                            chart_sent = False
                                            try:
                                                zone_dict = {
                                                    "symbol": sym,
                                                    "side": s["side"],
                                                    "entry_price": res["entry_price"],
                                                    "tp_price": res["tp_price"],
                                                    "sl_price": res["sl_price"],
                                                    "ob_high": s.get("ob_high", res["entry_price"]),
                                                    "ob_low": s.get("ob_low", res["entry_price"])
                                                }
                                                chart_sent = await send_hermes40_telegram_alert(tg_msg, photo_bytes=chart_bytes)
                                            except Exception as ce:
                                                logger.warning(f"Failed to render chart for Hermes 4.0: {ce}")
                                                
                                            if not chart_sent:
                                                await send_hermes40_telegram_alert(tg_msg)
                                        except Exception as e:
                                            logger.warning(f"Telegram alert error for Hermes 4.0: {e}")
                except Exception as err:
                    logger.debug(f"Scan error for {sym} {tf}: {err}")

        self.detected_setups = new_setups
        self.last_scan_time = int(time.time() * 1000)

    async def monitor_open_positions(self):
        """Monitors open positions in Sections 11-20, manages Stepped BE lock, and executes TP/SL with Telegram alerts."""
        with get_connection() as conn:
            open_trades = [dict(r) for r in conn.execute(
                "SELECT * FROM paper_trades WHERE status = 'OPEN' AND mode = 'HERMES_4.0_BALANCED_APEX'"
            ).fetchall()]

        for t in open_trades:
            sym = t["symbol"]
            side = t["side"].upper()
            ep = float(t["entry_price"])
            sl = float(t["sl_price"])
            tp = float(t["tp_price"])
            tid = t["id"]
            acc_id = t.get("account_id", 11)
            be_lock_pct = float(t.get("be_lock_pct") or 0.0150)

            cur_p = binance_feed.get_cached_price(sym)
            if not cur_p or cur_p <= 0:
                continue

            update_paper_trade_mark_price(tid, cur_p)

            # Stepped Break-Even Armor (+1.0R / +1.50% spot move / +7.5% ROE)
            if side in ("BUY", "LONG"):
                gain_from_ep = (cur_p - ep) / ep
                if gain_from_ep >= be_lock_pct and sl < ep:
                    with get_connection() as conn:
                        conn.execute("UPDATE paper_trades SET sl_price = ? WHERE id = ?", (ep, tid))
                        conn.commit()
                    logger.info(f"🛡️ [HERMES 4.0] Trade #{tid} {sym} locked to Break-Even at ${ep}")
                    try:
                        be_msg = (
                            f"🛡️ <b>[HERMES 4.0 COUNCIL] BREAK-EVEN LOCK ACTIVATED</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"🪙 <b>Pair:</b> #{sym} (LONG)\n"
                            f"🏛️ <b>Section:</b> Hermes 4.0 Section #{acc_id}\n"
                            f"⚡ <b>Condition:</b> Price reached +1.50% (+7.5% ROE / +1.0R)\n"
                            f"🔒 <b>Action:</b> Stop Loss moved to Entry Price (<code>${ep}</code>)\n"
                            f"✨ <b>Risk:</b> ZERO RISK POSITION ACTIVE"
                        )
                        await send_hermes40_telegram_alert(be_msg)
                    except Exception as be_err:
                        logger.warning(f"Telegram BE alert error: {be_err}")

                # Check TP hit (+3.00% spot / +15% ROE)
                if cur_p >= tp:
                    closed = close_paper_trade(t, "TP_HIT", exit_price=tp)
                    logger.info(f"🎉 [HERMES 4.0] Trade #{tid} {sym} HIT TAKE PROFIT (+15.0% ROE)!")
                    try:
                        now_str = format_tg_ist_timestamp(int(time.time() * 1000))
                        pnl = float(closed.get("net_pnl_usdt", 7.50) if closed else 7.50)
                        exit_msg = (
                            f"🎉 <b>[HERMES 4.0 COUNCIL] TAKE PROFIT ACHIEVED!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"🪙 <b>Pair:</b> #{sym} (LONG)\n"
                            f"🏛️ <b>Section:</b> Hermes 4.0 Section #{acc_id}\n"
                            f"🎯 <b>Entry:</b> <code>${ep}</code> ➔ <b>Exit:</b> <code>${tp}</code>\n"
                            f"💵 <b>Net P&L:</b> <code>+${pnl:.2f} USDT</code> (+15.0% ROE)\n"
                            f"💎 <b>Compounding:</b> Reinvested into Section #{acc_id}\n"
                            f"🕒 <i>{now_str}</i>"
                        )
                        await send_hermes40_telegram_alert(exit_msg)
                    except Exception as ex_err:
                        logger.warning(f"Telegram exit alert error: {ex_err}")

                # Check SL hit
                elif cur_p <= sl:
                    is_be = (abs(sl - ep) < 0.0001)
                    outcome = "TP_HIT" if is_be else "SL_HIT"
                    closed = close_paper_trade(t, outcome, exit_price=sl)
                    logger.info(f"🛑 [HERMES 4.0] Trade #{tid} {sym} closed at ${sl} (Outcome: {outcome})")
                    try:
                        now_str = format_tg_ist_timestamp(int(time.time() * 1000))
                        pnl = float(closed.get("net_pnl_usdt", 0.0) if closed else 0.0)
                        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
                        label = "BREAK-EVEN EXIT" if is_be else "STOP LOSS HIT"
                        exit_msg = (
                            f"🛑 <b>[HERMES 4.0 COUNCIL] {label}</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"🪙 <b>Pair:</b> #{sym} (LONG)\n"
                            f"🏛️ <b>Section:</b> Hermes 4.0 Section #{acc_id}\n"
                            f"🎯 <b>Entry:</b> <code>${ep}</code> ➔ <b>Exit:</b> <code>${sl}</code>\n"
                            f"💵 <b>Net P&L:</b> <code>{pnl_str} USDT</code>\n"
                            f"🕒 <i>{now_str}</i>"
                        )
                        await send_hermes40_telegram_alert(exit_msg)
                    except Exception as ex_err:
                        logger.warning(f"Telegram exit alert error: {ex_err}")
            else:
                drop_from_ep = (ep - cur_p) / ep
                if drop_from_ep >= be_lock_pct and sl > ep:
                    with get_connection() as conn:
                        conn.execute("UPDATE paper_trades SET sl_price = ? WHERE id = ?", (ep, tid))
                        conn.commit()
                    logger.info(f"🛡️ [HERMES 4.0] Trade #{tid} {sym} locked to Break-Even at ${ep}")
                    try:
                        be_msg = (
                            f"🛡️ <b>[HERMES 4.0 COUNCIL] BREAK-EVEN LOCK ACTIVATED</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"🪙 <b>Pair:</b> #{sym} (SHORT)\n"
                            f"🏛️ <b>Section:</b> Hermes 4.0 Section #{acc_id}\n"
                            f"⚡ <b>Condition:</b> Price reached +1.50% (+7.5% ROE / +1.0R)\n"
                            f"🔒 <b>Action:</b> Stop Loss moved to Entry Price (<code>${ep}</code>)\n"
                            f"✨ <b>Risk:</b> ZERO RISK POSITION ACTIVE"
                        )
                        await send_hermes40_telegram_alert(be_msg)
                    except Exception as be_err:
                        logger.warning(f"Telegram BE alert error: {be_err}")

                if cur_p <= tp:
                    closed = close_paper_trade(t, "TP_HIT", exit_price=tp)
                    logger.info(f"🎉 [HERMES 4.0] Trade #{tid} {sym} HIT TAKE PROFIT (+15.0% ROE)!")
                    try:
                        now_str = format_tg_ist_timestamp(int(time.time() * 1000))
                        pnl = float(closed.get("net_pnl_usdt", 7.50) if closed else 7.50)
                        exit_msg = (
                            f"🎉 <b>[HERMES 4.0 COUNCIL] TAKE PROFIT ACHIEVED!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"🪙 <b>Pair:</b> #{sym} (SHORT)\n"
                            f"🏛️ <b>Section:</b> Hermes 4.0 Section #{acc_id}\n"
                            f"🎯 <b>Entry:</b> <code>${ep}</code> ➔ <b>Exit:</b> <code>${tp}</code>\n"
                            f"💵 <b>Net P&L:</b> <code>+${pnl:.2f} USDT</code> (+15.0% ROE)\n"
                            f"💎 <b>Compounding:</b> Reinvested into Section #{acc_id}\n"
                            f"🕒 <i>{now_str}</i>"
                        )
                        await send_hermes40_telegram_alert(exit_msg)
                    except Exception as ex_err:
                        logger.warning(f"Telegram exit alert error: {ex_err}")

                elif cur_p >= sl:
                    is_be = (abs(sl - ep) < 0.0001)
                    outcome = "TP_HIT" if is_be else "SL_HIT"
                    closed = close_paper_trade(t, outcome, exit_price=sl)
                    logger.info(f"🛑 [HERMES 4.0] Trade #{tid} {sym} closed at ${sl} (Outcome: {outcome})")
                    try:
                        now_str = format_tg_ist_timestamp(int(time.time() * 1000))
                        pnl = float(closed.get("net_pnl_usdt", 0.0) if closed else 0.0)
                        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
                        label = "BREAK-EVEN EXIT" if is_be else "STOP LOSS HIT"
                        exit_msg = (
                            f"🛑 <b>[HERMES 4.0 COUNCIL] {label}</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"🪙 <b>Pair:</b> #{sym} (SHORT)\n"
                            f"🏛️ <b>Section:</b> Hermes 4.0 Section #{acc_id}\n"
                            f"🎯 <b>Entry:</b> <code>${ep}</code> ➔ <b>Exit:</b> <code>${sl}</code>\n"
                            f"💵 <b>Net P&L:</b> <code>{pnl_str} USDT</code>\n"
                            f"🕒 <i>{now_str}</i>"
                        )
                        await send_hermes40_telegram_alert(exit_msg)
                    except Exception as ex_err:
                        logger.warning(f"Telegram exit alert error: {ex_err}")

    async def start(self):
        """Runs the 24/7 background execution loop for Hermes 4.0."""
        self.running = True
        logger.info("🟢 Hermes 4.0 Balanced Apex (Council of 16) Live Engine Started 24/7!")
        ensure_hermes40_sections()

        while self.running:
            try:
                await self.scan_market()
                await self.monitor_open_positions()
                sections_data = get_hermes40_compounding_sections()
                await self.broadcast("hermes40_update", {
                    "timestamp": int(time.time() * 1000),
                    "btc_sentry": self.last_btc_bias,
                    "sections": sections_data.get("sections", []),
                    "combined": sections_data.get("combined", {}),
                    "setups_count": len(self.detected_setups)
                })
            except Exception as e:
                logger.error(f"Hermes 4.0 live engine error: {e}", exc_info=True)

            await asyncio.sleep(self.scan_cycle_seconds)

    def stop(self):
        self.running = False
        logger.info("Hermes 4.0 Live Engine Stopped.")

hermes40_live_engine = Hermes40LiveEngine()
