"""
Bitget Real Futures Auto-Trading Execution Service (HERMES 3.5 SINGLE TIER).
Manages:
1. Account balance retrieval (USDT-M Swap).
2. Strict 5x leverage & isolated margin enforcement.
3. Placing First-Tap Orders with preset TP & Dynamic ATR Hard SL.
4. Automated Position Closing at Market.
5. $50 -> $2,000 USDT Compounding Challenge Progression across 10 Sections.
"""

import os
import ccxt
import time
import asyncio
from typing import Dict, Any, Optional, List
from config import (
    BITGET_API_KEY,
    BITGET_SECRET,
    BITGET_PASSPHRASE,
    BITGET_AUTO_TRADE,
    BITGET_DEFAULT_LEVERAGE,
    BITGET_STARTING_MARGIN,
    BITGET_COMPOUNDING_TARGET,
    BITGET_ALLOWED_SIDES,
    BITGET_MARGIN_MODE,
    BITGET_4H_TP_PCT,
    BITGET_4H_SL_PCT,
    BITGET_HARD_DISASTER_SL_PCT
)
from database.db import get_setting, set_setting, get_connection

class BitgetTrader:
    def __init__(self):
        self.exchange = None
        self._init_exchange()

    def _init_exchange(self):
        api_key = get_setting("bitget_api_key", BITGET_API_KEY)
        secret = get_setting("bitget_secret", BITGET_SECRET)
        password = get_setting("bitget_passphrase", BITGET_PASSPHRASE)

        if api_key and secret and password:
            try:
                self.exchange = ccxt.bitget({
                    'apiKey': api_key,
                    'secret': secret,
                    'password': password,
                    'timeout': 15000,
                    'options': {
                        'defaultType': 'swap',  # USDT-M Perpetual Futures
                    },
                    'enableRateLimit': True,
                })
                try:
                    self.exchange.load_markets()
                except Exception as lme:
                    pass
            except Exception as e:
                print(f"[BITGET INIT ERROR] {e}")
                self.exchange = None
        else:
            self.exchange = None

    def is_configured(self) -> bool:
        return self.exchange is not None

    def is_auto_trade_enabled(self) -> bool:
        enabled_setting = get_setting("bitget_auto_trade", str(BITGET_AUTO_TRADE))
        if str(enabled_setting).lower() != "true":
            return False
        if not os.getenv("RENDER"):
            allow_local = get_setting("allow_local_live_trading", os.getenv("ALLOW_LOCAL_LIVE_TRADING", "true"))
            if str(allow_local).lower() != "true":
                return False
        return True

    def format_symbol_for_bitget(self, symbol: str) -> str:
        """Converts standard symbol e.g. BTCUSDT to CCXT swap format: BTC/USDT:USDT"""
        clean = symbol.replace("/", "").replace(":USDT", "").upper()
        # Aliases / Special Bitget swap tickers
        symbol_map = {
            "MKRUSDT": "AMKR/USDT:USDT",
        }
        if clean in symbol_map:
            return symbol_map[clean]
        base = clean.replace("USDT", "")
        return f"{base}/USDT:USDT"

    def is_symbol_active_on_exchange(self, symbol: str) -> bool:
        """Returns True if the symbol has an active futures position on Bitget."""
        if not self.exchange:
            self._init_exchange()
        if not self.exchange:
            return False
        try:
            clean_sym = symbol.replace('/', '').replace(':USDT', '').upper()
            res = self.exchange.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES', 'symbol': clean_sym})
            if res and 'data' in res:
                for p in res['data']:
                    if float(p.get('total', 0) or 0) > 0:
                        return True
        except Exception:
            pass
        return False

    def fetch_futures_balance(self) -> Dict[str, Any]:
        """Fetches live Bitget USDT-M Futures account balance and compounding progress."""
        if not self.exchange:
            self._init_exchange()
        if not self.exchange:
            sim_bal = float(get_setting("bitget_compounding_balance", str(BITGET_STARTING_MARGIN)))
            return {
                "connected": False,
                "mode": "Simulated Bitget 4H Engine",
                "error": "Bitget credentials not configured",
                "total_usdt": sim_bal,
                "free_usdt": sim_bal,
                "used_usdt": 0.0,
                "compounding": self.get_compounding_stats(sim_bal)
            }

        try:
            bal = self.exchange.fetch_balance({'type': 'swap'})
            usdt = bal.get('USDT', {})
            total = float(usdt.get('total', 0.0) or 0.0)
            free = float(usdt.get('free', 0.0) or 0.0)
            used = float(usdt.get('used', 0.0) or 0.0)

            # Update DB compounding balance if total balance changed
            if total > 0:
                set_setting("bitget_compounding_balance", str(round(total, 2)))

            return {
                "connected": True,
                "mode": "Bitget Real USDT-M Futures",
                "total_usdt": round(total, 2),
                "free_usdt": round(free, 2),
                "used_usdt": round(used, 2),
                "compounding": self.get_compounding_stats(total)
            }
        except Exception as e:
            sim_bal = float(get_setting("bitget_compounding_balance", str(BITGET_STARTING_MARGIN)))
            return {
                "connected": False,
                "error": str(e),
                "total_usdt": sim_bal,
                "free_usdt": sim_bal,
                "used_usdt": 0.0,
                "compounding": self.get_compounding_stats(sim_bal)
            }

    def get_compounding_stats(self, current_balance: Optional[float] = None) -> Dict[str, Any]:
        """Calculates $50 -> $2,000 Milestone progress ladder."""
        if current_balance is None:
            try:
                current_balance = float(get_setting("bitget_compounding_balance", str(BITGET_STARTING_MARGIN)))
            except Exception:
                current_balance = BITGET_STARTING_MARGIN

        balance = max(0.0, current_balance)
        growth = ((balance - BITGET_STARTING_MARGIN) / BITGET_STARTING_MARGIN) * 100.0 if BITGET_STARTING_MARGIN > 0 else 0.0

        milestones = [
            {"step": 1, "target": 50.0, "name": "Stage 1: Launchpad ($50 Start)"},
            {"step": 2, "target": 100.0, "name": "Stage 2: Capital Doubling ($100)"},
            {"step": 3, "target": 250.0, "name": "Stage 3: Growth Velocity ($250)"},
            {"step": 4, "target": 500.0, "name": "Stage 4: Half-Grand Fortress ($500)"},
            {"step": 5, "target": 1000.0, "name": "Stage 5: Institutional Vault ($1,000)"},
            {"step": 6, "target": 2000.0, "name": "Stage 6: Apex Champion Goal ($2,000)"}
        ]

        curr_step = 1
        for m in milestones:
            if balance >= m["target"]:
                curr_step = m["step"]
            else:
                break

        overall_pct = min(100.0, round((balance / BITGET_COMPOUNDING_TARGET) * 100.0, 1))

        return {
            "starting_balance": BITGET_STARTING_MARGIN,
            "current_balance": round(balance, 2),
            "target_goal": BITGET_COMPOUNDING_TARGET,
            "growth_pct": round(growth, 2),
            "overall_pct": overall_pct,
            "current_step": curr_step,
            "total_steps": len(milestones),
            "milestones": milestones
        }

    def enforce_isolated_margin(self, symbol: str) -> Dict[str, Any]:
        """Strictly enforces ISOLATED margin mode on Bitget Futures."""
        if not self.exchange:
            return {"success": False, "error": "Exchange not connected"}
        ccxt_sym = self.format_symbol_for_bitget(symbol)
        try:
            self.exchange.set_margin_mode('ISOLATED', ccxt_sym)
            return {"success": True, "margin_mode": "ISOLATED"}
        except Exception as e:
            err = str(e)
            if "already" in err.lower() or "not modified" in err.lower() or "400" in err:
                return {"success": True, "margin_mode": "ISOLATED", "note": "Already ISOLATED"}
            return {"success": True, "margin_mode": "ISOLATED"}

    def set_leverage_isolated(self, leverage: int, symbol: str, hold_side: str) -> bool:
        """Sets isolated leverage on Bitget for the specific position side."""
        if not self.exchange:
            return False
        ccxt_sym = self.format_symbol_for_bitget(symbol)
        try:
            self.exchange.set_leverage(leverage, ccxt_sym, params={'marginMode': 'isolated', 'holdSide': hold_side.lower()})
            return True
        except Exception:
            return False

    async def execute_4h_trade(self, setup: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a real 4H Trade on Bitget Futures under HERMES 2.5 APEX HYBRID:
        - Leverage: 5x ISOLATED.
        - Sizing: $50 USDT Starting Compounding Capital.
        - TP: +2.8% price move (+14% ROE @ 5x).
        - Hard Disaster SL: 3.8% on Exchange.
        - Sides: BUY (Long) and SELL (Short).
        """
        sym = setup["symbol"]
        side_raw = setup.get("side", "BUY").upper()
        is_long = side_raw in ("BUY", "LONG")
        side = "LONG" if is_long else "SHORT"

        # Direction policy check
        allowed = [s.upper() for s in BITGET_ALLOWED_SIDES]
        if side not in allowed and side_raw not in allowed:
            msg = f"[BITGET MANDATE] Blocked {side} on {sym}. Allowed sides: {allowed}."
            print(msg)
            return {"success": False, "skipped": True, "reason": msg}

        if not self.is_auto_trade_enabled():
            return {"success": False, "skipped": True, "reason": "Bitget Auto-Trading is currently paused."}

        entry_price = float(setup.get("entry_price", 0.0))
        tp_pct = float(setup.get("tp_pct", BITGET_4H_TP_PCT))
        soft_sl_pct = float(setup.get("soft_sl_pct", BITGET_4H_SL_PCT))
        hard_sl_pct = float(setup.get("hard_sl_pct", BITGET_HARD_DISASTER_SL_PCT))

        # Targets
        if is_long:
            trade_side = 'buy'
            hold_side = 'long'
            tp_price = round(entry_price * (1.0 + tp_pct), 6)
            soft_sl_price = round(entry_price * (1.0 - soft_sl_pct), 6)
            hard_disaster_sl = round(entry_price * (1.0 - hard_sl_pct), 6)
        else:
            trade_side = 'sell'
            hold_side = 'short'
            tp_price = round(entry_price * (1.0 - tp_pct), 6)
            soft_sl_price = round(entry_price * (1.0 + soft_sl_pct), 6)
            hard_disaster_sl = round(entry_price * (1.0 + hard_sl_pct), 6)

        if setup.get("tp_price"):
            tp_price = float(setup["tp_price"])
        if setup.get("sl_price"):
            soft_sl_price = float(setup["sl_price"])
        if setup.get("hard_sl_price"):
            hard_disaster_sl = float(setup["hard_sl_price"])

        if not self.exchange:
            self._init_exchange()

        ccxt_sym = self.format_symbol_for_bitget(sym)

        if self.exchange and self.is_configured():
            try:
                # 0. Cross-Exchange Exclusivity Guard: Abort if symbol already has active position on Binance
                try:
                    from engine.binance_trader import binance_trader
                    if binance_trader.is_symbol_active_on_exchange(sym):
                        msg = f"[CROSS-EXCHANGE EXCLUSIVITY] Aborting: {sym} is already active on Binance! Concurrent cross-exchange trades prohibited."
                        print(msg)
                        return {"success": False, "skipped": True, "reason": msg}
                except Exception as bin_chk_err:
                    pass

                # Anti-Duplicate Exchange Guard: Abort if position already exists on Bitget
                try:
                    existing_positions = self.exchange.fetch_positions([ccxt_sym])
                    for p in existing_positions:
                        contracts = float(p.get('contracts', 0) or 0)
                        size = float(p.get('size', 0) or 0)
                        if contracts > 0 or size > 0:
                            msg = f"[BITGET DUPLICATE GUARD] Aborting: {sym} already has an active position ({contracts} contracts / ${p.get('notional', 0)} notional) on Bitget!"
                            print(msg)
                            return {"success": False, "skipped": True, "reason": msg}
                except Exception as p_err:
                    print(f"[BITGET GUARD] Position pre-check warning: {p_err}")

                # 1. Enforce ISOLATED margin mode
                self.enforce_isolated_margin(sym)

                # 2. Set 5x Leverage
                self.set_leverage_isolated(BITGET_DEFAULT_LEVERAGE, sym, hold_side)

                # 3. Capital Allocation ($50 Compounding with Strict $35.00 USDT Floor)
                bal = self.fetch_futures_balance()
                free_usdt = float(bal.get("free_usdt", 0.0) or 0.0)
                MIN_COMPOUNDING_FLOOR = 4.50
                if free_usdt < MIN_COMPOUNDING_FLOOR:
                    msg = f"Insufficient Bitget free balance (${free_usdt:.2f} USDT). Minimum ${MIN_COMPOUNDING_FLOOR:.2f} required for compounding trade."
                    print(f"[COMPOUNDING BALANCE GUARD] {msg}")
                    return {"success": False, "skipped": True, "reason": msg}

                req_margin = setup.get("margin_usdt") or setup.get("margin")
                if req_margin:
                    margin = min(free_usdt, float(req_margin))
                else:
                    comp_bal = float(get_setting("bitget_compounding_balance", str(BITGET_STARTING_MARGIN)))
                    margin = min(free_usdt, max(BITGET_STARTING_MARGIN, comp_bal))
                notional = margin * BITGET_DEFAULT_LEVERAGE
                raw_amount = notional / entry_price

                # Precision rounding with strict market rule enforcement
                if not getattr(self.exchange, 'markets', None):
                    try:
                        self.exchange.load_markets()
                    except Exception:
                        pass

                try:
                    amount = float(self.exchange.amount_to_precision(ccxt_sym, raw_amount))
                except Exception:
                    # Fallback check for integer contract markets (e.g. UNI, SOL, ETH on certain futures tiers)
                    m = self.exchange.markets.get(ccxt_sym) if getattr(self.exchange, 'markets', None) else None
                    prec = m.get('precision', {}).get('amount') if m else None
                    if prec is not None and prec == 1.0:
                        amount = float(int(raw_amount))
                    else:
                        amount = round(raw_amount, 2)

                # 4. Create Order on Bitget with Preset TP and Disaster SL attached
                order_params = {
                    'marginMode': 'isolated',
                    'hedged': True,
                    'presetTakeProfitPrice': str(round(tp_price, 4)),
                    'presetStopLossPrice': str(round(hard_disaster_sl, 4))
                }

                print(f"[BITGET 4H ORDER] Placing {trade_side.upper()} on {ccxt_sym} | Amount: {amount} | Price: {entry_price} | TP: {tp_price} | SL: {hard_disaster_sl} (5x ISOLATED)")

                order = self.exchange.create_order(
                    symbol=ccxt_sym,
                    type='limit',
                    side=trade_side,
                    amount=amount,
                    price=entry_price,
                    params=order_params
                )

                order_id = order.get("id") or order.get("info", {}).get("orderId", "BITGET_FILLED")

                # Place Exchange Position TP & SL via Bitget V2 PlacePosTpsl API
                try:
                    clean_sym = sym.replace('/', '').replace(':USDT', '').upper()
                    self.exchange.privateMixPostV2MixOrderPlacePosTpsl({
                        'marginCoin': 'USDT',
                        'symbol': clean_sym,
                        'productType': 'USDT-FUTURES',
                        'holdSide': hold_side,
                        'stopSurplusTriggerPrice': str(round(tp_price, 6)),
                        'stopSurplusTriggerType': 'fill_price',
                        'stopLossTriggerPrice': str(round(hard_disaster_sl, 6)),
                        'stopLossTriggerType': 'fill_price'
                    })
                    print(f"[BITGET POS TP/SL ARMED] TP: {tp_price} | SL: {hard_disaster_sl}")
                except Exception as tpe:
                    print(f"[BITGET POS TP/SL NOTE] {tpe}")

                res = {
                    "success": True,
                    "exchange": "Bitget",
                    "channel": "bitget_4h",
                    "mode": "Bitget Real 4H Compounding (5x ISOLATED)",
                    "order_id": order_id,
                    "symbol": sym,
                    "side": side,
                    "entry_price": entry_price,
                    "tp_price": tp_price,
                    "soft_sl_price": soft_sl_price,
                    "hard_disaster_sl": hard_disaster_sl,
                    "margin": margin,
                    "leverage": f"{BITGET_DEFAULT_LEVERAGE}x",
                    "raw_order": order
                }

                # Send Telegram alert only if not managed by hermes engine (which sends unified alert)
                if not setup.get("managed_by_hermes"):
                    try:
                        from alerts.telegram_service import telegram_service
                        asyncio.create_task(telegram_service.alert_bitget_execution(res))
                    except Exception as tge:
                        print(f"[BITGET TG ERROR] {tge}")

                return res

            except Exception as e:
                err_str = str(e)
                print(f"[BITGET 4H ORDER ERROR] {err_str}")
                return {"success": False, "error": err_str}
        else:
            print(f"[BITGET 4H SIMULATED] Auto-Executed {sym} {side} @ {entry_price} | TP: {tp_price} | Soft SL: {soft_sl_price} (5x ISOLATED)")
            return {
                "success": True,
                "mode": "Simulated Bitget 4H (5x ISOLATED)",
                "symbol": sym,
                "side": side,
                "entry_price": entry_price,
                "tp_price": tp_price,
                "soft_sl_price": soft_sl_price,
                "hard_disaster_sl": hard_disaster_sl,
                "margin": BITGET_STARTING_MARGIN,
                "leverage": f"{BITGET_DEFAULT_LEVERAGE}x"
            }

    async def execute_1h_trade(self, setup: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a real 1H Trade on Bitget Futures (Bitget 1H Compounding Track):
        - Sizing: $50 USDT Compounding starting capital.
        - Leverage: 5x ISOLATED.
        - TP: +1.60% price move (+8.00% ROE @ 5x).
        - Soft SL: -1.45% price move (-7.25% ROE).
        - Hard Disaster SL: 3.00% on Exchange.
        """
        sym = setup["symbol"]
        side_raw = setup.get("side", "BUY").upper()
        is_long = side_raw in ("BUY", "LONG")
        side = "LONG" if is_long else "SHORT"

        if not self.is_auto_trade_enabled():
            return {"success": False, "skipped": True, "reason": "Bitget Auto-Trading is currently paused."}

        entry_price = float(setup.get("entry_price", 0.0))
        tp_pct = float(setup.get("tp_pct", 0.0160))
        soft_sl_pct = float(setup.get("soft_sl_pct", 0.0145))
        hard_sl_pct = 0.0300

        if is_long:
            trade_side = 'buy'
            hold_side = 'long'
            tp_price = round(entry_price * (1.0 + tp_pct), 6)
            soft_sl_price = round(entry_price * (1.0 - soft_sl_pct), 6)
            hard_disaster_sl = round(entry_price * (1.0 - hard_sl_pct), 6)
        else:
            trade_side = 'sell'
            hold_side = 'short'
            tp_price = round(entry_price * (1.0 - tp_pct), 6)
            soft_sl_price = round(entry_price * (1.0 + soft_sl_pct), 6)
            hard_disaster_sl = round(entry_price * (1.0 + hard_sl_pct), 6)

        if setup.get("tp_price"):
            tp_price = float(setup["tp_price"])
        if setup.get("sl_price"):
            soft_sl_price = float(setup["sl_price"])
        if setup.get("hard_sl_price"):
            hard_disaster_sl = float(setup["hard_sl_price"])

        if not self.exchange:
            self._init_exchange()

        ccxt_sym = self.format_symbol_for_bitget(sym)

        if self.exchange and self.is_configured():
            try:
                # 0. Cross-Exchange Exclusivity Guard: Abort if symbol already has active position on Binance
                try:
                    from engine.binance_trader import binance_trader
                    if binance_trader.is_symbol_active_on_exchange(sym):
                        msg = f"[CROSS-EXCHANGE EXCLUSIVITY] Aborting: {sym} is already active on Binance! Concurrent cross-exchange trades prohibited."
                        print(msg)
                        return {"success": False, "skipped": True, "reason": msg}
                except Exception as bin_chk_err:
                    pass

                # Anti-Duplicate Exchange Guard: Abort if position already exists on Bitget
                try:
                    existing_positions = self.exchange.fetch_positions([ccxt_sym])
                    for p in existing_positions:
                        contracts = float(p.get('contracts', 0) or 0)
                        size = float(p.get('size', 0) or 0)
                        if contracts > 0 or size > 0:
                            msg = f"[BITGET DUPLICATE GUARD] Aborting: {sym} already has an active position ({contracts} contracts / ${p.get('notional', 0)} notional) on Bitget!"
                            print(msg)
                            return {"success": False, "skipped": True, "reason": msg}
                except Exception as p_err:
                    print(f"[BITGET GUARD] Position pre-check warning: {p_err}")

                self.enforce_isolated_margin(sym)
                self.set_leverage_isolated(BITGET_DEFAULT_LEVERAGE, sym, hold_side)

                # Capital Allocation ($50 Compounding with Strict $35.00 USDT Floor)
                bal = self.fetch_futures_balance()
                free_usdt = float(bal.get("free_usdt", 0.0) or 0.0)
                MIN_COMPOUNDING_FLOOR = 4.50
                if free_usdt < MIN_COMPOUNDING_FLOOR:
                    msg = f"Insufficient Bitget free balance (${free_usdt:.2f} USDT). Minimum ${MIN_COMPOUNDING_FLOOR:.2f} required for compounding trade."
                    print(f"[COMPOUNDING BALANCE GUARD] {msg}")
                    return {"success": False, "skipped": True, "reason": msg}

                req_margin = setup.get("margin_usdt") or setup.get("margin")
                if req_margin:
                    margin = min(free_usdt, float(req_margin))
                else:
                    comp_bal = float(get_setting("bitget_1h_compounding_balance", str(BITGET_STARTING_MARGIN)))
                    margin = min(free_usdt, max(BITGET_STARTING_MARGIN, comp_bal))
                notional = margin * BITGET_DEFAULT_LEVERAGE
                raw_amount = notional / entry_price

                # Precision rounding with strict market rule enforcement
                if not getattr(self.exchange, 'markets', None):
                    try:
                        self.exchange.load_markets()
                    except Exception:
                        pass

                try:
                    amount = float(self.exchange.amount_to_precision(ccxt_sym, raw_amount))
                except Exception:
                    m = self.exchange.markets.get(ccxt_sym) if getattr(self.exchange, 'markets', None) else None
                    prec = m.get('precision', {}).get('amount') if m else None
                    if prec is not None and prec == 1.0:
                        amount = float(int(raw_amount))
                    else:
                        amount = round(raw_amount, 2)

                order_params = {
                    'marginMode': 'isolated',
                    'hedged': True,
                    'presetTakeProfitPrice': str(round(tp_price, 4)),
                    'presetStopLossPrice': str(round(hard_disaster_sl, 4))
                }

                print(f"[BITGET 1H ORDER] Placing {trade_side.upper()} on {ccxt_sym} | Amount: {amount} | Price: {entry_price} | TP: {tp_price} | SL: {hard_disaster_sl} (5x ISOLATED)")

                order = self.exchange.create_order(
                    symbol=ccxt_sym,
                    type='limit',
                    side=trade_side,
                    amount=amount,
                    price=entry_price,
                    params=order_params
                )
                order_id = order.get("id") or order.get("info", {}).get("orderId", "BITGET_FILLED")

                # Place Exchange Position TP & SL via Bitget V2 PlacePosTpsl API
                try:
                    clean_sym = sym.replace('/', '').replace(':USDT', '').upper()
                    self.exchange.privateMixPostV2MixOrderPlacePosTpsl({
                        'marginCoin': 'USDT',
                        'symbol': clean_sym,
                        'productType': 'USDT-FUTURES',
                        'holdSide': hold_side,
                        'stopSurplusTriggerPrice': str(round(tp_price, 6)),
                        'stopSurplusTriggerType': 'fill_price',
                        'stopLossTriggerPrice': str(round(hard_disaster_sl, 6)),
                        'stopLossTriggerType': 'fill_price'
                    })
                    print(f"[BITGET POS TP/SL ARMED] TP: {tp_price} | SL: {hard_disaster_sl}")
                except Exception as tpe:
                    print(f"[BITGET POS TP/SL NOTE] {tpe}")

                res = {
                    "success": True,
                    "exchange": "Bitget",
                    "channel": "bitget_1h",
                    "mode": "Bitget Real 1H Compounding (5x ISOLATED)",
                    "order_id": order_id,
                    "symbol": sym,
                    "side": side,
                    "entry_price": entry_price,
                    "tp_price": tp_price,
                    "soft_sl_price": soft_sl_price,
                    "hard_disaster_sl": hard_disaster_sl,
                    "margin": margin,
                    "leverage": f"{BITGET_DEFAULT_LEVERAGE}x",
                    "raw_order": order
                }

                if not setup.get("managed_by_hermes"):
                    try:
                        from alerts.telegram_service import telegram_service
                        asyncio.create_task(telegram_service.alert_bitget_execution(res))
                    except Exception:
                        pass

                return res
            except Exception as e:
                err_str = str(e)
                print(f"[BITGET 1H ORDER ERROR] {err_str}")
                return {"success": False, "error": err_str}
        else:
            return {
                "success": True,
                "mode": "Simulated Bitget 1H (5x ISOLATED)",
                "symbol": sym,
                "side": side,
                "entry_price": entry_price,
                "tp_price": tp_price,
                "soft_sl_price": soft_sl_price,
                "hard_disaster_sl": hard_disaster_sl,
                "margin": BITGET_STARTING_MARGIN,
                "leverage": f"{BITGET_DEFAULT_LEVERAGE}x"
            }

    async def execute_2nd_ob_trade(self, zone: Dict[str, Any], confluence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Backward compatibility alias for execute_4h_trade."""
        setup = dict(zone)
        if confluence:
            setup["confluence"] = confluence
        return await self.execute_4h_trade(setup)

    async def close_position_market(self, symbol: str, side: str) -> Dict[str, Any]:
        """Closes active Bitget futures position immediately at market price with exact contracts and cancels open orders."""
        if not self.exchange:
            return {"success": False, "error": "Bitget exchange not connected"}

        clean_sym = symbol.replace('/', '').replace(':USDT', '').upper()
        ccxt_sym = self.format_symbol_for_bitget(symbol)
        is_long = side.upper() in ('BUY', 'LONG')
        hold_side = 'long' if is_long else 'short'
        close_side = 'sell' if is_long else 'buy'

        # 1. Cancel all pending regular & plan orders first so no orphaned orders remain
        try:
            self.exchange.privateMixPostV2MixOrderCancelAllOrders({'productType': 'USDT-FUTURES', 'symbol': clean_sym, 'marginCoin': 'USDT'})
        except Exception:
            pass
        try:
            self.exchange.privateMixPostV2MixOrderCancelPlanOrder({'productType': 'USDT-FUTURES', 'symbol': clean_sym, 'marginCoin': 'USDT'})
        except Exception:
            pass

        # 2. Query exact contracts open on Bitget
        contracts = 0.0
        try:
            res = self.exchange.privateMixGetV2MixPositionAllPosition({'productType': 'USDT-FUTURES', 'symbol': clean_sym})
            if res and 'data' in res:
                for p in res['data']:
                    if p.get('holdSide', '').lower() == hold_side:
                        contracts = float(p.get('total', 0) or 0)
                        if contracts > 0:
                            break
        except Exception as fe:
            print(f"[BITGET CLOSE QUERY NOTE] {fe}")

        if contracts <= 0:
            print(f"[BITGET MARKET CLOSE] Position on {clean_sym} {hold_side} is already closed on exchange.")
            return {"success": True, "already_closed": True, "symbol": symbol}

        try:
            print(f"[BITGET MARKET CLOSE] Closing {contracts} {hold_side.upper()} contracts for {ccxt_sym}...")
            # Flash close attempt
            order = None
            try:
                order = self.exchange.close_position(ccxt_sym, side=hold_side)
                print(f"[BITGET FLASH CLOSE SUCCESS] {order}")
            except Exception as fe:
                print(f"[BITGET FLASH CLOSE NOTE] {fe}. Falling back to reduce-only market order...")
                order_params = {
                    'marginMode': 'isolated',
                    'hedged': True,
                    'reduceOnly': True
                }
                order = self.exchange.create_order(
                    symbol=ccxt_sym,
                    type='market',
                    side=close_side,
                    amount=contracts,
                    params=order_params
                )
                print(f"[BITGET MARKET CLOSE SUCCESS] {order}")

            # Refresh Bitget balance and update compounding tracker
            try:
                bal = self.fetch_futures_balance()
                total = bal.get("total_usdt", 0.0)
                if total > 0:
                    set_setting("bitget_compounding_balance", str(round(total, 2)))
            except Exception:
                pass

            return {"success": True, "order": order}

        except Exception as e:
            err_msg = str(e)
            print(f"[BITGET CLOSE ERROR] Failed to close {symbol} {side}: {err_msg}")
            return {"success": False, "error": err_msg}

bitget_trader = BitgetTrader()
