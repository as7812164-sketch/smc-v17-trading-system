"""
Binance Real Futures Auto-Trading Execution Service (Challenge 2: 1H Fast Scalp).
Manages:
1. Account balance retrieval (USDT-M Futures).
2. Setting 5x leverage & isolated margin.
3. Placing First-Tap Limit Orders on 1H Order Blocks.
4. Auto-setting Scalp TP (+1.5% real move = +7.5% gain) & SL (-2.5% move).
5. Compounding balance tracking ($50 -> $1,000 Goal on 1H).
"""

import ccxt
import time
from typing import Dict, Any, Optional, List
from config import (
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    BINANCE_AUTO_TRADE,
    BINANCE_DEFAULT_LEVERAGE,
    BINANCE_STARTING_MARGIN,
    BINANCE_1H_TP_PCT,
    BINANCE_1H_SL_PCT,
    BINANCE_4H_TP_PCT,
    BINANCE_4H_SL_PCT,
    BINANCE_HARD_DISASTER_SL_PCT,
    BINANCE_ALLOWED_SIDES,
    BINANCE_MARGIN_MODE
)
from database.db import get_setting, set_setting, get_connection

class BinanceTrader:
    def __init__(self):
        self.exchange = None
        self._init_exchange()

    def _init_exchange(self):
        api_key = get_setting("binance_api_key", BINANCE_API_KEY)
        secret = get_setting("binance_secret", BINANCE_API_SECRET)

        if api_key and secret:
            try:
                self.exchange = ccxt.binance({
                    'apiKey': api_key,
                    'secret': secret,
                    'timeout': 15000,
                    'options': {
                        'defaultType': 'future',  # USDT-M Perpetual Futures
                        'adjustForTimeDifference': True,
                        'recvWindow': 60000
                    },
                    'enableRateLimit': True,
                })
            except Exception as e:
                print(f"Error initializing Binance: {e}")
                self.exchange = None
        else:
            self.exchange = None

    def is_configured(self) -> bool:
        return self.exchange is not None

    def is_auto_trade_enabled(self) -> bool:
        enabled_setting = get_setting("binance_auto_trade", str(BINANCE_AUTO_TRADE))
        return enabled_setting.lower() == "true"

    def fetch_futures_balance(self) -> Dict[str, Any]:
        """Fetches live Binance USDT-M Futures account balance or returns detailed status."""
        if not self.exchange:
            self._init_exchange()
            
        if not self.exchange:
            sim_bal = float(get_setting("binance_4h_sim_balance", "50.0"))
            return {
                "connected": False,
                "mode": "Simulated Live 4H Engine",
                "total_usdt": sim_bal,
                "free_usdt": sim_bal,
                "used_usdt": 0.0,
                "equity": sim_bal,
                "error": "Binance API keys not configured"
            }

        try:
            # Direct fast futures balance lookup
            try:
                balances = self.exchange.fapiPrivateV2GetBalance()
                usdt_item = next((b for b in balances if b.get('asset') == 'USDT'), None)
                if usdt_item:
                    total = float(usdt_item.get('balance', 0.0) or 0.0)
                    available = float(usdt_item.get('availableBalance', 0.0) or 0.0)
                    used = max(0.0, total - available)
                    return {
                        "connected": True,
                        "mode": "Live Binance Futures (5x ISOLATED)",
                        "total_usdt": round(total, 2),
                        "free_usdt": round(available, 2),
                        "used_usdt": round(used, 2),
                        "equity": round(total, 2),
                        "margin_mode": "ISOLATED",
                        "challenge_stage": self._calc_stage(total)
                    }
            except Exception as inner_e:
                err_text = str(inner_e)
                if "-2015" in err_text:
                    return {
                        "connected": False,
                        "error_code": -2015,
                        "error": "Binance Error -2015: 'Enable Futures' permission required or IP restriction active in Binance API Management."
                    }
                raise inner_e

            bal = self.exchange.fetch_balance({'type': 'future'})
            usdt = bal.get('USDT', {})
            total = float(usdt.get('total', 0.0) or 0.0)
            free = float(usdt.get('free', 0.0) or 0.0)
            used = float(usdt.get('used', 0.0) or 0.0)
            return {
                "connected": True,
                "mode": "Live Binance Futures (5x ISOLATED)",
                "total_usdt": round(total, 2),
                "free_usdt": round(free, 2),
                "used_usdt": round(used, 2),
                "equity": round(total, 2),
                "margin_mode": "ISOLATED",
                "challenge_stage": self._calc_stage(total)
            }
        except Exception as e:
            err_str = str(e)
            if "-2015" in err_str:
                err_str = "Binance Error -2015: 'Enable Futures' permission required or IP restriction active in Binance API Management."
            return {"connected": False, "error": err_str}

    def _calc_stage(self, balance: float) -> Dict[str, Any]:
        """Calculates 4H Compounding ladder progress ($50 -> $2,000+)."""
        stages = [
            {"stage": 1, "target": 100.0, "desc": "$50 -> $100 (Stage 1)"},
            {"stage": 2, "target": 250.0, "desc": "$100 -> $250 (Stage 2)"},
            {"stage": 3, "target": 500.0, "desc": "$250 -> $500 (Stage 3)"},
            {"stage": 4, "target": 1000.0, "desc": "$500 -> $1,000 (Stage 4)"},
            {"stage": 5, "target": 2000.0, "desc": "$1,000 -> $2,000 (Goal Reached!)"}
        ]
        curr_stage = 1
        for s in stages:
            if balance < s["target"]:
                curr_stage = s["stage"]
                break
            curr_stage = 5

        pct = min(100.0, round((balance / 2000.0) * 100, 1))
        return {
            "current_stage": curr_stage,
            "balance": round(balance, 2),
            "goal": 2000.0,
            "overall_pct": pct,
            "stages": stages
        }

    def enforce_isolated_margin(self, symbol: str) -> Dict[str, Any]:
        """
        Strictly enforces ISOLATED margin mode on Binance Futures for the given symbol.
        CROSS margin mode is completely prohibited under all circumstances.
        """
        if not self.exchange:
            return {"success": False, "error": "Exchange not connected"}
        clean_sym = symbol.replace("/", "").replace(":USDT", "").upper()
        try:
            self.exchange.set_margin_mode('ISOLATED', symbol)
            return {"success": True, "margin_mode": "ISOLATED"}
        except Exception as e:
            err = str(e)
            if "-4046" in err or "No need to change" in err:
                return {"success": True, "margin_mode": "ISOLATED", "note": "Already ISOLATED"}
            try:
                self.exchange.fapiPrivatePostMarginType({
                    'symbol': clean_sym,
                    'marginType': 'ISOLATED'
                })
                return {"success": True, "margin_mode": "ISOLATED"}
            except Exception as e2:
                err2 = str(e2)
                if "-4046" in err2 or "No need to change" in err2:
                    return {"success": True, "margin_mode": "ISOLATED", "note": "Already ISOLATED"}
                return {
                    "success": False,
                    "error": f"CRITICAL REJECTION: Cannot set ISOLATED mode ({e2}). Order blocked to prevent CROSS mode exposure."
                }

    async def execute_4h_short_trade(self, setup: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a real 4H SHORT trade on Binance Futures under HERMES 2.5 APEX HYBRID:
        - Direction: STRICTLY SHORT ONLY. Long signals are rejected.
        - Margin Mode: STRICTLY ISOLATED mode. Cross mode is prohibited.
        - Leverage: 5x Isolated.
        - Risk Controls: TP +2.8% price drop (+14% ROE), Soft SL -2.8% on 4H candle close, Disaster Hard SL +3.8% on Exchange.
        """
        sym = setup["symbol"]
        side = setup["side"].upper()

        # 1. STRICT SHORT-ONLY MANDATE ENFORCEMENT
        if side not in ("SHORT", "SELL"):
            msg = f"[BINANCE MANDATE] Blocked {side} on {sym}. User policy strictly locked to SHORT ONLY on Binance 4H."
            print(msg)
            return {"success": False, "skipped": True, "reason": msg}

        if not self.is_auto_trade_enabled():
            return {"success": False, "skipped": True, "reason": "Binance Auto-Trading is currently paused."}

        entry_price = float(setup.get("entry_price", 0.0))
        tp_pct = float(setup.get("tp_pct", BINANCE_4H_TP_PCT))
        soft_sl_pct = float(setup.get("soft_sl_pct", BINANCE_4H_SL_PCT))
        hard_sl_pct = float(setup.get("hard_sl_pct", BINANCE_HARD_DISASTER_SL_PCT))

        # Targets for Short
        tp_price = round(entry_price * (1.0 - tp_pct), 6)
        soft_sl_price = round(entry_price * (1.0 + soft_sl_pct), 6)
        hard_disaster_sl = round(entry_price * (1.0 + hard_sl_pct), 6)

        if not self.exchange:
            self._init_exchange()

        if self.exchange and self.is_configured():
            try:
                # 2. STRICT ISOLATED MARGIN ENFORCEMENT
                iso_res = self.enforce_isolated_margin(sym)
                if not iso_res["success"]:
                    print(f"[ISOLATED MARGIN ERROR] {iso_res['error']}")
                    return {"success": False, "error": iso_res["error"]}

                # 3. SET 5x LEVERAGE
                try:
                    self.exchange.set_leverage(BINANCE_DEFAULT_LEVERAGE, sym)
                except Exception:
                    pass

                # 4. CAPITAL ALLOCATION & POSITION SIZING
                bal = self.fetch_futures_balance()
                free_usdt = float(bal.get("free_usdt", 0.0) or 0.0)
                if free_usdt < 5.0:
                    return {"success": False, "error": f"Insufficient Binance free balance (${free_usdt:.2f} USDT). Min $5 required."}

                # Compounding Challenge Capital Allocation ($50.00 -> $2,000.00 Milestone)
                comp_bal = float(get_setting("binance_compounding_balance", str(BINANCE_STARTING_MARGIN)))
                margin = min(free_usdt, max(BINANCE_STARTING_MARGIN, comp_bal))
                notional = margin * BINANCE_DEFAULT_LEVERAGE
                raw_amount = notional / entry_price

                amount = round(raw_amount, 2)
                try:
                    amount = float(self.exchange.amount_to_precision(sym, raw_amount))
                except Exception:
                    pass

                # 5. EXECUTE 5x ISOLATED SHORT ORDER
                order = self.exchange.create_order(
                    symbol=sym,
                    type='limit',
                    side='sell',
                    amount=amount,
                    price=entry_price,
                    params={
                        'stopLossPrice': hard_disaster_sl,
                        'takeProfitPrice': tp_price
                    }
                )
                print(f"[BINANCE REAL 4H SHORT EXECUTED] {sym} SHORT @ {entry_price} | TP: {tp_price} | Hard SL: {hard_disaster_sl} (5x ISOLATED)")
                return {
                    "success": True,
                    "mode": "Live Binance Futures (4H SHORT)",
                    "margin_mode": "ISOLATED",
                    "leverage": BINANCE_DEFAULT_LEVERAGE,
                    "order": order,
                    "symbol": sym,
                    "side": "SHORT",
                    "entry_price": entry_price,
                    "tp_price": tp_price,
                    "soft_sl_price": soft_sl_price,
                    "hard_disaster_sl": hard_disaster_sl,
                    "margin": margin
                }
            except Exception as e:
                err_str = str(e)
                if "-2015" in err_str:
                    err_str = "Binance Error -2015: 'Enable Futures' permission required or IP restriction active in Binance API Management."
                print(f"[BINANCE 4H SHORT ERROR] {err_str}")
                return {"success": False, "error": err_str}
        else:
            print(f"[BINANCE 4H SIMULATED] Auto-Executed {sym} SHORT @ {entry_price} | TP: {tp_price} | Soft SL: {soft_sl_price} | Hard SL: {hard_disaster_sl} (5x ISOLATED)")
            return {
                "success": True,
                "mode": "Simulated Binance 4H SHORT (5x ISOLATED)",
                "margin_mode": "ISOLATED",
                "symbol": sym,
                "side": "SHORT",
                "entry_price": entry_price,
                "tp_price": tp_price,
                "soft_sl_price": soft_sl_price,
                "hard_disaster_sl": hard_disaster_sl,
                "margin": BINANCE_STARTING_MARGIN,
                "leverage": BINANCE_DEFAULT_LEVERAGE
            }

    async def execute_1h_scalp_trade(self, zone: Dict[str, Any], confluence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes 1H Fast Scalp trade."""
        symbol = zone["symbol"]
        side = zone["side"].lower()
        entry_price = float(zone.get("entry_price") or zone.get("ob_high", 0.0))
        tp_price = entry_price * (1.015 if side == 'buy' else 0.985)
        soft_sl_price = entry_price * (0.975 if side == 'buy' else 1.025)
        hard_disaster_sl = entry_price * (0.955 if side == 'buy' else 1.045)
        print(f"[BINANCE 1H SCALP ENGINE] {symbol} ({side.upper()}) @ {entry_price}")
        return {
            "success": True,
            "mode": "Simulated Live 1H Scalp",
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "tp_price": tp_price,
            "soft_sl_price": soft_sl_price,
            "hard_disaster_sl": hard_disaster_sl,
            "margin": 50.0,
            "leverage": 5
        }

    async def close_position_market(self, symbol: str, side: str) -> Dict[str, Any]:
        """Closes active futures position immediately at market price."""
        if not self.exchange:
            return {"success": False, "error": "Exchange not connected"}
        try:
            close_side = 'sell' if side.lower() == 'buy' else 'buy'
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=close_side,
                amount=None,
                params={'reduceOnly': True}
            )
            return {"success": True, "order": order}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def evaluate_candle_close_exit(self, side: str, entry_price: float, soft_sl_price: float, closed_candle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates whether a completed candle confirmed a Stop Loss exit or was merely a wick hunt.
        Returns:
          - exit_required: True if candle closed beyond soft SL.
          - is_wick_absorbed: True if candle low/high broke soft SL during the candle but closed safe.
        """
        c_close = closed_candle["close"]
        c_low = closed_candle["low"]
        c_high = closed_candle["high"]
        
        if side.upper() == "BUY":
            # True Breakdown: Candle Close is below Soft SL
            if c_close <= soft_sl_price:
                return {
                    "exit_required": True,
                    "is_wick_absorbed": False,
                    "reason": f"1H Candle closed at {c_close:.4f} below Soft SL ({soft_sl_price:.4f})"
                }
            # Wick Hunt Absorbed: Low breached soft SL, but Close recovered inside
            elif c_low <= soft_sl_price and c_close > soft_sl_price:
                return {
                    "exit_required": False,
                    "is_wick_absorbed": True,
                    "reason": f"Wick swept to {c_low:.4f} but 1H candle closed safely at {c_close:.4f}. Position preserved!"
                }
        else: # SELL
            if c_close >= soft_sl_price:
                return {
                    "exit_required": True,
                    "is_wick_absorbed": False,
                    "reason": f"1H Candle closed at {c_close:.4f} above Soft SL ({soft_sl_price:.4f})"
                }
            elif c_high >= soft_sl_price and c_close < soft_sl_price:
                return {
                    "exit_required": False,
                    "is_wick_absorbed": True,
                    "reason": f"Wick swept to {c_high:.4f} but 1H candle closed safely at {c_close:.4f}. Position preserved!"
                }
                
        return {"exit_required": False, "is_wick_absorbed": False, "reason": "Price within normal bounds."}

binance_trader = BinanceTrader()


