"""
MARKET SENTIMENT, NEWS & WHALE CATALYST ENGINE (PHASE 6)
Integrates:
- Live CoinDesk & CoinTelegraph RSS news streams
- Alternative.me Crypto Fear & Greed Index
- Binance Futures Open Interest & Funding Rate
- Whale Block Orders and Liquidation tracking
"""

import time
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

_NEWS_CACHE = {"timestamp": 0.0, "data": []}
_SENTIMENT_CACHE = {"timestamp": 0.0, "data": {}}
_DERIVATIVES_CACHE: Dict[str, Dict[str, Any]] = {}

def get_crypto_news() -> List[Dict[str, Any]]:
    global _NEWS_CACHE
    now = time.time()
    if _NEWS_CACHE["data"] and (now - _NEWS_CACHE["timestamp"]) < 180:
        return _NEWS_CACHE["data"]

    feeds = [
        ("CoinTelegraph", "https://cointelegraph.com/rss"),
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/")
    ]
    items_list = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for source, url in feeds:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                xml_data = resp.read().decode("utf-8", errors="replace")
                tree = ET.fromstring(xml_data)
                for item in tree.findall(".//item")[:15]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    pub_elem = item.find("pubDate")
                    desc_elem = item.find("description")

                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                    pub = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                    desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""

                    clean_desc = re.sub(r"<[^<]+?>", "", desc)[:180] if desc else ""
                    tags = []
                    text_upper = (title + " " + clean_desc).upper()
                    for coin in ["BTC", "ETH", "SOL", "XRP", "DOGE", "FED", "SEC", "ETF", "BINANCE", "WHALE"]:
                        if coin in text_upper:
                            tags.append(coin)

                    if title:
                        items_list.append({
                            "source": source,
                            "title": title,
                            "link": link,
                            "pubDate": pub,
                            "description": clean_desc,
                            "tags": tags[:4]
                        })
        except Exception:
            pass

    if items_list:
        _NEWS_CACHE = {"timestamp": now, "data": items_list}
        return items_list

    return _NEWS_CACHE.get("data", [])

def get_fear_and_greed() -> Dict[str, Any]:
    global _SENTIMENT_CACHE
    now = time.time()
    if _SENTIMENT_CACHE["data"] and (now - _SENTIMENT_CACHE["timestamp"]) < 600:
        return _SENTIMENT_CACHE["data"]

    url = "https://api.alternative.me/fng/?limit=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            entry = data.get("data", [{}])[0]
            val = int(entry.get("value", 50))
            classification = entry.get("value_classification", "Neutral")
            res = {
                "value": val,
                "classification": classification,
                "timestamp": entry.get("timestamp", str(int(now))),
                "status": "ok"
            }
            _SENTIMENT_CACHE = {"timestamp": now, "data": res}
            return res
    except Exception:
        fallback = {"value": 50, "classification": "Neutral", "timestamp": str(int(now)), "status": "fallback"}
        return _SENTIMENT_CACHE.get("data") or fallback

def get_derivatives_macro(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    global _DERIVATIVES_CACHE
    symbol = symbol.upper()
    now = time.time()
    cached = _DERIVATIVES_CACHE.get(symbol)
    if cached and (now - cached["timestamp"]) < 30:
        return cached["data"]

    result = {
        "symbol": symbol,
        "funding_rate": "0.0100%",
        "open_interest": "--",
        "mark_price": 0.0,
        "next_funding_time": 0
    }

    headers = {"User-Agent": "Mozilla/5.0"}
    # 1. Premium Index / Funding Rate
    try:
        p_url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}"
        req = urllib.request.Request(p_url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            pd = json.loads(resp.read().decode())
            fr = float(pd.get("lastFundingRate", 0.0001)) * 100.0
            result["funding_rate"] = f"{fr:+.4f}%"
            result["mark_price"] = float(pd.get("markPrice", 0.0))
            result["next_funding_time"] = int(pd.get("nextFundingTime", 0))
    except Exception:
        pass

    # 2. Open Interest
    try:
        oi_url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}"
        req = urllib.request.Request(oi_url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            oid = json.loads(resp.read().decode())
            oi_val = float(oid.get("openInterest", 0.0))
            result["open_interest"] = f"{oi_val:,.1f}"
    except Exception:
        pass

    _DERIVATIVES_CACHE[symbol] = {"timestamp": now, "data": result}
    return result

def get_footprint_clusters(symbol: str = "BTCUSDT", limit: int = 500) -> Dict[str, Any]:
    """
    Fetches real-time aggressive trades from Binance Futures and clusters them
    by price tick into Bid Volume x Ask Volume footprint ladder with POC and Imbalances.
    """
    url = f"https://fapi.binance.com/fapi/v1/aggTrades?symbol={symbol.upper()}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            trades = json.loads(resp.read().decode())
    except Exception as e:
        return {"symbol": symbol.upper(), "error": str(e), "ladder": []}

    if not trades:
        return {"symbol": symbol.upper(), "ladder": []}

    prices = [float(t["p"]) for t in trades]
    min_p, max_p = min(prices), max(prices)
    span = max_p - min_p
    bucket_size = max(0.5, round(span / 12, 1)) if span > 10 else (round(span / 12, 4) or 0.001)

    clusters = {}
    tot_buy = 0.0
    tot_sell = 0.0

    for t in trades:
        p = float(t["p"])
        q = float(t["q"])
        is_buyer_maker = t["m"]
        bucket = round(p / bucket_size) * bucket_size

        if bucket not in clusters:
            clusters[bucket] = {"price": bucket, "bid_vol": 0.0, "ask_vol": 0.0}

        if is_buyer_maker:
            clusters[bucket]["bid_vol"] += q
            tot_sell += q
        else:
            clusters[bucket]["ask_vol"] += q
            tot_buy += q

    ladder = sorted(clusters.values(), key=lambda x: x["price"], reverse=True)
    max_vol = 0.0
    poc_price = ladder[0]["price"] if ladder else 0.0

    for row in ladder:
        tot = row["bid_vol"] + row["ask_vol"]
        row["total_vol"] = tot
        if tot > max_vol:
            max_vol = tot
            poc_price = row["price"]
        row["delta"] = row["ask_vol"] - row["bid_vol"]
        b = row["bid_vol"]
        a = row["ask_vol"]
        if a >= 2.5 * b and a > 0.05:
            row["imbalance"] = "BUY"
        elif b >= 2.5 * a and b > 0.05:
            row["imbalance"] = "SELL"
        else:
            row["imbalance"] = "NEUTRAL"

    for row in ladder:
        row["is_poc"] = (row["price"] == poc_price)

    tot_all = tot_buy + tot_sell
    buy_ratio = round((tot_buy / tot_all) * 100, 1) if tot_all > 0 else 50.0

    return {
        "symbol": symbol.upper(),
        "poc_price": poc_price,
        "max_vol": max_vol,
        "total_delta": tot_buy - tot_sell,
        "total_volume": tot_all,
        "buy_ratio": buy_ratio,
        "ladder": ladder[:18]
    }

def get_orderbook_depth(symbol: str = "BTCUSDT", limit: int = 20) -> Dict[str, Any]:
    """
    Fetches real-time Level 2 Order Book depth snapshot from Binance Futures REST API
    providing instant real data for DOM Ladder and Heatmap.
    """
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol.upper()}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            return {
                "symbol": symbol.upper(),
                "bids": data.get("bids", []),
                "asks": data.get("asks", [])
            }
    except Exception as e:
        return {"symbol": symbol.upper(), "error": str(e), "bids": [], "asks": []}

