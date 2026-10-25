import urllib.request
import json
import time
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FOREX_PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "USDCAD=X",
    "USDCHF=X",
    "NZDUSD=X",
    "EURGBP=X",
    "EURJPY=X",
    "GBPJPY=X",
    "DX-Y.NYB"  # US Dollar Index DXY (Macro Sentry)
]

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_forex")
os.makedirs(OUT_DIR, exist_ok=True)

def fetch_yahoo_forex(symbol, interval):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=2y&interval={interval}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
                chart = data["chart"]["result"][0]
                timestamps = chart.get("timestamp", [])
                quotes = chart["indicators"]["quote"][0]
                opens = quotes.get("open", [])
                highs = quotes.get("high", [])
                lows = quotes.get("low", [])
                closes = quotes.get("close", [])
                volumes = quotes.get("volume", [])

                clean_candles = []
                for i in range(len(timestamps)):
                    t = timestamps[i]
                    o = opens[i] if i < len(opens) else None
                    h = highs[i] if i < len(highs) else None
                    l = lows[i] if i < len(lows) else None
                    c = closes[i] if i < len(closes) else None
                    v = volumes[i] if i < len(volumes) else 0

                    if None not in (t, o, h, l, c) and o > 0 and h > 0 and l > 0 and c > 0:
                        clean_candles.append({
                            "time": int(t * 1000),
                            "open": float(o),
                            "high": float(h),
                            "low": float(l),
                            "close": float(c),
                            "volume": float(v) if v is not None else 0.0
                        })

                clean_candles.sort(key=lambda x: x["time"])
                return clean_candles
        except Exception as e:
            time.sleep(1.0 * (attempt + 1))
    return []

def main():
    print("=" * 90)
    print(" 📥 DOWNLOADING 2-YEAR HISTORICAL REAL FOREX DATA (1H & 4H)")
    print("=" * 90)

    total_candles = 0
    clean_sym_map = {}

    for sym in FOREX_PAIRS:
        clean_name = sym.replace("=X", "").replace("-", "_").replace(".", "_")
        for interval in ["1h", "4h"]:
            candles = fetch_yahoo_forex(sym, interval)
            out_file = os.path.join(OUT_DIR, f"{clean_name}_{interval}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(candles, f)
            total_candles += len(candles)
            print(f"  • [DOWNLOADED] {clean_name:<10} ({interval}): {len(candles):>5} candles -> {out_file}")
            time.sleep(0.2)

    print("=" * 90)
    print(f"✅ Forex Data Download Complete! Total Candles: {total_candles:,}")

if __name__ == "__main__":
    main()
