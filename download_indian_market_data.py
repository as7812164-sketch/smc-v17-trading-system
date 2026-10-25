import urllib.request
import json
import time
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

INDIAN_INSTRUMENTS = [
    "^NSEI",        # NIFTY 50 (Macro King)
    "^NSEBANK",     # BANK NIFTY
    "RELIANCE.NS",  # Reliance Industries
    "HDFCBANK.NS",  # HDFC Bank
    "ICICIBANK.NS", # ICICI Bank
    "INFY.NS",      # Infosys
    "TCS.NS",       # Tata Consultancy Services
    "TATAMOTORS.NS",# Tata Motors
    "SBIN.NS",      # State Bank of India
    "BHARTIARTL.NS",# Bharti Airtel
    "LT.NS",        # Larsen & Toubro
    "AXISBANK.NS"   # Axis Bank
]

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_indian_market")
os.makedirs(OUT_DIR, exist_ok=True)

def fetch_yahoo_indian(symbol, interval):
    clean_sym = urllib.parse.quote(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_sym}?range=1y&interval={interval}"
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
    print(" 📥 DOWNLOADING 1-YEAR REAL INDIAN MARKET (NSE) FUTURES & EQUITIES (1H & 4H)")
    print("=" * 90)

    total_candles = 0

    for sym in INDIAN_INSTRUMENTS:
        file_sym = sym.replace("^", "").replace(".NS", "")
        for interval in ["1h", "4h"]:
            candles = fetch_yahoo_indian(sym, interval)
            out_file = os.path.join(OUT_DIR, f"{file_sym}_{interval}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(candles, f)
            total_candles += len(candles)
            print(f"  • [DOWNLOADED] {file_sym:<12} ({interval}): {len(candles):>5} candles -> {out_file}")
            time.sleep(0.15)

    print("=" * 90)
    print(f"✅ Indian Market Data Download Complete! Total Historical Candlesticks: {total_candles:,}")

if __name__ == "__main__":
    main()
