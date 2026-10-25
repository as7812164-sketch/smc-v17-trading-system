import urllib.request
import json
import time
import sys
import numpy as np

# Forensic analysis of the 1H loss: SUIUSDT 2026-04-22 23:00 (timestamp: 1776898800000)
# Forensic analysis of the 4H loss: ARBUSDT 2025-11-11 20:00 (timestamp: 1762891200000)

def fetch_candles_around(symbol, interval, start_time, limit=30):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start_time}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            res = []
            for k in data:
                res.append({
                    "time": int(k[0]),
                    "date": time.strftime("%Y-%m-%d %H:%M", time.gmtime(k[0]/1000)),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "taker_buy": float(k[9])
                })
            return res
    except Exception as e:
        print("Error fetching:", e)
        return []

def run_forensic():
    print("=" * 85)
    print("                 FORENSIC POST-MORTEM: SL HITS & BREAKEVENS")
    print("=" * 85)

    # 1. Audit 1H Loss: SUIUSDT on 2026-04-22 23:00
    print("\n--- 1. AUDITING 1H LOSS: SUIUSDT (2026-04-22 23:00) ---")
    sui_candles = fetch_candles_around("SUIUSDT", "1h", 1776898800000 - 3600000 * 2, limit=25)
    btc_candles_1h = fetch_candles_around("BTCUSDT", "1h", 1776898800000 - 3600000 * 2, limit=25)
    
    if sui_candles:
        entry_p = 0.9513
        print(f"Entry Price: ${entry_p}")
        for idx, c in enumerate(sui_candles[:15]):
            high_move = (c["high"] - entry_p) / entry_p * 100
            low_move = (c["low"] - entry_p) / entry_p * 100
            close_move = (c["close"] - entry_p) / entry_p * 100
            btc_c = btc_candles_1h[idx] if idx < len(btc_candles_1h) else None
            btc_move = ((btc_c["close"] - btc_c["open"]) / btc_c["open"] * 100) if btc_c else 0.0
            print(f"  Bar +{idx} ({c['date']}): High {high_move:+.2f}% | Low {low_move:+.2f}% | Close {close_move:+.2f}% | BTC Move: {btc_move:+.2f}%")

    # 2. Audit 4H Loss: ARBUSDT on 2025-11-11 20:00
    print("\n--- 2. AUDITING 4H LOSS: ARBUSDT (2025-11-11 20:00) ---")
    arb_candles = fetch_candles_around("ARBUSDT", "4h", 1762891200000 - 14400000 * 2, limit=10)
    btc_candles_4h = fetch_candles_around("BTCUSDT", "4h", 1762891200000 - 14400000 * 2, limit=10)
    if arb_candles:
        entry_p = 0.2793
        print(f"Entry Price: ${entry_p}")
        for idx, c in enumerate(arb_candles[:8]):
            high_move = (c["high"] - entry_p) / entry_p * 100
            low_move = (c["low"] - entry_p) / entry_p * 100
            close_move = (c["close"] - entry_p) / entry_p * 100
            btc_c = btc_candles_4h[idx] if idx < len(btc_candles_4h) else None
            btc_move = ((btc_c["close"] - btc_c["open"]) / btc_c["open"] * 100) if btc_c else 0.0
            print(f"  4H Bar +{idx} ({c['date']}): High {high_move:+.2f}% | Low {low_move:+.2f}% | Close {close_move:+.2f}% | BTC Move: {btc_move:+.2f}%")

    # 3. Analyze the 36 Breakevens from 1H
    d1 = json.load(open("super_sniper_100trades_5months_ledger.json"))
    bes = [t for t in d1["trades"] if t["result"] == "BREAKEVEN"]
    print(f"\n--- 3. AUDITING 1H BREAKEVENS (Total {len(bes)} Trades) ---")
    be_bars = [t["bars_to_finish"] for t in bes]
    print(f"  Average holding duration before BE exit: {np.mean(be_bars):.1f} hours")
    print(f"  Fast BE exits (within 1-2 hours): {sum(1 for b in be_bars if b <= 2)} / {len(bes)}")
    print(f"  Slow BE exits (held 5+ hours): {sum(1 for b in be_bars if b >= 5)} / {len(bes)}")

if __name__ == "__main__":
    run_forensic()
