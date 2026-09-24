import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional
from database.db import set_metric, increment_metric

BINANCE_VISION_BASE = "https://data-api.binance.vision"
BINANCE_FAPI_BASE = "https://fapi.binance.com"
BYBIT_BASE = "https://api.bybit.com"

BYBIT_INTERVAL_MAP = {
    "15m": "15",
    "1h": "60",
    "4h": "240",
    "1d": "D"
}

def map_symbol_for_spot(sym: str):
    """Maps Futures symbol to Spot symbol and multiplier for 1000-tokens."""
    if sym.startswith("1000"):
        return sym[4:], 1000.0
    return sym, 1.0

class BinanceFeed:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_heartbeat = 0
        self.last_data_time = 0
        self.is_connected = False
        self.klines_cache: Dict[str, tuple] = {}
        self.oi_cache: Dict[str, tuple] = {}

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=60, limit_per_host=30, ttl_dns_cache=300, ssl=False)
            timeout = aiohttp.ClientTimeout(sock_connect=8, sock_read=12)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def fetch_klines(self, symbol: str, interval: str = "4h", limit: int = 200, force_fresh: bool = False) -> List[Dict[str, Any]]:
        """Fetch 4H historical klines with multi-provider fallback (Binance Vision -> Bybit -> Binance Futures)."""
        cache_key = f"{symbol}_{interval}_{limit}"
        now = time.time()
        if not force_fresh and cache_key in self.klines_cache:
            ts, data = self.klines_cache[cache_key]
            if now - ts < 60:
                return data

        session = await self.get_session()

        # Provider 1: Binance Vision API (Universal, no US geo-restrictions)
        if symbol != "KASUSDT":
            spot_sym, mult = map_symbol_for_spot(symbol)
            url = f"{BINANCE_VISION_BASE}/api/v3/klines"
            params = {"symbol": spot_sym, "interval": interval, "limit": limit}
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candles = []
                        running_cvd = 0.0
                        for k in data:
                            vol = float(k[5])
                            taker_buy = float(k[9]) * mult if len(k) > 9 else vol * 0.5
                            taker_sell = max(0.0, vol - taker_buy)
                            delta = taker_buy - taker_sell
                            running_cvd += delta
                            candles.append({
                                "time": int(k[0]),
                                "open": float(k[1]) * mult,
                                "high": float(k[2]) * mult,
                                "low": float(k[3]) * mult,
                                "close": float(k[4]) * mult,
                                "volume": vol,
                                "taker_buy": taker_buy,
                                "taker_sell": taker_sell,
                                "delta": delta,
                                "cvd": running_cvd
                            })
                        if candles:
                            self.last_heartbeat = time.time()
                            self.last_data_time = time.time()
                            self.is_connected = True
                            set_metric("binance_status", "CONNECTED")
                            self.klines_cache[cache_key] = (time.time(), candles)
                            return candles
            except Exception:
                pass

        # Provider 2: Bybit Linear API (For KASUSDT or if Binance Vision is unreachable)
        bybit_tf = BYBIT_INTERVAL_MAP.get(interval.lower(), "240")
        bybit_url = f"{BYBIT_BASE}/v5/market/kline"
        bybit_params = {"category": "linear", "symbol": symbol, "interval": bybit_tf, "limit": limit}
        try:
            async with session.get(bybit_url, params=bybit_params) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    kline_list = res_json.get("result", {}).get("list", [])
                    if kline_list:
                        # Bybit returns descending (newest first); reverse to chronological
                        candles = []
                        running_cvd = 0.0
                        for k in reversed(kline_list):
                            vol = float(k[5])
                            c_val = float(k[4])
                            o_val = float(k[1])
                            h_val = float(k[2])
                            l_val = float(k[3])
                            rng = max(1e-8, h_val - l_val)
                            body_bias = (c_val - o_val) / rng
                            taker_buy = vol * (0.5 + 0.25 * body_bias)
                            taker_sell = max(0.0, vol - taker_buy)
                            delta = taker_buy - taker_sell
                            running_cvd += delta
                            candles.append({
                                "time": int(k[0]),
                                "open": o_val,
                                "high": h_val,
                                "low": l_val,
                                "close": c_val,
                                "volume": vol,
                                "taker_buy": taker_buy,
                                "taker_sell": taker_sell,
                                "delta": delta,
                                "cvd": running_cvd
                            })
                        self.last_heartbeat = time.time()
                        self.last_data_time = time.time()
                        self.is_connected = True
                        set_metric("binance_status", "CONNECTED")
                        self.klines_cache[cache_key] = (time.time(), candles)
                        return candles
        except Exception:
            pass

        # Provider 3: Binance Futures Direct (Non-US servers fallback)
        try:
            fapi_url = f"{BINANCE_FAPI_BASE}/fapi/v1/klines"
            async with session.get(fapi_url, params={"symbol": symbol, "interval": interval, "limit": limit}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    candles = []
                    running_cvd = 0.0
                    for k in data:
                        vol = float(k[5])
                        taker_buy = float(k[9]) if len(k) > 9 else vol * 0.5
                        taker_sell = max(0.0, vol - taker_buy)
                        delta = taker_buy - taker_sell
                        running_cvd += delta
                        candles.append({
                            "time": int(k[0]),
                            "open": float(k[1]),
                            "high": float(k[2]),
                            "low": float(k[3]),
                            "close": float(k[4]),
                            "volume": vol,
                            "taker_buy": taker_buy,
                            "taker_sell": taker_sell,
                            "delta": delta,
                            "cvd": running_cvd
                        })
                    if candles:
                        self.last_heartbeat = time.time()
                        self.last_data_time = time.time()
                        self.is_connected = True
                        set_metric("binance_status", "CONNECTED")
                        self.klines_cache[cache_key] = (time.time(), candles)
                        return candles
        except Exception:
            pass

        increment_metric("errors")
        return []

    async def fetch_all_tickers(self) -> Dict[str, float]:
        """Fetch live ticker prices for all pairs using Vision and Bybit fallbacks."""
        session = await self.get_session()
        tickers: Dict[str, float] = {}

        # 1. Binance Futures direct (Primary for Futures pairs)
        try:
            async with session.get(f"{BINANCE_FAPI_BASE}/fapi/v1/ticker/price", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data:
                        tickers[item["symbol"]] = float(item["price"])
                    self.is_connected = True
                    set_metric("binance_status", "CONNECTED")
        except Exception:
            pass

        # 2. Binance Vision Tickers (Spot fallback/supplement)
        try:
            async with session.get(f"{BINANCE_VISION_BASE}/api/v3/ticker/price", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data:
                        sym = item["symbol"]
                        if sym not in tickers:
                            tickers[sym] = float(item["price"])
                        if f"1000{sym}" not in tickers:
                            tickers[f"1000{sym}"] = float(item["price"]) * 1000.0
                    self.is_connected = True
                    set_metric("binance_status", "CONNECTED")
        except Exception:
            pass

        # 3. Bybit Tickers (covers extra pairs)
        try:
            async with session.get(f"{BYBIT_BASE}/v5/market/tickers?category=linear", timeout=5) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    for item in res_json.get("result", {}).get("list", []):
                        sym = item.get("symbol")
                        price_str = item.get("lastPrice")
                        if sym and price_str and sym not in tickers:
                            tickers[sym] = float(price_str)
                    self.is_connected = True
                    set_metric("binance_status", "CONNECTED")
        except Exception:
            pass

        if tickers:
            self.last_heartbeat = time.time()
            self.last_data_time = time.time()

        return tickers

    async def fetch_multiple_symbols(self, symbols: List[str], interval: str = "4h", limit: int = 200, chunk_size: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Batch fetch klines for configured coins in gentle chunks."""
        results: Dict[str, List[Dict[str, Any]]] = {}
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]
            tasks = [self.fetch_klines(s, interval, limit) for s in chunk]
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            for sym, res in zip(chunk, chunk_results):
                if isinstance(res, list) and res:
                    results[sym] = res
            await asyncio.sleep(0.1)
        return results

    async def fetch_open_interest(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time Open Interest for a symbol with Bybit fallback and 30s cache."""
        now = time.time()
        if symbol in self.oi_cache:
            ts, data = self.oi_cache[symbol]
            if now - ts < 30:
                return data

        session = await self.get_session()
        
        # Provider 1: Binance Futures
        try:
            url = f"{BINANCE_FAPI_BASE}/fapi/v1/openInterest"
            async with session.get(url, params={"symbol": symbol}, timeout=5) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    oi_val = float(res.get("openInterest", 0.0))
                    result = {
                        "symbol": symbol,
                        "open_interest": oi_val,
                        "time": int(res.get("time", int(time.time() * 1000))),
                        "provider": "binance"
                    }
                    self.oi_cache[symbol] = (now, result)
                    return result
        except Exception:
            pass

        # Provider 2: Bybit Linear Fallback
        try:
            url = f"{BYBIT_BASE}/v5/market/open-interest"
            params = {"category": "linear", "symbol": symbol, "intervalTime": "5min", "limit": 1}
            async with session.get(url, params=params, timeout=5) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    item = res.get("result", {}).get("list", [{}])[0]
                    oi_val = float(item.get("openInterest", 0.0))
                    result = {
                        "symbol": symbol,
                        "open_interest": oi_val,
                        "time": int(item.get("timestamp", int(time.time() * 1000))),
                        "provider": "bybit"
                    }
                    self.oi_cache[symbol] = (now, result)
                    return result
        except Exception:
            pass

        return {"symbol": symbol, "open_interest": 0.0, "time": int(time.time() * 1000), "provider": "none"}

    async def fetch_open_interest_hist(self, symbol: str, period: str = "1h", limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch historical Open Interest trend (e.g. 1h periods) to calculate ΔOI%."""
        session = await self.get_session()
        try:
            url = f"{BINANCE_FAPI_BASE}/futures/data/openInterestHist"
            params = {"symbol": symbol, "period": period, "limit": limit}
            async with session.get(url, params=params, timeout=6) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    res = []
                    for item in data:
                        res.append({
                            "time": int(item["timestamp"]),
                            "open_interest": float(item["sumOpenInterest"]),
                            "value_usd": float(item.get("sumOpenInterestValue", 0.0))
                        })
                    return res
        except Exception:
            pass
    async def fetch_order_book_depth(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Fetch real-time order book depth (pending bids and asks) for resting liquidity detection."""
        session = await self.get_session()
        
        # Provider 1: Binance Futures
        try:
            url = f"{BINANCE_FAPI_BASE}/fapi/v1/depth"
            async with session.get(url, params={"symbol": symbol, "limit": limit}, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "symbol": symbol,
                        "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
                        "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
                        "provider": "binance_futures"
                    }
        except Exception:
            pass

        # Provider 2: Binance Vision Spot Fallback
        try:
            spot_sym, _ = map_symbol_for_spot(symbol)
            url = f"{BINANCE_VISION_BASE}/api/v3/depth"
            async with session.get(url, params={"symbol": spot_sym, "limit": limit}, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "symbol": symbol,
                        "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
                        "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
                        "provider": "binance_spot"
                    }
        except Exception:
            pass

        # Provider 3: Bybit Linear Fallback
        try:
            url = f"{BYBIT_BASE}/v5/market/orderbook"
            params = {"category": "linear", "symbol": symbol, "limit": limit}
            async with session.get(url, params=params, timeout=5) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    result = res.get("result", {})
                    return {
                        "symbol": symbol,
                        "bids": [[float(p), float(q)] for p, q in result.get("b", [])],
                        "asks": [[float(p), float(q)] for p, q in result.get("a", [])],
                        "provider": "bybit"
                    }
        except Exception:
            pass

        return {"symbol": symbol, "bids": [], "asks": [], "provider": "none"}

binance_feed = BinanceFeed()
