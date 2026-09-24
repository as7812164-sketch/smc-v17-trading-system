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
    BINANCE_1H_SL_PCT
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
        """Fetches live Binance USDT-M Futures account balance or returns simulated $50 compounding status."""
        if not self.exchange:
            self._init_exchange()
            
        if not self.exchange:
            # Return Simulated State for 1H Challenge
            sim_bal = float(get_setting("binance_1h_sim_balance", "50.0"))
            return {
                "connected": False,
                "mode": "Simulated Live 1H Engine",
                "total_usdt": sim_bal,
                "free_usdt": sim_bal,
                "used_usdt": 0.0,
                "equity": sim_bal,
                "challenge_stage": self._calc_stage(sim_bal)
            }

        try:
            bal = self.exchange.fetch_balance({'type': 'future'})
            usdt = bal.get('USDT', {})
            total = float(usdt.get('total', 0.0) or 0.0)
            free = float(usdt.get('free', 0.0) or 0.0)
            used = float(usdt.get('used', 0.0) or 0.0)
            return {
                "connected": True,
                "mode": "Live Binance Futures",
                "total_usdt": round(total, 2),
                "free_usdt": round(free, 2),
                "used_usdt": round(used, 2),
                "equity": round(total, 2),
                "challenge_stage": self._calc_stage(total)
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def _calc_stage(self, balance: float) -> Dict[str, Any]:
        """Calculates 1H Compounding ladder progress."""
        stages = [
            {"stage": 1, "target": 100.0, "desc": "$50 -> $100 (Stage 1)"},
            {"stage": 2, "target": 250.0, "desc": "$100 -> $250 (Stage 2)"},
            {"stage": 3, "target": 500.0, "desc": "$250 -> $500 (Stage 3)"},
            {"stage": 4, "target": 750.0, "desc": "$500 -> $750 (Stage 4)"},
            {"stage": 5, "target": 1000.0, "desc": "$750 -> $1,000 (Goal Reached!)"}
        ]
        curr_stage = 1
        for s in stages:
            if balance < s["target"]:
                curr_stage = s["stage"]
                break
            curr_stage = 5

        pct = min(100.0, round((balance / 1000.0) * 100, 1))
        return {
            "current_stage": curr_stage,
            "balance": round(balance, 2),
            "goal": 1000.0,
            "overall_pct": pct,
            "stages": stages
        }

    async def execute_1h_scalp_trade(self, zone: Dict[str, Any], confluence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes 1H Fast Scalp 5x trade on Binance with Hybrid Candle-Close Stop Loss.
        - Soft SL: -2.5% (Only triggered if 1H candle closes beyond this level, filtering wick hunts)
        - Disaster Hard Stop: -4.5% on Exchange (Prevents black-swan liquidation)
        - Take Profit: +1.5% Price (+7.5% ROE @ 5x)
        """
        symbol = zone["symbol"]
        side = zone["side"].lower() # 'buy' or 'sell'
        entry_price = float(zone.get("entry_price") or zone.get("ob_high", 0.0))
        
        # 1H Scalp Targets
        tp_price = entry_price * (1.015 if side == 'buy' else 0.985)
        soft_sl_price = entry_price * (0.975 if side == 'buy' else 1.025)
        hard_disaster_sl = entry_price * (0.955 if side == 'buy' else 1.045)
        
        # If Real Binance configured
        if self.exchange and self.is_auto_trade_enabled():
            try:
                # Set 5x leverage
                try:
                    self.exchange.set_leverage(BINANCE_DEFAULT_LEVERAGE, symbol)
                except Exception:
                    pass
                    
                bal = self.fetch_futures_balance()
                free = bal.get("free_usdt", 50.0)
                margin = min(free, max(50.0, free))
                notional = margin * BINANCE_DEFAULT_LEVERAGE
                amount = notional / entry_price
                
                order_side = 'buy' if side == 'buy' else 'sell'
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=order_side,
                    amount=amount,
                    price=entry_price,
                    params={
                        'stopLossPrice': hard_disaster_sl,  # Emergency circuit breaker
                        'takeProfitPrice': tp_price
                    }
                )
                return {
                    "success": True,
                    "mode": "Live Binance",
                    "order": order,
                    "soft_sl_price": soft_sl_price,
                    "hard_disaster_sl": hard_disaster_sl,
                    "tp_price": tp_price
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            # Simulated 1H Engine Execution
            print(f"[BINANCE 1H SCALP ENGINE] Auto-Executed {symbol} ({side.upper()}) @ {entry_price} | TP: {tp_price:.4f} (+7.5% ROE) | Soft SL (Candle Close): {soft_sl_price:.4f} | Disaster Hard SL: {hard_disaster_sl:.4f}")
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


