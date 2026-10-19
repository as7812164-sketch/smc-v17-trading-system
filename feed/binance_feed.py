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
        self.last_24h_tickers: Dict[str, Dict[str, Any]] = {}
        self.last_24h_time: float = 0.0
        self.last_all_tickers: Dict[str, float] = {}

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=60, limit_per_host=30, ttl_dns_cache=300, ssl=False)
            timeout = aiohttp.ClientTimeout(sock_connect=8, sock_read=12)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate"
            }
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers)
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

        # Provider 0: MEXC Global Futures Klines (Up to 2,000 candles, 1-year history, ZERO GEOBLOCKING on Render)
        try:
            mexc_map = {
                "1m": "Min1", "5m": "Min5", "15m": "Min15", "1h": "Min60", "4h": "Hour4",
                "1d": "Day1", "1w": "Week1", "1month": "Month1", "1m_month": "Month1"
            }
            clean_sym = symbol.upper().replace("1000", "") if "1000" in symbol.upper() else symbol.upper()
            mexc_sym = clean_sym.replace("USDT", "_USDT")
            mexc_iv = mexc_map.get(interval.lower(), "Min15" if "15" in interval else ("Min60" if "1h" in interval.lower() else "Hour4"))
            m_mult = 1000.0 if "1000" in symbol.upper() else 1.0
            
            url = f"https://contract.mexc.com/api/v1/contract/kline/{mexc_sym}?interval={mexc_iv}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    data = d.get("data", {})
                    t = data.get("time", [])
                    o = data.get("open", [])
                    h = data.get("high", [])
                    l = data.get("low", [])
                    c = data.get("close", [])
                    v = data.get("vol", [])
                    if t and len(t) > 0:
                        candles = []
                        running_cvd = 0.0
                        for i in range(len(t)):
                            vol = float(v[i])
                            c_val = round(float(c[i]) * m_mult, 6)
                            o_val = round(float(o[i]) * m_mult, 6)
                            h_val = round(float(h[i]) * m_mult, 6)
                            l_val = round(float(l[i]) * m_mult, 6)
                            rng = max(1e-8, h_val - l_val)
                            body_bias = (c_val - o_val) / rng
                            taker_buy = vol * (0.5 + 0.25 * body_bias)
                            taker_sell = max(0.0, vol - taker_buy)
                            delta = taker_buy - taker_sell
                            running_cvd += delta
                            candles.append({
                                "time": int(t[i]) * 1000,
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
                        if candles:
                            candles = candles[-limit:] if limit > 0 else candles
                            self.last_heartbeat = time.time()
                            self.last_data_time = time.time()
                            self.is_connected = True
                            set_metric("binance_status", "CONNECTED")
                            self.klines_cache[cache_key] = (time.time(), candles)
                            return candles
        except Exception:
            pass

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

    async def fetch_symbol_price(self, symbol: str) -> Optional[float]:
        """Direct ultra-fast single-symbol price fetch with 5-tier failover (Bitget -> MEXC -> Vision -> Bybit -> Peer)."""
        if not symbol:
            return None
        sym = symbol.upper()
        spot_sym, mult = map_symbol_for_spot(sym)
        session = await self.get_session()

        # Tier 1: Bitget Futures single ticker (Primary - exact exchange used by Hermes)
        try:
            url = f"https://api.bitget.com/api/v2/mix/market/ticker?symbol={sym}&productType=usdt-futures"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    data_list = d.get("data", [])
                    if data_list:
                        p = float(data_list[0].get("lastPr", 0.0) or data_list[0].get("markPrice", 0.0))
                        if p > 0:
                            return p
        except Exception:
            pass

        # Tier 2: MEXC single price (Global, ultra-fast, zero cloud geoblock)
        try:
            url = f"https://api.mexc.com/api/v3/ticker/price?symbol={sym}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    p = float(d.get("price", 0.0))
                    if p > 0:
                        return p
        except Exception:
            pass

        # Tier 3: Binance Vision single price (~60ms)
        try:
            url = f"{BINANCE_VISION_BASE}/api/v3/ticker/price?symbol={spot_sym}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    p = float(data.get("price", 0.0)) * mult
                    if p > 0:
                        return p
        except Exception:
            pass

        # Tier 4: Bybit linear single ticker
        try:
            url = f"{BYBIT_BASE}/v5/market/tickers?category=linear&symbol={sym}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lst = data.get("result", {}).get("list", [])
                    if lst:
                        p = float(lst[0].get("lastPrice", 0.0))
                        if p > 0:
                            return p
        except Exception:
            pass

        # Tier 5: Peer Render API
        try:
            url = f"https://nexuspro-terminal.onrender.com/api/ticker/{sym}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    p = float(data.get("last_price", 0.0))
                    if p > 0:
                        return p
        except Exception:
            pass

        return None

    async def fetch_all_tickers(self) -> Dict[str, float]:
        """Fetch live ticker prices for all pairs using Bitget Futures, MEXC, Vision, and Bybit fallbacks."""
        session = await self.get_session()
        tickers: Dict[str, float] = {}

        # 1. Bitget Futures Bulk (Primary - covers 846 Futures pairs, zero geoblock)
        try:
            url = "https://api.bitget.com/api/v2/mix/market/tickers?productType=usdt-futures"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    for item in d.get("data", []):
                        sym = item.get("symbol")
                        p_str = item.get("lastPr") or item.get("markPrice")
                        if sym and p_str:
                            tickers[sym] = float(p_str)
                    if tickers:
                        self.is_connected = True
                        set_metric("binance_status", "CONNECTED")
        except Exception:
            pass

        # 2. MEXC Bulk Tickers (Secondary - covers 1866 pairs, zero geoblock)
        if len(tickers) < 50:
            try:
                url = "https://api.mexc.com/api/v3/ticker/price"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data:
                            sym = item.get("symbol")
                            p = float(item.get("price", 0.0))
                            if sym and p > 0 and sym not in tickers:
                                tickers[sym] = p
                        if tickers:
                            self.is_connected = True
                            set_metric("binance_status", "CONNECTED")
            except Exception:
                pass

        # 3. Binance Vision Tickers (Spot fallback)
        if len(tickers) < 50:
            try:
                async with session.get(f"{BINANCE_VISION_BASE}/api/v3/ticker/price", timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data:
                            sym = item["symbol"]
                            p = float(item["price"])
                            if sym not in tickers:
                                tickers[sym] = p
                            k1000 = f"1000{sym}"
                            if k1000 not in tickers:
                                tickers[k1000] = p * 1000.0
                        if tickers:
                            self.is_connected = True
                            set_metric("binance_status", "CONNECTED")
            except Exception:
                pass

        # 4. Bybit Linear Tickers (Covers extra linear futures contracts)
        if len(tickers) < 50:
            try:
                async with session.get(f"{BYBIT_BASE}/v5/market/tickers?category=linear", timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        for item in res_json.get("result", {}).get("list", []):
                            sym = item.get("symbol")
                            price_str = item.get("lastPrice")
                            if sym and price_str:
                                p = float(price_str)
                                if sym not in tickers:
                                    tickers[sym] = p
            except Exception:
                pass

        # 5. Peer Render Endpoint Fallback
        if len(tickers) < 20:
            try:
                peer_url = "https://nexuspro-terminal.onrender.com/api/markets"
                async with session.get(peer_url, timeout=aiohttp.ClientTimeout(total=3.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("all_markets", []) or data.get("champions", []):
                            sym = item.get("symbol")
                            p = float(item.get("last_price", 0.0))
                            if sym and p > 0 and sym not in tickers:
                                tickers[sym] = p
            except Exception:
                pass

        if tickers:
            self.last_all_tickers = tickers
            self.last_heartbeat = time.time()
            self.last_data_time = time.time()
            return tickers

        # Last cached tickers guarantee (Never return empty if we previously had tickers)
        return self.last_all_tickers or {}

    async def fetch_24hr_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Fetch live 24h ticker statistics (price, change %, high, low, volume) with caching and fallbacks."""
        now = time.time()
        if self.last_24h_tickers and (now - self.last_24h_time < 10.0):
            return self.last_24h_tickers

        session = await self.get_session()
        data_map: Dict[str, Dict[str, Any]] = {}

        # 1. Bitget Futures 24hr (Primary - matches exchange execution, zero geoblock)
        try:
            url = "https://api.bitget.com/api/v2/mix/market/tickers?productType=usdt-futures"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=4.5)) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    for item in d.get("data", []):
                        sym = item.get("symbol")
                        if sym:
                            p = float(item.get("lastPr", 0.0) or item.get("markPrice", 0.0) or 0.0)
                            chg = float(item.get("change24h", 0.0) or 0.0) * 100.0
                            h = float(item.get("high24h", 0.0) or 0.0)
                            l = float(item.get("low24h", 0.0) or 0.0)
                            vol = float(item.get("usdtVolume", 0.0) or item.get("baseVolume", 0.0) or 0.0)
                            data_map[sym] = {
                                "price": p,
                                "change_24h": chg,
                                "high_24h": h,
                                "low_24h": l,
                                "volume_24h": vol,
                            }
                    if data_map:
                        self.is_connected = True
                        set_metric("binance_status", "CONNECTED")
                        self.last_24h_tickers = data_map
                        self.last_24h_time = time.time()
                        self.last_heartbeat = time.time()
                        self.last_data_time = time.time()
                        return self.last_24h_tickers
        except Exception:
            pass

        # 2. MEXC 24hr Tickers (Secondary - global spot pairs)
        try:
            url = "https://api.mexc.com/api/v3/ticker/24hr"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=4.5)) as resp:
                if resp.status == 200:
                    raw = await resp.json()
                    for item in raw:
                        sym = item.get("symbol")
                        if sym and sym not in data_map:
                            data_map[sym] = {
                                "price": float(item.get("lastPrice", 0.0) or 0.0),
                                "change_24h": float(item.get("priceChangePercent", 0.0) or 0.0),
                                "high_24h": float(item.get("highPrice", 0.0) or 0.0),
                                "low_24h": float(item.get("lowPrice", 0.0) or 0.0),
                                "volume_24h": float(item.get("quoteVolume", 0.0) or 0.0),
                            }
                    if data_map:
                        self.is_connected = True
                        set_metric("binance_status", "CONNECTED")
                        self.last_24h_tickers = data_map
                        self.last_24h_time = time.time()
                        self.last_heartbeat = time.time()
                        self.last_data_time = time.time()
                        return self.last_24h_tickers
        except Exception:
            pass

        # 3. Binance Vision 24hr
        try:
            async with session.get(f"{BINANCE_VISION_BASE}/api/v3/ticker/24hr", timeout=aiohttp.ClientTimeout(total=5.0)) as resp:
                if resp.status == 200:
                    raw = await resp.json()
                    for item in raw:
                        sym = item.get("symbol")
                        if sym and sym not in data_map:
                            data_map[sym] = {
                                "price": float(item.get("lastPrice", 0.0) or 0.0),
                                "change_24h": float(item.get("priceChangePercent", 0.0) or 0.0),
                                "high_24h": float(item.get("highPrice", 0.0) or 0.0),
                                "low_24h": float(item.get("lowPrice", 0.0) or 0.0),
                                "volume_24h": float(item.get("quoteVolume", 0.0) or 0.0),
                            }
                    if data_map:
                        self.last_24h_tickers = data_map
                        self.last_24h_time = time.time()
                        return self.last_24h_tickers
        except Exception:
            pass

        # 4. Peer Render Endpoint Fallback
        try:
            peer_url = "https://nexuspro-terminal.onrender.com/api/markets"
            async with session.get(peer_url, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data.get("all_markets", []) or data.get("champions", []):
                        sym = item.get("symbol")
                        if sym and sym not in data_map:
                            data_map[sym] = {
                                "price": float(item.get("last_price", 0.0)),
                                "change_24h": float(item.get("price_change_pct", 0.0)),
                                "high_24h": float(item.get("high_24h", 0.0)),
                                "low_24h": float(item.get("low_24h", 0.0)),
                                "volume_24h": float(item.get("volume_24h", 0.0)),
                            }
                    if data_map:
                        self.last_24h_tickers = data_map
                        self.last_24h_time = time.time()
                        return self.last_24h_tickers
        except Exception:
            pass

        if data_map:
            self.last_24h_tickers = data_map
            self.last_24h_time = time.time()
            self.last_heartbeat = time.time()
            self.last_data_time = time.time()

        return self.last_24h_tickers

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
