"""
BB 2.0 LIVE SNIPER ENGINE & SHADOW TRADING RUNNER
==================================================
- Pure Standalone: 100% Isolated from live Render engine.
- Data Feed: Binance Public Futures 15m & 1D Klines (Read-only, no API keys needed).
- Strategy: Day 1 (PDH/PDL) Mark + Extreme Order Block (Displacement + FVG)
- Execution: 50% Mean Threshold Limit | 0.15% Anti-Hunt Buffer SL
- Discipline: Strict Single-Shot (Max 1 Long & 1 Short per day per coin)
- Compounding: 10 Deca Sections ($50.00 each) @ 5% Section Risk
- Notifications: Dedicated Telegram Bot (Token: 8685685362:AAFWkKvRIs6cJ70gegcJVFyKB5soDtEttbU)
"""

import os
import sys
import time
import json
import ssl
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure repo root is on path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import bb20_config as cfg

# Telegram Notifier with Real Candlestick Chart
def send_telegram_alert(
    text: str,
    symbol: Optional[str] = None,
    setup_or_pos: Optional[Dict] = None,
    candles: Optional[List[Dict]] = None
):
    if not cfg.BB20_TELEGRAM_BOT_TOKEN or not cfg.BB20_TELEGRAM_CHAT_ID:
        return

    # Attempt to send with real candlestick chart if symbol and setup are provided
    if symbol and setup_or_pos:
        try:
            from scripts.bb30_chart_generator import send_telegram_alert_with_chart
            chart_candles = candles
            if not chart_candles:
                chart_candles = fetch_binance_klines(symbol, interval="15m", limit=50)
            if chart_candles:
                sent = send_telegram_alert_with_chart(
                    token=cfg.BB20_TELEGRAM_BOT_TOKEN,
                    chat_id=cfg.BB20_TELEGRAM_CHAT_ID,
                    caption=text,
                    symbol=symbol,
                    candles=chart_candles,
                    setup=setup_or_pos
                )
                if sent:
                    return
        except Exception as e:
            print(f"[Chart Dispatch Error]: {e}")

    # Fallback to standard text message
    url = f"https://api.telegram.org/bot{cfg.BB20_TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": cfg.BB20_TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, context=ctx, timeout=10)
    except Exception as e:
        print(f"[Telegram Alert Error]: {e}")

# Universal Multi-Provider Klines Fetcher (Binance Vision + Bybit Fallback - Zero Geo-block)
def fetch_binance_klines(symbol: str, interval: str = "15m", limit: int = 100) -> List[Dict]:
    ctx = ssl._create_unverified_context()
    spot_symbol = symbol[4:] if symbol.startswith("1000") else symbol
    multiplier = 1000.0 if symbol.startswith("1000") else 1.0

    # Provider 1: Binance Vision API (Universal, no US geo-restrictions)
    try:
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={spot_symbol}&interval={interval}&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list) and len(data) > 0:
                candles = []
                for row in data:
                    candles.append({
                        "time": int(row[0]),
                        "open": float(row[1]) * multiplier,
                        "high": float(row[2]) * multiplier,
                        "low": float(row[3]) * multiplier,
                        "close": float(row[4]) * multiplier,
                        "volume": float(row[5])
                    })
                return candles
    except Exception:
        pass

    # Provider 2: Bybit Linear API Fallback
    try:
        bybit_int = "15" if interval == "15m" else ("D" if interval == "1d" else "60")
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={bybit_int}&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_list = data.get("result", {}).get("list", [])
            if raw_list:
                candles = []
                for row in reversed(raw_list):
                    candles.append({
                        "time": int(row[0]),
                        "open": float(row[1]),
                        "high": float(row[2]),
                        "low": float(row[3]),
                        "close": float(row[4]),
                        "volume": float(row[5])
                    })
                return candles
    except Exception:
        pass

    # Provider 3: Binance Futures fallback
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list) and len(data) > 0:
                candles = []
                for row in data:
                    candles.append({
                        "time": int(row[0]),
                        "open": float(row[1]),
                        "high": float(row[2]),
                        "low": float(row[3]),
                        "close": float(row[4]),
                        "volume": float(row[5])
                    })
                return candles
    except Exception as e:
        print(f"Error fetching klines for {symbol} ({interval}): {e}")

    return []

