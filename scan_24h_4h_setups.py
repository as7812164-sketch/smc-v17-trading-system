"""
Inspect all qualified 4H Order Block setups across Top-22 Champions formed or tapped in the last 24 hours (2026-09-28).
"""

import sys
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
NOW_MS = int(time.time() * 1000)
PAST_24H_MS = NOW_MS - (24 * 3600 * 1000)

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

BINANCE_BASE = "https://data-api.binance.vision/api/v3/klines"

def fetch_klines(symbol: str, interval: str = "4h", limit: int = 100) -> List[Dict[str, Any]]:
    sym_query = "1000SHIBUSDT" if symbol == "SHIBUSDT" else symbol
    url = f"{BINANCE_BASE}?symbol={sym_query}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candles = []
            for c in data:
                candles.append({
                    "time": int(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5])
                })
            return candles
    except Exception:
        return []

def main():
    results = []

    for sym in TOP_22_CHAMPIONS:
        candles = fetch_klines(sym, "4h", 80)
        n = len(candles)
        if n < 30:
            continue

        # Check all possible setups that were valid in the last 15 candles (~60 hours)
        for i in range(max(10, n - 25), n - 1):
            # 1. Bullish Decisional OB
            if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 2:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= 0.050:
                        idm_low = candles[high_idx - 1]["low"]
                        best_mid = -1
                        max_bg = 0.0
                        for mid in range(i+1, high_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid

                        if best_mid != -1 and best_mid + 1 < n:
                            dec_c = candles[best_mid - 1]
                            dec_top = max(dec_c["open"], dec_c["close"])
                            dec_bot = dec_c["low"]
                            has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"])
                            if has_fvg:
                                # Check if tapped today
                                for t in range(high_idx + 1, min(high_idx + 28, n)):
                                    tap_c = candles[t]
                                    if tap_c["low"] <= dec_top * 1.002 and tap_c["time"] >= PAST_24H_MS:
                                        # Evaluated outcome
                                        entry = dec_top
                                        tp = entry * 1.028
                                        sl = entry * 0.972
                                        status = "IN_PLAY"
                                        for f in range(t + 1, n):
                                            if candles[f]["high"] >= tp:
                                                status = "TP_HIT"
                                                break
                                            elif candles[f]["low"] <= sl:
                                                status = "SL_HIT"
                                                break
                                        
                                        results.append({
                                            "symbol": sym,
                                            "side": "LONG",
                                            "entry": entry,
                                            "tp": tp,
                                            "sl": sl,
                                            "tap_time": datetime.fromtimestamp(tap_c["time"]/1000, IST).strftime("%Y-%m-%d %H:%M IST"),
                                            "status": status,
                                            "last_price": candles[-1]["close"]
                                        })
                                        break

            # 2. Bearish Decisional OB
            if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                lows = [c["low"] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)
                if low_idx > i + 2:
                    drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                    if drop >= 0.050:
                        idm_high = candles[low_idx - 1]["high"]
                        best_mid = -1
                        max_bg = 0.0
                        for mid in range(i+1, low_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid

                        if best_mid != -1 and best_mid + 1 < n:
                            dec_c = candles[best_mid - 1]
                            dec_top = dec_c["high"]
                            dec_bot = min(dec_c["open"], dec_c["close"])
                            has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"])
                            if has_bear_fvg:
                                for t in range(low_idx + 1, min(low_idx + 28, n)):
                                    tap_c = candles[t]
                                    if tap_c["high"] >= dec_bot * 0.998 and tap_c["time"] >= PAST_24H_MS:
                                        entry = dec_bot
                                        tp = entry * 0.972
                                        sl = entry * 1.028
                                        status = "IN_PLAY"
                                        for f in range(t + 1, n):
                                            if candles[f]["low"] <= tp:
                                                status = "TP_HIT"
                                                break
                                            elif candles[f]["high"] >= sl:
                                                status = "SL_HIT"
                                                break

                                        results.append({
                                            "symbol": sym,
                                            "side": "SHORT",
                                            "entry": entry,
                                            "tp": tp,
                                            "sl": sl,
                                            "tap_time": datetime.fromtimestamp(tap_c["time"]/1000, IST).strftime("%Y-%m-%d %H:%M IST"),
                                            "status": status,
                                            "last_price": candles[-1]["close"]
                                        })
                                        break

    # Deduplicate
    unique = []
    seen = set()
    for r in results:
        sig = (r["symbol"], r["side"], round(r["entry"], 4), r["tap_time"])
        if sig not in seen:
            seen.add(sig)
            unique.append(r)

    print(json.dumps(unique, indent=2))

if __name__ == "__main__":
    main()
