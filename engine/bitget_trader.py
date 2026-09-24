"""
Bitget Real Futures Auto-Trading Execution Service.
Manages:
1. Account balance retrieval (USDT-M Swap).
2. Setting 5x leverage & isolated margin.
3. Placing First-Tap Limit Orders on 2nd OB.
4. Auto-setting TP (+2.0% real move = +10% gain) & SL (2-candle close rule with -4% emergency hard stop).
5. Compounding balance tracking ($50 -> $1,000 Goal).
"""

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
    BITGET_STARTING_MARGIN
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
                    'options': {
                        'defaultType': 'swap',  # USDT-M Perpetual Futures
                    },
                    'enableRateLimit': True,
                })
            except Exception as e:
                print(f"Error initializing Bitget: {e}")
                self.exchange = None
        else:
            self.exchange = None

    def is_configured(self) -> bool:
        return self.exchange is not None

    def is_auto_trade_enabled(self) -> bool:
        enabled_setting = get_setting("bitget_auto_trade", str(BITGET_AUTO_TRADE))
        return enabled_setting.lower() == "true"

    def fetch_futures_balance(self) -> Dict[str, Any]:
        """Fetches live Bitget USDT-M Futures account balance."""
        if not self.exchange:
            self._init_exchange()
        if not self.exchange:
            return {"connected": False, "error": "Bitget credentials not configured"}

        try:
            bal = self.exchange.fetch_balance({'type': 'swap'})
            usdt = bal.get('USDT', {})
            total = float(usdt.get('total', 0.0) or 0.0)
            free = float(usdt.get('free', 0.0) or 0.0)
            used = float(usdt.get('used', 0.0) or 0.0)
            return {
                "connected": True,
                "total_usdt": round(total, 2),
                "free_usdt": round(free, 2),
                "used_usdt": round(used, 2)
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def format_symbol_for_bitget(self, symbol: str) -> str:
        """Converts standard symbol e.g. BTCUSDT to CCXT swap format: BTC/USDT:USDT"""
        base = symbol.replace("USDT", "")
        return f"{base}/USDT:USDT"

    async def execute_2nd_ob_trade(self, zone: Dict[str, Any], confluence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes real Bitget 5x leverage order when 2nd OB triggers.
        """
        if not self.is_auto_trade_enabled():
            return {"success": False, "reason": "Bitget Auto-Trading is currently paused in settings."}

        if not self.exchange:
            self._init_exchange()
        if not self.exchange:
            return {"success": False, "reason": "Bitget credentials missing."}

        symbol_std = zone["symbol"]
        ccxt_symbol = self.format_symbol_for_bitget(symbol_std)
        side = zone["side"].lower() # 'buy' or 'sell'
        entry_price = float(zone.get("entry_price") or zone.get("ob_high", 0.0))
        
        # Target: Real market +2.0% (5x leverage = +10% gain)
        tp_price = entry_price * (1.02 if side == 'buy' else 0.98)
        # Emergency Hard SL: Real market -4.0%
        sl_price = entry_price * (0.96 if side == 'buy' else 1.04)

        try:
            # 1. Check account balance for compounding
            bal_info = self.fetch_futures_balance()
            if not bal_info.get("connected"):
                return {"success": False, "reason": f"Balance fetch failed: {bal_info.get('error')}"}

            free_usdt = bal_info["free_usdt"]
            if free_usdt < 5.0:
                return {"success": False, "reason": f"Insufficient Bitget free balance (${free_usdt} USDT). Min $5 required."}

            # Compounding rule: Use entire free balance (or min $50) for 100% compounding
            margin_to_use = min(free_usdt, max(50.0, free_usdt))
            leverage = BITGET_DEFAULT_LEVERAGE

            # 2. Set Leverage
            try:
                self.exchange.set_leverage(leverage, ccxt_symbol, params={'marginMode': 'isolated'})
            except Exception as e:
                # May already be set
                pass

            # 3. Calculate position quantity in base currency
            position_value_usdt = margin_to_use * leverage
            amount = position_value_usdt / entry_price

            # Round amount based on market precision
            market = self.exchange.market(ccxt_symbol) if hasattr(self.exchange, 'market') else None
            if market and 'precision' in market and 'amount' in market['precision']:
                amount_prec = market['precision']['amount']
                amount = round(amount, amount_prec)

            # 4. Place Order on Bitget with TP and SL attached
            order_params = {
                'marginMode': 'isolated',
                'presetTakeProfitPrice': str(round(tp_price, 4)),
                'presetStopLossPrice': str(round(sl_price, 4))
            }

            order = self.exchange.create_order(
                symbol=ccxt_symbol,
                type='limit',
                side=side,
                amount=amount,
                price=entry_price,
                params=order_params
            )

            # Record in live database
            now_ms = int(time.time() * 1000)
            with get_connection() as conn:
                conn.execute("""
                INSERT INTO paper_trades (
                    zone_id, symbol, side, entry_price, position_size_usdt,
                    tp_price, sl_price, status, entry_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'BITGET_LIVE', ?)
                """, (
                    zone.get("id"), symbol_std, zone["side"], entry_price,
                    margin_to_use, tp_price, sl_price, now_ms
                ))
                conn.commit()

            res = {
                "success": True,
                "order_id": order.get("id"),
                "symbol": symbol_std,
                "margin_usdt": margin_to_use,
                "leverage": f"{leverage}x",
                "entry_price": entry_price,
                "tp_price": tp_price,
                "sl_price": sl_price,
                "confluence": confluence,
                "raw_order": order
            }

            try:
                from alerts.telegram_service import telegram_service
                asyncio.create_task(telegram_service.alert_bitget_execution(res))
            except Exception:
                pass

            return res

        except Exception as e:
            return {"success": False, "reason": str(e)}

    def evaluate_candle_close_exit(self, side: str, entry_price: float, soft_sl_price: float, closed_candle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates 4H candle close to filter wick hunts vs real invalidation.
        """
        c_close = closed_candle["close"]
        c_low = closed_candle["low"]
        c_high = closed_candle["high"]
        
        if side.upper() == "BUY":
            if c_close <= soft_sl_price:
                return {
                    "exit_required": True,
                    "is_wick_absorbed": False,
                    "reason": f"4H Candle closed at {c_close:.4f} below Soft SL ({soft_sl_price:.4f})"
                }
            elif c_low <= soft_sl_price and c_close > soft_sl_price:
                return {
                    "exit_required": False,
                    "is_wick_absorbed": True,
                    "reason": f"Wick swept to {c_low:.4f} but 4H candle closed safely at {c_close:.4f}. Position preserved!"
                }
        else: # SELL
            if c_close >= soft_sl_price:
                return {
                    "exit_required": True,
                    "is_wick_absorbed": False,
                    "reason": f"4H Candle closed at {c_close:.4f} above Soft SL ({soft_sl_price:.4f})"
                }
            elif c_high >= soft_sl_price and c_close < soft_sl_price:
                return {
                    "exit_required": False,
                    "is_wick_absorbed": True,
                    "reason": f"Wick swept to {c_high:.4f} but 4H candle closed safely at {c_close:.4f}. Position preserved!"
                }
                
        return {"exit_required": False, "is_wick_absorbed": False, "reason": "Price within normal bounds."}

bitget_trader = BitgetTrader()