# Shadow Ledger Manager
class ShadowLedger:
    def __init__(self, ledger_path: str = cfg.SHADOW_LEDGER_FILE):
        self.ledger_path = os.path.join(REPO_ROOT, ledger_path)
        self.data = self._load()

    def _load(self) -> Dict:
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Initialize default 10 Deca sections
        sections = {}
        for i in range(1, cfg.TOTAL_DECA_SECTIONS + 1):
            assigned = [c for c, s_id in cfg.PAIR_MAPPING.items() if s_id == i]
            sections[str(i)] = {
                "section_id": i,
                "assigned_coins": assigned,
                "initial_balance": cfg.STARTING_BALANCE_PER_SECTION,
                "balance": cfg.STARTING_BALANCE_PER_SECTION,
                "trades_count": 0,
                "wins": 0,
                "saves": 0,
                "losses": 0,
                "pnl_usd": 0.0,
                "status": "IDLE"
            }
        init_data = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_initial_capital": cfg.TOTAL_STARTING_CAPITAL,
            "total_current_equity": cfg.TOTAL_STARTING_CAPITAL,
            "sections": sections,
            "active_setups": {},
            "active_positions": {},
            "closed_trades": [],
            "daily_single_shot": {} # {YYYY-MM-DD: {symbol: {"LONG": bool, "SHORT": bool}}}
        }
        self._save_raw(init_data)
        return init_data

    def _save_raw(self, data: Dict):
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def save(self):
        tot_eq = sum(s["balance"] for s in self.data["sections"].values())
        self.data["total_current_equity"] = round(tot_eq, 2)
        self._save_raw(self.data)

class BB20LiveSniper:
    def __init__(self):
        self.ledger = ShadowLedger()
        print("=" * 80)
        print("🎯 BB 2.0 (BOOMING BULLS SNIPER) — LIVE SHADOW ENGINE ACTIVE")
        print(f"• Total Capital: ${self.ledger.data['total_current_equity']:.2f} USDT across 10 Sections ($50 each)")
        print(f"• Risk per Section: {cfg.SECTION_RISK_FRACTION * 100:.1f}% Compounding Mode")
        print(f"• Dedicated Telegram Alerts: Connected ✅")
        print("=" * 80)

    def get_day_key(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def run_scan_cycle(self):
        day_key = self.get_day_key()
        if day_key not in self.ledger.data["daily_single_shot"]:
            self.ledger.data["daily_single_shot"][day_key] = {}

        print(f"\n[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] Scanning Top-20 Champions for Extreme OB Setups...")

        for symbol in cfg.CHAMPIONS:
            sec_id = str(cfg.PAIR_MAPPING.get(symbol, 1))
            sec = self.ledger.data["sections"][sec_id]

            # Initialize daily single shot record for this symbol
            if symbol not in self.ledger.data["daily_single_shot"][day_key]:
                self.ledger.data["daily_single_shot"][day_key][symbol] = {"LONG": False, "SHORT": False}

            day_status = self.ledger.data["daily_single_shot"][day_key][symbol]

            # 1. Fetch Daily Candles for PDH / PDL
            daily_candles = fetch_binance_klines(symbol, interval="1d", limit=3)
            if len(daily_candles) < 2:
                continue
            prev_day = daily_candles[-2]
            pdh = prev_day["high"]
            pdl = prev_day["low"]

            # 2. Fetch 15m Candles
            candles_15m = fetch_binance_klines(symbol, interval="15m", limit=30)
            if len(candles_15m) < 5:
                continue

            last_c = candles_15m[-1]
            current_price = last_c["close"]

            # 3. Check existing active position for this symbol
            pos_key = f"{symbol}"
            if pos_key in self.ledger.data["active_positions"]:
                self._monitor_active_position(pos_key, candles_15m)
                continue

            # 4. Check existing pending limit setup
            setup_key = f"{symbol}"
            if setup_key in self.ledger.data["active_setups"]:
                self._check_pending_setup_fill(setup_key, candles_15m)
                continue

            # If this section is already busy with an active trade on another coin, skip arming a new setup
            if sec.get("status") != "IDLE" and pos_key not in self.ledger.data["active_positions"]:
                continue

            # If another coin in this same section already has a pending limit setup, skip to prevent double margin allocation
            if any(s.get("section_id") == sec_id and s_sym != symbol for s_sym, s in self.ledger.data.get("active_setups", {}).items()):
                continue

            # 5. Scan recent candles (up to 24 bars / 6 hours) for valid unmitigated Extreme OBs
            lookback_bars = min(24, len(candles_15m) - 3)
            for i in range(len(candles_15m) - lookback_bars, len(candles_15m) - 2):
                if symbol in self.ledger.data.get("active_setups", {}):
                    break

                c_base = candles_15m[i]
                c_disp = candles_15m[i + 1]
                c_curr = candles_15m[i + 2]
                subsequent_bars = candles_15m[i + 3:]

                # -----------------------------------------------------------------
                # BOTTOM ORDER BLOCK (LONG) AT/NEAR PDL
                # -----------------------------------------------------------------
                if not day_status["LONG"]:
                    dist_to_pdl = abs(c_base["low"] - pdl) / pdl if pdl > 0 else 1.0
                    if dist_to_pdl <= 0.015 or c_base["low"] <= pdl:
                        gain_1bar = (c_disp["high"] - c_base["low"]) / c_base["low"]
                        gain_2bar = (c_curr["high"] - c_base["low"]) / c_base["low"]
                        has_bull_fvg = c_curr["low"] > c_base["high"]

                        if (c_base["close"] < c_base["open"] or (c_base["high"] - c_base["low"]) > 0) and (gain_1bar >= 0.012 or gain_2bar >= 0.018) and has_bull_fvg:
                            ob_high = c_base["high"]
                            ob_low = c_base["low"]
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_low * (1.0 - cfg.SL_ANTI_HUNT_BUFFER)
                            risk = mt - sl

                            # Check if invalidated by SL hit
                            sl_hit = any(b["low"] <= sl for b in subsequent_bars) or current_price <= sl

                            if risk > 0 and not sl_hit:
                                self._arm_new_setup(symbol, sec_id, "LONG", mt, sl, risk, pdl, "PDL SUPPORT")
                                # Immediately check if current bar fills the limit order
                                self._check_pending_setup_fill(symbol, candles_15m)
                                break

                # -----------------------------------------------------------------
                # TOP ORDER BLOCK (SHORT) AT/NEAR PDH
                # -----------------------------------------------------------------
                if not day_status["SHORT"]:
                    dist_to_pdh = abs(c_base["high"] - pdh) / pdh if pdh > 0 else 1.0
                    if dist_to_pdh <= 0.015 or c_base["high"] >= pdh:
                        drop_1bar = (c_base["high"] - c_disp["low"]) / c_base["high"]
                        drop_2bar = (c_base["high"] - c_curr["low"]) / c_base["high"]
                        has_bear_fvg = c_curr["high"] < c_base["low"]

                        if (c_base["close"] > c_base["open"] or (c_base["high"] - c_base["low"]) > 0) and (drop_1bar >= 0.012 or drop_2bar >= 0.018) and has_bear_fvg:
                            ob_high = c_base["high"]
                            ob_low = c_base["low"]
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_high * (1.0 + cfg.SL_ANTI_HUNT_BUFFER)
                            risk = sl - mt

                            # Check if invalidated by SL hit
                            sl_hit = any(b["high"] >= sl for b in subsequent_bars) or current_price >= sl

                            if risk > 0 and not sl_hit:
                                self._arm_new_setup(symbol, sec_id, "SHORT", mt, sl, risk, pdh, "PDH RESISTANCE")
                                # Immediately check if current bar fills the limit order
                                self._check_pending_setup_fill(symbol, candles_15m)
                                break

        self.ledger.save()
        self._print_dashboard()

    def _arm_new_setup(self, symbol: str, sec_id: str, side: str, mt: float, sl: float, risk: float, anchor_price: float, anchor_name: str):
        sec = self.ledger.data["sections"][sec_id]
        risk_usd = sec["balance"] * cfg.SECTION_RISK_FRACTION

        setup_data = {
            "symbol": symbol,
            "section_id": sec_id,
            "side": side,
            "mt_entry": round(mt, 4),
            "sl": round(sl, 4),
            "risk": round(risk, 4),
            "risk_usd": round(risk_usd, 2),
            "anchor_name": anchor_name,
            "anchor_price": round(anchor_price, 4),
            "armed_at": datetime.now(timezone.utc).isoformat(),
            "target_1r": round(mt + risk if side == "LONG" else mt - risk, 4),
            "target_15r": round(mt + 1.5 * risk if side == "LONG" else mt - 1.5 * risk, 4),
            "target_3r": round(mt + 3.0 * risk if side == "LONG" else mt - 3.0 * risk, 4)
        }

        self.ledger.data["active_setups"][symbol] = setup_data
        print(f"🔥 [NEW PENDING SETUP] {symbol} {side} @ 50% MT ${mt:.4f} (Section #{sec_id})")

        # Telegram Alert
        emoji = "🟢 LONG" if side == "LONG" else "🔴 SHORT"
        msg = (
            f"🎯 <b>BB 3.0 SNIPER — PENDING LIMIT SETUP</b>\n\n"
            f"<b>Coin</b>: #{symbol} ({emoji})\n"
            f"<b>Strategy</b>: Day 1 {anchor_name} Sweep + 15m Extreme OB Retest\n"
            f"<b>Model</b>: 50% Mean Threshold Stepped Trailing SL\n\n"
            f"<b>Section</b>: #{sec_id} (${sec['balance']:.2f} USDT)\n"
            f"<b>Anchor</b>: {anchor_name} (${anchor_price:.4f})\n\n"
            f"🎯 <b>50% MT Limit Entry</b>: <code>${mt:.4f}</code>\n"
            f"🛑 <b>Stop Loss (0.15% Buffer)</b>: <code>${sl:.4f}</code>\n"
            f"💰 <b>Risk Amount (5%)</b>: ${risk_usd:.2f} USDT\n\n"
            f"🪜 <b>Profit Targets</b>:\n"
            f"• Tier 1 (+1.0R): ${setup_data['target_1r']:.4f} (SL ➔ +0.2R BE)\n"
            f"• Tier 2 (+1.5R): ${setup_data['target_15r']:.4f} (Lock +1.0R)\n"
            f"• Target (+3.0R): ${setup_data['target_3r']:.4f}\n\n"
            f"<i>Real-time candlestick chart attached above!</i>"
        )
        send_telegram_alert(msg, symbol=symbol, setup_or_pos=setup_data, candles=candles_15m)

    def _check_pending_setup_fill(self, symbol: str, candles: List[Dict]):
        setup = self.ledger.data["active_setups"][symbol]
        last_c = candles[-1]
        side = setup["side"]
        entry = setup["mt_entry"]
        sl = setup["sl"]

        # Check Setup Expiration (max 8 hours without tap)
        armed_str = setup.get("armed_at")
        if armed_str:
            try:
                armed_dt = datetime.fromisoformat(armed_str)
                if (datetime.now(timezone.utc) - armed_dt).total_seconds() >= 8 * 3600:
                    del self.ledger.data["active_setups"][symbol]
                    print(f"⌛ Setup {symbol} Expired (8 hours without mitigation)")
                    return
            except Exception:
                pass

        # Check Invalidation
        if side == "LONG" and last_c["low"] <= sl:
            del self.ledger.data["active_setups"][symbol]
            print(f"⚠️ Setup {symbol} Invalidated before fill (hit SL level)")
            return
        elif side == "SHORT" and last_c["high"] >= sl:
            del self.ledger.data["active_setups"][symbol]
            print(f"⚠️ Setup {symbol} Invalidated before fill (hit SL level)")
            return

        # Check Fill
        filled = False
        if side == "LONG" and last_c["low"] <= entry:
            filled = True
        elif side == "SHORT" and last_c["high"] >= entry:
            filled = True

        if filled:
            # Move from active_setups to active_positions
            del self.ledger.data["active_setups"][symbol]
            day_key = self.get_day_key()
            if day_key not in self.ledger.data.get("daily_single_shot", {}):
                self.ledger.data.setdefault("daily_single_shot", {})[day_key] = {}
            if symbol not in self.ledger.data["daily_single_shot"][day_key]:
                self.ledger.data["daily_single_shot"][day_key][symbol] = {"LONG": False, "SHORT": False}
            self.ledger.data["daily_single_shot"][day_key][symbol][side] = True # LOCK single-shot

            pos_data = dict(setup)
            pos_data["filled_at"] = datetime.now(timezone.utc).isoformat()
            pos_data["current_tier"] = 0
            pos_data["active_sl"] = sl
            pos_data["highest_r"] = 0.0
            self.ledger.data["active_positions"][symbol] = pos_data

            sec_id = setup["section_id"]
            self.ledger.data["sections"][sec_id]["status"] = f"IN TRADE ({symbol} {side})"

            print(f"✅ [LIMIT FILLED] {symbol} {side} @ ${entry:.4f}! Trade is LIVE!")

            msg = (
                f"⚡ <b>BB 3.0 SNIPER — LIMIT ORDER FILLED!</b>\n\n"
                f"<b>Coin</b>: #{symbol} ({side})\n"
                f"<b>Strategy</b>: BB 3.0 (50% MT Retest Entered)\n"
                f"<b>Fill Price</b>: <code>${entry:.4f}</code>\n"
                f"<b>Stop Loss</b>: <code>${sl:.4f}</code>\n"
                f"<b>Section #{sec_id}</b>: Risk ${setup['risk_usd']:.2f} USDT\n\n"
                f"🛡️ <b>Stepped Trailing Armor Active</b>: Monitoring live candles for profit locks."
            )
            send_telegram_alert(msg, symbol=symbol, setup_or_pos=pos_data, candles=candles)

    def _monitor_active_position(self, symbol: str, candles: List[Dict]):
        pos = self.ledger.data["active_positions"][symbol]
        last_c = candles[-1]
        side = pos["side"]
        entry = pos["mt_entry"]
        active_sl = pos["active_sl"]
        risk = pos["risk"]
        current_tier = pos["current_tier"]
        sec_id = pos["section_id"]
        sec = self.ledger.data["sections"][sec_id]

        # 1. Check SL Hit across recent bars
        recent_bars = candles[-2:] if len(candles) >= 2 else candles
        sl_hit = False
        if side == "LONG":
            sl_hit = any(b["low"] <= active_sl for b in recent_bars)
        elif side == "SHORT":
            sl_hit = any(b["high"] >= active_sl for b in recent_bars)

        if sl_hit:
            self._close_position(symbol, "SL_HIT", active_sl)
            return

        # 2. Check Favorable Excursion & Trailing Milestone (+1.0R -> +0.2R BE, +1.5R -> +1.0R lock, +2.0R -> +1.5R lock)
        high_price = max(b["high"] for b in recent_bars)
        low_price = min(b["low"] for b in recent_bars)
        max_fav_r = (high_price - entry) / risk if side == "LONG" else (entry - low_price) / risk
        if max_fav_r > pos["highest_r"]:
            pos["highest_r"] = round(max_fav_r, 2)

        if max_fav_r >= 1.0:
            tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
            if tier_candidate > current_tier:
                pos["current_tier"] = tier_candidate
                # Stepped Trailing SL: Tier 1 (+1.0R) -> +0.2R BE; Tier 2 (+1.5R) -> +1.0R lock; Tier 3 (+2.0R) -> +1.5R lock
                locked_r = 0.2 if tier_candidate == 1 else tier_candidate * 0.5
                new_sl = entry + (locked_r * risk) if side == "LONG" else entry - (locked_r * risk)
                pos["active_sl"] = round(new_sl, 4)

                print(f"🛡️ [TRAILING SL UPDATE] {symbol} {side}: Tier {tier_candidate} Locked! (SL ➔ ${new_sl:.4f})")
                tier_msg = "Fee Shield (+0.2R Breakeven)" if tier_candidate == 1 else f"+{locked_r:.1f}R Pure Profit Locked!"
                msg = (
                    f"🪜 <b>BB 3.0 SNIPER — TRAILING PROFIT LOCKED!</b>\n\n"
                    f"<b>Coin</b>: #{symbol} ({side})\n"
                    f"<b>Peak Reached</b>: +{max_fav_r:.2f} R\n"
                    f"<b>New Stop Loss</b>: <code>${new_sl:.4f}</code>\n"
                    f"<b>Lock Status</b>: {tier_msg}\n\n"
                    f"<i>Trade is protected against any sudden reversal! Real chart attached above.</i>"
                )
                send_telegram_alert(msg, symbol=symbol, setup_or_pos=pos, candles=candles)

    def _close_position(self, symbol: str, reason: str, exit_price: float):
        pos = self.ledger.data["active_positions"][symbol]
        tier = pos["current_tier"]
        sec_id = pos["section_id"]
        sec = self.ledger.data["sections"][sec_id]

        if tier == 0:
            realized_r = -1.0 - cfg.FRICTION_R
            outcome = "LOSS (SL HIT)"
            sec["losses"] += 1
        elif tier == 1:
            realized_r = 0.2 - cfg.FRICTION_R
            outcome = "FEE SHIELD SAVE (+0.2R)"
            sec["saves"] += 1
        else:
            locked_r = tier * 0.5
            realized_r = locked_r - cfg.FRICTION_R
            outcome = f"WIN (+{locked_r:.1f}R PROFIT LOCKED)"
            sec["wins"] += 1

        sec["trades_count"] += 1
        dollar_pnl = sec["balance"] * cfg.SECTION_RISK_FRACTION * realized_r
        sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))
        sec["pnl_usd"] = round(sec["pnl_usd"] + dollar_pnl, 2)
        sec["status"] = "IDLE"

        # Record trade in closed trades
        closed_rec = dict(pos)
        closed_rec["closed_at"] = datetime.now(timezone.utc).isoformat()
        closed_rec["exit_price"] = exit_price
        closed_rec["outcome"] = outcome
        closed_rec["realized_r"] = round(realized_r, 2)
        closed_rec["dollar_pnl"] = round(dollar_pnl, 2)
        closed_rec["section_new_balance"] = sec["balance"]
        self.ledger.data["closed_trades"].append(closed_rec)

        del self.ledger.data["active_positions"][symbol]
        self.ledger.save()

        print(f"🏁 [TRADE CLOSED] {symbol} {outcome} | PnL: ${dollar_pnl:+.2f} USDT | Sec #{sec_id} Bal: ${sec['balance']:.2f}")

        # Telegram Alert
        res_emoji = "🏆 WIN" if realized_r > 0 else ("🛡️ SAFE SAVE" if tier == 1 else "🛑 LOSS")
        msg = (
            f"🏁 <b>BB 3.0 SNIPER — TRADE COMPLETED</b>\n\n"
            f"<b>Result</b>: {res_emoji} ({outcome})\n"
            f"<b>Coin</b>: #{symbol} ({pos['side']})\n"
            f"<b>Strategy</b>: BB 3.0 (Stepped Trailing SL)\n"
            f"<b>Exit Price</b>: <code>${exit_price:.4f}</code>\n"
            f"<b>Realized R</b>: {realized_r:+.2f} R\n"
            f"<b>Dollar PnL</b>: <b>{dollar_pnl:+.2f} USDT</b>\n\n"
            f"<b>Section #{sec_id} Balance</b>: <b>${sec['balance']:.2f} USDT</b>\n"
            f"<b>Total Deca Equity</b>: <b>${self.ledger.data['total_current_equity']:.2f} USDT</b>"
        )
        send_telegram_alert(msg, symbol=symbol, setup_or_pos=closed_rec)

    def _print_dashboard(self):
        tot_eq = sum(s["balance"] for s in self.ledger.data["sections"].values())
        print("-" * 80)
        print(f"📊 LIVE SHADOW DECA DASHBOARD | Total Equity: ${tot_eq:.2f} USDT (Initial: $500.00)")
        print(f"Pending Setups: {len(self.ledger.data['active_setups'])} | Active Trades: {len(self.ledger.data['active_positions'])} | Closed: {len(self.ledger.data['closed_trades'])}")
        print("-" * 80)

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')

    sniper = BB20LiveSniper()
    # Send start greeting
    send_telegram_alert(
        "🚀 <b>BB 3.0 SNIPER AI MONITOR STARTED</b>\n\n"
        "• <b>Status</b>: Active 24/7 Scanning with Real Candlestick Charts\n"
        "• <b>Strategy</b>: Day 1 PDH/PDL Sweep Trap + 15m Extreme OB Retest\n"
        "• <b>Execution Model</b>: 50% Mean Threshold Limit Entry & Stepped Trailing SL\n"
        "• <b>Discipline</b>: Max 1 Long & 1 Short per day per coin\n"
        "• <b>Deca Capital</b>: $500.00 USDT (10 Sections @ 5% Risk)\n\n"
        "<i>All alerts will be delivered with live candlestick charts and strategy levels!</i>"
    )

    print("\nStarting live scan loop (runs every 60 seconds)... Press Ctrl+C to stop.\n")
    try:
        while True:
            sniper.run_scan_cycle()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nBB 2.0 Live Sniper Stopped safely.")

if __name__ == "__main__":
    main()
